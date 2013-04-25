from django.conf.urls import patterns, url
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.contrib.auth.decorators import permission_required
from mitesting.models import Assessment

class GenerateAssessmentView(DetailView):
    context_object_name = "assessment"
    model = Assessment
    template_name = "mitesting/assessment_generate.html"
    slug_field = 'code'
    @method_decorator(permission_required('mitesting.administer_assessment'))
    def dispatch(self, *args, **kwargs):
        return super(GenerateAssessmentView, self).dispatch(*args, **kwargs)


urlpatterns = patterns('mitesting.views',
   url(r'^assessment/list$','assessment_list_view', name='mit-assessmentlist'),
   url(r'^question/list$','question_list_view', name='mit-questionlist'),
   url(r'^question/(?P<question_id>\d+)$','question_view', name='mit-question'),
   url(r'^question/(?P<question_id>\d+)/solution$','question_solution_view', name='mit-questionsolution'),
   url(r'^(?P<assessment_code>\w+)$','assessment_view', name='mit-assessment'),
   url(r'^(?P<assessment_code>\w+)/solution$','assessment_view', kwargs={'solution': True}, name='mit-assessmentsolution'),
   url(r'^(?P<assessment_code>\w+)/avoid$','assessment_avoid_question_view', name='mit-assessmentavoidquestion'),
   url(r'^(?P<slug>\w+)/generate$', GenerateAssessmentView.as_view(), name='mit-assessmentgenerate'),

)
