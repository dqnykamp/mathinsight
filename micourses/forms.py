from django import forms
from micourses.models import StudentContentAttempt
from django.forms.widgets import HiddenInput


class StudentContentAttemptForm(forms.ModelForm):
    class Meta:
        model = StudentContentAttempt
        widgets = {
            'student': HiddenInput,
            'content': HiddenInput,
            'seed': HiddenInput,
            'score': forms.TextInput(attrs={'size': 1})
            }
