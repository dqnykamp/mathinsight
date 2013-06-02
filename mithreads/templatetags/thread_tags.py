from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)

register=Library()


class RenderThreadHtmlStringNode(Node):
    def __init__(self, thread, student, course, edit):
        self.thread=thread
        self.student = student
        self.course=course
        self.edit = edit
    def render(self, context):
        thread = self.thread.resolve(context)
        student = self.student.resolve(context)
        course = self.course.resolve(context)
        
        
        return thread.render_html_string(student=student, course=course,
                                         edit = self.edit)


@register.tag
def render_thread_html_string(parser, token):
    bits = token.split_contents()
    if len(bits) < 4:
        raise template.TemplateSyntaxError, "%r tag requires at least three arguments" % str(bits[0])
    thread = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    course = parser.compile_filter(bits[3])
    if len(bits) > 4:
        edit = bits[4]
    else:
        edit = False
    
    return RenderThreadHtmlStringNode(thread, student, course, edit)
