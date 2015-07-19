from mithreads.models import Thread, ThreadSection
from mithreads.forms import ThreadSectionForm, thread_content_form_factory
from micourses.models import INSTRUCTOR_ROLE
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404, JsonResponse
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.conf import settings
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.contrib.contenttypes.models import ContentType
import random
from math import *
import datetime
import json

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



class EditSectionView(View):
    """
    Perform one of the following changes to a ThreadSection
    depending on value of POST parameter action:
    - dec_level: decrement the level of the section
    - inc_level: increment the level of the section
    - move_up: move section up
    - move_down: move section down
    - delete: delete section
    - edit: change section name or code
    - insert: insert new section (below current if exists, else at top)

    """

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
    def dispatch(self, request, *args, **kwargs):
        return super(EditSectionView, self)\
            .dispatch(request, *args, **kwargs) 


    def post(self, request, *args, **kwargs):

        try:
            action = request.POST['action']
        except KeyError:
            return JsonResponse({})


        try:
            section_id = int(request.POST.get('section_id'))
        except ValueError:
            section_id = None

        
        # if no section id, then action must be insert
        # and the thread must be specified
        if section_id is None:
            if action == 'insert':
                try:
                    thread = Thread.objects.get(id=request.POST['thread_id'])
                except (KeyError, ObjectDoesNotExist):
                    return JsonResponse({})
                thread_section=None
            else:
                return JsonResponse({})
        else:
            try:
                thread_section = ThreadSection.objects.get(id=section_id)
            except ObjectDoesNotExist:
                return JsonResponse({})
            thread = thread_section.thread
        
        error_message=""
        form_errors=""

        # decrement level of section
        if action=='dec_level':
            if thread_section.level > 1:
                children = thread_section.find_children()
                for section in [thread_section,] + children:
                    section.level -= 1
                    section.save()

        # increment level of section
        elif action=='inc_level':
            children = thread_section.find_children()
            for section in [thread_section,] + children:
                section.level += 1
                section.save()

        # move section up
        elif action=="move_up":

            children = thread_section.find_children()

            move_sections=[thread_section,] + children

            last_section = move_sections[-1]

            previous_section = thread_section.find_previous_section()
            if previous_section:
                swap_sections=[previous_section,]
                
                # if previous section is at a higher level
                # swap all sections until find one at same level or below

                if previous_section.level > thread_section.level:
                    while True:
                        previous_section = previous_section.find_previous_section()
                        if not previous_section:
                            break
                            
                        swap_sections.append(previous_section)

                        if previous_section.level <= thread_section.level:
                            break


                first_section = swap_sections[-1]

                last_sort_order=last_section.sort_order
                first_sort_order=first_section.sort_order
                # if sort_orders are the same, 
                # redo all sort orders before continuing
                if last_sort_order==first_sort_order:
                    for (i,ts) in enumerate(thread.thread_sections.all()):
                        ts.sort_order=i
                        ts.save()
                    last_section.refresh_from_db()
                    first_section.refresh_from_db()
                    last_sort_order=last_section.sort_order
                    first_sort_order=first_section.sort_order


                d_order = (last_sort_order-first_sort_order)\
                          /(len(move_sections)+len(swap_sections))

                for (i,section) in enumerate(move_sections):
                    section.sort_order = first_sort_order + i*d_order
                    section.save()

                first_sort_order += len(move_sections)*d_order
                for (i,section) in enumerate(reversed(swap_sections)):
                    section.sort_order = first_sort_order + i*d_order
                    section.save()

        # move section down
        elif action=="move_down":

            children = thread_section.find_children()

            move_sections = [thread_section,] + children

            first_section = thread_section

            next_section = move_sections[-1].find_next_section()
            if next_section:
                swap_sections=[next_section,] 
                
                # if next section is at same level
                # then swap with all its children
                if next_section.level == thread_section.level:
                    swap_sections += next_section.find_children()

                last_section = swap_sections[-1]


                first_sort_order=first_section.sort_order
                last_sort_order=last_section.sort_order
                # if sort_orders are the same, 
                # redo all sort orders before continuing
                if first_sort_order==last_sort_order:
                    for (i,ts) in enumerate(thread_section.thread.thread_sections.all()):
                        ts.sort_order=i
                        ts.save()
                    first_section.refresh_from_db()
                    last_section.refresh_from_db()
                    first_sort_order=first_section.sort_order
                    last_sort_order=last_section.sort_order

                d_order = (last_sort_order-first_sort_order)\
                          /(len(move_sections)+len(swap_sections))

                for (i,section) in enumerate(swap_sections):
                    section.sort_order = first_sort_order + i*d_order
                    section.save()

                first_sort_order += len(swap_sections)*d_order
                for (i,section) in enumerate(move_sections):
                    section.sort_order = first_sort_order + i*d_order
                    section.save()

        # delete section
        elif action=="delete":
            thread_section.delete()

        elif action=="edit":
            form = ThreadSectionForm(request.POST)

            if form.is_valid():
                new_section_name = form.cleaned_data.get('section_name')
                new_section_code = form.cleaned_data.get('section_code')
                
                thread_section.name = new_section_name
                thread_section.code = new_section_code
                try:
                    thread_section.save()
                except IntegrityError as e:
                    error_message = "Cannot change section. Duplicate code: %s" % new_section_code
            
            else:
                # if form is not valid
                form_errors = {'section_name': form['section_name'].errors,
                               'section_code': form['section_code'].errors}
                
        elif action=="insert":
            
            form = ThreadSectionForm(request.POST)
            
            if form.is_valid():
                new_section_name = form.cleaned_data.get('section_name')
                new_section_code = form.cleaned_data.get('section_code')

                if thread_section:

                    # add section after current sectoin
                    this_sort_order=thread_section.sort_order
                    next_section = thread_section.find_next_section()
                    if next_section:
                        new_sort_order= (this_sort_order+next_section.sort_order)/2.0
                    else:
                        new_sort_order=this_sort_order+1.0
                    level = thread_section.level

                else:
                    try:
                        new_sort_order=thread.thread_sections.all()[0].sort_order-1.0
                    except:
                        new_sort_order=0
                    level=1

                new_section = ThreadSection(
                    name=new_section_name, code=new_section_code,
                    thread=thread,
                    sort_order=new_sort_order,
                    level=level)

                try:
                    new_section.save()
                except IntegrityError as e:
                    error_message = "Cannot add section. Duplicate code: %s" % new_section_code

            else:
                # if form is not valid
                form_errors = {'section_name': form['section_name'].errors,
                               'section_code': form['section_code'].errors}

        # if no errors, then thread was changed so rerender thread
        if not error_message and not form_errors:
            thread_contents = thread.render_html_edit_string()
            errors = False
        else:
            thread_contents = None
            errors=True

        return JsonResponse({'thread_contents': thread_contents,
                             'error_message': error_message,
                             'form_errors': form_errors,
                             'errors': errors,
                             'action': action,
                             'section_id': section_id,
                             'thread_id': thread.id,
                             })


class ReturnContentForm(View):
    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
    def dispatch(self, request, *args, **kwargs):
        return super(ReturnContentForm, self)\
            .dispatch(request, *args, **kwargs) 


    def post(self, request, *args, **kwargs):
        
        content_form_info = request.POST['content_form_info']
        
        # content_type_id = request.POST.get('content_type_id')
        # object_id = request.POST.get('object_id');
        # section_id = request.POST.get('section_id');
        
        if content_form_info.get('content_type_id') is not None:
            try:
                content_type = ContentType.objects.get(
                    id=content_form_info.get('content_type_id'))
            except ObjectDoesNotExist:
                content_type = None
        else:
            content_type=None

        if content_form_info.get('object_id') is None:
            id_base = 'insert_content_form_%s' % \
                      content_form_info.get('section_id')
            form = thread_content_form_factory()(
                auto_id=id_base + "_%s"
            )
        else:
            id_base = 'update_content_form_%s_%s' % \
                      (content_form.get('section_id'), 
                       content_form.get('object_id'))
            form = thread_content_form_factory(content_type)(
                {'content_type': content_type,
                 'object_id': content_form_info.get('object_id') },
                auto_id=id_base + "_%s"
            )

        update_options_command="update_content_options(%s, this.value)" % \
            json.dumps(content_form_info)


        form_html = '<p>%s %s' % (form['content_type'].label_tag(), form['content_type'].as_widget(attrs={"onchange": update_options_command}))
        form_html += ' <span id="%s_content_type_errors" class="error"></span></p>' % id_base
        form_html += '<p>%s %s' % (form['object_id'].label_tag(), form['object_id'].as_widget())
        form_html += ' <span id="%s_object_id_errors" class="error"></span></p>' % id_base
        form_html += '<p>%s %s' % (form['substitute_title'].label_tag(), form['substitute_title'].as_widget())
        form_html += ' <span id="%s_substitute_title_errors" class="error"></span></p>' % id_base
        form_html += '<p id="%s_errors" class="error"></p>' % id_base
        
        return JsonResponse({'content_form_info': content_form_info,
                             'form_html': form_html})



class ReturnContentOptions(View):
    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
    def dispatch(self, request, *args, **kwargs):
        return super(ReturnContentOptions, self)\
            .dispatch(request, *args, **kwargs) 


    def post(self, request, *args, **kwargs):
        
        content_form_info = {
            'content_type_id': request.POST.get('content_type_id'),
            'object_id': request.POST.get('object_id'),
            'section_id': request.POST.get('section_id'),
        }


        try:
            this_content_type = ContentType.objects.get(id=request.POST['option'])
        except (KeyError,ObjectDoesNotExist):
            return JsonResponse({})

        content_options = '<option selected="selected" value="">---------</option>\n'
        for item in this_content_type.model_class().objects.all():
            content_options += "<option value='%s'>%s</option>\n" \
                                    % (item.id, item)
        return JsonResponse({'content_form_info': content_form_info, 
                             'content_options': content_options})



class EditContentView(View):
    """
    Perform one of the following changes to a ThreadSection
    depending on value of POST parameter action:
    - move_up: move section up
    - move_down: move section down
    - delete: delete section
    - edit: change section name or code
    - insert: insert new section (below current if exists, else at top)

    """

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
    def dispatch(self, request, *args, **kwargs):
        return super(EditSectionView, self)\
            .dispatch(request, *args, **kwargs) 


    def post(self, request, *args, **kwargs):

        try:
            action = request.POST['action']
        except KeyError:
            return JsonResponse({})


        # if action is insert,
        # then thread_section or thread must be specified
        if action=="insert":
            try:
                thread_section = ThreadSection.objects.get(
                    id=request.POST['section_id'])
                thread = thread_section.thread
            except (KeyError, ObjectDoesNotExist):
                thread_section = None
            if thread_section is None:
                try:
                    thread = Thread.objects.get(id=request.POST['thread_id'])
                except (KeyError, ObjectDoesNotExist):
                    return JsonResponse({})

        # otherwise, content_id must be specified
        else:
            try:
                content_id = int(request.POST.get('content_id'))
            except ValueError:
                return JsonResponse({})

            try:
                thread_content = ThreadContent.objects.get(id=content_id)
            except ObjectDoesNotExist:
                return JsonResponse({})
            thread_section = thread_content.section
            thread = thread_section.thread
        
        error_message=""
        form_errors=""
        
        rerender_sections=[]


        # move content up
        if action=="move_up":
            
            # if previous content in section, switch order
            previous_content = thread_content.find_previous_in_section()
            if previous_content:
                this_sort_order = thread_content.sort_order
                previous_sort_order = previous_content.sort_order

                # if sort_orders are the same, 
                # redo all sort orders before continuing
                if this_sort_order==previous_sort_order:
                    for (i,tc) in enumerate(thread_content.section.threadcontent_set.all()):
                        tc.sort_order=i
                        tc.save()
                    thread_content.refresh_from_db()
                    previous_content.refresh_from_db()
                    this_sort_order = thread_content.sort_order
                    previous_sort_order = previous_content.sort_order
                thread_content.sort_order = previous_sort_order
                previous_content.sort_order = this_sort_order
                thread_content.save()
                previous_content.save()

                # rewrite just thread content of section
                rerender_section.push(
                    (thread_section.code, 
                     thread_section.return_content_html_string(edit=True)))


            # if content is first in section, move to end of previous section
            else:
                previous_section = thread_content.section.find_previous_section()
                if previous_section:
                    other_content =  previous_section.threadcontent_set.reverse()
                    if other_content:
                        last_sort_order = other_content[0].sort_order
                        new_sort_order = last_sort_order +1
                    else:
                        new_sort_order = 0
                    thread_content.section = previous_section
                    thread_content.sort_order = new_sort_order
                    thread_content.save()

                    # rewrite just thread content of section and previous
                    rerender_section.push(
                        (thread_section.code, 
                         thread_section.return_content_html_string(edit=True)))
                    rerender_section.push(
                        (previous_section.code, 
                         previous_section.return_content_html_string(edit=True)))

        # move content down
        elif action=="move_down":

            # if next content in section, switch order
            next_content = thread_content.find_next_in_section()
            if next_content:
                this_sort_order = thread_content.sort_order
                next_sort_order = next_content.sort_order

                # if sort_orders are the same, 
                # redo all sort orders before continuing
                if this_sort_order==next_sort_order:
                    for (i,tc) in enumerate(thread_content.section.threadcontent_set.all()):
                        tc.sort_order=i
                        tc.save()
                    thread_content.refresh_from_db()
                    next_content.refresh_from_db()
                    this_sort_order = thread_content.sort_order
                    next_sort_order = next_content.sort_order
                thread_content.sort_order = next_sort_order
                next_content.sort_order = this_sort_order
                thread_content.save()
                next_content.save()

                # rewrite just thread content of section
                rerender_section.push(
                    (thread_section.code, 
                     thread_section.return_content_html_string(edit=True)))

            # if content is last in section, move to beginning of next section
            else:
                next_section = thread_content.section.find_next_section()
                if next_section:
                    other_content=next_section.threadcontent_set.all()
                    if other_content:
                        first_sort_order=other_content[0].sort_order
                        new_sort_order = first_sort_order-1
                    else:
                        new_sort_order = 0
                    thread_content.section = next_section
                    thread_content.sort_order = new_sort_order
                    thread_content.save()


                    # rewrite just thread content of section and next_section
                    rerender_section.push(
                        (thread_section.code, 
                         thread_section.return_content_html_string(edit=True)))
                    rerender_section.push(
                        (next_section.code, 
                         next_section.return_content_html_string(edit=True)))


        # delete section
        elif action=="delete":
            thread_content.delete()
            rerender_section.push(
                (thread_section.code, 
                 thread_section.return_content_html_string(edit=True)))
                        
        elif action=="edit":
            form = ThreadSectionForm(request.POST)

            if form.is_valid():
                new_section_name = form.cleaned_data.get('section_name')
                new_section_code = form.cleaned_data.get('section_code')
                
                thread_section.name = new_section_name
                thread_section.code = new_section_code
                try:
                    thread_section.save()
                except IntegrityError as e:
                    error_message = "Cannot change section. Duplicate code: %s" % new_section_code
            
            else:
                # if form is not valid
                form_errors = {'section_name': form['section_name'].errors,
                               'section_code': form['section_code'].errors}
                
        elif action=="insert":
            
            form = ThreadSectionForm(request.POST)
            
            if form.is_valid():
                new_section_name = form.cleaned_data.get('section_name')
                new_section_code = form.cleaned_data.get('section_code')

                if thread_section:

                    # add section after current sectoin
                    this_sort_order=thread_section.sort_order
                    next_section = thread_section.find_next_section()
                    if next_section:
                        new_sort_order= (this_sort_order+next_section.sort_order)/2.0
                    else:
                        new_sort_order=this_sort_order+1.0
                    level = thread_section.level

                else:
                    try:
                        new_sort_order=thread.thread_sections.all()[0].sort_order-1.0
                    except:
                        new_sort_order=0
                    level=1

                new_section = ThreadSection(
                    name=new_section_name, code=new_section_code,
                    thread=thread,
                    sort_order=new_sort_order,
                    level=level)

                try:
                    new_section.save()
                except IntegrityError as e:
                    error_message = "Cannot add section. Duplicate code: %s" % new_section_code

            else:
                # if form is not valid
                form_errors = {'section_name': form['section_name'].errors,
                               'section_code': form['section_code'].errors}

        # if no errors, then thread was changed so rerender thread
        if not error_message and not form_errors:
            thread_contents = thread.render_html_edit_string()
            errors = False
        else:
            thread_contents = None
            errors=True

        return JsonResponse({'thread_contents': thread_contents,
                             'error_message': error_message,
                             'form_errors': form_errors,
                             'errors': errors,
                             'action': action,
                             'section_id': section_id,
                             'thread_id': thread.id,
                             })
