from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Question, QuestionAnswerOption, Expression
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
import logging

logger = logging.getLogger(__name__)


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
            if round(float(thevalue),3) != 1.0:
                use_plural=True
        except (ValueError, TypeError):
            pass

        if use_plural:
            return self.word_plural.resolve(context)
        else:
            return self.word.resolve(context)


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

        local_dict = context["_sympy_local_dict_"]

        from mitesting.math_objects import math_object
        from mitesting.sympy_customized import parse_and_process, EVALUATE_NONE

        expression = parse_and_process(expression,
                                       local_dict=local_dict,
                                       evaluate_level=EVALUATE_NONE)

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


@register.inclusion_tag('mitesting/question_body.html')
def question_body(question_data):
    return {'question_data': question_data}

@register.inclusion_tag('mitesting/question_solution_body.html')
def question_solution_body(question_data):
    return {'question_data': question_data}

    

def _render_question(question, rng, seed, context):


    questions_rendered = context.get('_questions_rendered',0)
    questions_rendered += 1
    context['_questions_rendered'] = questions_rendered

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
        raise TemplateSyntaxError("%r tag requires at least one argument" \
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
            rows=int(kwargs['rows'])
        except:
            rows=3
        try:
            cols=int(kwargs['cols'])
        except:
            cols=20
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
            answer_code_dict = answer_data['valid_answer_codes']\
                               [self.answer_code]
            answer_type=answer_code_dict['answer_type']
            expression_type=answer_code_dict.get('expression_type')
        except KeyError:
            return return_error("Invalid answer blank: %s" % self.answer_code)

        answer_number = len(answer_data['answer_info'])+1
        question_identifier = answer_data['question_identifier']
        answer_identifier = "%s_%s" % (answer_number, question_identifier)
        answer_field_name = 'answer_%s' % answer_identifier

        if answer_data['readonly']:
            readonly_string = ' readonly'
        else:
            readonly_string = ''

        assign_to_expression = kwargs.get('assign_to_expression')
        expressionfromanswer = None
        if assign_to_expression and \
           context.get("_process_expressions_from_answers"):
            question=context.get('question')
            if question:
                expressionfromanswer, created= \
                    question.expressionfromanswer_set.get_or_create(
                        name=assign_to_expression, answer_code=self.answer_code,
                        answer_number=answer_number,
                        split_symbols_on_compare=\
                        answer_code_dict['split_symbols_on_compare'],
                        answer_type=answer_type,
                    )
        given_answer=None
        try:
            prefilled_answers = answer_data['prefilled_answers']
            the_answer_dict = prefilled_answers[answer_number-1]

            if the_answer_dict["code"] == self.answer_code:
                given_answer = the_answer_dict["answer"]
            else:
                logger.warning("Invalid previous answer for question %s: %s != %s" % 
                    (answer_data.get("question"), the_answer_dict["code"], 
                     self.answer_code))
        except (KeyError, IndexError, TypeError):
            pass

        answer_data['answer_info'].append(\
            {'code': self.answer_code, 'points': points, 
             'type': answer_type, 'identifier': answer_identifier,
             'group': group, 'assign_to_expression': assign_to_expression,
             'prefilled_answer': given_answer,
             'expression_type': expression_type})

        if answer_type == QuestionAnswerOption.EXPRESSION or \
           answer_type == QuestionAnswerOption.FUNCTION:
            
            value_string = ''

            if expression_type == Expression.MATRIX:
                if given_answer is not None:
                    value_string = given_answer                
                input_html = '<span class="matrix"><textarea class=mi_answer" id="id_%s" name="%s" rows=%s cols=%s>%s</textarea></span>' %\
                    (answer_field_name, answer_field_name,
                     rows, cols, value_string)
            else:
                if given_answer is not None:
                    value_string = ' value="%s"' %  given_answer
                input_html = '<input class="mi_answer" type="text" id="id_%s" maxlength="200" name="%s" size="%i"%s%s />' % \
                    (answer_field_name, answer_field_name,
                     size, readonly_string, value_string, )
                
            return '<span style="vertical-align: middle; display: inline-block;">%s<br/><span class="info answerfeedback_%s" id="%s_feedback"></span></span>' % \
                (input_html,
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

            if expressionfromanswer:
                mc_answer_dict = {}
                for a in rendered_answer_list:
                    mc_answer_dict[a['answer_id']]=a['rendered_answer']
                import pickle
                expressionfromanswer.answer_data=pickle.dumps(mc_answer_dict)
                expressionfromanswer.save()

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

