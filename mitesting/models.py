from django.db import models
from django.contrib.auth.models import Group
from midocs.models import Video, Page
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from math import *
import random 
from mitesting.permissions import return_user_assessment_permission_level
import re
import sympy
from sympy import Symbol, Function
from sympy.printing import latex
from django.db.models import Max

def create_greek_dict():
    from sympy.abc import (alpha, beta,  delta, epsilon, eta,
                           theta, iota, kappa, mu, nu, xi, omicron, pi,
                           rho, sigma, tau, upsilon, phi, chi, psi, omega)
    lambda_symbol = Symbol('lambda')
    gamma_symbol = Symbol('gamma')
    zeta_symbol = Symbol('zeta')
    greek_dict = {'alpha': alpha, 'alpha_symbol': alpha, 
                  'beta': beta,'beta_symbol': beta, 
                  'gamma_symbol': gamma_symbol, 
                  'delta': delta, 'delta_symbol': delta, 
                  'epsilon': epsilon, 'epsilon_symbol': epsilon,
                  'zeta_symbol': zeta_symbol, 
                  'eta': eta, 'eta_symbol': eta, 
                  'theta': theta, 'theta_symbol': theta, 
                  'iota': iota, 'iota_symbol': iota, 
                  'kappa': kappa, 'kappa_symbol': kappa, 
                  'lambda_symbol': lambda_symbol, 
                  'mu': mu, 'mu_symbol': mu,
                  'nu': nu, 'nu_symbol': nu,
                  'xi': xi,'xi_symbol': xi, 
                  'omicron': omicron,'omicron_symbol': omicron, 
                  'rho': rho, 'rho_symbol': rho, 
                  'sigma': sigma, 'sigma_symbol': sigma, 
                  'tau': tau, 'tau_symbol': tau, 
                  'upsilon': upsilon,'upsilon_symbol': upsilon,
                  'phi': phi, 'phi_symbol': phi, 
                  'chi': chi, 'chi_symbol': chi, 
                  'psi': psi, 'psi_symbol': psi, 
                  'omega': omega, 'omega_symbol': omega }

    return greek_dict
    
def create_symbol_name_dict():

    symbol_list = 'bigstar bigcirc clubsuit spadesuit heartsuit diamondsuit Diamond bigtriangleup bigtriangledown blacklozenge blacksquare blacktriangle blacktriangledown blacktriangleleft blacktriangleright Box circ lozenge star'.split(' ')
    symbol_name_dict = {}
    for symbol in symbol_list:
        symbol_name_dict[eval("Symbol('%s')" % symbol)] = '\\%s' % symbol

    return symbol_name_dict

class sympy_word:
    def __init__(self, the_word):
        self.word=the_word
    def __unicode__(self):
        output = latex(self.word, symbol_names=create_symbol_name_dict())
        return output

class evaluated_expression:
    def __init__(self, expression, n_digits=None, round_decimals=None, use_ln=False):
        self.expression=expression
        self.n_digits=n_digits
        self.round_decimals=round_decimals
        self.use_ln=use_ln
    def convert_expression(self):
        expression=self.expression
        if self.n_digits:
            try:
                expression = expression.evalf(self.n_digits)
            except:
                pass

        if self.round_decimals is not None:
            try:
                expression = expression.round(self.round_decimals)
                if self.round_decimals == 0:
                    expression = int(expression)
            except:
                pass
        return expression
    def __unicode__(self):
        expression = self.convert_expression()
        output=""
        symbol_name_dict = create_symbol_name_dict()
        output = latex(expression, symbol_names=symbol_name_dict)
        if self.use_ln:
            output = re.sub('operatorname{log}', 'operatorname{ln}', output)
            output = re.sub('\\log', 'ln', output)
        return output
    def __float__(self):
        expression = self.convert_expression()
        try:
            return float(expression)
        except:
            return expression
    def float(self):
        return self.__float__()

class deferred_gcd(Function):
    nargs = 2
    
    def doit(self, **hints):        
        if hints.get('deep', True):
            return sympy.gcd(self.args[0].doit(**hints), self.args[1].doit(**hints))
        else:
            return sympy.gcd(self.args[0], self.args[1])
       
        
# class deferred_max(Function):
#     nargs = 2
    
#     def doit(self, **hints):
#         if hints.get('deep',True):
#             return max(self.args[0].doit(**hints), self.args[1].doit(**hints))
#         else:
#             return max(self.args[0], self.args[1])
        
# class deferred_min(Function):
#     nargs = 2
    
#     def doit(self, **hints):
#         if hints.get('deep',True):
#             return min(self.args[0].doit(**hints), self.args[1].doit(**hints))
#         else:
#             return min(self.args[0], self.args[1])

# class deferred_sign(Function):
#     nargs = 1
    
#     def doit(self, **hints):
#         if hints.get('deep',True):
#             return sympy.sign(self.args[0].doit(**hints))
#         else:
#             return sympy.sign(self.args[0])

    
class QuestionSpacing(models.Model):
    name = models.CharField(max_length=50, unique=True)
    css_code = models.SlugField(max_length=50, unique=True)

    def __unicode__(self):
        return  self.name

    class Meta:
        ordering = ['name']


class QuestionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    privacy_level=models.SmallIntegerField(default=0)
    privacy_level_solution=models.SmallIntegerField(default=0)
    def __unicode__(self):
        return  self.name
   

class Question(models.Model):
    #code = models.SlugField(max_length=200, blank=True, null=True)
    name = models.CharField(max_length=200)
    question_type = models.ForeignKey(QuestionType)
    description = models.CharField(max_length=400,blank=True, null=True)
    question_spacing = models.ForeignKey(QuestionSpacing, blank=True, null=True)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)
    allow_expand = models.BooleanField()
    video = models.ForeignKey(Video, blank=True,null=True)
    reference_pages = models.ManyToManyField(Page, through='QuestionReferencePage')
    allowed_sympy_commands = models.ManyToManyField('SympyCommandSet', blank=True, null=True)
    
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
            return self.question_type.privacy_level_solution
        else:
            return self.question_type.privacy_level

    def need_help_html_string(self, identifier, user=None, seed_used=None):
        
        html_string=""
        question_subparts = self.questionsubpart_set.exists()
        if question_subparts:
            reference_pages = self.questionreferencepage_set.filter(question_subpart=None)
        else:
            reference_pages = self.questionreferencepage_set.all()
            
        if self.solution_text and user and self.user_can_view(user,solution=True):
            include_solution_link=True
        else:
            include_solution_link=False

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

    def return_sympy_local_dict(self):

        # obtain list of all allowed sympy commands
        allowed_commands = set()
        command_lists = self.allowed_sympy_commands.all()
        for clist in command_lists:
            allowed_commands=allowed_commands.union([item.strip() for item in clist.commands.split(",")])
        
        allowed_commands= allowed_commands.union(['Symbol', 'Integer','Float','Rational'])
        # since don't have a whitelist function
        # make a blacklist of all functions except those allowed
        all_commands = {}
        exec "from sympy import *" in all_commands
        disallowed_commands_set = set(all_commands.keys()) - allowed_commands
        disallowed_commands = dict([(key, Symbol(str(key))) for key in disallowed_commands_set]) 
        
        local_dict = disallowed_commands
        if 'gcd' in allowed_commands:
            local_dict['gcd'] = deferred_gcd
        # if 'max' in allowed_commands:
        #     local_dict['max'] = deferred_max
        # if 'min' in allowed_commands:
        #     local_dict['min'] = deferred_min
        # if 'sign' in allowed_commands:
        #     local_dict['sign'] = deferred_sign
            
        return local_dict
    
    def setup_context(self, identifier="", seed=None):

        identifier = "%s_%s" % (identifier, self.id)

        if seed is None:
            seed=self.get_new_seed()

        random.seed(seed)
            
        the_context={'the_question': self}

        max_tries=100
        success=False

        for i in range(max_tries):
            # select random numbers and add to context
            substitutions=[]
            function_dict = create_greek_dict()
            function_dict['abs'] = abs
            function_dict.update(self.return_sympy_local_dict())

            for random_number in self.randomnumber_set.all():
                try:
                    the_context[random_number.name] = random_number.get_sample()
                    substitutions.append((Symbol(str(random_number.name)), the_context[random_number.name]))

                except Exception as e:
                    return "Error in random number %s: %s" % (random_number.name, e)
   

            # select random words and add to context
            # if two words have the same group, use the same random index
            groups = self.randomword_set.values('group').distinct()
            for group_dict in groups:
                group = group_dict['group']
                random_words =self.randomword_set.filter(group=group)
                for (ind, random_word) in enumerate(random_words):
                    if ind==0 or group=='' or group is None:
                        word_index=None
                    try:
                        (the_word, the_plural, word_index) = random_word.get_sample(word_index)
                    except Exception as e:
                        return "Error in random word %s: %s" % (random_word.name, e)
                    the_context[random_word.name] = the_word
                    the_context[random_word.name+"_plural"] = the_plural
                    if isinstance(the_word, sympy_word):
                        new_sympy_word = the_word.word
                    else:
                        # sympy can't handle spaces
                        word_text=re.sub(' ', '_', the_word)
                        new_sympy_word = Symbol(str(the_word))
                        
                    substitutions.append((Symbol(str(random_word.name)), 
                                          new_sympy_word))


            failed_required_condition = False
            for expression in self.expression_set.all():
                try:
                    expression_evaluated = expression.evaluate(substitutions, function_dict)
                except Exception as e:
                    return "Error in expression %s: %s" % (expression.name, e)
                the_context[expression.name]=expression_evaluated
                substitutions.append((Symbol(str(expression.name)),expression_evaluated.expression))
                if expression.required_condition:
                    if not expression_evaluated.expression:
                        failed_required_condition=True
                        break
            
            if not failed_required_condition:
                success=True
                break

        if not success:
            return "Failed to satisfy question condition"

        
        the_context['sympy_substitutions']=substitutions
        the_context['sympy_function_dict']=function_dict
        the_context['question_%s_seed' % identifier] = seed
        return the_context

    def render_text(self, context, identifier, user=None, solution=False, 
                    show_help=True, seed_used=None):

        c= Context(context)
        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base
        if solution:
            template_string += self.solution_text
        else:
            template_string += self.question_text
            if show_help:
                template_string += self.need_help_html_string(identifier=identifier, user=user, seed_used=seed_used)
        try:
            t = Template(template_string)
            html_string = t.render(c)
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
                        template_string += subpart.need_help_html_string(identifier=identifier, user=user, seed_used=seed_used)
                    
                html_string += "<li class='question"
                if not solution and subpart.spacing_css():
                    html_string += " %s" % subpart.spacing_css()
                if subpart.css_class:
                    html_string += " %s" % subpart.css_class
                html_string += "'>"
                try:
                    t = Template(template_string)
                    html_string += t.render(c) + "</li>\n"
                except TemplateSyntaxError as e:
                    return "Error in question subpart template: %s" % e
                
            html_string += "</ol>\n"
        return mark_safe(html_string)

    def render_question(self, context, user=None, show_help=True, identifier=""):
        identifier = "%s_%s" % (identifier, self.id)
        
        context['identifier'] = identifier

        seed_used = context['question_%s_seed' % identifier]
        if self.question_type.name=="Multiple choice":
            return self.render_multiple_choice_question(context,
                                                        identifier=identifier,
                                                        seed_used=seed_used)
        elif self.question_type.name=="Math write in":
            return self.render_math_write_in_question(context,
                                                      seed_used=seed_used,
                                                      identifier=identifier)
        else:
            return self.render_text(context,identifier=identifier, user=user, 
                                    solution=False, 
                                    show_help=show_help, seed_used=seed_used)

    def render_solution(self, context, user=None, identifier=""):
        
        identifier = "%s_%s" % (identifier, self.id)

        seed_used = context['question_%s_seed' % identifier]
        
        return self.render_text(context, identifier=identifier, user=user, 
                                    solution=True, seed_used=seed_used)


    def render_multiple_choice_question(self, context,identifier, 
                                        seed_used=None):
        html_string = '<p>%s</p>' % self.render_text(context, identifier, 
                                                     show_help=False)
        
        answer_options = self.questionansweroption_set.all()
        rendered_answer_list = []
        for answer in answer_options:
            rendered_answer_list.append({'answer_id':answer.id, 'rendered_answer': answer.render_answer(context)})
        random.shuffle(rendered_answer_list)
        
        send_command = "Dajaxice.midocs.send_multiple_choice_question_form(callback_%s,{'form':$('#question_%s').serializeObject(), 'prefix':'%s', 'seed':'%s', 'identifier':'%s' })" % (identifier, identifier, identifier, seed_used, identifier)

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

        html_string = '%s<div id="question_%s_feedback" class="info"></div><p><input type="button" value="Submit" onclick="%s"></p></form>'  % (html_string, identifier, send_command)

        return mark_safe(html_string)

    def render_math_write_in_question(self, context, seed_used,
                                      identifier):
        

        send_command = "Dajaxice.midocs.check_math_write_in(callback_%s,{'answer':$('#id_question_%s').serializeObject(), 'seed':'%s', 'question_id': '%s', 'identifier': '%s' });" % ( identifier, identifier, seed_used, self.id, identifier)

        callback_script = '<script type="text/javascript">function callback_%s(data){Dajax.process(data); MathJax.Hub.Queue(["Typeset",MathJax.Hub,"question_%s_feedback"]);}</script>' % (identifier, identifier)


        html_string = '%s<form onkeypress="return event.keyCode != 13;" action="" method="post" id="id_question_%s" >' %  (callback_script, identifier)

        html_string += '<p>%s</p>' % self.render_text(context, identifier=identifier, show_help=False)


        # html_string += '<label for="answer_%s">Answer: </label><input type="text" id="id_answer_%s" maxlength="200" name="answer_%s" size="60" />' % \
        #     (identifier, identifier, identifier)
        html_string += '<div id="question_%s_feedback" class="info"></div><p><input type="button" value="Submit" onclick="%s"></form>'  % (identifier, send_command)
        
        return mark_safe(html_string)
    

class QuestionSubpart(models.Model):
    question= models.ForeignKey(Question)
    question_spacing = models.ForeignKey(QuestionSpacing, blank=True, null=True)
    css_class = models.CharField(max_length=100,blank=True, null=True)
    sort_order = models.SmallIntegerField(default=0)
    question_text = models.TextField(blank=True, null=True)
    solution_text = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "subpart %s" % self.get_subpart_number()
    
    
    class Meta:
        ordering = ['sort_order','id']
                                         
    def fullcode(self):
        return "%s_%s" % (self.question.id, self.id)

    def get_subpart_number(self):
        try:
            return list(self.question.questionsubpart_set.all()).index(self)+1
        except:
            return None

    def spacing_css(self):
        if self.question_spacing:
            return self.question_spacing.css_code


    def need_help_html_string(self, identifier, user=None, seed_used=None):
        
        identifier="%s_%s" % (identifier, self.id)

        html_string=""

        order_in_sort = self.get_subpart_number()
        
        reference_pages = self.question.questionreferencepage_set.filter(question_subpart=order_in_sort)
        
        if self.solution_text and user and self.question.user_can_view(user,solution=True):
            include_solution_link=True
        else:
            include_solution_link=False

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
    page = models.ForeignKey(Page)
    sort_order = models.SmallIntegerField(default=0)
    question_subpart = models.SmallIntegerField(blank=True,null=True)
    
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
        c= Context(context)
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base
        template_string += self.answer
        try:
            t = Template(template_string)
            html_string = t.render(c)
        except TemplateSyntaxError as e:
            return "Error in answer template: %s" % e
        return mark_safe(html_string)

    def render_feedback(self, context):
        c= Context(context)
        template_string_base = "{% load testing_tags mi_tags humanize %}{% load url from future %}"
        template_string=template_string_base
        template_string += self.feedback
        try:
            t = Template(template_string)
            html_string = t.render(c)
        except TemplateSyntaxError as e:
            return "Error in answer template: %s" % e
        return mark_safe(html_string)

class MathWriteinAnswer(models.Model):
    answer = models.CharField(max_length=200)
    question = models.ForeignKey(Question)
    number = models.IntegerField(blank=True)
    
    def __unicode__(self):
        return self.answer

    class Meta:
        unique_together = ("question", "number")

    def save(self, *args, **kwargs):
        # if number is blank, make it be the next number for the question
        if self.number is None:
            max_number = self.question.mathwriteinanswer_set.aggregate(Max('number'))
            max_number = max_number['number__max']
            if max_number:
                self.number= max_number+1
            else:
                self.number = 1
                
        super(MathWriteinAnswer, self).save(*args, **kwargs) 


class AssessmentType(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    privacy_level = models.SmallIntegerField(default=0)
    privacy_level_solution = models.SmallIntegerField(default=0)
    def __unicode__(self):
        return  self.name

class Assessment(models.Model):
    code = models.SlugField(max_length=200, unique=True)
    name = models.CharField(max_length=200, unique=True)
    assessment_type = models.ForeignKey(AssessmentType)
    description = models.CharField(max_length=400,blank=True, null=True)
    questions = models.ManyToManyField(Question, through='QuestionAssigned')
    fixed_order = models.BooleanField(default=False)
    instructions = models.TextField(blank=True, null=True)
    time_limit = models.CharField(max_length=20, blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    groups_can_view = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view")
    groups_can_view_solution = models.ManyToManyField(Group, blank=True, null=True, related_name = "assessments_can_view_solution")
    
    def __unicode__(self):
        return  self.name

    def return_link(self, **kwargs):
        try:
            link_text=kwargs["link_text"]
        except KeyError:
            link_text="%s: %s" % (self.assessment_type.name,self.name)
        try:
            link_class=kwargs["link_class"]
        except KeyError:
            link_class='assessment'
        try:
            seed=kwargs["seed"]
        except KeyError:
            seed="1"
        link_title="%s: %s" % (self.name,self.description)
        
        if seed is None:
            seed_arg = ""
        else:
            seed_arg = "?seed=%s" % seed
        return mark_safe('<a href="%s%s" class="%s" title="%s">%s</a>' % (self.get_absolute_url(), seed_arg, link_class,  link_title, link_text))

    def get_title(self):
        return self.name


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
    def get_solution_url(self):
        return('mit-assessmentsolution', (), {'assessment_type': self.assessment_type.code, 'assessment_code': self.code})

    class Meta:
        permissions = (
            ("view_assessment_1", "Can view 1"),
            ("view_assessment_1_solution", "Can view 1 solution"),
            ("view_assessment_2", "Can view 2"),
            ("view_assessment_2_solution", "Can view 2 solution"),
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


    def render_question_list(self, seed=None, user=None):
        if seed is not None:
            random.seed(seed)
            
        question_list = self.get_question_list(seed)

        rendered_question_list = []

        for (i, question) in enumerate(question_list):

            # use qa for identifier since coming from assessment
            identifier="qa%s" % i

            the_question = question['question']
            question_context = the_question.setup_context(seed=question['seed'],
                                                          identifier=identifier)
            
            # if there was an error, question_context is a string string,
            # so just make rendered question text be that string
            if not isinstance(question_context, dict):
                question_text = question_context
            else:
                question_text = the_question.render_question(question_context, user=user, identifier=identifier)


            rendered_question_list.append({'question_text': question_text,
                                           'question': the_question,
                                           'points': question['points'],
                                           'seed': question['seed'],
                                           'question_set': question['question_set']})
        if not self.fixed_order:
            random.shuffle(rendered_question_list)
        

        return rendered_question_list

    def render_solution_list(self, seed=None):
        if seed is not None:
            random.seed(seed)
            
        question_list = self.get_question_list(seed)

        rendered_solution_list = []

        for (i, question) in enumerate(question_list):

            # use qa for identifier since coming from assessment
            identifier="qa%s" % i

            solution_dict = question

            the_question = question['question']
            question_context = the_question.setup_context(seed=question['seed'],
                                                          identifier=identifier)
            
            # if there was an error, question_context is a string string,
            # so just make rendered question text be that string
            if not isinstance(question_context, dict):
                question_text = question_context
                solution_text = question_context
            else:
                question_text = the_question.render_question(question_context,
                                                          identifier=identifier)
                solution_text = the_question.render_solution(question_context,
                                                          identifier=identifier)

            solution_dict['question_text'] = question_text
            solution_dict['solution_text'] = solution_text

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

    def total_points(self):
        total_points=0
        for question_set in self.question_sets():
            the_points = self.points_of_question_set(question_set)
            if the_points:
                total_points += the_points
        return total_points


    def avoid_question_seed(self, avoid_list):
        
        avoid_list = [item.strip() for item in avoid_list.split(",")]
        
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

        for seed in range(1000):

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
                    

class QuestionSetDetail(models.Model):
    assessment = models.ForeignKey(Assessment)
    question_set = models.SmallIntegerField(default=0,db_index=True)
    points = models.IntegerField(default=0)

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
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=10)
    increment = models.FloatField(default=1)
    
    class Meta:
        unique_together = ("name", "question")

    def __unicode__(self):
        return  self.name

    def get_sample(self):
        num_possibilities = 1+int(ceil((self.max_value-self.min_value)/self.increment))
        choices=(self.min_value+n*self.increment for n in range(num_possibilities))
        the_num = random.choice(list(choices))

        # if the_num is an integer, convert to integer so don't have decimal
        if int(the_num)==the_num:
            the_num = int(the_num)
        else:
            # try to round the answer to the same number of decimal places
            # as the input values
            # seems to help with rounding error with the float arithmetic
            for i in range(1,11):
                if(round(self.min_value*pow(10,i)) == self.min_value*pow(10,i)
                   and round(self.max_value*pow(10,i)) == self.max_value*pow(10,i)
                   and round(self.increment*pow(10,i)) == self.increment*pow(10,i)):
                    the_num = round(the_num,i)
                    break
                
        return the_num
    


class RandomWord(models.Model):
    name = models.SlugField(max_length=50)
    question = models.ForeignKey(Question)
    option_list = models.CharField(max_length=400)
    plural_list = models.CharField(max_length=400, blank=True, null=True)
    group = models.CharField(max_length=50, blank=True, null=True)
    sympy_parse = models.BooleanField()

    class Meta:
        unique_together = ("name", "question")
        
    def __unicode__(self):
        return  self.name

    def get_sample(self, index=None):
        
        # turn comma separated list to python list. 
        # strip off leading/trailing whitespace
        option_list = [item.strip() for item in self.option_list.split(",")]
        plural_list = [item.strip() for item in self.plural_list.split(",")]
        
        # if index isn't prescribed, generate randomly
        if index is None:
            index = random.randrange(len(option_list))
        the_word=None
        if self.sympy_parse:
            from sympy.parsing.sympy_parser import parse_expr
            try:
                the_word = sympy_word(parse_expr(option_list[index], local_dict=create_greek_dict()))
            except:
                pass
        if not the_word:
            the_word = option_list[index]
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
    expand = models.BooleanField()
    n_digits = models.IntegerField(blank=True, null=True)
    round_decimals = models.IntegerField(blank=True, null=True)
    question = models.ForeignKey(Question)
    function_inputs = models.CharField(max_length=50, blank=True, null=True)
    figure = models.IntegerField(blank=True, null=True)
    linestyle = models.CharField(max_length=10, blank=True, null=True)
    linewidth = models.IntegerField(blank=True, null=True)
    xmin = models.FloatField(blank=True, null=True)
    xmax = models.FloatField(blank=True, null=True)
    use_ln = models.BooleanField()
    #pre_eval_subs = models.CharField(max_length=100, blank=True, null=True)
    #post_eval_subs = models.CharField(max_length=100, blank=True, null=True)
    sort_order = models.FloatField(default=0)
    class Meta:
        unique_together = ("name", "question")
        ordering = ['sort_order','id']

    def __unicode__(self): 
        return  self.name

    def evaluate(self, substitutions, function_dict):

        from sympy.parsing.sympy_parser import parse_expr

        expression = parse_expr(self.expression,local_dict=function_dict,convert_xor=True)


        # if self.pre_eval_subs:
        #     pre_eval_sub_list = []
        #     for item in self.pre_eval_subs.split(","):
        #         sub_pair = item.strip().split(':')
        #         if len(sub_pair==2):
        #             pre_eval_sub_list.append( (sub_pair[0].strip(), sub_pair[1].strip()) )
        #     if pre_eval_sub_list:
        #         expression=expression.subs(pre_eval_sub_list)


        try: 
            expression=expression.subs(substitutions)
        except AttributeError:
            pass
        try: 
            expression=expression.doit()
        except AttributeError:
            pass
        
        if self.expand:
            expression=expression.expand()

        if self.function_inputs:
            input_list = [item.strip() for item in self.function_inputs.split(",")]
            # if any input variables are in substitution list, need to remove
            slist_2=[s for s in substitutions if s[0] not in input_list]
            expr2= parse_expr(self.expression,local_dict=function_dict,convert_xor=True).subs(slist_2).doit()

            from sympy.utilities.lambdify import lambdify
            the_function = lambdify(input_list, expr2)
            function_dict[self.name] = the_function
            
        return evaluated_expression(expression, n_digits=self.n_digits, round_decimals=self.round_decimals, use_ln=self.use_ln)


class SympyCommandSet(models.Model):
    name = models.CharField(max_length=50, unique=True)
    commands = models.TextField()

    def __unicode__(self):
        return self.name
