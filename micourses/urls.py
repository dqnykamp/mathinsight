from django.conf.urls import url, include
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import SelectCourseView, CourseView, CourseContentRecordView, EditCourseContentAttempts, ContentRecordView, ChangeScore, ContentAttemptView, QuestionAttemptsView, QuestionResponseView, EditCourseContentAttemptScores, OpenCloseAttempt, RecordContentCompletion, ContentListView, InstructorGradebook, StudentGradebook, ExportGradebook, GradebookCSV, LatestContentAttemptsCSV, ImportClassRosterView
from micourses.attendance_views import AdjustedDueCalculation, AttendanceDisplay, UpdateAttendance, UpdateIndividualAttendance
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

attendance_patterns = [
    url(r'^/update$', UpdateAttendance.as_view(), name='update_attendance'),
    url(r'^/update_individual$', UpdateIndividualAttendance.as_view(), 
        name='update_individual_attendance'),
    url(r'^/display$', 
        AttendanceDisplay.as_view(), name='attendance_display'),
]


course_patterns = [
    url(r'^$', CourseView.as_view(), name='coursemain'),
    url(r'^/not_enrolled$', 
        SelectCourseView.as_view(not_enrolled=True), 
        name='notenrolled'),
    url(r'^/record/(?P<content_id>\d+)', include(content_attempt_patterns)),
    url(r'^/contentlist$', ContentListView.as_view(),
        name='contentlist'),
    url(r'^/attendance', include(attendance_patterns)),
    url(r'^/adjusted_due_calculation/(?P<content_id>\d+)$',
        AdjustedDueCalculation.as_view(), name='adjusted_due_calculation'),
    url(r'^/adjusted_due_calculation/(?P<content_id>\d+)/student/(?P<student_id>\w+)$',
        AdjustedDueCalculation.as_view(instructor_view=True),
        name='instructor_adjusted_due_calculation'),
    url(r'^/grades$',StudentGradebook.as_view(),
        name='student_gradebook'),
    url(r'^/gradebook$', InstructorGradebook.as_view(),
        name='instructor_gradebook'),
    url(r'^/gradebook/(?P<content_id>\d+)$',
        EditCourseContentAttemptScores.as_view(), 
        name='edit_course_content_attempt_scores'),
    url(r'^/gradebook/(?P<content_id>\d+)/latest_csv$',
        LatestContentAttemptsCSV.as_view(), 
        name='latest_attempt_csv'),
    url(r'^/gradebook/(?P<content_id>\d+)/openclose$',
        OpenCloseAttempt.as_view(), 
        name='open_close_attempt'),
    url(r'^/record_content_completion$', RecordContentCompletion.as_view(),
        name = "record_completion"),
    url(r'^/gradebook/export$', ExportGradebook.as_view(), 
        name='exportgradebook'),
    url(r'^/gradebook/exportcsv$',GradebookCSV.as_view(), name='gradebookcsv'),
    url(r'^/import_class_roster$', ImportClassRosterView.as_view(),
        name='importclassroster'),

]

urlpatterns = [
    url(r'^$',  SelectCourseView.as_view(), name='selectcourse'),
    url(r'^(?P<course_code>\w+)', include(course_patterns)),
]
