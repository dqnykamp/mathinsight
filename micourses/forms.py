from django import forms
from micourses.models import ContentAttempt, ThreadContent
from django.forms.widgets import HiddenInput,SplitDateTimeWidget, Select
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from midocs.models import Page


class ContentAttemptForm(forms.ModelForm):
    attempt_began = forms.DateTimeField(label="Date/time", 
                                   widget=forms.TextInput(attrs={'size': 10}))
    class Meta:
        model = ContentAttempt
        fields = ['record', 'attempt_began', 'score', 'seed']
        widgets = {
            'record': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1}),
            'attempt_began': forms.TextInput(attrs={'size': 10}),
            }

class ContentAttemptRequiredScoreForm(forms.ModelForm):
    score = forms.FloatField(required=True)
    attempt_began = forms.DateTimeField(label="Date/time", 
                                   widget=forms.TextInput(attrs={'size': 10}))
    class Meta:
        model = ContentAttempt
        fields = ['record', 'attempt_began', 'score', 'seed']
        widgets = {
            'record': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1}),
            'attempt_began': forms.TextInput(attrs={'size': 10}),
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
            fields = ('content_type', 'object_id', 'substitute_title', 'assigned', 'initial_due', 'final_due', 'grade_category', 'points', 'individualize_by_student', 'attempt_aggregation', 'optional', 'available_before_assigned', 'record_scores')


    return ThreadContentForm
