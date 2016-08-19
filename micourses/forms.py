from django import forms
from micourses.models import ContentAttempt, ThreadContent
from django.forms.widgets import HiddenInput,SplitDateTimeWidget, Select
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
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



def thread_content_form_factory(course, the_content_type=None, update_options_command=""):

    if the_content_type is None:
        the_content_type = ContentType.objects.get(app_label="midocs", model="page")


    from micourses.utils import return_allowed_content_types
    allowed_content_types = return_allowed_content_types()

    default_object_choices = [(None, "---------")]
    for item in the_content_type.model_class().objects.all():
        default_object_choices.append((item.id, str(item)))

    class ThreadContentForm(forms.ModelForm):
        content_type = forms.ModelChoiceField(
            queryset=allowed_content_types, 
            empty_label=None, 
            initial=the_content_type, 
            widget= Select(attrs={"onchange": update_options_command})
        )
        object_id =forms.ChoiceField(
            choices=default_object_choices,
            label="Object"
        )
        grade_category = forms.ModelChoiceField(
            queryset = course.coursegradecategory_set.all(),
            required=False,
        )
        browser_exam_keys = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={'rows':'1', 'cols': '65'})
        )


        class Meta:
            model=ThreadContent
            fields = ('content_type', 'object_id', 'substitute_title', 'comment', 'assigned', 'initial_due', 'final_due', 'time_limit', 'grade_category', 'points', 'individualize_by_student', 'assessment_attempt_aggregation', "question_attempt_aggregation", 'optional', 'available_before_assigned', 'record_scores', 'allow_solution_buttons', 'access_only_open_attempts', 'show_response_correctness', 'require_secured_browser', 'browser_exam_keys', 'restrict_to_ip_address')


    return ThreadContentForm


def validate_number_list(value):
    """
    Validate that string value is a comman separate list of numbers
    """

    value_list = value.split(",")

    for item in value_list:
        try:
            int(item)
        except ValueError:
            raise ValidationError("Must be a comma separated list of numbers")


    
class GenerateCourseAttemptForm(forms.Form):
    assessment_datetime = forms.SplitDateTimeField(
        label='Assessment date and time', initial=timezone.now)
    version_description = forms.CharField(
        max_length=100, label="Version description (optional)", required=False)
    seed = forms.CharField(
        max_length=50, label="Starting seed (optional)", required=False)
    include_list = forms.CharField(
        max_length=200, validators=[validate_number_list],
        label="Question numbers to include", required=False)
    avoid_list = forms.CharField(
        max_length=200, validators=[validate_number_list],
        label="Question numbers to avoid", required=False)

class ScoreForm(forms.Form):
    score = forms.FloatField(widget=forms.TextInput(attrs={'size': 4}))

class CreditForm(forms.Form):
    percent = forms.FloatField(widget=forms.TextInput(attrs={'size': 4}))


class AttemptScoresForm(forms.Form):
    def __init__(self, *args, **kwargs):
        attempts = kwargs.pop('attempts')
        super(AttemptScoresForm, self).__init__(*args, **kwargs)

        for attempt in attempts:
            self.fields['score_%s' % attempt.id] = \
                    forms.FloatField(widget=forms.TextInput(attrs={'size': 4}),
                                     required=False)
