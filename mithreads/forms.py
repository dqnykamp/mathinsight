
from django import forms
from mithreads.models import Thread, ThreadSection, ThreadContent
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from midocs.models import Page


class ThreadSectionForm(forms.Form):
    section_name = forms.CharField(max_length=100)
    section_code = forms.SlugField(max_length=50)


def thread_content_form_factory(the_content_type=None):

    if the_content_type is None:
        the_content_type = ContentType.objects.get(model="page")
    
    class ThreadContentForm(forms.ModelForm):
        content_type = forms.ModelChoiceField(queryset=ContentType.objects.filter(Q(model='applet') | Q(model='page') | Q(model='assessment') | Q(model='video')), empty_label=None, initial=ContentType.objects.get(model=the_content_type.model))
        object_id =forms.ModelChoiceField(queryset=the_content_type.model_class().objects.all(), label="Object")

        class Meta:
            model=ThreadContent
            fields = ('content_type', 'object_id', 'substitute_title')

    return ThreadContentForm
