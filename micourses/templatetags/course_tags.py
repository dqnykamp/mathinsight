from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)

register=Library()

class AssessmentStudentScoreNode(Node):
    def __init__(self, module_assessment, student):
        self.module_assessment = module_assessment
        self.student = student
    def render(self, context):
        module_assessment = self.module_assessment.resolve(context)
        student = self.student.resolve(context)
        try:
            return module_assessment.student_score(student)
        except:
            return ""


@register.tag
def assessment_student_score(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % str(bits[0])
    module_assessment = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    return AssessmentStudentScoreNode(module_assessment, student)


class InitialDueDateNode(Node):
    def __init__(self, module_assessment, student, asvar):
        self.module_assessment = module_assessment
        self.student = student
        self.asvar = asvar
    def render(self, context):
        module_assessment = self.module_assessment.resolve(context)
        student = self.student.resolve(context)
        try:
            initial_due_date= module_assessment.get_initial_due_date(student)
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
    module_assessment = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return InitialDueDateNode(module_assessment, student, asvar)


class FinalDueDateNode(Node):
    def __init__(self, module_assessment, student, asvar):
        self.module_assessment = module_assessment
        self.student = student
        self.asvar = asvar
    def render(self, context):
        module_assessment = self.module_assessment.resolve(context)
        student = self.student.resolve(context)
        try:
            final_due_date= module_assessment.get_final_due_date(student)
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
    module_assessment = parser.compile_filter(bits[1])
    student = parser.compile_filter(bits[2])
    
    if len(bits)==5 and bits[3]=='as':
        asvar=bits[4]
    else:
        asvar=None

    return FinalDueDateNode(module_assessment, student, asvar)
