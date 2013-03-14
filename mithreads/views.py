from mithreads.models import Thread
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required
import random
from math import *
import datetime

def thread_view(request, thread_code):
    thread = get_object_or_404(Thread, code=thread_code)

    # no Google analytics for now
    noanalytics=True

    if request.user.has_perm('mithreads.change_thread'):
        include_edit_link = True
    else:
        include_edit_link = False


    return render_to_response \
        ('mithreads/thread_detail.html', {'thread': thread, 
                                          'include_edit_link': include_edit_link,
                                          'thread_list': Thread.objects.all(),
                                          'noanalytics': noanalytics,
                                          },
         context_instance=RequestContext(request))


@permission_required('mithreads.change_thread')
def thread_edit_view(request, thread_code):
    thread = get_object_or_404(Thread, code=thread_code)

    # no Google analytics for now
    noanalytics=True

    return render_to_response \
        ('mithreads/thread_edit.html', {'thread': thread, 
                                          'noanalytics': noanalytics,
                                          },
         context_instance=RequestContext(request))

