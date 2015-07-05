
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import AssessmentAttempted, AssessmentAttemptedInstructor, AssessmentAttempt, AssessmentAttemptInstructor, AssessmentAttemptQuestion, AssessmentAttemptQuestionInstructor, AssessmentAttemptQuestionAttempt, AssessmentAttemptQuestionAttemptInstructor,EditAssessmentAttempt
from micourses import views

urlpatterns = [
    url(r'^$', views.course_main_view, name='mic-coursemain'),
    url(r'^select_course$',  TemplateView.as_view(template_name="micourses/select_course.html"), name='mic-selectcourse'),
    url(r'^not_enrolled$',  TemplateView.as_view(template_name="micourses/not_enrolled.html"), name='mic-notenrolled'),
    url(r'^assessment/(?P<pk>\w+)$',AssessmentAttempted.as_view(), name='mic-assessmentattempted'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)$', AssessmentAttempt.as_view(), name='mic-assessmentattempt'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$', AssessmentAttemptQuestion.as_view(), name='mic-assessmentattemptquestion'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttempt.as_view(), name='mic-assessmentattemptquestionattempt'),
    url(r'^contentlist$',views.content_list_view, name='mic-contentlist'),
    url(r'^update_attendance$', views.update_attendance_view, name='mic-updateattendance'),
    url(r'^update_individual_attendance$', views.update_individual_attendance_view, name='mic-updateindividualattendance'),
    url(r'^add_excused_absence$', views.add_excused_absence_view, name='mic-addexcusedabsence'),
    url(r'^attendance_display$', views.attendance_display_view, name='mic-attendancedisplay'),
    url(r'^adjusted_due_date_calculation/(?P<pk>\w+)$',views.adjusted_due_date_calculation_view, name='mic-adjustedduedatecalculation'),
    url(r'^gradebook/(?P<student_id>\w+)/adjusted_due_date_calculation/(?P<pk>\w+)$',views.adjusted_due_date_calculation_instructor_view, name='mic-instructoradjustedduedatecalculation'),
    url(r'^grades$',views.student_gradebook_view, name='mic-studentgradebook'),
    url(r'^gradebook$',views.instructor_gradebook_view, name='mic-instructorgradebook'),
    url(r'^gradebook/export$',views.export_gradebook_view, name='mic-exportgradebook'),
    url(r'^gradebook/exportcsv$',views.gradebook_csv_view, name='mic-gradebookcsv'),
    url(r'^list_assessments$',views.instructor_list_assessments_view, name='mic-instructorlistassessments'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)$',AssessmentAttemptedInstructor.as_view(), name='mic-assessmentattemptedinstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)$',AssessmentAttemptInstructor.as_view(), name='mic-assessmentattemptinstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$',AssessmentAttemptQuestionInstructor.as_view(), name='mic-assessmentattemptquestioninstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttemptInstructor.as_view(), name='mic-assessmentattemptquestionattemptinstructor'),
    url(r'^gradebook/assessment/(?P<pk>\w+)$',EditAssessmentAttempt.as_view(), name='mic-editassessmentattempt'),
    url(r'^gradebook/assessment/(?P<pk>\w+)/add_new_attempt$',views.add_assessment_attempts_view, name='mic-addnewassessmentattempt'),
]
