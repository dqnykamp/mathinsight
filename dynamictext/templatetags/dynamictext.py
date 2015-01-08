from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from django.utils.encoding import smart_text

from dynamictext.models import DynamicText

register = template.Library()

class DynamicTextNode(template.Node):
    def __init__(self, object, kwargs, nodelist):
        self.object=object
        self.kwargs=kwargs
        self.nodelist=nodelist
    def render(self, context):
        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        object = self.object.resolve(context)

        initial_render = kwargs.get("initial_render")

        if context.get("_process_dynamictext"):
            DynamicText.add_new(object=self.object, nodelist=self.nodelist)
        number_dynamictext=context.get("_number_dynamictext",0)
        dynamictext=DynamicText.return_dynamictext(self.object,
                                                   number=number_dynamictext)
        if dynamictext:
            context['_number_dynamictext']=number_dynamictext+1
            if initial_render:
                return dynamictext.render(context=context,
                                          include_container=True)
            else:
                return dynamictext.render(context=None,
                                          include_container=True)
        else:
            return ""

@register.tag
def dynamictext(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    
    object = parser.compile_filter(bits[1])

    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    nodelist = parser.parse(('endintlink',))
    parser.delete_first_token()

    return DynamicTextNode(object, kwargs, nodelist)

