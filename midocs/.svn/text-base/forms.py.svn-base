from django import forms
from midocs.models import Question, QuestionAnswerOption


class QuestionForm(forms.Form):
    answers = forms.ModelChoiceField(queryset=QuestionAnswerOption.objects.all(),widget=forms.RadioSelect, empty_label=None)
    
