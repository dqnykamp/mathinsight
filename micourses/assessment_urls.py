from django.conf.urls import url, include
from micourses.assessment_views import AssessmentView, GenerateNewAttempt, GenerateCourseAttempt, AssessmentOverview

assessment_patterns = [
    url(r'^$', 
        AssessmentView.as_view(), name='assessment'),
    url(r'^/(?P<question_only>\d+)$', AssessmentView.as_view(),
        name='assessment_question'),
    url(r'^/overview$', AssessmentOverview.as_view(),
        name='assessment_overview'),
    url(r'^/solution$', AssessmentView.as_view(solution=True),
        name='assessment_solution'),
]

generate_patterns = [
    url(r'^/courseattempt$', GenerateCourseAttempt.as_view(), 
        name='generate_course_attempt'),
    url(r'^/newattempt$', GenerateNewAttempt.as_view(),
        name='generate_new_attempt'),
]

urlpatterns = [
    url(r'^(?P<content_id>\d+)/generate/assessment', include(generate_patterns)),
    url(r'^(?P<course_code>\w+)/(?P<assessment_code>\w+)', include(assessment_patterns)),
]
