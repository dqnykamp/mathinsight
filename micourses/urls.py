from django.conf.urls import url, include
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import SelectCourseView, CourseView, CourseContentRecordView, EditCourseContentAttempts, ContentRecordView, ChangeScore, ContentAttemptView, QuestionAttemptsView, QuestionResponseView, EditCourseContentAttemptScores, RecordContentCompletion, ContentListView, InstructorGradebook, StudentGradebook
from micourses.attendance_views import AdjustedDueCalculation, AttendanceDisplay
from micourses import views
from micourses.models import Course
from micourses import attendance_views

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
    url(r'^not_enrolled/(?P<course_code>\w+)$', 
        DetailView.as_view(model=Course, 
                           slug_url_kwarg = 'course_code', slug_field = 'code',
                           template_name="micourses/not_enrolled.html"), 
        name='notenrolled'),
    url(r'^record/(?P<course_code>\w+)/(?P<content_id>\d+)', include(content_attempt_patterns)),
    url(r'^contentlist/(?P<course_code>\w+)$', ContentListView.as_view(),
        name='contentlist'),
    url(r'^update_attendance$', attendance_views.update_attendance_view, name='updateattendance'),
    url(r'^update_individual_attendance$', attendance_views.update_individual_attendance_view, name='updateindividualattendance'),
    url(r'^add_excused_absence$', attendance_views.add_excused_absence_view, name='addexcusedabsence'),
    url(r'^attendance_display/(?P<course_code>\w+)$', 
        AttendanceDisplay.as_view(), name='attendance_display'),
    url(r'^adjusted_due_calculation/(?P<course_code>\w+)/(?P<content_id>\d+)$',
        AdjustedDueCalculation.as_view(), name='adjusted_due_calculation'),
    url(r'^adjusted_due_calculation/(?P<course_code>\w+)/(?P<content_id>\d+)/student/(?P<student_id>\w+)$',
        AdjustedDueCalculation.as_view(instructor_view=True),
        name='instructor_adjusted_due_calculation'),
    url(r'^grades/(?P<course_code>\w+)$',StudentGradebook.as_view(),
        name='student_gradebook'),
    url(r'^gradebook/(?P<course_code>\w+)$', InstructorGradebook.as_view(),
        name='instructor_gradebook'),
    url(r'^gradebook/export$',views.export_gradebook_view, name='exportgradebook'),
    url(r'^gradebook/exportcsv$',views.gradebook_csv_view, name='gradebookcsv'),
    url(r'^list_assessments$',views.instructor_list_assessments_view, name='instructorlistassessments'),
    url(r'^gradebook/(?P<course_code>\w+)/(?P<content_id>\d+)$',
        EditCourseContentAttemptScores.as_view(), 
        name='edit_course_content_attempt_scores'),
    url(r'^gradebook/(?P<course_code>\w+)/(?P<content_id>\d+)/add_new_attempt$',views.add_assessment_attempts_view, name='addnewassessmentattempt'),
    url(r'^record_content_completion/(?P<course_code>\w+)$', RecordContentCompletion.as_view(),
        name = "record-completion"),
]
