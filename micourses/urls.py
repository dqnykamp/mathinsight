
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import AssessmentAttempted, AssessmentAttemptedInstructor, AssessmentAttempt, AssessmentAttemptInstructor, AssessmentAttemptQuestion, AssessmentAttemptQuestionInstructor, AssessmentAttemptQuestionAttempt, AssessmentAttemptQuestionAttemptInstructor,EditAssessmentAttempt, RecordContentCompletion
from micourses import views

urlpatterns = [
    url(r'^$', views.course_main_view, name='coursemain'),
    url(r'^select_course$',  TemplateView.as_view(template_name="micourses/select_course.html"), name='selectcourse'),
    url(r'^not_enrolled$',  TemplateView.as_view(template_name="micourses/not_enrolled.html"), name='notenrolled'),
    url(r'^assessment/(?P<pk>\w+)$',AssessmentAttempted.as_view(), name='assessmentattempted'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)$', AssessmentAttempt.as_view(), name='assessmentattempt'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$', AssessmentAttemptQuestion.as_view(), name='assessmentattemptquestion'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttempt.as_view(), name='assessmentattemptquestionattempt'),
    url(r'^contentlist$',views.content_list_view, name='contentlist'),
    url(r'^update_attendance$', views.update_attendance_view, name='updateattendance'),
    url(r'^update_individual_attendance$', views.update_individual_attendance_view, name='updateindividualattendance'),
    url(r'^add_excused_absence$', views.add_excused_absence_view, name='addexcusedabsence'),
    url(r'^attendance_display$', views.attendance_display_view, name='attendancedisplay'),
    url(r'^adjusted_due_date_calculation/(?P<pk>\w+)$',views.adjusted_due_date_calculation_view, name='adjustedduedatecalculation'),
    url(r'^gradebook/(?P<student_id>\w+)/adjusted_due_date_calculation/(?P<pk>\w+)$',views.adjusted_due_date_calculation_instructor_view, name='instructoradjustedduedatecalculation'),
    url(r'^grades$',views.student_gradebook_view, name='studentgradebook'),
    url(r'^gradebook$',views.instructor_gradebook_view, name='instructorgradebook'),
    url(r'^gradebook/export$',views.export_gradebook_view, name='exportgradebook'),
    url(r'^gradebook/exportcsv$',views.gradebook_csv_view, name='gradebookcsv'),
    url(r'^list_assessments$',views.instructor_list_assessments_view, name='instructorlistassessments'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)$',AssessmentAttemptedInstructor.as_view(), name='assessmentattemptedinstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)$',AssessmentAttemptInstructor.as_view(), name='assessmentattemptinstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$',AssessmentAttemptQuestionInstructor.as_view(), name='assessmentattemptquestioninstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttemptInstructor.as_view(), name='assessmentattemptquestionattemptinstructor'),
    url(r'^gradebook/assessment/(?P<pk>\w+)$',EditAssessmentAttempt.as_view(), name='editassessmentattempt'),
    url(r'^gradebook/assessment/(?P<pk>\w+)/add_new_attempt$',views.add_assessment_attempts_view, name='addnewassessmentattempt'),
    url(r'^record_content_completion', RecordContentCompletion.as_view(),
        name = "record-completion")
]
