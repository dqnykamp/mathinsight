from django.db import models
from django.contrib.auth.models import Group
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from math import *
import random 
from mitesting.permissions import return_user_assessment_permission_level
import re
import sympy
from sympy import Symbol, Function, Tuple
from sympy.printing import latex
from django.db.models import Max
from mitesting.math_objects import math_object, parse_expr, parse_and_process


def roots_tuple(f, *gens, **flags):
    from sympy import roots
    rootslist = roots(f, *gens, **flags).keys()
    rootslist.sort()
    return Tuple(*rootslist)

def real_roots(f, *gens):
    from sympy import roots
    return roots(f, *gens, filter='R').keys()

def real_roots_tuple(f, *gens):
    from sympy import roots
    rootslist = roots(f, *gens, filter='R').keys()
    rootslist.sort()
    return Tuple(*rootslist)

def try_round(number, ndigits=0):
    try:
        return round(number, ndigits)
    except TypeError:
        return number

    
class QuestionSpacing(models.Model):
    name = models.CharField(max_length=50, unique=True)
    css_code = models.SlugField(max_length=50, unique=True)
    sort_order = models.FloatField(default=0)

    def __unicode__(self):
        return  self.name

    class Meta:
        ordering = ['sort_order', 'name']


class QuestionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __unicode__(self):
        return  self.name
   
class QuestionPermission(models.Model):
    name = models.CharField(max_length=50, unique=True)
    privacy_level=models.SmallIntegerField(default=0)
    privacy_level_solution=models.SmallIntegerField(default=0)
    def __unicode__(self):
        return  self.name
    

class Question(models.Model):
    name = models.CharField(max_length=200)
    question_type = models.ForeignKey(QuestionType)
    question_permission = models.ForeignKey(QuestionPermission)
    description = models.CharField(max_length=400,blank=True, null=True)
    question_spacing = models.ForeignKey(QuestionSpacing, blank=True, null=True)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reference_pages = models.ManyToManyField('midocs.Page', through='QuestionReferencePage')
    allowed_sympy_commands = models.ManyToManyField('SympyCommandSet', blank=True, null=True)
    show_solution_button_after_attempts=models.IntegerField(default=0)
    keywords = models.ManyToManyField('midocs.Keyword', blank=True, null=True)
    subjects = models.ManyToManyField('midocs.Subject', blank=True, null=True)
    authors = models.ManyToManyField('midocs.Author', through='QuestionAuthor')


    def __unicode__(self):
        return "%s: %s" % (self.id, self.name)

    def user_can_view(self, user, solution=True):
        permission_level=return_user_assessment_permission_level(user, solution)
        privacy_level=self.return_privacy_level(solution)
        # if permission level is high enough, user can view
        if permission_level >= privacy_level:
            return True
        else:
            return False

    def spacing_css(self):
        if self.question_spacing:
            return self.question_spacing.css_code
 
    def get_new_seed(self):
        return str(random.randint(0,1E8))

    @models.permalink
    def get_absolute_url(self):
        return('mit-question', (), {'question_id': self.id})

    @models.permalink
    def get_solution_url(self):
        return('mit-questionsolution', (), {'question_id': self.id})

    def return_privacy_level(self, solution=True):
        # privacy level is just that of the question type
        if solution:
            return self.question_permission.privacy_level_solution
        else:
            return self.question_permission.privacy_level

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

    def need_help_html_string(self, identifier, user=None, seed_used=None,
                              assessment=None):
        
        html_string=""
        question_subparts = self.questionsubpart_set.exists()
        if question_subparts:
            reference_pages = self.questionreferencepage_set.filter(question_subpart=None)
        else:
            reference_pages = self.questionreferencepage_set.all()
            
        include_solution_link=False
        if self.solution_text and user and self.user_can_view(user,solution=True):
            if assessment:
                if assessment.user_can_view(user, solution=True):
                    include_solution_link=True
            else:
                include_solution_link=True


        if self.hint_text or reference_pages or include_solution_link:
            html_string += '<div class="question_help_container"><p><a id="%s_help_show" class="show_help" onclick="showHide(\'%s_help\');">Need help?</a></p>' % (identifier, identifier)
            html_string += '<section id="%s_help" class="question_help info">' % identifier
            if self.hint_text:
                html_string += "<h5>Hint</h5>"
                html_string += self.hint_text
            
            if reference_pages:
                html_string += "<h5>Helpful pages</h5><ul>"
                for reference_page in reference_pages:
                    html_string += "<li>" + reference_page.page.return_link() + "</li>"
                html_string += "</ul>"

            if include_solution_link:
                solution_url =  self.get_solution_url()
                if seed_used:
                    solution_url += "?seed=%s" % seed_used
                html_string += "<p><a href='%s'>View solution</a></p>" % solution_url
            html_string += '<p><a id="%s_help_hide" class="hide_help" onclick="showHide(\'%s_help\');">Hide help</a></p></section></div>' % (identifier, identifier)
            
        return html_string

    def return_sympy_global_dict(self):

        # make a whitelist of allowed commands

        all_sympy_commands = {}
        exec "from sympy import *" in all_sympy_commands

        localized_commands = {'roots_tuple': roots_tuple, 
                              'real_roots': real_roots,
                              'real_roots_tuple': real_roots_tuple, 
                              'round': try_round,
                              'e': all_sympy_commands['E'], 
                              'max': all_sympy_commands['Max'], 
                              'min': all_sympy_commands['Min'],
                              'abs': all_sympy_commands['Abs'], }
  
        # obtain list of allowed commands from database
        allowed_commands = set()
        command_lists = self.allowed_sympy_commands.all()
        for clist in command_lists:
            allowed_commands=allowed_commands.union([item.strip() for item in clist.commands.split(",")])

        from mitesting.math_objects import create_greek_dict
        global_dict = create_greek_dict()
        for command in allowed_commands:
            try:
                global_dict[str(command)]=localized_commands[command]
            except KeyError:
                try:
                    global_dict[str(command)]=all_sympy_commands[command]
                except KeyError:
                    pass

            
        return global_dict
    
    def setup_context(self, identifier="", seed=None, allow_solution_buttons=False, previous_context = None, question_set=None):

        # attempt to set identifier to be unique for each question that
        # occurs in a page
        # if question set is specified, that should make it unique
        # if question set is not specified 
        # (meaning, either question was embedded directly with tag in page
        # or we are at a question page), then assume question id will
        # make it unique
        identifier = "%s_%s_qs%s" % (identifier, self.id, question_set)

        if seed is None:
            seed=self.get_new_seed()

        random.seed(seed)
        
        the_context=Context({})
        if previous_context:
            try:
                for d in previous_context.dicts:
                    the_context.update(d)
            except:
                pass

        the_context['the_question'] = self
        the_context['allow_solution_buttons']=allow_solution_buttons

        max_tries=500
        success=False

        for i in range(max_tries):
            # select random numbers and add to context
            global_dict = self.return_sympy_global_dict()

            for random_number in self.randomnumber_set.all():
                try:
                    the_sample = random_number.get_sample \
                        (global_dict=global_dict)
                    the_context[random_number.name] = the_sample
                    global_dict[str(random_number.name)] = the_sample.return_expression()

                except Exception as e:
                    return "Error in random number %s: %s" % (random_number.name, e)
   

            # select random words and add to context
            # if two words have the same group, use the same random index
            groups = self.randomword_set.values('group').distinct()
            function_dict = {}
            for group_dict in groups:
                group = group_dict['group']
                random_words =self.randomword_set.filter(group=group)
                for (ind, random_word) in enumerate(random_words):
                    if ind==0 or group=='' or group is None:
                        word_index=None
                    try:
                        (the_word, the_plural, word_index) = random_word.get_sample(word_index, function_dict=function_dict)
                    except Exception as e:
                        return "Error in random word %s: %s" % (random_word.name, e)
                    the_context[random_word.name] = the_word
                    the_context[random_word.name+"_plural"] = the_plural
                    if isinstance(the_word, math_object):
                        sympy_word = the_word.return_expression()
                    else:
                        # sympy can't handle spaces
                        word_text=re.sub(' ', '_', the_word)
                        sympy_word = Symbol(str(word_text))
                        
                    global_dict[str(random_word.name)]=sympy_word


            failed_required_condition = False
            for expression in self.expression_set.all():
                try:
                    expression_evaluated = expression.evaluate(global_dict=global_dict)
                except Exception as e:
                    return "Error in expression %s: %s" % (expression.name, e)
                the_context[expression.name]=expression_evaluated

                # # add to substitutions only if not list
                # if not isinstance(expression_evaluated.return_expression(), list):
                #     global_dict[expression.name] = expression_evaluated.return_expression()
                if expression.required_condition:
                    if not expression_evaluated.return_expression():
                        failed_required_condition=True
                        break

            if not failed_required_condition:
                success=True
                break

        if not success:
            return "Failed to satisfy question condition"

        
        the_context['sympy_global_dict']=global_dict
        the_context['sympy_function_dict'] = function_dict
        the_context['question_%s_seed' % identifier] = seed
        return the_context

    def render_text(self, context, identifier, user=None, solution=False, 
                    show_help=True, seed_used=None, assessment=None):

        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base
        if solution:
            template_string += self.solution_text
        else:
            template_string += self.question_text
            if show_help:
                template_string += self.need_help_html_string(identifier=identifier, user=user, seed_used=seed_used, assessment=assessment)
        try:
            t = Template(template_string)
            html_string = t.render(context)
        except TemplateSyntaxError as e:
            return "Error in question template: %s" % e
        subparts = self.questionsubpart_set.all()
        if subparts:
            html_string += "\n<ol class='question_subparts'>\n"
            for subpart in subparts:
                template_string=template_string_base
                if solution:
                    template_string += subpart.solution_text
                else:
                    template_string += subpart.question_text
                    if show_help:
                        template_string += subpart.need_help_html_string(identifier=identifier, user=user, seed_used=seed_used, assessment=assessment)
                    
                html_string += "<li class='question"
                if not solution and subpart.spacing_css():
                    html_string += " %s" % subpart.spacing_css()
                if subpart.css_class:
                    html_string += " %s" % subpart.css_class
                html_string += "'>"
                try:
                    t = Template(template_string)
                    html_string += t.render(context) + "</li>\n"
                except TemplateSyntaxError as e:
                    return "Error in question subpart template: %s" % e
                
            html_string += "</ol>\n"
        return mark_safe(html_string)

    def render_question(self, context, user=None, show_help=True,
                        identifier="", assessment=None, question_set=None, 
                        assessment_seed=None, pre_answers=None, readonly=False,
                        precheck=False):

        # attempt to set identifier to be unique for each question that
        # occurs in a page
        # if question set is specified, that should make it unique
        # if question set is not specified 
        # (meaning, either question was embedded directly with tag in page
        # or we are at a question page), then assume question id will
        # make it unique
        identifier_base = "%s_%s_qs%s" % (identifier, self.id, question_set)
        
        context['readonly'] = readonly
        if pre_answers:
            context['pre_answers'] = pre_answers

        seed_used = context['question_%s_seed' % identifier_base]


        # set applet counter to zero
        context['_applet_counter'] = 0
        identifier = identifier_base + "_sol"
        context['identifier'] = identifier
        # render solution so that obtain geogebra_oninit_commands
        # into context.  Throw away actual text
        self.render_text(context,identifier=identifier, user=user, 
                         solution=True, 
                         seed_used=seed_used,
                         assessment=assessment)

        identifier = identifier_base
        context['identifier'] = identifier
        context['_applet_counter'] = 0
        if self.question_type.name=="Multiple choice":
            rendered_text = self.render_multiple_choice_question\
                (context, identifier=identifier, seed_used=seed_used,
                 assessment=assessment,
                 assessment_seed=assessment_seed, question_set=question_set)
        elif self.question_type.name=="Math write in":
            rendered_text= self.render_math_write_in_question\
                (context, identifier=identifier, seed_used=seed_used,
                 assessment=assessment,
                 assessment_seed=assessment_seed, question_set=question_set,
                 precheck=precheck)
        else:
            rendered_text= self.render_text\
                (context,identifier=identifier, user=user, 
                 solution=False, 
                 show_help=show_help, seed_used=seed_used,
                 assessment=assessment)
                
        
        return rendered_text
        

    def render_solution(self, context, user=None, identifier="",
                        question_set=None):
        
        # attempt to set identifier to be unique for each question that
        # occurs in a page
        # if question set is specified, that should make it unique
        # if question set is not specified 
        # (meaning, either question was embedded directly with tag in page
        # or we are at a question page), then assume question id will
        # make it unique
        identifier = "%s_%s_qs%s" % (identifier, self.id, question_set)

        context['identifier'] = identifier

        seed_used = context['question_%s_seed' % identifier]
        
        return self.render_text(context, identifier=identifier, user=user, 
                                    solution=True, seed_used=seed_used)


    def render_multiple_choice_question(self, context, identifier, 
                                        seed_used=None, assessment=None,
                                        assessment_seed=None, question_set=None):
        html_string = '<p>%s</p>' % self.render_text(context, identifier, 
                                                     show_help=False)
        
        answer_options = self.questionansweroption_set.all()
        rendered_answer_list = []
        for answer in answer_options:
            rendered_answer_list.append({'answer_id':answer.id, 'rendered_answer': answer.render_answer(context)})
        random.shuffle(rendered_answer_list)
        
        send_command = "Dajaxice.midocs.send_multiple_choice_question_form(callback_%s,{'form':$('#question_%s').serializeArray(), 'prefix':'%s', 'seed':'%s', 'identifier':'%s' })" % (identifier, identifier, identifier, seed_used, identifier)

        callback_script = '<script type="text/javascript">function callback_%s(data){Dajax.process(data); MathJax.Hub.Queue(["Typeset",MathJax.Hub,"question_%s_feedback"]);}</script>' % (identifier, identifier)

        html_string += '%s<form action="" method="post" id="question_%s" >' % (callback_script,  identifier)

        # Format html so that it is formatted as though it came from 
        # MultipleChoiceQuestionForm(prefix=identifier)
        # ajax will use that form to parse the result
        answer_field_name = '%s-answers' % identifier
        html_string = html_string + '<ul class="answerlist">'
        for (counter,answer) in enumerate(rendered_answer_list):
            html_string = '%s<li><label for="%s_%s" id="label_%s_%s"><input type="radio" id="id_%s_%s" value="%s" name="%s" /> %s</label>' % \
                (html_string, answer_field_name, counter, answer_field_name,
                 answer['answer_id'], answer_field_name, counter, 
                 answer['answer_id'], answer_field_name, 
                 answer['rendered_answer'] )
            html_string = '%s<div id="feedback_%s_%s" ></div></li>' % \
                (html_string, answer_field_name, answer['answer_id'])
        html_string = html_string + "</ul>"

        html_string = '%s<div id="question_%s_feedback" class="info"></div><p><input type="button" class="mi_answer_submit" value="Submit" onclick="%s"></p></form>'  % (html_string, identifier, send_command)

        return mark_safe(html_string)

    def render_math_write_in_question(self, context, identifier, seed_used,
                                      assessment=None,
                                      assessment_seed=None, question_set=None,
                                      precheck=False):
        
        # render question text at the beginning so that have answer_list in context
        question_text = '<div id=question_text_%s>%s</div>' % (identifier,self.render_text(context, identifier=identifier, show_help=False))

        if assessment:
            assessment_code = assessment.code
        else:
            assessment_code = ""
            assessment_seed = None
        
        if question_set is None:
            question_set = ""
        
        if precheck:
            record = 'false'
        else:
            record = 'true'

        send_command = "Dajaxice.midocs.check_math_write_in(callback_%s,{'answer_serialized':$('#id_question_%s').serializeArray(), 'seed':'%s', 'question_id': '%s', 'identifier': '%s', 'assessment_code': '%s', 'assessment_seed': '%s', 'question_set': '%s', 'record': %s });" % ( identifier, identifier, seed_used, self.id, identifier, assessment_code, assessment_seed, question_set, record)

        the_correct_answers = context.get('_math_writein_answer_list',[])
        answer_feedback_strings=""
        for answer_tuple in the_correct_answers:
            answer_string = answer_tuple[0]

            answer_feedback_strings += "answer_%s_%s_feedback" % (answer_string, identifier)
            break


        #callback_script = '<script type="text/javascript">function callback_%s(data){Dajax.process(data); MathJax.Hub.Queue(["Typeset",MathJax.Hub,"question_%s_feedback%s"]);}</script>' % (identifier, identifier, answer_feedback_strings)

        # for callback script, process question with Mathjax
        # after processing ajax
        callback_script = '<script type="text/javascript">function callback_%s(data){Dajax.process(data); MathJax.Hub.Queue(["Typeset",MathJax.Hub,"the_question_%s"]); }</script>' % (identifier, identifier)

        # for solution callback script, process solution with Mathjax
        # after processing ajax,
        # then call web (defined in GeoGebraWeb .js file) to process any
        # new geogebra web applet
        # ajax removed class geogebraweb from any previous applets so that
        # don't get applets duplicated by web()
        callback_solution_script = '<script type="text/javascript">function callback_solution_%s(data){Dajax.process(data); MathJax.Hub.Queue(["Typeset",MathJax.Hub,"question_%s_solution"]);web();}</script>' % (identifier, identifier)


        html_string = '%s%s<form onkeypress="return event.keyCode != 13;" action="" method="post" id="id_question_%s" ><div id="the_question_%s">' %  (callback_script, callback_solution_script, identifier, identifier)

        html_string += question_text

        asb_string = 0
        if context['allow_solution_buttons'] and not precheck:
            asb_string = 1

        html_string += '<input type="hidden" id="id_number_attempts_%s" maxlength="5" name="number_attempts_%s" size="5" value = "0" /><input type="hidden" id="id_asb_%s" maxlength="5" name="asb_%s" size="5" value = "%s">' % (identifier, identifier, identifier, identifier, asb_string)
        # html_string += '<label for="answer_%s">Answer: </label><input type="text" id="id_answer_%s" maxlength="200" name="answer_%s" size="60" />' % \
        #     (identifier, identifier, identifier)

        # html_string += '<div id="question_%s_feedback" class="info"></div><div id="question_%s_solution" class="info"></div><input type="button" value="Submit" onclick="%s"> <span id="solution_button_%s"></span></form>'  % (identifier, send_command, identifier, identifier)
        
        if not precheck:
            html_string += '<div id="question_%s_feedback" class="info"></div><br/><input type="button" class="mi_answer_submit" value="Submit" onclick="%s"> </div></form><div id="question_%s_solution" class="info"></div><span id="solution_button_%s"></span>'  % (identifier, send_command, identifier, identifier,)
        else:
            html_string += '<div id="question_%s_feedback" class="info"></div> </div></form><script type="text/javascript">%s</script>'  % (identifier, send_command)

        return mark_safe(html_string)

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

  
class QuestionAuthor(models.Model):
    question = models.ForeignKey(Question)
    author = models.ForeignKey('midocs.Author')
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("question","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author


class QuestionSubpart(models.Model):
    question= models.ForeignKey(Question)
    question_spacing = models.ForeignKey(QuestionSpacing, blank=True, null=True)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    sort_order = models.FloatField(default=0)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "subpart %s" % self.get_subpart_letter()
    
    
    class Meta:
        ordering = ['sort_order','id']
                                         
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
            return self.question_spacing.css_code


    def need_help_html_string(self, identifier, user=None, seed_used=None,
                              assessment=None):
        
        identifier="%s_%s" % (identifier, self.id)

        html_string=""

        reference_pages = self.question.questionreferencepage_set.filter(question_subpart=self.get_subpart_letter())
        
        include_solution_link=False
        
        if self.solution_text and user and self.question.user_can_view(user,solution=True):
            if assessment:
                if assessment.user_can_view(user, solution=True):
                    include_solution_link=True
            else:
                include_solution_link=True


        if self.hint_text or reference_pages or include_solution_link:
            html_string += '<div class="question_help_container"><p><a id="%s_help_show" class="show_help" onclick="showHide(\'%s_help\');">Need help?</a></p>' % (identifier, identifier)
            html_string += '<section id="%s_help" class="question_help info">' % identifier

            if self.hint_text:
                html_string += "<h5>Hint</h5>"
                html_string += self.hint_text
            
            if reference_pages:
                html_string += "<h5>Helpful pages</h5><ul>"
                for reference_page in reference_pages:
                    html_string += "<li>" + reference_page.page.return_link() + "</li>"
                html_string += "</ul>"

            if include_solution_link:
                solution_url =  self.question.get_solution_url()
                if seed_used:
                    solution_url += "?seed=%s" % seed_used
                html_string += "<p><a href='%s'>View solution</a></p>" % solution_url
            html_string += '<p><a id="%s_help_hide" class="hide_help" onclick="showHide(\'%s_help\');">Hide help</a></p></section></div>' % (identifier, identifier)
            
        return html_string



class QuestionReferencePage(models.Model):
    question = models.ForeignKey(Question)
    page = models.ForeignKey('midocs.Page')
    sort_order = models.FloatField(default=0)
    question_subpart = models.CharField(max_length=1, blank=True,null=True)
    
    class Meta:
        unique_together = ("question", "page", "question_subpart")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s for %s" % (self.page, self.question)

class QuestionAnswerOption(models.Model):
    question = models.ForeignKey(Question)
    answer = models.CharField(max_length=400)
    correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return  self.answer

    def render_answer(self, context):
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base
        template_string += self.answer
        try:
            t = Template(template_string)
            html_string = t.render(context)
        except TemplateSyntaxError as e:
            return "Error in answer template: %s" % e
        return mark_safe(html_string)

    def render_feedback(self, context):
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base
        template_string += self.feedback
        try:
            t = Template(template_string)
            html_string = t.render(context)
        except TemplateSyntaxError as e:
            return "Error in answer template: %s" % e
        return mark_safe(html_string)


class AssessmentType(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    privacy_level = models.SmallIntegerField(default=0)
    privacy_level_solution = models.SmallIntegerField(default=0)
    template_base_name = models.CharField(max_length=50, blank=True, null=True)
    record_online_attempts = models.BooleanField(default=True)
    
    def __unicode__(self):
        return  self.name

class Assessment(models.Model):
    code = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=30, blank=True)
    assessment_type = models.ForeignKey(AssessmentType)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    questions = models.ManyToManyField(Question, through='QuestionAssigned')
    fixed_order = models.BooleanField(default=False)
    instructions = models.TextField(blank=True, null=True)
    instructions2 = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    time_limit = models.CharField(max_length=20, blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    groups_can_view = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view")
    groups_can_view_solution = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view_solution")
    allow_solution_buttons = models.BooleanField(default=False)
    background_pages = models.ManyToManyField('midocs.Page', through='AssessmentBackgroundPage')
    hand_graded_component = models.BooleanField(default=True)
    nothing_random = models.BooleanField(default=False)
    total_points = models.FloatField(blank=True, null=True)

    def __unicode__(self):
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

    def user_can_view(self, user, solution=True):
        permission_level=return_user_assessment_permission_level(user, solution)
        privacy_level=self.return_privacy_level(solution)
        # if permission level is high enough, user can view
        if permission_level >= privacy_level:
            return True
        
        # else check if user is in one of the groups 
        allowed_users=self.return_users_of_groups_can_view(solution)
        if user in allowed_users:
            return True
        else:
            return False

    def return_users_of_groups_can_view(self, solution=True):
        if solution:
            allowed_groups= self.groups_can_view_solution.all()
        else:
            allowed_groups= self.groups_can_view.all()
        allowed_users = []
        for group in allowed_groups:
            allowed_users += list(group.user_set.all())
        return allowed_users

    def get_new_seed(self):
        return str(random.randint(0,1E8))

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
            ("view_assessment_1", "Can view 1"),
            ("view_assessment_1_solution", "Can view 1 solution"),
            ("view_assessment_2", "Can view 2"),
            ("view_assessment_2_solution", "Can view 2 solution"),
            ("administer_assessment","Can administer assessments"),
        )

    def return_privacy_level(self, solution=True):
        # privacy level is max of privacy level from assessment type
        # and all question sets
        if solution:
            privacy_level = self.assessment_type.privacy_level_solution
        else:
            privacy_level = self.assessment_type.privacy_level
        for question in self.questions.all():
            privacy_level = max(privacy_level, question.return_privacy_level(solution))
        return privacy_level
                                
    def render_instructions(self):
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base + self.instructions
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions template: %s" % e

    def render_instructions2(self):
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base + self.instructions2
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions2 template: %s" % e


    def render_question_list(self, seed=None, user=None, current_attempt=None):
        if seed is not None:
            random.seed(seed)
            
        question_list = self.get_question_list(seed)

        rendered_question_list = []
        
        previous_context=Context({})
        for (i, question_dict) in enumerate(question_list):

            # use qa for identifier since coming from assessment
            identifier="qa%s" % i

            question = question_dict['question']
            question_set = question_dict['question_set']
            question_context = question.setup_context\
                (seed=question_dict['seed'], identifier=identifier, \
                     allow_solution_buttons = self.allow_solution_buttons,\
                     previous_context = previous_context, \
                     question_set = question_set)
            
            # if there was an error, question_context is a string string,
            # so just make rendered question text be that string
            if not isinstance(question_context, Context):
                question_text = question_context
                geogebra_oninit_commands=""
            else:
                question_text = question.render_question(question_context, user=user, identifier=identifier, assessment=self, assessment_seed = seed, question_set=question_set)
                geogebra_oninit_commands=question_context.dicts[0].get('geogebra_oninit_commands')
                #geogebra_oninit_commands=question.render_javascript_commands(question_context, question=True, solution=False)
                previous_context = question_context


            # if have a latest attempt, look for maximum score on question_set
            current_score=None
            if current_attempt:
                try:
                    current_credit =current_attempt\
                        .get_percent_credit_question_set(question_set)
                    if question_dict['points']:
                        current_score = current_credit\
                            *question_dict['points']/100
                    else:
                        current_score=0
                except ObjectDoesNotExist:
                    current_credit = None
            else:
                current_credit = None

            rendered_question_list.append({'question_text': question_text,
                                           'question': question,
                                           'points': question_dict['points'],
                                           'seed': question_dict['seed'],
                                           'question_set': question_set,
                                           'current_credit': current_credit,
                                           'current_score': current_score,
                                           'geogebra_oninit_commands':\
                                               geogebra_oninit_commands})


        if not self.fixed_order:
            random.shuffle(rendered_question_list)
        

        return rendered_question_list

    def render_solution_list(self, seed=None):
        if seed is not None:
            random.seed(seed)
            
        question_list = self.get_question_list(seed)

        rendered_solution_list = []

        previous_context = Context({})
        for (i, solution_dict) in enumerate(question_list):

            # use qa for identifier since coming from assessment
            identifier="qa%s" % i

            question = solution_dict['question']
            question_set = solution_dict['question_set']
            question_context = question.setup_context\
                (seed=solution_dict['seed'], identifier=identifier, \
                     allow_solution_buttons = self.allow_solution_buttons, \
                     previous_context = previous_context,\
                     question_set = question_set)

            # if there was an error, question_context is a string string,
            # so just make rendered question text be that string
            if not isinstance(question_context, Context):
                question_text = question_context
                solution_text = question_context
                geogebra_oninit_commands=""
            else:
                question_text = question.render_question\
                    (question_context, identifier=identifier,\
                         question_set=question_set)
                solution_text = question.render_solution\
                    (question_context, identifier=identifier, \
                         question_set=question_set)
                geogebra_oninit_commands=question_context.dicts[0].get('geogebra_oninit_commands')
                #geogebra_oninit_commands=question.render_javascript_commands(question_context, question=True, solution=True)
                
                previous_context = question_context


            solution_dict['question_text'] = question_text
            solution_dict['solution_text'] = solution_text
            solution_dict['geogebra_oninit_commands'] = geogebra_oninit_commands

            rendered_solution_list.append(solution_dict)


        if not self.fixed_order:
            random.shuffle(rendered_solution_list)

        return rendered_solution_list


    def get_question_list(self, seed=None):
        if seed is not None:
            random.seed(seed)

        question_list = []

        for question_set in self.question_sets():
            questions_in_set = self.questionassigned_set.filter(question_set=question_set)
            the_question=random.choice(questions_in_set).question

            # generate a seed for the question
            # so that can have link to this version of question and solution
            question_seed=self.get_new_seed()
            the_points = self.points_of_question_set(question_set)
            if the_points is None:
                the_points = ""    
            question_list.append({'question_set': question_set,
                                  'question': the_question,
                                  'points': the_points,
                                  'seed': question_seed}
                                 )

        return question_list
            


    def question_sets(self):
        question_set_dicts= self.questionassigned_set.order_by('question_set').values('question_set').distinct()
        question_sets = []
        for question_set_dict in question_set_dicts:
            question_sets.append(question_set_dict['question_set'])
        return question_sets


    def points_of_question_set(self, question_set):
        try:
            question_detail=self.questionsetdetail_set.get(question_set=question_set)
            return question_detail.points
        except:
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

        for seed in range(start_seed, start_seed+1000):

            question_list = self.get_question_list(str(seed))

            number_disallowed_questions=0

            for (i, question_set) in enumerate(question_sets):
                if not question_list[i]['question'] in allowed_question_lists[i]:
                    number_disallowed_questions += 1
            
            if number_disallowed_questions < min_disallowed_questions:
                min_disallowed_questions = number_disallowed_questions
                seed_min_disallowed = seed
            
            if  min_disallowed_questions==0:
                break

        return seed_min_disallowed
                    

class AssessmentBackgroundPage(models.Model):
    assessment = models.ForeignKey(Assessment)
    page = models.ForeignKey('midocs.Page')
    sort_order = models.FloatField(default = 0.0)

    class Meta:
        ordering = ['sort_order']

class QuestionSetDetail(models.Model):
    assessment = models.ForeignKey(Assessment)
    question_set = models.SmallIntegerField(default=0,db_index=True)
    points = models.FloatField(default=0)

    class Meta:
        unique_together = ("assessment", "question_set")
    def __unicode__(self):
        return "%s for %s" % (self.question_set, self.assessment)


class QuestionAssigned(models.Model):
    assessment = models.ForeignKey(Assessment)
    question = models.ForeignKey(Question)
    question_set = models.SmallIntegerField(blank=True)

    class Meta:
        verbose_name_plural = "Questions assigned"
        ordering = ['question_set', 'id']
    def __unicode__(self):
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

class RandomNumber(models.Model):
    name = models.SlugField(max_length=50)
    question = models.ForeignKey(Question)
    min_value = models.CharField(max_length=200, default='0')
    max_value = models.CharField(max_length=200, default='10')
    increment = models.CharField(max_length=200, default='1')
    
    def __unicode__(self):
        return  self.name

    def get_sample(self, global_dict=None):
        
        max_value = parse_and_process(self.max_value, global_dict=global_dict)

        min_value = parse_and_process(self.min_value, global_dict=global_dict)
        
        increment = parse_and_process(self.increment, global_dict=global_dict)
  
        # multiply by 1+1E-10 before rounding down to integer
        # so small floating point errors don't bring it down to next integer
        num_possibilities = 1+int(floor((max_value-min_value)/increment)*(1+1E-10))
        choices=(min_value+n*increment for n in range(num_possibilities))
        the_num = random.choice(list(choices))

        # if the_num is an integer, convert to integer so don't have decimal
        if int(the_num)==the_num:
            the_num = int(the_num)
        else:
            # try to round the answer to the same number of decimal places
            # as the input values
            # seems to help with rounding error with the float arithmetic
            for i in range(1,11):
                if(round(min_value*pow(10,i)) == min_value*pow(10,i)
                   and round(max_value*pow(10,i)) == max_value*pow(10,i)
                   and round(increment*pow(10,i)) == increment*pow(10,i)):
                    the_num = round(the_num,i)
                    break
                
        return math_object(the_num)
    


class RandomWord(models.Model):
    name = models.SlugField(max_length=50)
    question = models.ForeignKey(Question)
    option_list = models.CharField(max_length=400)
    plural_list = models.CharField(max_length=400, blank=True, null=True)
    group = models.CharField(max_length=50, blank=True, null=True)
    sympy_parse = models.BooleanField(default=False)
    treat_as_function = models.BooleanField(default=False)

    def __unicode__(self):
        return  self.name

    def get_sample(self, index=None, global_dict=None, function_dict=None):

        # turn comma separated list to python list. 
        # strip off leading/trailing whitespace
        option_list = [item.strip() for item in self.option_list.split(",")]
        plural_list = [item.strip() for item in self.plural_list.split(",")]
        
        # if index isn't prescribed, generate randomly
        if index is None:
            index = random.randrange(len(option_list))
        the_word=option_list[index]
        if self.sympy_parse or self.treat_as_function:
            try:
                if not global_dict:
                    from mitesting.math_objects import create_greek_dict
                    global_dict = create_greek_dict()
                temp_global_dict = {}
                temp_global_dict.update(global_dict)
                if self.treat_as_function:
                    temp_global_dict[str(the_word)] = Function(str(the_word))
                    if function_dict is not None:
                        function_dict[str(the_word)] = Function(str(the_word))
                the_word = math_object(parse_expr(the_word, global_dict=temp_global_dict))
            except:
                pass
        try:
            the_plural = plural_list[index]
        except:
            the_plural = ""

        if not the_plural:
            the_plural = "%ss" % the_word
            
        return (the_word, the_plural, index)
 

class Expression(models.Model):
    name = models.SlugField(max_length=50)
    expression = models.CharField(max_length=200)
    required_condition = models.BooleanField(default=False)
    expand = models.BooleanField(default=False)
    doit = models.BooleanField(default=True)
    n_digits = models.IntegerField(blank=True, null=True)
    round_decimals = models.IntegerField(blank=True, null=True)
    question = models.ForeignKey(Question)
    function_inputs = models.CharField(max_length=50, blank=True, null=True)
    use_ln = models.BooleanField(default=False)
    expand_on_compare = models.BooleanField(default=False)
    tuple_is_ordered = models.BooleanField(default=False)
    collapse_equal_tuple_elements=models.BooleanField(default=False)
    output_no_delimiters = models.BooleanField(default=False)
    sort_list = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)
    class Meta:
        ordering = ['sort_order','id']

    def __unicode__(self): 
        return  self.name

    def evaluate(self, global_dict):

        expression = parse_and_process(self.expression, global_dict=global_dict, doit=self.doit)
        
        if self.expand:
            expression=expression.expand()

        # sort_list means sort list or Tuple
        if self.sort_list and isinstance(expression,list):
            expression.sort()

        # for Tuple, must turn to list in order to sort
        if self.sort_list and isinstance(expression,Tuple):
            expression = list(expression)
            expression.sort()
            expression = Tuple(*expression)

        # turn list to Tuple
        if isinstance(expression,list):
            expression = Tuple(*expression)

        if self.function_inputs:
            input_list = [str(item.strip()) for item in self.function_inputs.split(",")]
            # if any input variables are in global_dict, need to remove
            global_dict_sub = dict((key, global_dict[key]) for key in global_dict.keys() if key not in input_list)


            expr2= parse_and_process(self.expression,
                                     global_dict=global_dict_sub)
            
            class parsed_function(Function):
                the_input_list = input_list
                n_args = len(input_list)
                the_global_dict_sub = global_dict_sub
                expression = expr2
                __name__ = self.name

                @classmethod
                def eval(cls, *args):
                    expr_sub=cls.expression
                    for i in range(len(cls.the_input_list)):
                        expr_sub=expr_sub.xreplace({Symbol(cls.the_input_list[i]): args[i]})
                    return expr_sub

                
            global_dict[str(self.name)] = parsed_function   
            
        # if not function, just add expression to global dict
        else:
            global_dict[str(self.name)] = expression


        return math_object(expression, n_digits=self.n_digits, round_decimals=self.round_decimals, use_ln=self.use_ln, expand_on_compare=self.expand_on_compare, tuple_is_ordered=self.tuple_is_ordered, collapse_equal_tuple_elements=self.collapse_equal_tuple_elements, output_no_delimiters=self.output_no_delimiters)


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

    def __unicode__(self):
        return self.name
