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

    # if user is logged in and has active a course associated with thread
    # show course completion buttons
    show_course_completetion_buttons = False
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
              'thread_list': Thread.objects.all(),
              'student': student, 'course': course,              
              'noanalytics': noanalytics,
              },
         context_instance=RequestContext(request))


@permission_required('mithreads.change_thread')
def thread_edit_view(request, thread_code):
    thread = get_object_or_404(Thread, code=thread_code)

    # no Google analytics for edit
    noanalytics=True

    return render_to_response \
        ('mithreads/thread_edit.html', {'thread': thread, 
                                          'noanalytics': noanalytics,
                                          },
         context_instance=RequestContext(request))

