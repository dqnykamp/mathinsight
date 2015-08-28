from django.conf.urls import url, include
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import SelectCourseView, CourseView, CourseContentRecordView, EditCourseContentAttempts, ContentRecordView, ChangeScore, ContentAttemptView, QuestionAttemptsView, QuestionResponseView, EditAssessmentAttempt, RecordContentCompletion, ContentListView
from micourses import views
from micourses.models import Course

content_attempt_patterns = [
    url(r'^$', ContentRecordView.as_view(),
         name='content_record'),
    url(r'^/coursewide$', CourseContentRecordView.as_view(),
         name='course_content_record'),
    url(r'^/coursewide/edit_course_attempts$',
        EditCourseContentAttempts.as_view(),
         name='edit_course_content_attempts'),
    url(r'^/student_record/(?P<student_id>\d+)$',
        ContentRecordView.as_view(instructor_view=True),
        name='content_record_instructor'),
    url(r'^/(?P<attempt_number>\w+)$', 
        ContentAttemptView.as_view(), name='content_attempt'),
    url(r'^/student_record/(?P<student_id>\d+)/(?P<attempt_number>\w+)$', 
        ContentAttemptView.as_view(instructor_view=True),
        name='content_attempt_instructor'),
    url(r'^/(?P<attempt_number>\w+)/(?P<question_number>\d+)$', 
        QuestionAttemptsView.as_view(), name='question_attempts'),
    url(r'^/student_record/(?P<student_id>\d+)/(?P<attempt_number>\w+)/(?P<question_number>\d+)$',
        QuestionAttemptsView.as_view(instructor_view=True), 
        name='question_attempts_instructor'),
    url(r'^/(?P<attempt_number>\w+)/(?P<question_number>\d+)/(?P<response_number>\w+)$',
        QuestionResponseView.as_view(), name='question_response'),
    url(r'^/student_record/(?P<student_id>\d+)/(?P<attempt_number>\w+)/(?P<question_number>\d+)/(?P<response_number>\w+)$',
        QuestionResponseView.as_view(instructor_view=True),
        name='question_response_instructor'),
    url(r'^/student_record/(?P<student_id>\d+)/change/score',
        ChangeScore.as_view(),
        name="change_score"),
]


urlpatterns = [
    url(r'^$',  SelectCourseView.as_view(), name='selectcourse'),
    url(r'^(?P<course_code>\w+)$', CourseView.as_view(), name='coursemain'),
    url(r'^(?P<course_code>\w+)/not_enrolled$', 
        DetailView.as_view(model=Course, 
                           slug_url_kwarg = 'course_code', slug_field = 'code',
                           template_name="micourses/not_enrolled.html"), 
        name='notenrolled'),
    url(r'^record/(?P<course_code>\w+)/(?P<content_id>\d+)', include(content_attempt_patterns)),
    url(r'^(?P<course_code>\w+)/contentlist$', ContentListView.as_view(),
        name='contentlist'),
    url(r'^update_attendance$', views.update_attendance_view, name='updateattendance'),
    url(r'^update_individual_attendance$', views.update_individual_attendance_view, name='updateindividualattendance'),
    url(r'^add_excused_absence$', views.add_excused_absence_view, name='addexcusedabsence'),
    url(r'^attendance_display$', views.attendance_display_view, name='attendancedisplay'),
    url(r'^adjusted_due_calculation/(?P<pk>\w+)$',views.adjusted_due_calculation_view, name='adjustedduedatecalculation'),
    url(r'^gradebook/(?P<student_id>\w+)/adjusted_due_calculation/(?P<pk>\w+)$',views.adjusted_due_calculation_instructor_view, name='instructoradjustedduedatecalculation'),
    url(r'^grades$',views.student_gradebook_view, name='studentgradebook'),
    url(r'^gradebook$',views.instructor_gradebook_view, name='instructorgradebook'),
    url(r'^gradebook/export$',views.export_gradebook_view, name='exportgradebook'),
    url(r'^gradebook/exportcsv$',views.gradebook_csv_view, name='gradebookcsv'),
    url(r'^list_assessments$',views.instructor_list_assessments_view, name='instructorlistassessments'),
    url(r'^gradebook/assessment/(?P<pk>\w+)$',EditAssessmentAttempt.as_view(), name='editassessmentattempt'),
    url(r'^gradebook/assessment/(?P<pk>\w+)/add_new_attempt$',views.add_assessment_attempts_view, name='addnewassessmentattempt'),
    url(r'^record_content_completion', RecordContentCompletion.as_view(),
        name = "record-completion"),
]
