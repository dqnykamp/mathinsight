from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference, Question, QuestionAnswerOption
from midocs.forms import QuestionForm
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
import re
import random
from django.contrib.sites.models import Site
from django.db.models import  Max
# from django.utils.encoding import smart_text

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


class FigureNode(Node):
    def __init__(self, fignum, args, kwargs, asvar):
        self.fignum = fignum
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        # for django 1.5
        # kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
        #                for k, v in self.kwargs.items()])
        kwargs = dict([(k, v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_url_GET_string = ""
        
        width=500
        height=500
        for k in kwargs.keys():
            if k=='width':
                try:
                    width = int(kwargs[k])
                except:
                    pass
            elif k=='height':
                try:
                    height = int(kwargs[k])
                except:
                    pass
            else:
                if kwargs_url_GET_string:
                    kwargs_url_GET_string += "&"
                kwargs_url_GET_string = "%s%s=%s" % (kwargs_url_GET_string, k, kwargs[k])

        fignum = self.fignum.resolve(context)

        if not fignum:
            return "[Broken figure]"
            #raise TemplateSyntaxError("'figure' requires a non-empty first argument. ")

        # find question
        the_question = Variable("the_exam_question").resolve(context)
        
        # get URL for graph fignum (fails if no function with graph=fignum)
        try:
            url = reverse('mi-examquestiongraph', kwargs={'question_code':the_question.code, 'graph_number': fignum})
        except:
            raise
            
        if not the_question.examfunction_set.filter(graph=fignum):
            return "[Broken figure]"
        
        # find all random variables from question and add to GET arguments
        for randnum in the_question.examrandomnumber_set.all():
            randnum_value = Variable(randnum.name).resolve(context)
            if kwargs_url_GET_string:
                kwargs_url_GET_string += "&"
            kwargs_url_GET_string = "%s%s=%s" % (kwargs_url_GET_string, randnum.name, randnum_value)
            
        return "<img src='%s?%s' width=%s height=%s>" %(url, kwargs_url_GET_string, width, height)
        


@register.tag
def figure(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % str(bits[0])
    
    fignum = parser.compile_filter(bits[1])
    args = []
    kwargs = {}
    asvar = None
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

    return FigureNode(fignum, args, kwargs, asvar)
