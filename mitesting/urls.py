from django.conf.urls import patterns

urlpatterns = patterns('mitesting.views',
   url(r'^assessment/list$','assessment_list_view', name='mit-assessmentlist'),
   url(r'^question/list$','question_list_view', name='mit-questionlist'),
   url(r'^question/(?P<question_id>\d+)$','question_view', name='mit-question'),
   url(r'^question/(?P<question_id>\d+)/solution$','question_solution_view', name='mit-questionsolution'),
   url(r'^(?P<assessment_code>\w+)$','assessment_view', name='mit-assessment'),
   url(r'^(?P<assessment_code>\w+)/solution$','assessment_view', kwargs={'solution': True}, name='mit-assessmentsolution'),
   url(r'^(?P<assessment_code>\w+)/avoid$','assessment_avoid_question_view'),
   url(r'^question/(?P<question_id>\d+)/figure(?P<figure_number>\d+)$','question_figure_view', name='mit-questionfigure'),
)
