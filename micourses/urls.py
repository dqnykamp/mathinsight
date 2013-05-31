from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView, ListView, DetailView


urlpatterns = patterns \
    ('micourses.views',
     url(r'^$', 'course_main_view', name='mic-coursemain'),
     url(r'^select_course$',  TemplateView.as_view(template_name="micourses/select_course.html"), name='mic-selectcourse'),
     url(r'^not_enrolled$',  TemplateView.as_view(template_name="micourses/not_enrolled.html"), name='mic-notenrolled'),
     url(r'^assessment_attempts/(?P<module_code>\w+)/(?P<assessment_code>\w+)$','assessment_attempts_view', name='mic-assessmentattempts'),
     url(r'^update_attendance$', 'update_attendance_view', name='mic-updateattendance'),
     url(r'^update_individual_attendance$', 'update_individual_attendance_view', name='mic-updateindividualattendance'),
     url(r'^attendance_display$', 'attendance_display_view', name='mic-attendancedisplay'),
     url(r'^adjusted_due_date_calculation/(?P<module_code>\w+)/(?P<assessment_code>\w+)$','adjusted_due_date_calculation_view', name='mic-adjustedduedatecalculation'),
)
