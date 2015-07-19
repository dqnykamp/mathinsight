from django import forms
from micourses.models import StudentContentAttempt, ThreadContent
from django.forms.widgets import HiddenInput,SplitDateTimeWidget, Select
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from midocs.models import Page


class StudentContentAttemptForm(forms.ModelForm):
    datetime = forms.DateTimeField(label="Date/time", 
                                   widget=forms.TextInput(attrs={'size': 10}))
    class Meta:
        model = StudentContentAttempt
        fields = ['student', 'content', 'datetime', 'score', 'seed']
        widgets = {
            'student': HiddenInput,
            'content': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1}),
            'datetime': forms.TextInput(attrs={'size': 10}),
            }

class StudentContentAttemptRequiredScoreForm(forms.ModelForm):
    score = forms.FloatField(required=True)
    datetime = forms.DateTimeField(label="Date/time", 
                                   widget=forms.TextInput(attrs={'size': 10}))
    class Meta:
        model = StudentContentAttempt
        fields = ['student', 'content', 'datetime', 'score', 'seed']
        widgets = {
            'student': HiddenInput,
            'content': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1}),
            'datetime': forms.TextInput(attrs={'size': 10}),
            }



def thread_content_form_factory(the_content_type=None, update_options_command=""):

    if the_content_type is None:
        the_content_type = ContentType.objects.get(model="page")
    
    allowed_content_types = ContentType.objects.filter(\
        Q(model='applet') | Q(model='page') | Q(model='assessment') |\
                                                Q(model='video'))

    default_object_choices = [(None, "---------")]
    for item in the_content_type.model_class().objects.all():
        default_object_choices.append((item.id, str(item)))

    class ThreadContentForm(forms.ModelForm):
        content_type = forms.ModelChoiceField(
            queryset=allowed_content_types, 
            empty_label=None, 
            initial=ContentType.objects.get(model=the_content_type.model), 
            widget= Select(attrs={"onchange": update_options_command})
        )
        object_id =forms.ChoiceField(
            choices=default_object_choices,
            label="Object"
        )

        class Meta:
            model=ThreadContent
            fields = ('content_type', 'object_id', 'substitute_title', 'assigned_date', 'initial_due_date', 'final_due_date', 'assessment_category', 'individualize_by_student', 'optional', 'available_before_assigned')


    return ThreadContentForm
