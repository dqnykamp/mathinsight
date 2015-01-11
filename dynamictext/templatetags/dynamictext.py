from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from django.utils.encoding import smart_text
from django.template.base import kwarg_re

from dynamictext.models import DynamicText

register = template.Library()

class DynamicTextNode(template.Node):
    def __init__(self, kwargs, nodelist):
        self.kwargs=kwargs
        self.nodelist=nodelist
    def render(self, context):
        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        # object will be from kwargs if defined, else from context
        object = kwargs.get("object", context.get("_dynamictext_object"))
        if not object:
            return ""

        if context.get("_process_dynamictext"):
            DynamicText.add_new(object=object, nodelist=self.nodelist)
        number_dynamictext=context.get("_number_dynamictext",0)
        dynamictext=DynamicText.return_dynamictext(object,
                                                   number=number_dynamictext)

        if dynamictext:
            identifier=context.get("_dynamictext_instance_identifier","")
            context['_number_dynamictext']=number_dynamictext+1
            return dynamictext.render(context=context,
                                      include_container=True,
                                      instance_identifier=identifier)
        else:
            return ""

@register.tag
def dynamictext(parser, token):

    bits = token.split_contents()

    kwargs = {}
    bits = bits[1:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    nodelist = parser.parse(('enddynamictext',))
    parser.delete_first_token()
    return DynamicTextNode(kwargs, nodelist)

