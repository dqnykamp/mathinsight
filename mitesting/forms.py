
from django import forms
from mitesting.models import Question, QuestionAnswerOption


class MultipleChoiceQuestionForm(forms.Form):
    answers = forms.ModelChoiceField(queryset=QuestionAnswerOption.objects.all(),widget=forms.RadioSelect, empty_label=None)

class MathWriteInForm(forms.Form):
    answer = forms.CharField(max_length=200)
