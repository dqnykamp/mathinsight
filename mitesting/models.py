from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.contrib.auth.models import Group
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from math import *
from mitesting.permissions import return_user_assessment_permission_level
import re
from sympy import Symbol, Function, Tuple, expand
from django.db.models import Max
from mitesting.math_objects import math_object
from mitesting.sympy_customized import parse_expr, parse_and_process, customized_sort_key, SymbolCallable
import six

@python_2_unicode_compatible
class QuestionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return  self.name
   
@python_2_unicode_compatible
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
    description = models.CharField(max_length=400,blank=True, null=True)
    question_spacing = models.CharField(max_length=20, blank=True, null=True,
                                         choices=SPACING_CHOICES)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reference_pages = models.ManyToManyField('midocs.Page', 
                                             through='QuestionReferencePage')
    allowed_sympy_commands = models.ManyToManyField('SympyCommandSet', 
                                                    blank=True, null=True)
    customize_user_sympy_commands = models.BooleanField(default=False)
    allowed_user_sympy_commands = models.ManyToManyField(
        'SympyCommandSet', blank=True, null=True,
        related_name='question_set_user')
    computer_graded=models.BooleanField(default=False)
    show_solution_button_after_attempts=models.IntegerField(default=3)
    keywords = models.ManyToManyField('midocs.Keyword', blank=True, null=True)
    subjects = models.ManyToManyField('midocs.Subject', blank=True, null=True)
    authors = models.ManyToManyField('midocs.Author', through='QuestionAuthor')


    def __str__(self):
        return "%s: %s" % (self.id, self.name)

    @models.permalink
    def get_absolute_url(self):
        return('mit-question', (), {'question_id': self.id})

    @models.permalink
    def get_solution_url(self):
        return('mit-questionsolution', (), {'question_id': self.id})

    def question_with_number(self):
        return "%s: %s" % (self.id, self.name)
    question_with_number.admin_order_field = 'id'
    question_with_number.short_description = "Question"

    def user_can_view(self, user, solution=True):
        permission_level=return_user_assessment_permission_level(user)
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

    def render(*args, **kwargs):
        from .render_assessments import render_question
        return render_question(*args, **kwargs)

    def get_new_seed(self):
        from .render_assessments import get_new_seed
        return get_new_seed()

    def return_sympy_global_dict(self, user_response=False):
        """
        Return dictionary containing sympy command mappings for 
        parsing expressions.
        If user_response is True and customize_sympy_user_commands is True,
        then use the commands from allowed_user_sympy_commands.
        Otherwise use commands from allowed_sympy_commands.
        """
        from .utils import return_sympy_global_dict
        if user_response and self.customize_user_sympy_commands:
            return return_sympy_global_dict(
                [a.commands for a in \
                     self.allowed_user_sympy_commands.all()])
        return return_sympy_global_dict(
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
            template_string_base = "{% load testing_tags mi_tags humanize %}"
            template_string = template_string_base+template_string
            try:
                t = Template(template_string)
                html_string = t.render(context)
            except TemplateSyntaxError as e:
                pass
            
            return mark_safe(html_string)
        else:
            return ""

@python_2_unicode_compatible
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


@python_2_unicode_compatible
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




@python_2_unicode_compatible
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


@python_2_unicode_compatible
class QuestionAnswerOption(models.Model):
    EXPRESSION = 0
    MULTIPLE_CHOICE = 1
    ANSWER_TYPE_CHOICES = (
        (EXPRESSION, "Expression"),
        (MULTIPLE_CHOICE, "Multiple Choice"),
        )
    question = models.ForeignKey(Question)
    answer_type = models.IntegerField(choices = ANSWER_TYPE_CHOICES,
                                         default = EXPRESSION)
    answer_code = models.SlugField(max_length=50)
    answer = models.CharField(max_length=400)
    percent_correct = models.IntegerField(default=100)
    feedback = models.TextField(blank=True,null=True)

    normalize_on_compare = models.BooleanField(default=False)
    split_symbols_on_compare = models.BooleanField(default=True)
    match_partial_tuples_on_compare = models.BooleanField(default=False)

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
        template_string = "{% load testing_tags mi_tags humanize %}"
        template_string += self.feedback
        try:
            t = Template(template_string)
            return mark_safe(t.render(expr_context))
        except TemplateSyntaxError as e:
            logger.warning("Error in feedback for answer option with "
                           + " code = %s: %s"
                           % (self.answer_code, self))
            return ""


@python_2_unicode_compatible
class AssessmentType(models.Model):
    PRIVACY_CHOICES = (
        (0, 'Public'),
        (1, 'Logged in users'),
        (2, 'Instructors only'),
        )

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    assessment_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES, 
                                             default=2)
    solution_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,
                                                default=2)
    template_base_name = models.CharField(max_length=50, blank=True, null=True)
    record_online_attempts = models.BooleanField(default=True)
    
    def __str__(self):
        return  self.name

@python_2_unicode_compatible
class Assessment(models.Model):
    code = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=30, blank=True)
    assessment_type = models.ForeignKey(AssessmentType)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    questions = models.ManyToManyField(Question, through='QuestionAssigned')
    instructions = models.TextField(blank=True, null=True)
    instructions2 = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    time_limit = models.CharField(max_length=20, blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    groups_can_view = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view")
    groups_can_view_solution = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view_solution")
    background_pages = models.ManyToManyField('midocs.Page', through='AssessmentBackgroundPage')
    allow_solution_buttons = models.BooleanField(default=True)
    fixed_order = models.BooleanField(default=False)
    nothing_random = models.BooleanField(default=False)
    total_points = models.FloatField(blank=True, null=True)

    def __str__(self):
        return  self.name

    def return_short_name(self):
        if self.short_name:
            return self.short_name
        else:
            return self.name

    def get_title(self):
        return self.name

    def annotated_title(self):
        return "%s: %s" % (self.assessment_type.name,self.name)

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "assessment")

        direct = kwargs.get("direct")
        if direct:
            link_url = self.get_absolute_url()
        
            seed = kwargs.get("seed",None)
            if seed is not None:
                link_url += "?seed=%s" % seed
        else:
            link_url = self.get_overview_url()

        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))


    def return_direct_link(self, **kwargs):
        kwargs['direct']=True
        if not self.nothing_random:
            kwargs['seed']=1
        return self.return_link(**kwargs)

    def return_direct_link_no_seed(self, **kwargs):
        kwargs['direct']=True
        kwargs['seed']=None
        return self.return_link(**kwargs)

    @models.permalink
    def get_absolute_url(self):
        return('mit-assessment', (), {'assessment_code': self.code})

    @models.permalink
    def get_overview_url(self):
        return('mit-assessmentoverview', (), {'assessment_code': self.code})

    @models.permalink
    def get_solution_url(self):
        return('mit-assessmentsolution', (), {'assessment_type': self.assessment_type.code, 'assessment_code': self.code})

    class Meta:
        permissions = (
            ("administer_assessment","Can administer assessments"),
        )

    def get_new_seed(self):
        from .render_assessments import get_new_seed
        return get_new_seed()

    def get_active_thread_content_set(self):
        return self.thread_content_set.filter(section__thread__active=True)

    def user_can_view(self, user, solution=True, include_questions=True):
        permission_level=return_user_assessment_permission_level(user)
        privacy_level=self.return_privacy_level(
            solution=solution, include_questions=include_questions)
        # if permission level is high enough, user can view
        if permission_level >= privacy_level:
            return True
        
        # else check if user is in one of the groups 
        allowed_users=self.return_users_of_groups_can_view(solution)
        if user in allowed_users:
            return True
        else:
            return False

    def return_users_of_groups_can_view(self, solution=False):
        if solution:
            allowed_groups= self.groups_can_view_solution.all()
        else:
            allowed_groups= self.groups_can_view.all()
        allowed_users = []
        for group in allowed_groups:
            allowed_users += list(group.user_set.all())
        return allowed_users

    def return_privacy_level(self, solution=True, include_questions=True):
        # privacy level is max of privacy level from assessment type
        # and (if include_questions==True) all question sets
        if solution:
            privacy_level = self.assessment_type.solution_privacy
        else:
            privacy_level = self.assessment_type.assessment_privacy
        if include_questions:
            for question in self.questions.all():
                privacy_level = max(privacy_level, 
                                    question.return_privacy_level(solution))
        return privacy_level
    
    def privacy_level_description(self, solution=False):
        """
        Returns description of the privacy of the assessment or solution.
        using the words of the PRIVACY_CHOICES from AssessmentType.
        Also includes statements alerting to the following situations:
        - If the privacy level was increased from that of the assessment type
          due to a higher privacy level associated with a question
        - If a privacy override will allow some groups to view a non-public
          assessment or solution.
        """
        privacy_level = self.return_privacy_level(solution=solution)
        privacy_description= AssessmentType.PRIVACY_CHOICES[privacy_level][1]
        privacy_description_addenda = []
        if privacy_level > self.return_privacy_level(solution=solution, 
                                                     include_questions=False):
            privacy_description_addenda.append(
                "increased due to an assigned question")
        
        if (solution and self.groups_can_view_solution.exists()) or \
                (not solution and self.groups_can_view.exists()):
            if privacy_level > 0:
                privacy_description_addenda.append("overridden for some groups")

        if privacy_description_addenda:
            privacy_description += " (%s)" %\
                ", ".join(privacy_description_addenda)
        
        return privacy_description
    privacy_level_description.short_description = "Assessment privacy"


    def privacy_level_solution_description(self):
        return self.privacy_level_description(solution=True)
    privacy_level_solution_description.short_description = "Solution privacy"

    def render_instructions(self):
        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base + self.instructions
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions template: %s" % e

    def render_instructions2(self):
        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base + self.instructions2
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions2 template: %s" % e


    def question_sets(self):
        question_set_dicts= self.questionassigned_set.order_by('question_set').values('question_set').distinct()
        question_sets = []
        for question_set_dict in question_set_dicts:
            question_sets.append(question_set_dict['question_set'])
        return question_sets


    def points_of_question_set(self, question_set):
        try:
            question_detail=self.questionsetdetail_set.get(
                question_set=question_set)
            return question_detail.points
        except ObjectDoesNotExist:
            return None

    def get_total_points(self):
        if self.total_points is None:
            total_points=0
            for question_set in self.question_sets():
                the_points = self.points_of_question_set(question_set)
                if the_points:
                    total_points += the_points
            return total_points
        else:
            return self.total_points


    def avoid_question_seed(self, avoid_list, start_seed=0):
        
        avoid_list = [item.strip() for item in avoid_list.split(",")]
        
        try:
            start_seed = int(start_seed)
        except:
            start_seed=0

        question_sets = self.question_sets()

        # form allowable sets of questions for each set
        allowed_question_lists = []

        for question_set in question_sets:
            questions_in_set = [q.question for q in self.questionassigned_set.filter(question_set=question_set)]

            # make list of all questions that are not in avoid list
            allowed_questions = [q for q in questions_in_set if str(q.id) not in avoid_list]

            # if removed all questions, but back all questions in set
            if len(allowed_questions) == 0:
                allowed_questions=list(questions_in_set)
                
            allowed_question_lists.append(allowed_questions)
            

        min_disallowed_questions=1000
        seed_min_disallowed=None

        import random
        rng=random.Random()

        from .render_assessments import get_question_list

        for seed in range(start_seed, start_seed+1000):

            rng.seed(str(seed))
            question_list=get_question_list(self, rng=rng)

            number_disallowed_questions=0

            for (i, question_set) in enumerate(question_sets):
                if not question_list[i]['question'] \
                   in allowed_question_lists[i]:
                    number_disallowed_questions += 1
            
            if number_disallowed_questions < min_disallowed_questions:
                min_disallowed_questions = number_disallowed_questions
                seed_min_disallowed = seed
            
            if  min_disallowed_questions==0:
                break

        return seed_min_disallowed
                    

@python_2_unicode_compatible
class AssessmentBackgroundPage(models.Model):
    assessment = models.ForeignKey(Assessment)
    page = models.ForeignKey('midocs.Page')
    sort_order = models.FloatField(blank=True)

    class Meta:
        ordering = ['sort_order']
    def __str__(self):
        return "%s for %s" % (self.page, self.assessment)

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.assessment.assessmentbackgroundpage_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(AssessmentBackgroundPage, self).save(*args, **kwargs)

@python_2_unicode_compatible
class QuestionSetDetail(models.Model):
    assessment = models.ForeignKey(Assessment)
    question_set = models.SmallIntegerField(default=0,db_index=True)
    points = models.FloatField(default=0)
    group = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ("assessment", "question_set")
    def __str__(self):
        return "%s for %s" % (self.question_set, self.assessment)


@python_2_unicode_compatible
class QuestionAssigned(models.Model):
    assessment = models.ForeignKey(Assessment)
    question = models.ForeignKey(Question)
    question_set = models.SmallIntegerField(blank=True)

    class Meta:
        verbose_name_plural = "Questions assigned"
        ordering = ['question_set', 'id']
    def __str__(self):
        return "%s for %s" % (self.question, self.assessment)

    def save(self, *args, **kwargs):
        # and the question set is null
        # make it be a unique question set,
        # i.e., one more than any other in the assessment
        if self.question_set is None:
            max_question_set = self.assessment.questionassigned_set.aggregate(Max('question_set'))
            max_question_set = max_question_set['question_set__max']
            if max_question_set:
                self.question_set = max_question_set+1
            else:
                self.question_set = 1
                
        super(QuestionAssigned, self).save(*args, **kwargs)

        
@python_2_unicode_compatible
class Expression(models.Model):
    RANDOM_NUMBER = "RN"
    RANDOM_WORD = "RW"
    RANDOM_EXPRESSION = "RE"
    RANDOM_FUNCTION_NAME = "RF"
    FUNCTION = "FN"
    FUNCTION_NAME = "FE"
    CONDITION = "CN"
    EXPRESSION = "EX"
    ORDERED_TUPLE = "OT"
    UNORDERED_TUPLE = "UT"
    SORTED_TUPLE = "ST"
    RANDOM_ORDER_TUPLE = "RT"
    EXPRESSION_TYPES = (
        ('General', (
                (EXPRESSION, "Expression"),
                (RANDOM_NUMBER, "Rand number"),
                (FUNCTION, "Function"),
                (FUNCTION_NAME, "Function name"),
                (CONDITION, "Required cond"),
                )
         ),
        ('Random from list', (
                (RANDOM_WORD, "Rand word"),
                (RANDOM_EXPRESSION, "Rand expr"),
                (RANDOM_FUNCTION_NAME, "Rand fun name"),
                )
         ),
        ('Tuples', (
                (ORDERED_TUPLE, "Ordered tuple"),
                (UNORDERED_TUPLE, "Unordered tuple"),
                (SORTED_TUPLE, "Sorted tuple"),
                (RANDOM_ORDER_TUPLE, "Rand order tuple"),
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
        max_length=2, choices = EXPRESSION_TYPES, default=EXPRESSION)
    expression = models.CharField(max_length=1000)
    expand = models.BooleanField(default=False)
    evaluate_level = models.IntegerField(choices = EVALUATE_CHOICES,
                                         default = EVALUATE_FULL)
    n_digits = models.IntegerField(blank=True, null=True,
                                   verbose_name = "signif digits")
    round_decimals = models.IntegerField(blank=True, null=True,
                                         verbose_name = "round")
    question = models.ForeignKey(Question)
    function_inputs = models.CharField(max_length=50, blank=True,
                                       null=True)
    use_ln = models.BooleanField(default=False)

    collapse_equal_tuple_elements=models.BooleanField(
        default=False, verbose_name="elim dup tuple els")
    output_no_delimiters = models.BooleanField(
        default=False, verbose_name="no delims")
    group = models.CharField(max_length=50, blank=True, null=True)
    sort_order = models.FloatField(blank=True)
    class Meta:
        ordering = ['sort_order','id']

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


    def evaluate(self, rng, global_dict=None, user_function_dict=None,
                 random_group_indices=None):
        """
        Return evaluated expression and add result to dicts.
        Add sympy version of result to global_dict with key self.name.
        If result is a function name that user may enter to answer 
        question, then add function to user_function_dict.

        Result is calculated based on expression_type.

        In all cases, except RANDOM_WORD, the expression is first
        parsed with sympy, making the substitution from global_dict. 
        The resulting math_object returned. The sympy expression is
        added to global_dict[self.name] so that its value will
        be substituted in following expressions.
        
        If error occurs, add Symbol("??") to global_dict,
        don't add to user_function_dict, and raise an exception

        For entries selected randomly from lists,
        (RANDOM_WORD, RANDOM_EXPRESSION, RANDOM_FUNCTION_NAME),
        the dictionary random_group_indices is used to keep
        track of indices used for groups so that the same item number
        is chosen from each list in the group.

        The following fields of Expression modify the returned result:
        expand: if true, call .expand() on the expression or 
           on each expression in a tuple
        n_digits: on display or comparison with other expression,
           round all numbers and number symbols in expression
           to n_digits significant digits
        round_decimals: on display or comparison with other expression,
           round all numbers and number symbols in expression
           to round_decimals digits to right of decimal or,
           if negative, |round_digits| to left of decimal.
           If round_decimals <=0, also convert to integer
        use_ln: if true, display all logarithms as ln(),
           otherwise, display all logarithms as log()
           (Entering logarithms as ln() or log() makes no difference.)
        collapse_equal_tuple_elements: it true, then
            when expression is a tuple and multiple elements
            are equal, remove the duplicates elements.
            If results is a single element, convert to singleton element.
        output_no_delimiters: if true, and expression is a tuple,
            display as comma separated values 
            rather than with parentheses.
        evaluate_level: specify to what except the input is processed.
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
        EXPRESSION
        The generic expression form.  The expression field
        must be a mathematical expression.

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
        a sympy Symbol(), then it is added to global_dict[self.name].
        
        RANDOM_EXPRESSION
        Expression should be a list of expressions of the form
        e1, e2, ....
        where each "e" can be any legal mathematical expression.

        FUNCTION_NAME
        Expression should must parse to a single Symbol() 
        (multiple characters are fine).  
        The function name "f" will then be treated as undefined function
        so that f(x) is function evaluation, not multipliation
        
        RANDOM_FUNCTION_NAME
        Expression should be a list of expressions of the form
        f1, f2, ....
        where each "f" must parse to a single Symbol() 
        (multiple characters are fine).  
        The function name chosen will then be treated as undefined function
        so that f(x) is function evaluation, not multipliation

        FUNCTION
        The expression field must be a mathematical expression
        and the function inputs field must be a tuple of symbols.
        The expression will be then viewed as a function of the
        function input symbol(s). 
        A math object containing the evaluated expression 
        is returned, so it is displayed like a generic EXPRESSION.
        However, a function with inpues given by function_inputs
        is added to global_dict.  In this way, when included in 
        subsequent expressions, the expression
        will act like a function, with the values of the 
        function input symbol(s) being replaced by the arguments
        of the function.  (It cannot be included in other expressions
        without the arguments being supplied.)

        CONDITION
        Parsed like a generic EXPRESSION.  If it does not evaluate
        to true, an Expression.FailedCondition exception is raised.
        
        ORDERED_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...)
        The tuple is considered ordered so that it will
        compare as equivalent to another tuple only if
        the elements appear in the same order.
        ORDERED_TUPLE is treated identical to EXPRESSION
        except that a list is converted to a Tuple.

        UNORDERED_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...)
        The tuple is considered unordered so that it will
        compare as equivalent to another tuple if both tuples
        contain the same elements regardless of order.

        SORTED_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...)
        The elements in the tuple are sorted using
        Sympy conventions for sorting, after which the tuple
        is treated like an ORDERED_TUPLE

        RANDOM_ORDER_TUPLE
        Expression should be a tuple of the form e1, e2, ...
        or (e1, e2, ...)
        The order of the elements is randomized, after which the tuple
        is treated like an ORDERED_TUPLE

        """

    
        from mitesting.utils import return_random_number_sample, \
            return_random_expression, return_random_word_and_plural, \
            return_parsed_function
        from mitesting.sympy_customized import bottom_up
        from sympy.parsing.sympy_tokenize import TokenError
        from sympy.core.function import UndefinedFunction

        try:
            # if randomly selecting from a list,
            # determine if the index for the group was chosen already
            if self.expression_type in [self.RANDOM_WORD,
                                        self.RANDOM_EXPRESSION,
                                        self.RANDOM_FUNCTION_NAME]:
                
                if self.group:
                    try:
                        group_index = random_group_indices.get(self.group)
                    except AttributeError:
                        group_index = None
                else:
                    group_index = None

                # treat RANDOM_WORD as special case
                # as it involves two output and hasn't been
                # parsed by sympy
                # Complete all processing and return
                if self.expression_type == self.RANDOM_WORD:
                    try:
                        result = return_random_word_and_plural( 
                            self.expression, index=group_index, rng=rng)
                    except IndexError:
                        raise IndexError("Insufficient entries for group: " \
                                             + self.group)

                    # record index chosen for group, if group exist
                    if self.group:
                        try:
                            random_group_indices[self.group]=result[2]
                        except TypeError:
                            pass

                    # attempt to add word to global dictionary
                    word_text=re.sub(' ', '_', result[0])
                    sympy_word = Symbol(word_text)
                    try:
                        global_dict[self.name]=sympy_word
                    except TypeError:
                        pass
                    
                    return (result[0], result[1])
                

                if self.expression_type == self.RANDOM_FUNCTION_NAME:
                    try:
                        (math_expr, index) = return_random_expression(
                            self.expression, index=group_index,
                            global_dict=global_dict,
                            evaluate_level = self.evaluate_level, rng=rng)
                    except IndexError:
                        raise IndexError("Insufficient entries for group: " \
                                             + self.group)
                    

                    # math_expr should be a Symbol or an UndefinedFunction
                    # otherwise not a valid function name
                    if not (isinstance(math_expr,Symbol) or
                            isinstance(math_expr,UndefinedFunction)):
                        raise ValueError("Invalid function name: %s " \
                                         % math_expr)


                    # turn to SymbolCallable and add to user_function_dict
                    # should use:
                    # function_text = six.text_type(math_expr)
                    # but sympy doesn't yet accept unicode for function name
                    function_text = str(math_expr)
                    math_expr = SymbolCallable(function_text)
                    try:
                        user_function_dict[function_text] = math_expr
                    except TypeError:
                        pass
                    
                # if RANDOM_EXPRESSION
                else:
                    try:
                        (math_expr, index) = return_random_expression(
                            self.expression, index=group_index,
                            global_dict=global_dict,
                            evaluate_level = self.evaluate_level, rng=rng)
                    except IndexError:
                        raise IndexError("Insufficient entries for group: " \
                                             + self.group)
                            
                # record index chosen for group, if group exist
                if self.group:
                    try:
                        random_group_indices[self.group]=index
                    except TypeError:
                        pass

            elif self.expression_type == self.RANDOM_NUMBER:
                math_expr = return_random_number_sample(
                    self.expression, global_dict=global_dict, rng=rng)

            # if not randomly generating
            else:
                try:
                    math_expr = parse_and_process(
                        self.expression, global_dict=global_dict,
                        evaluate_level = self.evaluate_level)
                except (TokenError, SyntaxError, TypeError, AttributeError):
                    if self.expression_type in [
                        self.RANDOM_ORDER_TUPLE, self.ORDERED_TUPLE, 
                        self.UNORDERED_TUPLE, self.SORTED_TUPLE]:
                        et = "tuple"
                    elif self.expression_type == self.CONDITION:
                        et = "condition"
                    elif self.expression_type == self.FUNCTION:
                        et = "function"
                    else:
                        et = "expression"
                    raise ValueError("Invalid format for %s: %s" \
                                         % (et, self.expression))

                if self.expand:
                    math_expr = bottom_up(math_expr, expand)

                # if CONDITION is not met, raise exception
                if self.expression_type == self.CONDITION:
                    try:
                        if not math_expr:
                            raise Expression.FailedCondition(
                                "Condition %s was not met" % self.name)
                    except TypeError:
                        # symbolic will raise type error.  Consider test failed.
                        message= "Could not determine truth value of required condition %s, evaluated as: %s" % (self.expression, math_expr)
                        if re.search('!=[^=]',self.expression):
                            message += "\nComparison != returns truth value only for numerical values.  Use !== to compare if two symbolic expressions are not identical."
                        if re.search('[^<>!=]=[^=]',self.expression):
                            message += "\nComparison = returns truth value only for numerical values.  Use == to compare if two symbolic expressions are identical."
                        raise TypeError(message)

                        
                if self.expression_type == self.RANDOM_ORDER_TUPLE:
                    if isinstance(math_expr,list):
                        rng.shuffle(math_expr)
                        math_expr = Tuple(*math_expr)
                    elif isinstance(math_expr, Tuple):
                        math_expr = list(math_expr)
                        rng.shuffle(math_expr)
                        math_expr = Tuple(*math_expr)
                elif self.expression_type == self.SORTED_TUPLE:
                    if isinstance(math_expr,list):
                        math_expr.sort(key=customized_sort_key)
                        math_expr = Tuple(*math_expr)
                    elif isinstance(math_expr, Tuple):
                        math_expr = list(math_expr)
                        math_expr.sort(key=customized_sort_key)
                        math_expr = Tuple(*math_expr)
                elif self.expression_type == self.ORDERED_TUPLE or \
                        self.expression_type == self.UNORDERED_TUPLE:
                    if isinstance(math_expr,list):
                        math_expr = Tuple(*math_expr)
                    

                if self.expression_type == self.FUNCTION_NAME:
                    # math_expr should be a Symbol or an UndefinedFunction
                    # otherwise not a valid function name
                    if not (isinstance(math_expr,Symbol) or
                            isinstance(math_expr,UndefinedFunction)):
                        raise ValueError("Invalid function name: %s " \
                                         % math_expr)


                    # turn to SymbolCallable and add to user_function_dict
                    # should use:
                    # function_text = six.text_type(math_expr)
                    # but sympy doesn't yet accept unicode for function name
                    function_text = str(math_expr)
                    math_expr = SymbolCallable(function_text)
                    try:
                        user_function_dict[function_text] = math_expr
                    except TypeError:
                        pass
                    
                    
                if self.expression_type == self.FUNCTION:
                    parsed_function = return_parsed_function(
                        self.expression, function_inputs=self.function_inputs,
                        name = self.name, global_dict=global_dict,
                        expand = self.expand, default_value=math_expr)

                    # for FUNCTION, add parsed_function rather than
                    # math_expr to global dict
                    try:
                        global_dict[self.name] = parsed_function   
                    except TypeError:
                        pass

            # for all expression_types except FUNCTION (and RANDOM WORD)
            # add math_expr to global dict
            if not self.expression_type == self.FUNCTION:
                try:
                    # convert list to Tuple
                    if isinstance(math_expr,list):
                        global_dict[self.name] = Tuple(*math_expr)
                    # for boolean, convert to sympy integer
                    elif isinstance(math_expr,bool):
                        global_dict[self.name] = sympify(int(math_expr))
                    else:
                        global_dict[self.name] = math_expr
                except TypeError:
                    pass

            # for all expression_types (except RANDOM WORD)
            # return math_object of math_expr to context
            return math_object(
                math_expr, 
                n_digits=self.n_digits, 
                round_decimals=self.round_decimals, 
                use_ln=self.use_ln, 
                evaluate_level = self.evaluate_level,
                tuple_is_unordered=self.expression_type==self.UNORDERED_TUPLE,
                collapse_equal_tuple_elements \
                    =self.collapse_equal_tuple_elements, 
                output_no_delimiters=self.output_no_delimiters)


        # no additional processing for FailedCondition
        except self.FailedCondition:
            raise
        # on any other exception, add "??" to  global_dict for self.name
        # add name of expression to error message
        except Exception as exc:
            # don't want to raise another exception 
            # so test if global_dict is a dictionary rather
            # than just trying to assign
            if isinstance(global_dict, dict):
                global_dict[self.name] = Symbol('??')

            import sys
            raise exc.__class__, "Error in expression: %s\n%s" \
                % (self.name, exc), sys.exc_info()[2]

class PlotFunction(models.Model):
    function = models.SlugField(max_length=50)
    figure = models.IntegerField()
    question = models.ForeignKey(Question)
    linestyle = models.CharField(max_length=10, blank=True, null=True)
    linewidth = models.IntegerField(blank=True, null=True)
    xmin = models.CharField(max_length=200, blank=True, null=True)
    xmax = models.CharField(max_length=200, blank=True, null=True)
    invert = models.BooleanField(default=False)
    condition_to_show = models.CharField(max_length=200, blank=True, null=True)
    

class SympyCommandSet(models.Model):
    name = models.CharField(max_length=50, unique=True)
    commands = models.TextField()
    default = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
