from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mithreads.models import Thread
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required
from django.conf import settings
import random
from math import *
import datetime

def thread_view(request, thread_code):
    thread = get_object_or_404(Thread, code=thread_code)

    noanalytics=False
    if settings.SITE_ID==2:
        noanalytics=True

    if request.user.has_perm('mithreads.change_thread'):
        include_edit_link = True
    else:
        include_edit_link = False

    # record if user is logged in and has active a course associated with thread
    course = None
    student = None
    if request.user.is_authenticated():
        try:
            student = request.user.courseuser
            course = student.return_selected_course()
            if course not in thread.course_set.all():
                course = None
        except:
            pass

    return render_to_response \
        ('mithreads/thread_detail.html', \
             {'thread': thread, 
              'include_edit_link': include_edit_link,
              'thread_list': Thread.activethreads.all(),
              'student': student, 'course': course,              
              'noanalytics': noanalytics,
              },
         context_instance=RequestContext(request))


@permission_required('mithreads.change_thread')
def thread_edit_view(request, thread_code):
    thread = get_object_or_404(Thread, code=thread_code)

    # record if user is logged in and has active a course associated with thread
    course = None
    courseuser = None
    if request.user.is_authenticated():
        try:
            courseuser = request.user.courseuser
            course = courseuser.return_selected_course()
            if course not in thread.course_set.all():
                course = None
        except:
            pass

    # no Google analytics for edit
    noanalytics=True

    return render_to_response \
        ('mithreads/thread_edit.html', {'thread': thread, 
                                        'courseuser': courseuser,
                                        'course': course,
                                        'noanalytics': noanalytics,
                                        },
         context_instance=RequestContext(request))

