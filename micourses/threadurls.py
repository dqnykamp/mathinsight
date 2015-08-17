
from django.conf.urls import patterns, url
from django.views.generic import ListView
from micourses.models import Course
from micourses import views
from micourses.threadviews import ThreadView, ThreadEditView, EditSectionView, EditContentView, ReturnContentForm, ReturnContentOptions

paginate_by=20

urlpatterns = [
    url(r'^list$', ListView.as_view
        (template_name="micourses/threads/thread_list.html", 
         queryset=Course.active_courses.all(),
         paginate_by=paginate_by),
        name="list"),
    url(r'^(?P<course_code>\w+)$', ThreadView.as_view(), name="thread"),
    url(r'^(?P<course_code>\w+)/edit$', ThreadEditView.as_view(),
        name="thread-edit"),
    url(r'^edit/section$', 
        EditSectionView.as_view(), name='edit-section'),
    url(r'^edit/content$', 
        EditContentView.as_view(), name='edit-content'),
    url(r'^edit/return_content_form$', 
        ReturnContentForm.as_view(), name='return-content-form'),
    url(r'^edit/return_content_options$',
        ReturnContentOptions.as_view(), 
        name='return-options'),
]

