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
        raise template.TemplateSyntaxError("%r tag requires two arguments" % str(bits[0]))
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
        raise template.TemplateSyntaxError("%r tag requires at least two arguments" % str(bits[0]))
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
            initial_due= course_thread_content.get_initial_due(student)
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
            final_due= course_thread_content.get_final_due(student)
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
        return "[Add complete skip button]"
        # course_thread_content = self.course_thread_content.resolve(context)
        # student = self.student.resolve(context)

        # return course_thread_content.complete_skip_button_html(student,
        #                                                        full_html=True)

@register.inclusion_tag('micourses/thread_section.html', takes_context=True)
def thread_section(context, section):
    return {'thread_section': section, 
            'id': section.id,
            'student': context.get('student'),
            'ltag': context['ltag'],
    }

@register.inclusion_tag('micourses/thread_section_edit.html',
                        takes_context=True)
def thread_section_edit(context, section):

    move_left=True
    move_right=True
    move_up=True
    move_down=True

    if section.course:
        move_left = False
    
    siblings = section.return_siblings()
    sections_of_grandparent = None

    if section == siblings.first():
        move_right = False

    if section == siblings.first():
        if section.course:
            move_up=False
        else:
            sections_of_grandparent=section.parent.return_siblings()
            if section.parent == sections_of_grandparent.first():
                move_up=False

    if section == siblings.last():
        if section.course:
            move_down=False
        else:
            if not sections_of_grandparent:
                sections_of_grandparent=section.parent.return_siblings()
            if section.parent == sections_of_grandparent.last():
                move_down=False

    return {'thread_section': section, 
            'id': section.id,
            'ltag': context['ltag'],
            'move_left': move_left,
            'move_right': move_right,
            'move_up': move_up,
            'move_down': move_down,
    }

@register.inclusion_tag('micourses/thread_content.html', takes_context=True)
def thread_content(context, content):
    student = context.get('student')
    if student:
        student_in_course = content.course in student.course_set.all()
    else:
        student_in_course = False

    # check if student already completed content
    try:
        completed = content.studentcontentcompletion_set\
            .get(student=student).complete
    except:
        completed = False

    return {'thread_content': content, 
            'id': content.id,
            'student': student,
            'student_in_course': student_in_course,
            'completed': completed,
    }


@register.inclusion_tag('micourses/thread_content_edit.html', 
                        takes_context=True)
def thread_content_edit(context, content):
    move_up=False
    move_down=False
    if content.find_previous() or content.section.find_previous():
        move_up=True
    if content.find_next() or content.section.find_next():
        move_down=True

    return {'thread_content': content, 
            'id': content.id,
            'move_up': move_up,
            'move_down': move_down,
    }
