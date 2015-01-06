from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Question, QuestionAnswerOption
from mitesting.render_assessments import get_new_seed, render_question
from mitesting.forms import MultipleChoiceQuestionForm
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from django.template.base import kwarg_re
import re
from django.contrib.sites.models import Site
from django.db.models import  Max
from django.utils.encoding import force_unicode
from django.utils.encoding import smart_text
import json
from math import floor, ceil
from django.utils.safestring import mark_safe


register=Library()


class PluralizeWordNode(Node):
    def __init__(self, value, word, word_plural):
        self.value=value
        self.word=word
        self.word_plural=word_plural
    def render(self, context):
        
        use_plural=False
        thevalue = self.value.resolve(context)
        try:
            if int(thevalue) != 1:
                use_plural=True
        except:
            pass

        # except ValueError: # Invalid string that's not a number.
        #     pass
        # except TypeError: # Value isn't a string or a number; maybe it's a list?
        #     try:
        #         if len(thevalue) != 1:
        #             use_plural=True
        #     except TypeError: # len() of unsized object.
        #         pass
    
        if use_plural:
            return self.word_plural.resolve(context)
        else:
            return self.word.resolve(context)
        # if use_plural:
        #     try:
        #         return template.Variable(self.word+"_plural").resolve(context)
            
        #     except:
        #         return ""

        # else:
        #     try:
        #         return  template.Variable(self.word).resolve(context)
        #     except:
        #         return ""


@register.tag
def pluralize_word(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise TemplateSyntaxError("%r tag requires two arguments" % bits[0])
    value=parser.compile_filter(bits[1])
    word=parser.compile_filter(bits[2])
    # word_plural is the same as word but with "_plural" appended
    # check if word has a filter, if so add "_plural" before |
    word_string = bits[2]
    if "|" in word_string:
        word_string = word_string.replace("|","_plural|",1)
    else:
        word_string = word_string.rstrip() + "_plural"
    word_plural=parser.compile_filter(word_string)

    return PluralizeWordNode(value, word, word_plural)


class ExprNode(Node):
    def __init__(self, expression, asvar, kwargs):
        self.expression = expression
        self.asvar = asvar
        self.kwargs = kwargs
    def render(self, context):

        kwargs = dict([(k, v.resolve(context))
                       for k, v in self.kwargs.items()])

        expression = force_unicode(self.expression.resolve(context))

        global_dict = context["_sympy_global_dict_"]

        from mitesting.math_objects import math_object
        from mitesting.sympy_customized import parse_and_process

        expression = parse_and_process(expression,
                                       global_dict=global_dict)

        expression=math_object(expression, **kwargs)

        if self.asvar:
            context[self.asvar] = expression
            return ''
        else:
            return expression


@register.tag
def expr(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag requires at least one argument" \
                                      % str(bits[0]))
    expression = parser.compile_filter(bits[1])

    asvar = None
    kwargs = {}
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %r tag" \
                                              % str(bits[0]))
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)

    
    return ExprNode(expression, asvar, kwargs)

    
@register.inclusion_tag("mitesting/exam_header.html", takes_context=True)
def new_exam_page(context):
    return {
        'course': context.get('course'),
        'assessment_date': context.get('assessment_date'),
        'assessment_short_name': context.get('assessment_short_name'),
        'version_string': context.get('version_string'),
        }


@register.filter
def addplus(text):
    input_val = force_unicode(text)
    
    negative_number = False
    try:
        # take out any commas before testing for negative number
        val_no_commas = re.sub(',','',input_val)
        if float(val_no_commas) < 0:
            negative_number = True
    except: 
        try:
            if input_val[0] == '-':
                negative_number = True
        except:
            pass
    
    if negative_number:
        return input_val
    else:
        return "+" + input_val
addplus.is_safe = True

    
@register.filter
def invisible_one(text):
    input_val = force_unicode(text)
    
    try:
        plus_added = False
        if input_val[0] == "+":
            plus_added = True

        float_val = float(input_val)
        if float_val == 1:
            if plus_added:
                return "+"
            else:
                return ""
        if float_val == -1:
            return "-"
    except:
        pass
            
    return input_val
invisible_one.is_safe = True

def color_from_linestyle(linestyle):
    if 'k' in linestyle:
        return '#000'
    elif 'b' in linestyle:
        return '#0000FF'
    elif 'r' in linestyle:
        return '#FF0000'
    elif 'g' in linestyle:
        return '#00FF00'
    elif 'c' in linestyle:
        return '#00FFFF'
    elif 'm' in linestyle:
        return
    return None

def linepattern_from_linestyle(linestyle):
    dashmatch = re.search('([-.]+)',linestyle)
    if dashmatch:
        return dashmatch.group()
    else:
        return None

def markerpattern_from_linestyle(linestyle):
    if 'fo' in linestyle:
        return 'filledCircle'
    elif 'fs' in linestyle:
        return 'filledSquare'
    elif 'fd' in linestyle:
        return 'filledDiamond'
    elif 'o' in linestyle:
        return 'circle'
    elif 'x' in linestyle:
        return 'x'
    elif 's' in linestyle:
        return 'square'
    elif 'd' in linestyle:
        return 'diamond'
    else:
        return None

def convert_greek_to_unicode(string):

    greek = {'\[alpha\]':u'\u03b1', '\[beta\]':u'\u03b2', '\[gamma\]':u'\u03b3', '\[delta\]':u'\u03b4', '\[epsilon\]':u'\u03b5', '\[zeta\]':u'\u03b6', '\[eta\]':u'\u03b7', '\[theta\]':u'\u03b8', '\[kappa\]':u'\u03ba', '\[lambda\]':u'\u03bb', '\[mu\]':u'\u03bc', '\[nu\]':u'\u03bd', '\[xi\]':u'\u03be', '\[pi\]':u'\u03c0', '\[rho\]':u'\u03c1', '\[sigma\]':u'\u03c3', '\[tau\]':u'\u03c4', '\[upsilon\]':u'\u03c5', '\[phi\]':u'\u03c6', '\[chi\]':u'\u03c7', '\[psi\]':u'\u03c8', '\[omega\]':u'\u03c9', '\[Gamma\]':u'\u0393', '\[Delta\]':u'\u0394', '\[Theta\]':u'\u0398', '\[Lambda\]':u'\u039b', '\[Xi\]':u'\u039e', '\[Pi\]':u'\u03A1', '\[Sigma\]':u'\u03A3', '\[Upsilon\]':u'\u03A5', '\[Phi\]':u'\u03A6', '\[Psi\]':u'\u03A8', '\[Omega\]':u'\u03A9'}

    for k in greek.keys():
        string=re.sub(k, greek[k], string)

    return string

def convert_to_superscript_unicode(string):

    superscripts={'0': u'\u2070', '1':u'\u00b9', '2':u'\u00b2', '3':u'\u00b3', '4':u'\u2074', '5':u'\u2075', '6':u'\u2076', '7':u'\u2077', '8':u'\u2078', '9':u'\u2079', '\+':u'\u207a', '\-':u'\u207b', '\=':u'\u207c', '\(':u'\u207d', '\)':u'\u207e', 'a':u'\u1d43', 'b':u'\u1d47', 'c':u'\u1d9c', 'd':u'\u1d48', 'e':u'\u1d49', 'f':u'\u1da0', 'g':u'\u1d4d', 'h':u'\u02b0', 'i':u'\u2071', 'j':u'\u02b2', 'k': u'\u1d4f', 'l':u'\u02e1', 'm':u'\u1d50', 'n':u'\u207f', 'o':u'\u1d52', 'p':u'\u1d56', 'r':u'\u02b3', 's':u'\u02e2', 't':u'\u1d57', 'u':u'\u1d58', 'v':u'\u1d5b', 'w':u'\u02b7', 'x':u'\u02e3', 'y':u'\u02b8', 'z':u'\u1dbb', u'\u03b1':u'\u1d45', u'\u03b2':u'\u1d5d', u'\u03b3':u'\u1d5e', u'\u03b4': u'\u1d5f', u'\u03b5':u'\u1d4b', u'\u03b8':u'\u1dbf', u'\u03c4':u'\u1da5', u'\u03c6':u'\u1db2', u'\u03c8':u'\u1d60', u'\u03c7':u'\u1d61' }

    for k in superscripts.keys():
        string=re.sub(k, superscripts[k], string)

    return string


def convert_to_subscript_unicode(string):

    subscripts = { '0':u'\u2080', '1':u'\u2081', '2':u'\u2082', '3':u'\u2083', '4':u'\u2084', '5':u'\u2085', '6':u'\u2086', '7':u'\u2087', '8':u'\u2088', '9':u'\u2089', '\+':u'\u208a', '\-':u'\u208b', '\=':u'\u208c', '\(':u'\u208d', '\)':u'\u208e', 'a':u'\u2090', 'e':u'\u2091', 'h':u'\u2095', 'i':u'\u1d62', 'j':u'\u2c7c', 'k':u'\u2096', 'l':u'\u2097', 'm':u'\u2098', 'n':u'\u2099', 'o':u'\u2092', 'p':u'\u209a', 'r':u'\u1d63', 's':u'\u209b', 't':u'\u209c', 'u':u'\u1d64', 'v':u'\u1d65', 'x':u'\u2093', u'\u03b2':u'\u1d66', u'\u03b3':u'\u1d67', u'\u03c1':u'\u1d68', u'\u03c8':u'\u1d69', u'\u03c7':u'\u1d6a'}
    for k in subscripts.keys():
        string=re.sub(k, subscripts[k], string)

    return string



def convert_math_to_unicode(string):

    string=force_unicode(string)
    
    # first convert substring of form [greekletter] to the unicode greek symbol
    string = convert_greek_to_unicode(string)

    # find and replace any subscripts in braces
    found_subscript=True
    while found_subscript:
        m=re.search('(_{[^}]+})', string)
        if m:
            the_subscript=m.group(0)
            the_subscript_unicode=convert_to_subscript_unicode(the_subscript[2:-1])
            string=re.sub(re.escape(the_subscript), the_subscript_unicode, string)
        else:
            found_subscript=False

    # find and replace any single character subscripts
    found_subscript=True
    while found_subscript:
        m=re.search('(_[^{}])', string)
        if m:
            the_subscript=m.group(0)
            the_subscript_unicode=convert_to_subscript_unicode(the_subscript[1:])
            string=re.sub(re.escape(the_subscript), the_subscript_unicode, string)
        else:
            found_subscript=False

    # find and replace any superscripts in braces
    found_superscript=True
    while found_superscript:
        m=re.search('(\^{[^}]+})', string)
        if m:
            the_superscript=m.group(0)
            the_superscript_unicode=convert_to_superscript_unicode(the_superscript[2:-1])
            string=re.sub(re.escape(the_superscript), the_superscript_unicode, string)
        else:
            found_superscript=False
    
    # find and replace any single character superscripts
    found_superscript=True
    while found_superscript:
        m=re.search('(\^[^{}])', string)
        if m:
            the_superscript=m.group(0)
            the_superscript_unicode=convert_to_superscript_unicode(the_superscript[1:])
            string=re.sub(re.escape(the_superscript), the_superscript_unicode, string)
        else:
            found_superscript=False
    
    return string


def find_ticks(min_val, max_val, n_ticks_start=8):
    if not (min_val < max_val):
        return []
    
    # find d_tick to one significant digit
    d_tick = (max_val-min_val)/float(n_ticks_start)
    from math import log10
    n_decimals= -int(floor(log10(d_tick)))
    d_tick=round(d_tick, n_decimals)
    
    # d_tick digit is the one significant digit
    d_tick_digit = int(round(d_tick*10**(n_decimals)))

    # make d_tick_digit be 1, 2, or 5
    if d_tick_digit==8 or d_tick_digit==9:
        d_tick_digit=1
        n_decimals -= 1
    elif d_tick_digit==4 or d_tick_digit==6 or d_tick_digit==7:
        d_tick_digit=5
    elif d_tick_digit==3:
        d_tick_digit=2

    d_tick = round(d_tick_digit*0.1**n_decimals,n_decimals)
    

    # ticks should be multiples of d_tick
    first_tick = floor(min_val/d_tick)*d_tick
    n_ticks = int(ceil((max_val-first_tick)/d_tick)+1)
    

    ticks = [round(first_tick+i*d_tick,n_decimals) for i in range(n_ticks)]

    # if d_tick is an integer, make ticks integers
    if round(d_tick)==d_tick:
        ticks = [int(x) for x in ticks]

    return ticks


@register.inclusion_tag('mitesting/question_body.html')
def question_body(question_data):
    return {'question_data': question_data}

@register.inclusion_tag('mitesting/question_solution_body.html')
def question_solution_body(question_data):
    return {'question_data': question_data}

    

def _render_question(question, rng, seed, context):


    try: 
        questions_rendered = context['questions_rendered']
    except KeyError:
        questions_rendered = 0

    questions_rendered += 1
    context['questions_rendered'] = questions_rendered

    # use qtag in identifier since coming from tag
    identifier = "qtag_%s" % questions_rendered
    
    try:
        applet_data=context['_applet_data_']
    except KeyError:
        appet_data = Applet.return_initial_applet_data()
        context['_applet_data_'] = applet_data

    question_data = question.render(question_identifier=identifier,
                                    seed=seed, applet_data=applet_data,
                                    rng=rng)
    
    html_string = template.loader.render_to_string("mitesting/question_body.html",
                                                   {'question_data': question_data})
    
    
    html_string = '<div class="question">%s</div>' % html_string

    return html_string


class QuestionNode(template.Node):
    def __init__(self,question_id, seed):
        self.question_id = question_id
        self.seed = seed
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass
        
        question_id = self.question_id.resolve(context)
        if self.seed is None:
            seed=None
        else:
            seed = self.seed.resolve(context)
        
        # test if question with question_id exists
        try:
            thequestion=Question.objects.get(id=question_id)
        # if question does not exist, mark as broken. 
        except ObjectDoesNotExist:

            # if blank style,
            # and show that it is broken so can search for it
            if(blank_style):
                return " BRKNQST "
            else:
                return "<p>[Broken Question, question not found]</p>"
            
        try:
            rng = context['_answer_data_']['rng']
        except:
            import random
            rng = random.Random()


        if seed is None:
            seed = get_new_seed(rng)
            
        return _render_question(thequestion, rng=rng, seed=seed, 
                                context=context)


@register.tag
def display_question(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag requires at least one arguments" \
                                      % bits[0])
    
    question_id=parser.compile_filter(bits[1])
  
    if len(bits) > 2:
        seed = parser.compile_filter(bits[2])
    else:
        seed = None
    return QuestionNode(question_id, seed)


class VideoQuestionsNode(template.Node):
    def __init__(self,video_code,seed):
        self.video_code = video_code
        self.seed=seed
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass
        
        if self.seed is None:
            seed=None
        else:
            seed = self.seed.resolve(context)
        video_code = self.video_code.resolve(context)
        # test if video with video_code exists
        try:
            thevideo=Video.objects.get(code=video_code)
        # if video does not exist, mark as broken. 
        except ObjectDoesNotExist:

            # if blank style,
            # and show that it is broken so can search for it
            if(blank_style):
                return " BRKNQST "
            else:
                return "<p>[Broken Question, video not found]</p>"

        # render for each question associated with video
        html_string=""

        try:
            rng = context['_answer_data_']['rng']
        except:
            import random
            rng = random.Random()

        if seed is not None:
            rng.seed(seed)

        for videoquestion in thevideo.videoquestion_set.all():
            question = videoquestion.question
            question_seed = get_new_seed(rng)
            html_string += _render_question(question, rng=rng, seed=seed, 
                                            context=context)

        return html_string


@register.tag
def display_video_questions(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag requires at least one arguments" \
                                      % bits[0])
    
    video_code=parser.compile_filter(bits[1])

    if len(bits) > 2:
        seed = parser.compile_filter(bits[2])
    else:
        seed = None

    return VideoQuestionsNode(video_code, seed)



class AnswerNode(template.Node):
    def __init__(self, answer_code, kwargs):
        self.answer_code = answer_code
        self.kwargs = kwargs
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        
        try: 
            size=int(kwargs['size'])
        except:
            size=20
        try:
            points=float(kwargs['points'])
        except:
            points=1
        group = kwargs.get('group')
            
        try:
            answer_data = context['_answer_data_']
        except KeyError:
            return "[No answer data]"


        def return_error(message):
            answer_data['error']=True
            answer_data['answer_errors'].append(message)
            return "[%s]" % message
        
        # answer code should be a code defined in the question answer options
        try:
            answer_type = answer_data['valid_answer_codes'][self.answer_code]
        except KeyError:
            return return_error("Invalid answer blank: %s" % self.answer_code)

        answer_number = len(answer_data['answer_info'])+1
        question_identifier = answer_data['question_identifier']
        answer_identifier = "%s_%s" % (answer_number, question_identifier)
        answer_field_name = 'answer_%s' % answer_identifier
        answer_data['answer_info'].append(\
            {'code': self.answer_code, 'points': points, 
             'type': answer_type, 'identifier': answer_identifier, 'group': group })

        if answer_data['readonly']:
            readonly_string = ' readonly'
        else:
            readonly_string = ''

        given_answer=None
        try:
            prefilled_answers = answer_data['prefilled_answers']
            the_answer_dict = prefilled_answers[answer_number-1]

            if the_answer_dict["code"] == self.answer_code:
                given_answer = the_answer_dict["answer"]
            else:
                answer_data['error'] = True
                answer_data['answer_errors'].append(
                    "Invalid previous answer: %s != %s" % 
                (the_answer_dict["code"], self.answer_code))
        except (KeyError, IndexError, TypeError):
            pass

        if answer_type == QuestionAnswerOption.EXPRESSION or \
           answer_type == QuestionAnswerOption.FUNCTION:

            value_string = ''
            if given_answer is not None:
                value_string = ' value="%s"' %  given_answer
                
            return '<span style="vertical-align: middle; display: inline-block;"><input class="mi_answer" type="text" id="id_%s" maxlength="200" name="%s" size="%i"%s%s /><br/><span class="info answerfeedback_%s" id="%s_feedback"></span></span>' % \
                (answer_field_name, answer_field_name,
                 size, readonly_string, value_string, 
                 question_identifier, answer_field_name)

        elif answer_type == QuestionAnswerOption.MULTIPLE_CHOICE:
            try:
                question = answer_data["question"]
            except KeyError:
                return return_error("Invalid answer_data")

            answer_options = question.questionansweroption_set.filter(
                answer_type=QuestionAnswerOption.MULTIPLE_CHOICE,
                answer_code=self.answer_code)
            
            rendered_answer_list=[]
            for answer in answer_options:
                template_string = "{% load testing_tags mi_tags humanize %}"
                template_string += answer.answer
                try:
                    t = Template(template_string)
                    rendered_answer = mark_safe(t.render(context))
                except TemplateSyntaxError as e:
                    return return_error("Invalid multiple choice answer: %s" \
                                            % self.answer_code)
                rendered_answer_list.append({
                        'answer_id': answer.id,
                        'rendered_answer': rendered_answer})
            answer_data['rng'].shuffle(rendered_answer_list)
        
            html_string = ""
            if kwargs.get("select"):
                html_string += "<option></option>"
                for answer in rendered_answer_list:
                    ans_id = answer['answer_id']
                    selected_string = ""
                    if given_answer is not None:
                        if str(ans_id) == str(given_answer):
                            selected_string = " selected"
                    html_string += '<option id="id_%s_%s" value="%s"%s> %s</option>' % \
                        (answer_field_name, ans_id, 
                         ans_id, selected_string, answer['rendered_answer'] )
                html_string = '<select id="id_%s" name="%s" class="mi_select">%s</select>' % \
                              (answer_field_name, answer_field_name, html_string)
                html_string = '<span style="vertical-align: middle; display: inline-block;">%s<br/><span class="info answerfeedback_%s" id="%s_feedback"></span></span>'  %\
                              (html_string, question_identifier, answer_field_name)
            else:
                for answer in rendered_answer_list:
                    ans_id = answer['answer_id']
                    checked_string = ""
                    if given_answer is not None:
                        if str(ans_id) == str(given_answer):
                            checked_string = " checked"
                    html_string += '<li><label for="%s_%s" id="label_%s_%s"><input type="radio" id="id_%s_%s" value="%s" name="%s"%s%s /> %s</label></li>' % \
                        (answer_field_name, ans_id, answer_field_name,
                         ans_id, answer_field_name, ans_id, 
                         ans_id, answer_field_name, readonly_string, checked_string,
                         answer['rendered_answer'] )

                html_string = '<ul class="answerlist">%s</ul>' % html_string
                html_string += '<div class="info answerfeedback_%s" id="%s_feedback" ></div>' % \
                               (question_identifier, answer_field_name)
            
            return mark_safe(html_string)
        
        # if not recognized type, return error
        else:
            return return_error("Unrecognized answer type")

                
@register.tag
def answer(parser, token):
    bits = token.split_contents()

    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag requires at least one argument" \
                                      % bits[0])

    answer_code = bits[1]

    kwargs = {} 
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %r tag" \
                                              % str(bits[0]))
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)


    return AnswerNode(answer_code, kwargs)


class AssessmentUserCanViewNode(Node):
    def __init__(self, assessment, user, asvar):
        self.assessment = assessment
        self.user = user
        self.asvar = asvar
    def render(self, context):
        assessment = self.assessment.resolve(context)
        user = self.user.resolve(context)
        try:
            can_view=assessment.user_can_view(user)
        except:
            can_view= False

        if self.asvar:
            context[self.asvar]=can_view
            return ""
        else:
            return can_view


@register.tag
def assessment_user_can_view(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("%r tag requires at least two arguments" \
                                      % str(bits[0]))
    assessment = parser.compile_filter(bits[1])
    user = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return AssessmentUserCanViewNode(assessment, user, asvar)


@register.filter(is_safe=False)
def pluralize_float(value, arg='s'):
    """
    Returns a plural suffix if the value, rounded to nearest thousandth,
    is not 1. By default, 's' is used as the suffix:

    * If value is 0, vote{{ value|pluralize }} displays "0 votes".
    * If value is 1, vote{{ value|pluralize }} displays "1 vote".
    * If value is 2, vote{{ value|pluralize }} displays "2 votes".

    If an argument is provided, that string is used instead:

    * If value is 0, class{{ value|pluralize:"es" }} displays "0 classes".
    * If value is 1, class{{ value|pluralize:"es" }} displays "1 class".
    * If value is 2, class{{ value|pluralize:"es" }} displays "2 classes".

    If the provided argument contains a comma, the text before the comma is
    used for the singular case and the text after the comma is used for the
    plural case:

    * If value is 0, cand{{ value|pluralize:"y,ies" }} displays "0 candies".
    * If value is 1, cand{{ value|pluralize:"y,ies" }} displays "1 candy".
    * If value is 2, cand{{ value|pluralize:"y,ies" }} displays "2 candies".
    """
    if not ',' in arg:
        arg = ',' + arg
    bits = arg.split(',')
    if len(bits) > 2:
        return ''
    singular_suffix, plural_suffix = bits[:2]

    try:
        if round(float(value),3) != 1.0:
            return plural_suffix
    except ValueError: # Invalid string that's not a number.
        pass
    except TypeError: # Value isn't a string or a number; maybe it's a list?
        try:
            if len(value) != 1:
                return plural_suffix
        except TypeError: # len() of unsized object.
            pass
    return singular_suffix


@register.filter
def round(value, n=0):
    from mitesting.math_objects import math_object

    if isinstance(value,math_object):
        expression=value.return_expression()
        copy_from=value
    else:
        from sympy import sympify,SympifyError
        try:
            expression=sympify(value)
        except SympifyError:
            return value
        copy_from=None

    from mitesting.customized_commands import round_expression
    
    return math_object(round_expression(expression,n),
                       copy_parameters_from=copy_from)

@register.filter
def evalf(value, n_digits=15):
    from mitesting.math_objects import math_object

    if isinstance(value,math_object):
        expression=value.return_expression()
        copy_from=value
    else:
        from sympy import sympify,SympifyError
        try:
            expression=sympify(value)
        except SympifyError:
            return value
        copy_from=None

    from mitesting.customized_commands import evalf_expression
    
    return math_object(evalf_expression(expression,n_digits),
                       copy_parameters_from=copy_from)

