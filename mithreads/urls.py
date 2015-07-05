
from django.conf.urls import patterns, url
from django.views.generic import ListView
from mithreads.models import Thread
from mithreads import views

paginate_by=20

urlpatterns = [
   url(r'^list$', ListView.as_view
     (template_name="mithreads/thread_list.html", 
      queryset=Thread.activethreads.all(),
      paginate_by=paginate_by),
     name="mithreads-list"),
   url(r'^(?P<thread_code>\w+)$', views.thread_view, 
     name="mithreads-thread"),
   url(r'^(?P<thread_code>\w+)/edit$', views.thread_edit_view, 
     name="mithreads-thread-edit"),
]

