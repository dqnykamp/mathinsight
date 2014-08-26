from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.conf.urls import patterns, url
from django.views.generic import ListView
from mithreads.models import Thread

paginate_by=20

urlpatterns = patterns('mithreads.views',
   url(r'^list$', ListView.as_view
     (template_name="mithreads/thread_list.html", 
      queryset=Thread.activethreads.all(),
      paginate_by=paginate_by),
     name="mithreads-list"),
   url(r'^(?P<thread_code>\w+)$', 'thread_view', 
     name="mithreads-thread"),
   url(r'^(?P<thread_code>\w+)/edit$', 'thread_edit_view', 
     name="mithreads-thread-edit"),
)

