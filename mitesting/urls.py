from django.conf.urls import patterns, url
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.contrib.auth.decorators import permission_required
from mitesting.models import Assessment
from mitesting.views import QuestionView, \
    GradeQuestionView, InjectQuestionSolutionView, \
    AssessmentView, GenerateNewAssessmentAttemptView
from mitesting.permissions import user_can_administer_assessment_decorator
from mitesting import views

class GenerateAssessmentView(DetailView):
    context_object_name = "assessment"
    model = Assessment
    template_name = "mitesting/assessment_generate.html"
    slug_url_kwarg = 'assessment_code'
    slug_field = 'code'

    @method_decorator(user_can_administer_assessment_decorator())
    def dispatch(self, *args, **kwargs):
        return super(GenerateAssessmentView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GenerateAssessmentView, self).get_context_data(**kwargs)
        context['the_assessment_name'] = self.get_object().name
        return context

    def get_queryset(self):
        return self.model._default_manager.filter(course__code=
                                                  self.kwargs["course_code"])


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
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/generatenewattempt$',
        GenerateNewAssessmentAttemptView.as_view(),
        name='generatenewassessmentattempt'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/avoid$',
        views.assessment_avoid_question_view, name='assessmentavoidquestion'),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)/generate$', 
        GenerateAssessmentView.as_view(), name='assessmentgenerate'),
]
