
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
import pickle, base64

class DynamicText(models.Model):
    contained_in_content_type = models.ForeignKey(ContentType)
    contained_in_object_id = models.PositiveIntegerField()
    contained_in_object = GenericForeignKey(
        'contained_in_content_type', 'contained_in_object_id')
    number = models.IntegerField()
    nodelisttext = models.TextField()

    class Meta:
        unique_together = ("contained_in_content_type", 
                           "contained_in_object_id", "number")

    def __str__(self):
        return  "%s in %s" % (self.number, self.contained_in_object)

    def render(self, context, include_container=False,
               instance_identifier=""):
        nodelist=pickle.loads(base64.b64decode(self.nodelisttext))

        # if context doesn't have a template associated with it,
        # add template so that context.template.engine.string_if_invalid
        # is defined, which is needed if a variable doesn't exist
        if not context.template:
            from django.template import Template
            context.template = Template("")

        content= nodelist.render(context)

        if include_container:
            span_id="id_%s" % self.return_identifier(instance_identifier)
            content = "<span id='%s'>%s</span>" % \
                      (span_id, content)
            content=mark_safe(content)
        return content

    def return_identifier(self, instance_identifier=""):
        return "dt_%s_%s_%s_%s" % \
            (self.contained_in_content_type.pk,
             self.contained_in_object_id, self.number,
             instance_identifier)
        

    def return_javascript_render_function(self, mathjax=False, 
                                          instance_identifier=""):
        span_id = "id_%s" % self.return_identifier(instance_identifier)
        function_string='jQuery("#%s").html(html_string);' % span_id
        if mathjax:
            function_string+='MathJax.Hub.Queue(["Typeset",MathJax.Hub,"%s"]);'\
                % span_id
        return "function(html_string) {%s}" % function_string


    @classmethod
    def return_dynamictext(cls, object, number):
        object_type = ContentType.objects.get_for_model(object)
        try:
            return cls.objects.get(contained_in_content_type__pk=object_type.id,
                                   contained_in_object_id=object.id,
                                   number=number)
        except ObjectDoesNotExist:
            return None
            
        
    @classmethod
    def return_number_for_object(cls, object):
        object_type = ContentType.objects.get_for_model(object)
        return cls.objects.filter(contained_in_content_type__pk=object_type.id,
                                  contained_in_object_id=object.id).count()

    @classmethod
    def add_new(cls, object, nodelist):
        nodelisttext=base64.b64encode(pickle.dumps(nodelist)).decode();
        return cls.objects.create(contained_in_object=object, 
                                  number=cls.return_number_for_object(object),
                                  nodelisttext=nodelisttext)
    
    @classmethod
    def initialize(cls, object):
        object_type = ContentType.objects.get_for_model(object)
        cls.objects.filter(contained_in_content_type__pk=object_type.id,
                           contained_in_object_id=object.id).delete()
        
