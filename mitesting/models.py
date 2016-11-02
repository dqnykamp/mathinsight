from django.db import models
from django.contrib.auth.models import Group
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from math import *
import re
from sympy import Function, Tuple, Symbol
from django.db.models import Max
from mitesting.math_objects import math_object
from mitesting.sympy_customized import parse_expr, parse_and_process, customized_sort_key, SymbolCallable, TupleNoParen
import logging

logger = logging.getLogger(__name__)

# make sure sympification doesn't turn matrices to immutable
from sympy.core.sympify import converter as sympify_converter
from sympy import MatrixBase
sympify_converter[MatrixBase] = lambda x: x

class QuestionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return  self.name

class QuestionDatabaseManager(models.Manager):
    def get_queryset(self):
        return super(QuestionDatabaseManager, self).get_queryset() \
                                                   .filter(course=None)


class Question(models.Model):

    # spacing choices must correspond to css classes
    SPACING_CHOICES = (
        ('large3spacebelow', 'large3'),
        ('large2spacebelow', 'large2'),
        ('largespacebelow', 'large'),
        ('medlargespacebelow', 'medium large'),
        ('medspacebelow', 'medium'),
        ('smallspacebelow', 'small'),
        ('tinyspacebelow', 'tiny'),
        )
    PRIVACY_CHOICES = (
        (0, 'Public'),
        (1, 'Logged in users'),
        (2, 'Instructors only'),
        )

    name = models.CharField(max_length=200)
    question_type = models.ForeignKey(QuestionType)
    question_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,
                                           default=2)
    solution_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,
                                           default=2)
    course = models.ForeignKey('micourses.Course', blank=True, null=True)
    base_question = models.ForeignKey('self', related_name="derived_questions",
                                      blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    question_spacing = models.CharField(max_length=20, blank=True, null=True,
                                         choices=SPACING_CHOICES)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reference_pages = models.ManyToManyField('midocs.Page', 
                                             through='QuestionReferencePage',
                                             blank=True)
    allowed_sympy_commands = models.ManyToManyField('SympyCommandSet', 
                                                    blank=True)
    customize_user_sympy_commands = models.BooleanField(default=False)
    allowed_user_sympy_commands = models.ManyToManyField(
        'SympyCommandSet', related_name='question_set_user', blank=True)
    computer_graded=models.BooleanField(default=False)
    show_solution_button_after_attempts=models.IntegerField(default=0)
    keywords = models.ManyToManyField('midocs.Keyword', blank=True)
    subjects = models.ManyToManyField('midocs.Subject', blank=True)
    authors = models.ManyToManyField('midocs.Author', through='QuestionAuthor',
                                     blank=True)
    objects = models.Manager()
    question_database = QuestionDatabaseManager()

    class Meta:
        permissions = (
            ("administer_question","Can administer questions"),
        )

    def __str__(self):
        return "%s: %s" % (self.id, self.name)

    @models.permalink
    def get_absolute_url(self):
        return('miquestion:question', (), {'question_id': self.id})

    @models.permalink
    def get_solution_url(self):
        return('miquestion:questionsolution', (), {'question_id': self.id})

    def question_with_number(self):
        return "%s: %s" % (self.id, self.name)
    question_with_number.admin_order_field = 'id'
    question_with_number.short_description = "Question"

    def user_can_view(self, user, solution=True, course=None):

        if user.has_perm('mitesting.administer_question'):
            return True

        from micourses.permissions import return_user_assessment_permission_level
        permission_level=return_user_assessment_permission_level(user, course)
        privacy_level=self.return_privacy_level(solution)
        # if permission level is high enough, user can view
        if permission_level >= privacy_level:
            return True
        else:
            return False

    def return_privacy_level(self, solution=True):
        if solution:
            return self.solution_privacy
        else:
            return self.question_privacy

    def spacing_css(self):
        if self.question_spacing:
            return self.question_spacing
 
    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.questionauthor_set.all(), 
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.questionauthor_set.all(), 
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.questionauthor_set.all(), 
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.questionauthor_set.all(), 
                                include_link=include_link)

    def get_new_seed(self):
        from .utils import get_new_seed
        return get_new_seed()

    def return_sympy_local_dict(self, user_response=False):
        """
        Return dictionary containing sympy command mappings for 
        parsing expressions.
        If user_response is True and customize_sympy_user_commands is True,
        then use the commands from allowed_user_sympy_commands.
        Otherwise use commands from allowed_sympy_commands.
        """
        from .utils import return_sympy_local_dict
        if user_response and self.customize_user_sympy_commands:
            return return_sympy_local_dict(
                [a.commands for a in \
                     self.allowed_user_sympy_commands.all()])
        return return_sympy_local_dict(
            [a.commands for a in self.allowed_sympy_commands.all()])
    

    def render_javascript_commands(self, context, question=True, solution=False):
        template_string=""
        if question:
            if self.question_javascript:
                template_string += self.question_javascript
        if solution:
            if template_string:
                template_string += "\n"
            if self.solution_javascript:
                template_string += self.solution_javascript
        if template_string:
            template_string_base = "{% load question_tags mi_tags humanize %}"
            template_string = template_string_base+template_string
            try:
                t = Template(template_string)
                html_string = t.render(context)
            except TemplateSyntaxError as e:
                pass
            
            return mark_safe(html_string)
        else:
            return ""

    def save_as_new(self, course=None):
        """
        Create a new question and copy all fields to new question.

        Set course if specified.
        """

        from copy import copy

        new_q = copy(self)
        new_q.id = None

        if self.base_question:
            new_q.base_question = self.base_question
        else:
            new_q.base_question = self

        if course:
            new_q.course = course

        new_q.save()
        
        for qrp in self.questionreferencepage_set.all():
            qrp.id = None
            qrp.question = new_q
            qrp.save()
            
        for asc in self.allowed_sympy_commands.all():
            new_q.allowed_sympy_commands.add(asc)
        for ausc in self.allowed_user_sympy_commands.all():
            new_q.allowed_user_sympy_commands.add(ausc)
        for kw in self.keywords.all():
            new_q.keywords.add(kw)
        for sb in self.subjects.all():
            new_q.subjects.add(sb)

        for qa in self.questionauthor_set.all():
            qa.id = None
            qa.question = new_q
            qa.save()

        
        for qsp in self.questionsubpart_set.all():
            qsp.id = None
            qsp.question = new_q
            qsp.save()

        for qao in self.questionansweroption_set.all():
            qao.id = None
            qao.question = new_q
            qao.save()

        for expr in self.expression_set.all():
            expr.id = None
            expr.question = new_q
            expr.save()

        from mitesting.render_questions import process_expressions_from_answers
        process_expressions_from_answers(new_q)

        return new_q


    def overwrite_base_question(self):
        """
        Overwrite the base question with all fields of question
        except preserves fields: .course and .base_question
        """

        from copy import copy

        base_question = self.base_question
        if base_question is None:
            return
        
        base_q = copy(self)
        base_q.id = base_question.id
        base_q.base_question = base_question.base_question
        base_q.course = base_question.course

        base_q.save()
        
        base_q.questionreferencepage_set.all().delete()
        for qrp in self.questionreferencepage_set.all():
            qrp.id = None
            qrp.question = base_q
            qrp.save()

        base_q.allowed_sympy_commands.clear()
        for asc in self.allowed_sympy_commands.all():
            base_q.allowed_sympy_commands.add(asc)
        base_q.allowed_user_sympy_commands.clear()
        for ausc in self.allowed_user_sympy_commands.all():
            base_q.allowed_user_sympy_commands.add(ausc)
        base_q.keywords.clear()
        for kw in self.keywords.all():
            base_q.keywords.add(kw)
        base_q.subjects.clear()
        for sb in self.subjects.all():
            base_q.subjects.add(sb)

        base_q.questionauthor_set.all().delete()
        for qa in self.questionauthor_set.all():
            qa.id = None
            qa.question = base_q
            qa.save()

        base_q.questionsubpart_set.all().delete()
        for qsp in self.questionsubpart_set.all():
            qsp.id = None
            qsp.question = base_q
            qsp.save()

        base_q.questionansweroption_set.all().delete()
        for qao in self.questionansweroption_set.all():
            qao.id = None
            qao.question = base_q
            qao.save()

        base_q.expression_set.all().delete()
        for expr in self.expression_set.all():
            expr.id = None
            expr.question = base_q
            expr.save()

        from mitesting.render_questions import process_expressions_from_answers
        process_expressions_from_answers(base_q)

        return base_q

        

    def update_from_base_question(self):
        """
        Overwrite the question with all fields from base question
        except preserves fields: .course and .base_question
        """

        from copy import copy

        base_question = self.base_question
        if base_question is None:
            return
        
        new_self = copy(base_question)
        new_self.id = self.id
        new_self.base_question = base_question
        new_self.course = self.course

        new_self.save()
        
        new_self.questionreferencepage_set.all().delete()
        for qrp in base_question.questionreferencepage_set.all():
            qrp.id = None
            qrp.question = new_self
            qrp.save()

        new_self.allowed_sympy_commands.clear()
        for asc in base_question.allowed_sympy_commands.all():
            new_self.allowed_sympy_commands.add(asc)
        new_self.allowed_user_sympy_commands.clear()
        for ausc in base_question.allowed_user_sympy_commands.all():
            new_self.allowed_user_sympy_commands.add(ausc)
        new_self.keywords.clear()
        for kw in base_question.keywords.all():
            new_self.keywords.add(kw)
        new_self.subjects.clear()
        for sb in base_question.subjects.all():
            new_self.subjects.add(sb)

        new_self.questionauthor_set.all().delete()
        for qa in base_question.questionauthor_set.all():
            qa.id = None
            qa.question = new_self
            qa.save()

        new_self.questionsubpart_set.all().delete()
        for qsp in base_question.questionsubpart_set.all():
            qsp.id = None
            qsp.question = new_self
            qsp.save()

        new_self.questionansweroption_set.all().delete()
        for qao in base_question.questionansweroption_set.all():
            qao.id = None
            qao.question = new_self
            qao.save()

        new_self.expression_set.all().delete()
        for expr in base_question.expression_set.all():
            expr.id = None
            expr.question = new_self
            expr.save()

        from mitesting.render_questions import process_expressions_from_answers
        process_expressions_from_answers(new_self)

        return new_self

        

    def find_replacement_question_for_course(self, course):
        # If question is from assessment's course, return question.
        # Else, attempt the following in order
        # 1. assign a question from the course that has
        #    the original question as its base_question
        # 2. if the original question's base question is from the course
        #    then assign the base question
        # 3. assign a question from the course that has
        #    the original question's base question as its base_question
        # 4. save question as new question with that course
        #    and assign new question

        if self.course == course:
            return self

        replacement_question = self.derived_questions\
                                       .filter(course=course).first()
        if replacement_question:
            return replacement_question

        if self.base_question:
            if self.base_question.course==course:
                return self.base_question
            replacement_question = self.base_question.derived_questions\
                                                .filter(course=course).first()
            if replacement_question:
                return replacement_question

        return self.save_as_new(course=course)


class QuestionAuthor(models.Model):
    question = models.ForeignKey(Question)
    author = models.ForeignKey('midocs.Author')
    sort_order = models.FloatField(blank=True)

    class Meta:
        unique_together = ("question","author")
        ordering = ['sort_order','id']
    def __str__(self):
        return "%s" % self.author

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.question.questionauthor_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(QuestionAuthor, self).save(*args, **kwargs)


class QuestionSubpart(models.Model):
    question= models.ForeignKey(Question)
    question_spacing = models.CharField(max_length=20, blank=True, null=True,
                                        choices=Question.SPACING_CHOICES)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    sort_order = models.FloatField(blank=True)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return "subpart %s" % self.get_subpart_letter()
    
    
    class Meta:
        ordering = ['sort_order','id']
                 
    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.question.questionsubpart_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(QuestionSubpart, self).save(*args, **kwargs)

                        
    def fullcode(self):
        return "%s_%s" % (self.question.id, self.id)

    def get_subpart_letter(self):
        try:
            subpart_number = list(self.question.questionsubpart_set.all()).index(self)
            alphabet="abcdefghijklmnopqrstuvwxyz"
            return alphabet[subpart_number]
        except:
            return None

    def spacing_css(self):
        if self.question_spacing:
            return self.question_spacing




class QuestionReferencePage(models.Model):
    question = models.ForeignKey(Question)
    page = models.ForeignKey('midocs.Page')
    sort_order = models.FloatField(blank=True)
    question_subpart = models.CharField(max_length=1, blank=True,null=True)
    
    class Meta:
        unique_together = ("question", "page", "question_subpart")
        ordering = ['sort_order','id']
    def __str__(self):
        return "%s for %s" % (self.page, self.question)

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.question.questionreferencepage_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(QuestionReferencePage, self).save(*args, **kwargs)


class QuestionAnswerOption(models.Model):
    EXPRESSION = 0
    MULTIPLE_CHOICE = 1
    FUNCTION = 2
    TEXT=3
    ANSWER_TYPE_CHOICES = (
        (EXPRESSION, "Expression"),
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (FUNCTION, "Function"),
        (TEXT, "Text"),
        )
    question = models.ForeignKey(Question)
    answer_type = models.IntegerField(choices = ANSWER_TYPE_CHOICES,
                                         default = EXPRESSION)
    answer_code = models.SlugField(max_length=50)
    answer = models.CharField(max_length=400)
    percent_correct = models.IntegerField(default=100)
    feedback = models.TextField(blank=True,null=True)

    round_on_compare = models.IntegerField(blank=True, null=True)
    round_absolute = models.BooleanField(default=False)
    round_partial_credit_digits = models.IntegerField(blank=True,null=True)
    round_partial_credit_percent = models.IntegerField(blank=True,null=True)

    sign_error_partial_credit = models.BooleanField(default=False)
    sign_error_partial_credit_percent = models.IntegerField(blank=True,null=True)
    constant_term_error_partial_credit = models.BooleanField(default=False)
    constant_term_error_partial_credit_percent = models.IntegerField(blank=True,null=True)
    constant_factor_error_partial_credit = models.BooleanField(default=False)
    constant_factor_error_partial_credit_percent = models.IntegerField(blank=True,null=True)
    
    normalize_on_compare = models.BooleanField(default=False)
    split_symbols_on_compare = models.BooleanField(default=True)
    match_partial_on_compare = models.BooleanField(default=False)

    sort_order = models.FloatField(blank=True)

    class Meta:
        ordering = ['sort_order','id']

    def __str__(self):
        return  "code: %s, answer: %s" % (self.answer_code, self.answer)

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.question.questionansweroption_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(QuestionAnswerOption, self).save(*args, **kwargs)


    def render_feedback(self, expr_context):
        if not self.feedback:
            return ""
        template_string = "{% load question_tags mi_tags humanize %}"
        template_string += self.feedback
        try:
            t = Template(template_string)
            return mark_safe(t.render(expr_context))
        except TemplateSyntaxError as e:
            logger.warning("Error in feedback for answer option with "
                           + " code = %s: %s"
                           % (self.answer_code, self))
            return ""

        
class Expression(models.Model):
    RANDOM_NUMBER = "RN"
    RANDOM_WORD = "RW"
    RANDOM_EXPRESSION = "RE"
    RANDOM_FUNCTION_NAME = "RF"
    FUNCTION = "FN"
    FUNCTION_NAME = "FE"
    UNSPLIT_SYMBOL = "US"
    CONDITION = "CN"
    GENERIC = "EX"
    UNORDERED_TUPLE = "UT"
    SORTED_TUPLE = "ST"
    RANDOM_ORDER_TUPLE = "RT"
    INTERVAL = "IN"
    SET = "SE"
    EXPRESSION_WITH_ALTERNATES = "EA"
    MATRIX="MX"
    VECTOR="VC"
    EXPRESSION_TYPES = (
        ('General', (
            (GENERIC, "Generic"),
            (RANDOM_NUMBER, "Rand number"),
            (FUNCTION, "Function"),
            (FUNCTION_NAME, "Function name"),
            (UNSPLIT_SYMBOL, "Unsplit symbol"),
            (CONDITION, "Required cond"),
        )
     ),
        ('Random from list', (
            (RANDOM_WORD, "Rand word"),
            (RANDOM_EXPRESSION, "Rand expr"),
            (RANDOM_FUNCTION_NAME, "Rand fun name"),
        )
     ),
        ('Tuples and sets', (
            (UNORDERED_TUPLE, "Unordered tuple"),
            (SORTED_TUPLE, "Sorted tuple"),
            (RANDOM_ORDER_TUPLE, "Rand order tuple"),
            (SET, "Set"),
            (INTERVAL, "Interval"),
            (EXPRESSION_WITH_ALTERNATES, "Expr w/ alts"),
        )
     ),
        ('Matrix and vector', (
            (MATRIX, "Matrix"),
            (VECTOR, "Vector"),
        )
     ),
    )

    from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL,\
        EVALUATE_FULL

    EVALUATE_CHOICES = (
        (EVALUATE_NONE, "None"),
        (EVALUATE_PARTIAL, "Partial"),
        (EVALUATE_FULL, "Full")
        )


    name = models.SlugField(max_length=50)
    expression_type = models.CharField(
        max_length=2, choices = EXPRESSION_TYPES, default=GENERIC)
    expression = models.CharField(max_length=1000)
    evaluate_level = models.IntegerField(choices = EVALUATE_CHOICES,
                                         default = EVALUATE_FULL)
    question = models.ForeignKey(Question)
    function_inputs = models.CharField(max_length=50, blank=True,
                                       null=True)
    random_list_group = models.CharField(max_length=50, blank=True, null=True)
    real_variables = models.BooleanField(default=True)
    parse_subscripts = models.BooleanField(default=False)
    post_user_response = models.BooleanField(default=False)
    sort_order = models.FloatField(blank=True)
    class Meta:
        ordering = ['post_user_response','sort_order','id']

    class FailedCondition(Exception):
        pass

    def __str__(self): 
        return  self.name

    def save(self, *args, **kwargs):
        # if sort_order is nul, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.question.expression_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(Expression, self).save(*args, **kwargs)


    def evaluate(self, rng, local_dict=None, user_dict=None,
                 alternate_dicts=[], 
                 random_group_indices=None,
                 random_outcomes={}):
        """
        Returns dictionary of evaluated expression and alternate forms.
        Keys:
        - expression_evaluated: the expression evaluated against local_dict
        - alternate_exprs: if alternate_dicts passed in or expression is
          an EXPRESSION_WITH_ALTERNATES, a list of alternate versions
          of the evaluated expression
        - alternate_funcs: if alternate_dicts passed in and expression is
          a FUNCTION, a list of alternate versions of the function

        Add result to local_dict and user_dict:
        Add sympy version of result to local_dict with key self.name.
        If result is a function name that user may enter to answer 
        question, then add function to user_dict.

        If alternate_dicts passed, each dict is treated as local_dict
        and sympy version is added with key self.name.
        In addition, if expression is an EXPRESSION_WITH_ALTERNATES,
        additional dictionaries are added to alternate_dicts.


        Result is calculated based on expression_type.

        In all cases, except RANDOM_WORD, the expression is first
        parsed with sympy, making the substitution from local_dict. 
        The resulting math_object returned. The sympy expression is
        added to local_dict[self.name] so that its value will
        be substituted in following expressions.
        
        If error occurs, add Symbol("??") to local_dict,
        don't add to user_dict, and raise an exception

        For entries selected randomly from lists,
        (RANDOM_WORD, RANDOM_EXPRESSION, RANDOM_FUNCTION_NAME),
        the dictionary random_group_indices is used to keep
        track of indices used for random_list_groups so that
        the same item number is chosen from each list in the group.

        The evaluate_level field of Expression specifies to what except
        the input is processed.
            Options are
            EVALUATE_NONE: expression is left as much as possible 
            in original form. Term and factors are reordered but not combined.
            EVALUATE_PARTIAL: Expression is simplified using standard sympy
            conventions.  E.g. like terms are combined, repeated factors
            are combined to powers.
            EVALUATE_FULL: .doit() is called on expression to evaluate
            all commands, such as derivatives and integrals
            
            
        expression_type specific information
        ------------------------------------
        GENERIC
        The generic expression form.  The expression field
        must be a mathematical expression.

        Expression in the form  of
        e1, e2, ...  or (e1, e2, ...)
        or [e1, e2, ... ]  or {e1, e2, ... }
        will result in a TupleNoParen, Tuple, list, or set, respectively.
        With the exception of the set, the result will be considered ordered
        when compared with other expressions

        RANDOM_NUMBER
        Expression should be in the form (minval, maxvalue [, increment])
        where minval is the minimum value and maxvalue is the maximum
        value of the random number.  Random number is sampled uniformly
        from the values minval + i*increment, for integer i, that are
        between minval and maxvalue.  If optional value increment
        is missing it is set to 1.
        
        RANDOM_WORD
        Expression should be in the form: w1, w2, ...
        where the ws list the possible words, which are sampled
        from uniformly.  Each word can be either in the form
        singular_form
        or in the form
        (singular_form, plural_form)
        In the case where just the singular form is specified, 
        the plural form is created by adding an "s".
        Each singular_form or plural_form can be either
        a single word or a quoted phrase.
        For random words, a tuple is returned of the form
        (singular form, plural_form).
        If the singular form can be successfully converted to 
        a sympy Symbol(), then it is added to local_dict[self.name].
        
        RANDOM_EXPRESSION
        Expression should be a list of expressions of the form
        e1, e2, ....
        where each "e" can be any legal mathematical expression.

        FUNCTION_NAME
        Expression should must parse to a single Symbol() 
        (multiple characters are fine).  
        The function name "f" will then be treated as undefined function
        so that f(x) is function evaluation, not multiplication
        Expression is added to user dictionary so will act as undefined function
        in answers
        
        UNSPLIT_SYMBOL
        Expression should must parse to a single Symbol() 
        (multiple characters are fine).  
        Expression is added to user dictionary so will act as an unsplit symbol
        in answers

        RANDOM_FUNCTION_NAME
        Expression should be a list of expressions of the form
        f1, f2, ....
        where each "f" must parse to a single Symbol() 
        (multiple characters are fine).  
        The function name chosen will then be treated as undefined function
        so that f(x) is function evaluation, not multipliation
        Expression is added to user dictionary so will act as undefined function
        in answers

        FUNCTION
        The expression field must be a mathematical expression
        and the function inputs field must be a tuple of symbols.
        The expression will be then viewed as a function of the
        function input symbol(s). 
        A math object containing the evaluated expression 
        is returned, so it is displayed like a GENERIC.
        However, a function with inpues given by function_inputs
        is added to local_dict.  In this way, when included in 
        subsequent expressions, the expression
        will act like a function, with the values of the 
        function input symbol(s) being replaced by the arguments
        of the function.  (It cannot be included in other expressions
        without the arguments being supplied.)

        CONDITION
        Parsed like a GENERIC.  If it does not evaluate
        to true, an Expression.FailedCondition exception is raised.

        UNORDERED_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...) or [e1, e2, ... ]
        which will result in a TupleNoParen, Tuple, or list, respectively
        The tuple is considered unordered so that it will
        compare as equivalent to another tuple if both tuples
        contain the same elements regardless of order.

        SORTED_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...) or [e1, e2, ... ]
        which will result in a TupleNoParen, Tuple, or list, respectively
        The elements in the tuple are sorted using customized_sort_key
        which attempts to all expression that are real numbers like numbers

        RANDOM_ORDER_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...) or [e1, e2, ... ]
        which will result in a TupleNoParen, Tuple, or list, respectively
        The order of the elements is randomized.

        SET
        If expression is a tuple of the form e1, e2, ...
        it is converted to a set to remove duplicate entries,
        after which it is treaded like an UNORDERED_TUPLE

        INTERVAL
        Expressions of the form (a,b), (a,b], [a,b), and [a,b]
        are converted to intervals as long as the limits are real variables

        EXPRESSION_WITH_ALTERNATES
        Expression should be a tuple of the form e1, e2, ...
        The first expression e1 will be used when displaying the expression
        unless the alt template filter is used to select an alternative.
        When used in later expressions, all alternate forms are tracked,
        including combinates of different alternates.
        When used in an answer option, any of the alternates forms 
        will be deemed correct.

        MATRIX
        Expression must be in the form 
        a b c
        d e f
        g h i
        which is converted into a matrix.  
        Spaces are the column delimiters.
        Newlines are the row delimiters.

        VECTOR
        Any Tuples (not TupleNoParens) are converted to column Matrices
        so that matrix vector-multiplication works.


        """
        
        from mitesting.utils import evaluate_expression

        new_alternate_dict_list=[]
        new_alternate_expr_list=[]
        new_alternate_func_list=[]
        try:
            if self.post_user_response:
                # cannot have a required condition as a post user reponse
                if self.expression_type == self.CONDITION:
                   raise ValueError("Cannot have a required condition be flagged as post user response")

            new_alternate_dicts_sub=[]
            new_alternate_exprs_sub=[]

            expression_evaluated= evaluate_expression(
                self, rng=rng,
                local_dict=local_dict,
                user_dict=user_dict,
                random_group_indices=random_group_indices,
                new_alternate_dicts=new_alternate_dicts_sub,
                new_alternate_exprs=new_alternate_exprs_sub,
                random_outcomes=random_outcomes)

            new_alternate_dict_list.append(new_alternate_dicts_sub)
            new_alternate_expr_list.append(new_alternate_exprs_sub)
            max_alt_length=len(new_alternate_dicts_sub)

            results = {'expression_evaluated': expression_evaluated}

        # no additional processing for FailedCondition
        except self.FailedCondition:
            raise
        # on any other exception, add "??" to  local_dict for self.name
        # add name of expression to error message
        except Exception as exc:
            # don't want to raise another exception 
            # so test if local_dict is a dictionary rather
            # than just trying to assign
            if isinstance(local_dict, dict):
                local_dict[self.name] = Symbol('??')

            import sys
            raise exc.__class__("Error in expression: %s<br/>%s" \
                % (self.name, exc)).with_traceback(sys.exc_info()[2])

        # if have alternate dictionaries, 
        alternate_exprs=[]
        alternate_funcs=[]
        for alt_dict in alternate_dicts:
            try:
                # since random outcomes were set in original version
                # will get same random selections with alternate dicts.
                # (rng shouldn't be used)
                
                new_alternate_dicts_sub=[]
                new_alternate_exprs_sub=[]
                
                # The alt_dict gets modified in place.
                # Append new evaluated expression to alternate_expr
                expression_evaluated_sub= evaluate_expression(
                    self, rng=rng,
                    local_dict=alt_dict,
                    user_dict=user_dict,
                    random_group_indices=random_group_indices,
                    new_alternate_dicts=new_alternate_dicts_sub,
                    new_alternate_exprs=new_alternate_exprs_sub,
                    random_outcomes=random_outcomes)

                if expression_evaluated_sub != expression_evaluated \
                   and expression_evaluated_sub not in alternate_exprs:
                    alternate_exprs.append(expression_evaluated_sub)

                    if self.expression_type==self.FUNCTION:
                        try:
                            alternate_funcs.append(alt_dict[self.name])
                        except KeyError:
                            pass

                # If additional alternates are created,
                # they are appended to new list of lists
                new_alternate_dict_list.append(new_alternate_dicts_sub)
                new_alternate_expr_list.append(new_alternate_exprs_sub)
                max_alt_length=max(max_alt_length,
                                   len(new_alternate_dicts_sub))

            except:
                pass
        
        # Append any new alts to original alternate lists.
        # Order so that for each new alternate, all original
        # alternates are included sequentially
        for ind in range(max_alt_length):
            for alt_list in new_alternate_dict_list:
                try:
                    alternate_dicts.append(alt_list[ind])
                except IndexError:
                    pass
            for alt_list in new_alternate_expr_list:
                try:
                    ae=alt_list[ind]
                    if ae not in alternate_exprs:
                        alternate_exprs.append(ae)
                except IndexError:
                    pass
        
        results['alternate_exprs'] = alternate_exprs
        results['alternate_funcs'] = alternate_funcs

        return results


class ExpressionFromAnswer(models.Model):
    name = models.SlugField(max_length=100)
    question = models.ForeignKey(Question)
    answer_code = models.SlugField(max_length=50)
    answer_number = models.IntegerField()
    split_symbols_on_compare = models.BooleanField(default=True)
    answer_type = models.IntegerField(default=QuestionAnswerOption.EXPRESSION,
                                      null=True)
    answer_data = models.TextField(null=True)
    real_variables = models.BooleanField(default=True)
    parse_subscripts = models.BooleanField(default=True)
    default_value = models.CharField(max_length=20, default="_long_underscore_")

    class Meta:
        unique_together = ("name", "question","answer_number")
    
    def __str__(self): 
        return  self.name


class SympyCommandSet(models.Model):
    name = models.CharField(max_length=50, unique=True)
    commands = models.TextField()
    default = models.BooleanField(default=False)
    def __str__(self):
        return self.name
