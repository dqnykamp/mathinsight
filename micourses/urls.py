from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView


urlpatterns = patterns \
    ('micourses.views',
     url(r'^$', 'course_main_view', name='mic-coursemain'),
     url(r'^select_course$',  TemplateView.as_view(template_name="micourses/select_course.html"), name='mic-selectcourse'),
     url(r'^not_enrolled$',  TemplateView.as_view(template_name="micourses/not_enrolled.html"), name='mic-notenrolled'),
     url(r'^assessment/(?P<id>\w+)$','assessment_attempts_view', name='mic-assessmentattempts'),
     url(r'^assessment/(?P<id>\w+)/(?P<attempt_number>\d+)$','assessment_attempt_questions_view', name='mic-assessmentattemptquestions'),
     url(r'^assessment/(?P<id>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$','assessment_attempt_question_detail_view', name='mic-assessmentattemptquestiondetail'),
     url(r'^assessment/(?P<id>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$','assessment_attempt_question_attempt_view', name='mic-assessmentattemptquestionattempt'),
     url(r'^upcoming$','upcoming_assessments_view', name='mic-upcomingassessments'),
     url(r'^update_attendance$', 'update_attendance_view', name='mic-updateattendance'),
     url(r'^update_individual_attendance$', 'update_individual_attendance_view', name='mic-updateindividualattendance'),
     url(r'^attendance_display$', 'attendance_display_view', name='mic-attendancedisplay'),
     url(r'^adjusted_due_date_calculation/(?P<id>\w+)$','adjusted_due_date_calculation_view', name='mic-adjustedduedatecalculation'),
     url(r'^gradebook$','student_gradebook_view', name='mic-studentgradebook'),
)
