from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Question, QuestionAnswerOption
from midocs.forms import QuestionForm
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
    color=''
    if 'k' in linestyle:
        color= '#000'
    elif 'b' in linestyle:
        color= '#0000FF'
    elif 'r' in linestyle:
        color= '#FF0000'
    elif 'g' in linestyle:
        color= '#00FF00'
    elif 'c' in linestyle:
        color= '#00FFFF'
    elif 'm' in linestyle:
        color= '#FF00FF'
    if color:
        color =  "color: '%s',\n" % color
    return color

def dashes_from_linestyle(linestyle):
    dashmatch = re.search('([-.]+)',linestyle)
    if dashmatch:
        return "linePattern: '%s'" % dashmatch.group()
    else:
        return ''

        
class FigureNode(Node):
    def __init__(self, figure_number, args, kwargs):
        self.figure_number = figure_number
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
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
        # also try xlabel, ylabel, linestyle, linewidth, ylim
            
        n_points=200
        dx = (xmax-xmin)/(n_points-1)
        x = [xmin+i*dx for i in range(n_points)]

        figure_number = self.figure_number.resolve(context)

        if not figure_number:
            return "[Broken figure]"
            #raise TemplateSyntaxError("'figure' requires a non-empty first argument. ")

        # find question
        the_question = Variable("the_question").resolve(context)
        
        function_dict = Variable('sympy_function_dict').resolve(context)

        combined_text=''
        point_lists=[]

        for expression in the_question.expression_set.filter(figure=figure_number):
            if expression.function_inputs:
                the_function = function_dict[expression.name]
                point_lists.append([(i,the_function(i)) for i in x])
                linewidth=2
                if expression.linewidth:
                    try:
                        linewidth = int(expression.linewidth)
                    except:
                        pass
                series_text=''
                if expression.linestyle:
                    series_text += color_from_linestyle(expression.linestyle)
                    series_text += dashes_from_linestyle(expression.linestyle)
            
        if len(point_lists)==0:
            return "[Bad figure]"

        thedata=json.dumps(point_lists)

        html_string = '<div id="placeholder" style="width:%spx;height:%spx;"></div>\n' % (width, height)
        html_string += '<script type="text/javascript">\n'
        html_string += 'var thedata = [\n %s ]\n' % combined_text
        html_string += 'var theoptions = {\n seriesDefaults: { shadow: false  },\n }\n'


        html_string += '$(document).ready(function () {\n'
        html_string += "$.jqplot('placeholder', %s, {\n" % thedata
        html_string += "seriesDefaults: {\n shadow: false,\n linewidth: 2,\n showMarker: false,\n  },\n"
        html_string += "axesDefaults: {\n tickOptions: {\n showGridline: false,\n },\n },\n"
        #html_string += "axes: {\n xaxis: {\n min: %s,\n max: %s, ticks: [-10, -5, 0, 5, 10], tickOptions: { formatString: '%%.0f', } \n},\n },\n" % (xmin, xmax)
        html_string += "axes: { xaxis: { pad: 0, }, },\n"
        html_string += "grid: {\n shadow: false, background: '#fff',\n}\n,"
        html_string += " });\n"
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
