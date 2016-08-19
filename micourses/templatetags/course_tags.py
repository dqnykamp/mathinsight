from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from django.template.defaultfilters import floatformat
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text
from django.template.base import kwarg_re
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


class LinkOrSpanNode(template.Node):
    def __init__(self, target, kwargs, nodelist):
        self.target=target
        self.kwargs=kwargs
        self.nodelist=nodelist

    def render(self, context):

        target = self.target.resolve(context)

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        # get content
        try:
            content = self.nodelist.render(context)
        except:
            content=""

        link_id = kwargs.get("id")
        if link_id:
            id_text = " id='%s'" % link_id
        else:
            id_text = ""

        if kwargs.get("no_links"):
            return mark_safe("<span%s>%s</span>" % (id_text, content))
        else:
            return mark_safe("<a%s href='%s'>%s</a>" % (id_text, target, content))


@register.tag
def linkorspan(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])


    target = parser.compile_filter(bits[1])

    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    nodelist = parser.parse(('endlinkorspan',))
    parser.delete_first_token()

    return LinkOrSpanNode(target, kwargs, nodelist)




# # This doesn't seem to be used
# @register.tag
# def assessment_user_can_view(parser, token):
#     bits = token.split_contents()
#     if len(bits) < 3:
#         raise TemplateSyntaxError("%r tag requires at least two arguments" \
#                                       % str(bits[0]))
#     assessment = parser.compile_filter(bits[1])
#     user = parser.compile_filter(bits[2])
    
#     if len(bits)==5 and bits[3]=='as':
#         asvar=bits[4]
#     else:
#         asvar=None

#     return AssessmentUserCanViewNode(assessment, user, asvar)

# class AssessmentUserCanViewNode(Node):
#     def __init__(self, assessment, user, asvar):
#         self.assessment = assessment
#         self.user = user
#         self.asvar = asvar
#     def render(self, context):
#         assessment = self.assessment.resolve(context)
#         user = self.user.resolve(context)
#         try:
#             can_view=assessment.user_can_view(user)
#         except:
#             can_view= False

#         if self.asvar:
#             context[self.asvar]=can_view
#             return ""
#         else:
#             return can_view

