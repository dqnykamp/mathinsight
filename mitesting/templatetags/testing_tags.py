from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Question, QuestionAnswerOption
from mitesting.forms import MultipleChoiceQuestionForm
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
import re
import random
from django.contrib.sites.models import Site
from django.db.models import  Max
from django.utils.encoding import force_unicode
from django.utils.encoding import smart_text
import json
from math import floor, ceil

register=Library()

# do this until have Django 1.5, then add back to django.template.base  import
# Regex for token keyword arguments
kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")


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
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % bits[0]
    value=parser.compile_filter(bits[1])
    word=parser.compile_filter(bits[2])
    # word_plural is the same as word but with "_plural" appended
    # check if word has a filter, if so add "_plural" before |
    word_string = bits[2]
    if "|" in word_string:
        word_string = word_string.replace("|","_plural",1)
    else:
        word_string = word_string.rstrip() + "_plural"
    word_plural=parser.compile_filter(word_string)

    return PluralizeWordNode(value, word, word_plural)


# class FigureNode(Node):
#     def __init__(self, figure_number, args, kwargs):
#         self.figure_number = figure_number
#         self.args = args
#         self.kwargs = kwargs

#     def render(self, context):
#         args = [arg.resolve(context) for arg in self.args]
#         # for django 1.5
#         # kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
#         #                for k, v in self.kwargs.items()])
#         kwargs = dict([(k, v.resolve(context))
#                        for k, v in self.kwargs.items()])
#         kwargs_url_GET_string = ""
        
#         width=500
#         height=500
#         for k in kwargs.keys():
#             if k=='width':
#                 try:
#                     width = int(kwargs[k])
#                 except:
#                     pass
#             elif k=='height':
#                 try:
#                     height = int(kwargs[k])
#                 except:
#                     pass
#             else:
#                 if kwargs_url_GET_string:
#                     kwargs_url_GET_string += "&"
#                 kwargs_url_GET_string = "%s%s=%s" % (kwargs_url_GET_string, k, kwargs[k])

#         figure_number = self.figure_number.resolve(context)

#         if not figure_number:
#             return "[Broken figure]"
#             #raise TemplateSyntaxError("'figure' requires a non-empty first argument. ")

#         # find question
#         the_question = Variable("the_question").resolve(context)
        
#         # get URL for figure figure_number (fails if no function with figure=figure_number)
#         try:
#             url = reverse('mit-questionfigure', kwargs={'question_id':the_question.id, 'figure_number': figure_number})
#         except:
#             raise
            
#         if not the_question.function_set.filter(figure=figure_number):
#             return "[Broken figure]"
        
#         # find all random variables from question and add to GET arguments
#         for randnum in the_question.randomnumber_set.all():
#             randnum_value = Variable(randnum.name).resolve(context)
#             if kwargs_url_GET_string:
#                 kwargs_url_GET_string += "&"
#             kwargs_url_GET_string = "%s%s=%s" % (kwargs_url_GET_string, randnum.name, randnum_value)
            
#         return "<img src='%s?%s' width=%s height=%s>" %(url, kwargs_url_GET_string, width, height)
        


# @register.tag
# def figure(parser, token):
#     bits = token.split_contents()
#     if len(bits) < 2:
#         raise template.TemplateSyntaxError, "%r tag requires at least one argument" % str(bits[0])
    
#     figure_number = parser.compile_filter(bits[1])
#     args = []
#     kwargs = {}
#     bits = bits[2:]

#     if len(bits):
#         for bit in bits:
#             match = kwarg_re.match(bit)
#             if not match:
#                 raise TemplateSyntaxError("Malformed arguments to %r tag" % str(bits[0]))
#             name, value = match.groups()
#             if name:
#                 kwargs[name] = parser.compile_filter(value)
#             else:
#                 args.append(parser.compile_filter(value))

#     return FigureNode(figure_number, args, kwargs)


class ExprNode(Node):
    def __init__(self, expression, asvar, args, kwargs):
        self.expression = expression
        self.asvar = asvar
        self.args = args
        self.kwargs = kwargs
    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        # for django 1.5
        # kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
        #                for k, v in self.kwargs.items()])
        kwargs = dict([(k, v.resolve(context))
                       for k, v in self.kwargs.items()])

        expression = force_unicode(self.expression.resolve(context))

        try:
            function_dict = template.Variable("sympy_function_dict").resolve(context)
        except:
            function_dict = {}
        try:
            substitutions =  template.Variable("sympy_substitutions").resolve(context)
        except:
            subsitutions = []
        

        from sympy.parsing.sympy_parser import parse_expr
        expression = parse_expr(expression,local_dict=function_dict,convert_xor=True).subs(substitutions)

        from mitesting.models import evaluated_expression

        expression=evaluated_expression(expression, args, kwargs)

        if self.asvar:
            context[self.asvar] = expression
            return ''
        else:
            return expression


@register.tag
def expr(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % str(bits[0])
    expression = parser.compile_filter(bits[1])

    asvar = None
    args = []
    kwargs = {}
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %r tag" % str(bits[0]))
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    
    return ExprNode(expression, asvar, args, kwargs)

    
@register.inclusion_tag("mitesting/exam_header.html", takes_context=True)
def new_exam_page(context):
    return {
        'course': context['course'],
        'semester': context['semester'],
        'assessment_date': context['assessment_date'],
        'the_assessment_name': context['the_assessment_name'],
        'version': context['version'],
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
    except: pass
    
    if negative_number:
        return input_val
    else:
        return "+" + input_val
addplus.is_safe = True

    
@register.filter
def invisible_one(text):
    input_val = force_unicode(text)
    
    plus_added = False
    if input_val[0] == "+":
        plus_added = True

    try:
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


class FigureNode(Node):
    def __init__(self, figure_number, args, kwargs):
        self.figure_number = figure_number
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        xaxis_options=dict()
        yaxis_options=dict()

        args = [arg.resolve(context) for arg in self.args]
        # for django 1.5
        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        try: 
            width=int(kwargs['width'])
        except:
            width=500
        try:
            height=int(kwargs['height'])
        except:
            height=400
        try:
            xmin=float(kwargs['xmin'])
        except:
            xmin=-10.0
        try:
            xmax=float(kwargs['xmax'])
        except:
            xmax=10.0
        try:
            ymin=float(kwargs['ymin'])
        except:
            ymin=None
        try:
            ymax=float(kwargs['ymax'])
        except:
            ymax=None

        

        try:
            xaxis_options['label'] = convert_math_to_unicode(kwargs['xlabel'])
            xaxis_options['labelRenderer'] = '$.jqplot.CanvasAxisLabelRenderer'
            xaxis_options['labelOptions']=dict()
            xaxis_options['labelOptions']['textColor']='#222'
        except:
            pass

        try:
            yaxis_options['label'] = convert_math_to_unicode(kwargs['ylabel'])
            yaxis_options['labelRenderer'] = '$.jqplot.CanvasAxisLabelRenderer'
            yaxis_options['labelOptions']=dict()
            yaxis_options['labelOptions']['textColor']='#222'
        except:
            pass

        # also try xlabel, ylabel, linestyle, linewidth, ylim
            

        n_points=200
        dx = (xmax-xmin)/(n_points-1)
        x = [xmin+i*dx for i in range(n_points)]

        figure_number = self.figure_number.resolve(context)

        if not figure_number:
            return "[Broken figure]"
            #raise TemplateSyntaxError("'figure' requires a non-empty first argument. ")

        # find question
        the_question = context['the_question']
        function_dict = context['sympy_function_dict']

        combined_text=''
        point_lists=[]
        series_option_list=[]

        for expression in the_question.expression_set.filter(figure=figure_number):
            if expression.function_inputs:
                series_options=dict()
                the_function = function_dict[expression.name]
                this_x = x
                if expression.xmin is not None or expression.xmax is not None:
                    if expression.xmin is not None:
                        this_xmin=expression.xmin
                    else:
                        this_xmin=xmin
                    if expression.xmax is not None:
                        this_xmax=expression.xmax
                    else:
                        this_xmax=xmax
                    this_n_points = int(ceil(n_points/(xmax-xmin)*(this_xmax-this_xmin)))
                    this_dx = (this_xmax-this_xmin)/(this_n_points-1)
                    this_x = [this_xmin+i*this_dx for i in range(this_n_points)]

                point_lists.append([(i,the_function(i)) for i in this_x])
                series_options['lineWidth'] = 1
                if expression.linewidth:
                    try:
                        series_options['lineWidth'] = float(expression.linewidth)
                    except:
                        pass
                if expression.linestyle:
                    color = color_from_linestyle(expression.linestyle)
                    if color:
                        series_options['color']=color
                    linePattern = linepattern_from_linestyle(expression.linestyle)
                    if linePattern:
                        series_options['linePattern']=linePattern
                series_option_list.append(series_options)
            
        if len(point_lists)==0:
            return "[Broken figure]"

        thedata=json.dumps(point_lists)

        plot_options=dict()
        plot_options['seriesDefaults']=dict()
        plot_options['seriesDefaults']['shadow']=False
        plot_options['seriesDefaults']['showMarker']=False
        
        plot_options['series'] = series_option_list

        plot_options['axesDefaults']=dict()
        plot_options['axesDefaults']['tickOptions']=dict()
        plot_options['axesDefaults']['tickOptions']['showGridline']=False

        xaxis_options['pad']=0
        xaxis_options['min']=xmin
        xaxis_options['max']=xmax

        xticks = find_ticks(xmin,xmax,width/50.0)
        xaxis_options['ticks']=xticks
        try:
            if isinstance(xticks[0],int):
                xaxis_options['tickOptions']=dict()
                xaxis_options['tickOptions']['formatString']='%.0f'
        except:
            pass

        
        if ymin is not None or ymax is not None:
            if ymin is None:
                ymin=ymax
                for ptl in point_lists:
                    for pt in ptl:
                        ymin = min(ymin, pt[1])
                ymin=ymin-(ymax-ymin)*0.1

            if ymax is None:
                ymax=ymin
                for ptl in point_lists:
                    for pt in ptl:
                        ymax = max(ymax, pt[1])
                
                ymax=ymax+(ymax-ymin)*0.1

            yticks = find_ticks(ymin,ymax,height/70.0)
            yaxis_options['ticks']=yticks
            try:
                if isinstance(yticks[0],int):
                    yaxis_options['tickOptions']=dict()
                    yaxis_options['tickOptions']['formatString']='%.0f'
            except:
                pass

        if ymin is not None:
            yaxis_options['min']=ymin
        if ymax is not None:
            yaxis_options['max']=ymax

        plot_options['axes']=dict()
        plot_options['axes']['xaxis']=xaxis_options
        plot_options['axes']['yaxis']=yaxis_options

        plot_options['grid']=dict()
        plot_options['grid']['shadow']=False
        plot_options['grid']['background']='#fff'
        plot_options['grid']['borderColor']='#222'

        

        # jqplot needs the CanvasAxisLabelRenderer reference to not be in quotes
        plot_options_string = json.dumps(plot_options)\
            .replace('"$.jqplot.CanvasAxisLabelRenderer"', \
                         '$.jqplot.CanvasAxisLabelRenderer')

        try:
            plotnum = context['plotnum']+1
        except KeyError:
            plotnum = 1
        context['plotnum']=plotnum

        html_string = '<div class="plot"><div id="jqplot_%s" style="width:%spx;height:%spx;"></div></div>\n' % (plotnum, width, height)
        html_string += '<script type="text/javascript">\n'
        html_string += '$(document).ready(function () {\n'
        html_string += "    $.jqplot('jqplot_%s', %s, %s);\n" % (plotnum, thedata, plot_options_string)
        html_string += '});\n</script>'
        return html_string


@register.tag
def figure(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % str(bits[0])
    
    figure_number = parser.compile_filter(bits[1])
    args = []
    kwargs = {} 
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %r tag" % str(bits[0]))
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return FigureNode(figure_number, args, kwargs)


def _render_question(question, seed, context):


    try: 
        questions_rendered = context['questions_rendered']
    except KeyError:
        questions_rendered = 0

    questions_rendered += 1
    context['questions_rendered'] = questions_rendered

    # use qtag in identifier since coming from tag
    identifier = "qtag_%s" % questions_rendered
    
    question_context = question.setup_context(identifier=identifier,
                                              seed=seed)

    html_string = '<div class="question">%s</div>' % \
        question.render_question(question_context, identifier = identifier)
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
            
        if seed is None:
            seed = thequestion.get_new_seed()
            
        return _render_question(thequestion, seed, context)


@register.tag
def display_question(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    
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

        if seed is not None:
            random.seed(seed)

        for question in thevideo.question_set.all():
            question_seed = question.get_new_seed()
            html_string += _render_question(question, seed, context)

        return html_string


@register.tag
def display_video_questions(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    
    video_code=parser.compile_filter(bits[1])

    if len(bits) > 2:
        seed = parser.compile_filter(bits[2])
    else:
        seed = None

    return VideoQuestionsNode(video_code, seed)



class AnswerBlankNode(template.Node):
    def __init__(self, answer_expression, answer_expression_string, size):
        self.answer_expression = answer_expression
        self.answer_expression_string = answer_expression_string
        self.size = size
    def render(self, context):

        answer_dict = context.get('answer_dict',{})

        # answer expression should refer to an expression that is
        # defined in the question context
        try:
            answer_expression = self.answer_expression.resolve(context)
        except:
            return ""
        
        answer_dict[self.answer_expression_string] = answer_expression
        
        context['answer_dict'] = answer_dict

        size=None
        if self.size is not None:
            try:
                size = int(self.size.resolve(context))
            except:
                pass
        if size is None:
            size = 60

        identifier = context['identifier']
        
        return '<input type="text" id="id_answer_%s_%s" maxlength="200" name="answer_%s_%s" size="%i" />' % \
            (self.answer_expression_string, identifier,  self.answer_expression_string,
             identifier, size)
    

@register.tag
def answer_blank(parser, token):
    bits = token.split_contents()

    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]

    answer_expression = parser.compile_filter(bits[1])
    answer_expression_string = bits[1]


    if len(bits) > 2:
        size = parser.compile_filter(bits[2])
    else:
        size = None

    return AnswerBlankNode(answer_expression, answer_expression_string, size)
