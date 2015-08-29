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

class AssessmentStudentScoreNode(Node):
    def __init__(self, thread_content, student, float_format):
        self.thread_content = thread_content
        self.student = student
        self.float_format = float_format
    def render(self, context):
        thread_content = self.thread_content.resolve(context)
        student = self.student.resolve(context)
        float_format = self.float_format.resolve(context)
        score = thread_content.student_score(student)
        return floatformat_or_dash(score)


@register.tag
def assessment_student_score(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError("%r tag requires at least two arguments" % str(bits[0]))
    thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    float_format = "1"
    if len(bits) > 3:
        float_format = bits[3]
    float_format = parser.compile_filter(float_format)
    
    return AssessmentStudentScoreNode(thread_content, student,
                                      float_format)


class InitialDueDateNode(Node):
    def __init__(self, thread_content, student, asvar):
        self.thread_content = thread_content
        self.student = student
        self.asvar = asvar
    def render(self, context):
        thread_content = self.thread_content.resolve(context)
        student = self.student.resolve(context)
        try:
            initial_due= thread_content.get_initial_due(student)
        except:
            return ""

        if self.asvar:
            context[self.asvar]=initial_due
            return ""
        else:
            return initial_due


@register.tag
def get_initial_due(parser, token):
    bits = token.split_contents()
    if len(bits) <= 3:
        raise template.TemplateSyntaxError("%r tag requires at least two arguments" % str(bits[0]))
    thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return InitialDueDateNode(thread_content, student, asvar)


class FinalDueDateNode(Node):
    def __init__(self, thread_content, student, asvar):
        self.thread_content = thread_content
        self.student = student
        self.asvar = asvar
    def render(self, context):
        thread_content = self.thread_content.resolve(context)
        student = self.student.resolve(context)
        try:
            final_due= thread_content.get_final_due(student)
        except:
            return ""

        if self.asvar:
            context[self.asvar]=final_due
            return ""
        else:
            return final_due


@register.tag
def get_final_due(parser, token):
    bits = token.split_contents()
    if len(bits) <= 3:
        raise template.TemplateSyntaxError("%r tag requires at least two arguments" % str(bits[0]))
    thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return FinalDueDateNode(thread_content, student, asvar)


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


@register.tag
def complete_skip_button(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("%r tag requires two arguments" % str(bits[0]))
    thread_content = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    return CompleteSkipButtonNode(thread_content, student)


class CompleteSkipButtonNode(Node):
    def __init__(self, thread_content, student):
        self.thread_content = thread_content
        self.student = student
    def render(self, context):
        return "[Add complete skip button]"
        # thread_content = self.thread_content.resolve(context)
        # student = self.student.resolve(context)

        # return thread_content.complete_skip_button_html(student,
        #                                                        full_html=True)

