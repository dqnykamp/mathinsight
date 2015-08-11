
from django.conf.urls import url, include
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView
from micourses.views import SelectCourseView, CourseView, ContentRecordView, ContentAttemptView, AssessmentAttemptQuestion, AssessmentAttemptQuestionInstructor, AssessmentAttemptQuestionAttempt, AssessmentAttemptQuestionAttemptInstructor,EditAssessmentAttempt, RecordContentCompletion
from micourses import views
from micourses.models import Course

coursepatterns = [
    url(r'^$', CourseView.as_view(), name='coursemain'),
    url(r'^not_enrolled$', 
        DetailView.as_view(model=Course, 
                           slug_url_kwarg = 'course_code', slug_field = 'code',
                           template_name="micourses/not_enrolled.html"), 
        name='notenrolled'),
    url(r'^(?P<content_id>\d+)$', ContentRecordView.as_view(),
         name='contentrecord'),
    url(r'^studentrecord/(?P<student_id>\d+)/(?P<content_id>\d+)$',
        ContentRecordView.as_view(instructor_view=True),
        name='contentrecordinstructor'),
    url(r'^(?P<content_id>\d+)/(?P<attempt_number>\d+)$', 
        ContentAttemptView.as_view(), name='contentattempt'),
    url(r'^studentrecord/(?P<student_id>\d+)/(?P<content_id>\d+)/(?P<attempt_number>\d+)$', 
        ContentAttemptView.as_view(instructor_view=True),
        name='contentattemptinstructor'),
]

urlpatterns = [
    url(r'^$',  SelectCourseView.as_view(), name='selectcourse'),
    url(r'^(?P<course_code>\w+)/', include(coursepatterns)),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$', AssessmentAttemptQuestion.as_view(), name='assessmentattemptquestion'),
    url(r'^assessment/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttempt.as_view(), name='assessmentattemptquestionattempt'),
    url(r'^contentlist$',views.content_list_view, name='contentlist'),
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
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)$',AssessmentAttemptQuestionInstructor.as_view(), name='assessmentattemptquestioninstructor'),
    url(r'^gradebook/student/(?P<student_id>\w+)/(?P<pk>\w+)/(?P<attempt_number>\d+)/(?P<question_number>\d+)/(?P<question_attempt_number>\d+)$',AssessmentAttemptQuestionAttemptInstructor.as_view(), name='assessmentattemptquestionattemptinstructor'),
    url(r'^gradebook/assessment/(?P<pk>\w+)$',EditAssessmentAttempt.as_view(), name='editassessmentattempt'),
    url(r'^gradebook/assessment/(?P<pk>\w+)/add_new_attempt$',views.add_assessment_attempts_view, name='addnewassessmentattempt'),
    url(r'^record_content_completion', RecordContentCompletion.as_view(),
        name = "record-completion")
]
