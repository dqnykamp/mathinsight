from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import AssessmentAttempted, AssessmentAttemptedInstructor, AssessmentAttempt, AssessmentAttemptInstructor, AssessmentAttemptQuestion, AssessmentAttemptQuestionInstructor, AssessmentAttemptQuestionAttempt, AssessmentAttemptQuestionAttemptInstructor

urlpatterns = patterns \
    ('micourses.views',
     url(r'^$', 'course_main_view', name='mic-coursemain'),
     url(r'^select_course$',  TemplateView.as_view(template_name="micourses/select_course.html"), name='mic-selectcourse'),
     url(r'^not_enrolled$',  TemplateView.as_view(template_name="micourses/not_enrolled.html"), name='mic-notenrolled'),
     url(r'^assessment/(?P<pk>\w+)$',AssessmentAttempted.as_view(), name='mic-assessmentattempted'),
     url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)$', AssessmentAttempt.as_view(), name='mic-assessmentattempt'),
     url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$', AssessmentAttemptQuestion.as_view(), name='mic-assessmentattemptquestion'),
     url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttempt.as_view(), name='mic-assessmentattemptquestionattempt'),
     url(r'^upcoming$','upcoming_assessments_view', name='mic-upcomingassessments'),
     url(r'^update_attendance$', 'update_attendance_view', name='mic-updateattendance'),
     url(r'^update_individual_attendance$', 'update_individual_attendance_view', name='mic-updateindividualattendance'),
     url(r'^attendance_display$', 'attendance_display_view', name='mic-attendancedisplay'),
     url(r'^adjusted_due_date_calculation/(?P<id>\w+)$','adjusted_due_date_calculation_view', name='mic-adjustedduedatecalculation'),
     url(r'^grades$','student_gradebook_view', name='mic-studentgradebook'),
     url(r'^gradebook$','instructor_gradebook_view', name='mic-instructorgradebook'),
     url(r'^gradebook/(?P<student_id>\w+)/(?P<pk>\w+)$',AssessmentAttemptedInstructor.as_view(), name='mic-assessmentattemptedinstructor'),
     url(r'^gradebook/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)$',AssessmentAttemptInstructor.as_view(), name='mic-assessmentattemptinstructor'),
     url(r'^gradebook/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$',AssessmentAttemptQuestionInstructor.as_view(), name='mic-assessmentattemptquestioninstructor'),
     url(r'^gradebook/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttemptInstructor.as_view(), name='mic-assessmentattemptquestionattemptinstructor'),

)
