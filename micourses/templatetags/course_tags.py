from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from django.template.defaultfilters import floatformat
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings

register=Library()

@register.filter(is_safe=True)
def floatformat_or_dash(text,arg=1):
    if text is None:
        return "--"
    else:
        return floatformat(text,arg)

@register.filter(needs_autoescape=True)
def percent_checked_100(text, arg=0, autoescape=None):
    checked=False
    if text==100:
        checked = True
    text = floatformat(text,arg)
    if autoescape:
        escaped_text = conditional_escape(text)
    else:
        escaped_text = text
    escaped_text = '%s%%' % escaped_text
    if checked:
        
        escaped_text += ' <img src="%sadmin/img/icon-yes.gif" alt="Full credit" />'\
            % (settings.STATIC_URL)

    return mark_safe(escaped_text)


@register.inclusion_tag("micourses/assessments/exam_header.html", takes_context=True)
def new_exam_page(context):
    return {
        'course': context.get('course'),
        'assessment_date': context.get('assessment_date'),
        'assessment_short_name_with_version': \
        context.get('assessment_short_name_with_version'),
        }



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

