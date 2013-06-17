from django import forms
from micourses.models import StudentContentAttempt
from django.forms.widgets import HiddenInput,SplitDateTimeWidget


class StudentContentAttemptForm(forms.ModelForm):
    datetime = forms.DateTimeField(label="Date/time", 
                                   widget=forms.TextInput(attrs={'size': 10}))
    class Meta:
        model = StudentContentAttempt
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
        widgets = {
            'student': HiddenInput,
            'content': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1}),
            'datetime': forms.TextInput(attrs={'size': 10}),
            }
