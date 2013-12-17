from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from django.template.defaultfilters import floatformat
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings

register=Library()

@register.tag
def complete_skip_button(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % str(bits[0])
    course_thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    return CompleteSkipButtonNode(course_thread_content, student)

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

class AssessmentStudentScoreNode(Node):
    def __init__(self, course_thread_content, student, float_format):
        self.course_thread_content = course_thread_content
        self.student = student
        self.float_format = float_format
    def render(self, context):
        course_thread_content = self.course_thread_content.resolve(context)
        student = self.student.resolve(context)
        float_format = self.float_format.resolve(context)
        score = course_thread_content.student_score(student)
        return floatformat_or_dash(score)


@register.tag
def assessment_student_score(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % str(bits[0])
    course_thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    float_format = "1"
    if len(bits) > 3:
        float_format = bits[3]
    float_format = parser.compile_filter(float_format)
    
    return AssessmentStudentScoreNode(course_thread_content, student,
                                      float_format)


class InitialDueDateNode(Node):
    def __init__(self, course_thread_content, student, asvar):
        self.course_thread_content = course_thread_content
        self.student = student
        self.asvar = asvar
    def render(self, context):
        course_thread_content = self.course_thread_content.resolve(context)
        student = self.student.resolve(context)
        try:
            initial_due_date= course_thread_content.get_initial_due_date(student)
        except:
            return ""

        if self.asvar:
            context[self.asvar]=initial_due_date
            return ""
        else:
            return initial_due_date


@register.tag
def get_initial_due_date(parser, token):
    bits = token.split_contents()
    if len(bits) <= 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % str(bits[0])
    course_thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return InitialDueDateNode(course_thread_content, student, asvar)


class FinalDueDateNode(Node):
    def __init__(self, course_thread_content, student, asvar):
        self.course_thread_content = course_thread_content
        self.student = student
        self.asvar = asvar
    def render(self, context):
        course_thread_content = self.course_thread_content.resolve(context)
        student = self.student.resolve(context)
        try:
            final_due_date= course_thread_content.get_final_due_date(student)
        except:
            return ""

        if self.asvar:
            context[self.asvar]=final_due_date
            return ""
        else:
            return final_due_date


@register.tag
def get_final_due_date(parser, token):
    bits = token.split_contents()
    if len(bits) <= 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % str(bits[0])
    course_thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return FinalDueDateNode(course_thread_content, student, asvar)


class CompleteSkipButtonNode(Node):
    def __init__(self, course_thread_content, student):
        self.course_thread_content = course_thread_content
        self.student = student
    def render(self, context):
        course_thread_content = self.course_thread_content.resolve(context)
        student = self.student.resolve(context)

        return course_thread_content.complete_skip_button_html(student,
                                                               full_html=True)

