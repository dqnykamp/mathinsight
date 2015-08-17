from django.conf.urls import patterns, url
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.contrib.auth.decorators import permission_required
from mitesting.views import QuestionView, \
    GradeQuestionView, InjectQuestionSolutionView
from mitesting import views

urlpatterns = [
    url(r'^(?P<question_id>\d+)$', QuestionView.as_view(), 
        name='question'),
    url(r'^(?P<question_id>\d+)/solution$',
        QuestionView.as_view(solution=True), name='questionsolution'),
    url(r'^(?P<question_id>\d+)/grade_question$', 
        GradeQuestionView.as_view(), name='gradequestion'),
    url(r'^(?P<question_id>\d+)/inject_solution$', 
        InjectQuestionSolutionView.as_view(), name='injectquestionsolution'),
    url(r'^default_sympy_commands$', views.default_sympy_commands),
]
