from django.conf.urls import patterns
from django.views.generic import ListView
from mithreads.models import Thread

paginate_by=20

urlpatterns = patterns('mithreads.views',
   url(r'^list$', ListView.as_view
     (template_name="mithreads/thread_list.html", 
      model=Thread,
      paginate_by=paginate_by),
     name="mithreads-list"),
   url(r'^(?P<thread_code>\w+)$', 'thread_view', 
     name="mithreads-thread"),
   url(r'^(?P<thread_code>\w+)/edit$', 'thread_edit_view', 
     name="mithreads-thread-edit"),
)

