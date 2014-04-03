from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import forms
from mithreads.models import Thread, ThreadSection, ThreadContent
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from midocs.models import Page


class ThreadSectionForm(forms.Form):
    section_name = forms.CharField(max_length=100)
    section_code = forms.SlugField(max_length=50)

# def return_object_queryset(content_type):
#     if content_type:
#         return ContentType.objects.get(id=content_type.id).model_class().objects.all()
#     else:
#         return ContentType.objects.none()


class ChoiceFieldNoValidate(forms.ChoiceField):
    def validate(self, value):
        pass

class ThreadContentForm(forms.ModelForm):
    content_type = forms.ModelChoiceField(queryset=ContentType.objects.filter(Q(model='applet') | Q(model='page') | Q(model='assessment') | Q(model='video')))
    #object_id =  ChoiceFieldNoValidate(choices=(('1','hi'),('2','goodbye')), label="Object")
    object_id = ChoiceFieldNoValidate(choices=(), label="Object")
    class Meta:
        model=ThreadContent
        fields = ('content_type', 'object_id', 'substitute_title')

