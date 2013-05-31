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

