from django.conf.urls import patterns, url
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.contrib.auth.decorators import permission_required
from mitesting.models import Assessment
from mitesting.views import QuestionView, \
    GradeQuestionView, InjectQuestionSolutionView, \
    AssessmentView, GenerateNewAssessmentAttemptView, GenerateAssessmentView
from mitesting.permissions import user_can_administer_assessment_decorator
from mitesting import views

urlpatterns = [
    url(r'^assessment/list$',views.assessment_list_view, name='assessmentlist'),
    url(r'^question/list$', views.question_list_view, name='questionlist'),
    url(r'^question/(?P<question_id>\d+)$', QuestionView.as_view(), 
        name='question'),
    url(r'^question/(?P<question_id>\d+)/solution$',
        QuestionView.as_view(solution=True), name='questionsolution'),
    url(r'^question/(?P<question_id>\d+)/grade_question$', 
        GradeQuestionView.as_view(), name='gradequestion'),
    url(r'^question/(?P<question_id>\d+)/inject_solution$', 
        InjectQuestionSolutionView.as_view(), name='injectquestionsolution'),
    url(r'^question/default_sympy_commands$', views.default_sympy_commands),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)$', 
        AssessmentView.as_view(), name='assessment'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/(?P<question_only>\d+)$',
        AssessmentView.as_view()),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/overview$',
        views.assessment_overview_view, name='assessmentoverview'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/solution$',
        AssessmentView.as_view(solution=True), name='assessmentsolution'),
    url(r'^(?P<pk>\d+)/generate/newattempt$',
        GenerateNewAssessmentAttemptView.as_view(),
        name='generatenewassessmentattempt'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/avoid$',
        views.assessment_avoid_question_view, name='assessmentavoidquestion'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/generate$', 
        GenerateAssessmentView.as_view(), name='assessmentgenerate'),
]
