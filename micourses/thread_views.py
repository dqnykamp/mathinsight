from micourses.models import Course, ThreadContent, ThreadSection, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from micourses.forms import thread_content_form_factory
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView, View
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.template import Context, Template
import pytz
import reversion


class ThreadView(DetailView):
    model=Course
    slug_field='code'
    slug_url_kwarg ='course_code'
    template_name = 'micourses/threads/thread_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.user = request.user

        if self.user.is_authenticated():
            self.courseuser = self.user.courseuser

            # make sure this course is saved as selected course enrollment
            try:
                self.enrollment = self.object.courseenrollment_set.get(
                    student=self.courseuser)
            except ObjectDoesNotExist:
                self.enrollment=None
            else:
                if self.enrollment!=self.courseuser.selected_course_enrollment:
                    self.courseuser.selected_course_enrollment =self.enrollment
                    self.courseuser.save()
        else:
            self.courseuser= None
            self.enrollment=None

        # update session with last course viewed
        request.session['last_course_viewed'] = self.object.id

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)

        noanalytics=False
        if settings.SITE_ID <= 2:
            noanalytics=True

        context['noanalytics'] = noanalytics

        if self.enrollment and self.enrollment.role==DESIGNER_ROLE:
            context['include_edit_link'] = True
        else:
            context['include_edit_link'] = False

        context['student'] = self.courseuser
        context['enrollment'] = self.enrollment

        if self.object.numbered:
            context['ltag'] = "ol"
        else:
            context['ltag'] = "ul"

        context['course_list'] = Course.active_courses.all()

        return context


class ThreadEditView(DetailView):
    model=Course
    slug_field='code'
    slug_url_kwarg ='course_code'
    template_name = 'micourses/threads/thread_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(self.object) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return redirect('mithreads:thread', course_code=self.object.code)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        context = super(ThreadEditView, self).get_context_data(**kwargs)

        # no Google analytics for edit
        context['noanalytics'] = False

        if self.object.numbered:
            context['ltag'] = "ol"
        else:
            context['ltag'] = "ul"

        return context


class EditSectionView(View):
    """
    Perform one of the following changes to a ThreadSection
    depending on value of POST parameter action:
    - dec_level: decrement the level of the section
    - inc_level: increment the level of the section
    - move_up: move section up
    - move_down: move section down
    - delete: delete section
    - edit: change section name
    - insert: insert new section (below current if exists, else at top)

    # must be designer of course
    
    """

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
                    course = Course.objects.get(id=request.POST['course_id'])
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
            course = thread_section.get_course()

        
        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})

      
        rerender_thread=True
        new_section_html={}
        rerender_sections=[]
        replace_section_html={}

        if course.numbered:
            ltag = "ol"
        else:
            ltag = "ul"

        # decrement level of section
        if action=='dec_level':
            if thread_section.course is None:
                parent = thread_section.parent
                next_sibling = parent.find_next_sibling()

                if next_sibling:
                    if parent.sort_order==next_sibling.sort_order:
                        course.reset_thread_section_sort_order()
                        parent.refresh_from_db()
                        next_sibling.refresh_from_db()

                    thread_section.sort_order = \
                        (parent.sort_order+next_sibling.sort_order)/2

                else:
                    thread_section.sort_order = parent.sort_order+1

                if parent.course:
                    if parent.course != course:
                        return JsonResponse({})

                    thread_section.parent = None
                    thread_section.course = course

                else:
                    thread_section.parent = parent.parent
                    

                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()


        # increment level of section
        elif action=='inc_level':
            previous_sibling = thread_section.find_previous_sibling()
            
            if previous_sibling:
                last_child = previous_sibling.child_sections.last()
                thread_section.parent = previous_sibling
                thread_section.course = None
                if last_child:
                    thread_section.sort_order = last_child.sort_order+1
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()

        # move section up
        elif action=="move_up":

            previous_sibling = thread_section.find_previous_sibling()
            if previous_sibling:
                if previous_sibling.sort_order == thread_section.sort_order:
                    course.reset_thread_section_sort_order()
                    previous_sibling.refresh_from_db()
                    thread_section.refresh_from_db()
                sort_order = thread_section.sort_order
                thread_section.sort_order = previous_sibling.sort_order
                previous_sibling.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()
                    previous_sibling.save()

            elif not thread_section.course:
                previous_parent_sibling = \
                    thread_section.parent.find_previous_sibling()
            
                if previous_parent_sibling:
                    last_child = previous_parent_sibling.child_sections.last()
                    if last_child:
                        thread_section.sort_order = last_child.sort_order+1
                    thread_section.parent = previous_parent_sibling
                    with transaction.atomic(), reversion.create_revision():
                        thread_section.save()


        # move section down
        elif action=="move_down":

            next_sibling = thread_section.find_next_sibling()
            if next_sibling:
                if next_sibling.sort_order == thread_section.sort_order:
                    course.reset_thread_section_sort_order()
                    next_sibling.refresh_from_db()
                    thread_section.refresh_from_db()
                sort_order = thread_section.sort_order
                thread_section.sort_order = next_sibling.sort_order
                next_sibling.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()
                    next_sibling.save()

            elif not thread_section.course:
                next_parent_sibling = \
                    thread_section.parent.find_next_sibling()
            
                if next_parent_sibling:
                    first_child = next_parent_sibling.child_sections.first()
                    if first_child:
                        thread_section.sort_order = first_child.sort_order-1
                    thread_section.parent = next_parent_sibling
                    with transaction.atomic(), reversion.create_revision():
                        thread_section.save()

        # delete section
        elif action=="delete":
            # rerender next and prevous siblings as commands may have changed
            sibling=thread_section.find_next_sibling()
            if sibling:
                rerender_sections.append(sibling)
            sibling=thread_section.find_previous_sibling()
            if sibling:
                rerender_sections.append(sibling)

            thread_section.mark_deleted()
            rerender_thread=False
            
        # edit section name
        elif action=="edit":
            thread_section.name = request.POST['section_name']
            with transaction.atomic(), reversion.create_revision():
                thread_section.save();
            rerender_thread=False

        # insert section
        elif action=="insert":
            new_section_name = request.POST['section_name']
            
            if thread_section:
                # add section as first child of current section
                try:
                    new_sort_order = thread_section.child_sections.first()\
                                                                .sort_order-1
                except AttributeError:
                    new_sort_order=0

                with transaction.atomic(), reversion.create_revision():
                    new_section = ThreadSection.objects.create(
                        name=new_section_name, 
                        parent=thread_section,
                        sort_order=new_sort_order)

                prepend_section = "child_sections_%s" % thread_section.id

            else:
                # add section as first in course
                try:
                    new_sort_order = course.thread_sections.first().sort_order-1
                except AttributeError:
                    new_sort_order = 0
                    
                with transaction.atomic(), reversion.create_revision():
                    new_section = ThreadSection.objects.create(
                        name=new_section_name, 
                        course=course,
                        sort_order=new_sort_order)
                    
                prepend_section = "child_sections_top"

            # rerender next siblings as commands may have changed
            sibling=new_section.find_next_sibling()
            if sibling:
                rerender_sections.append(sibling)
            
            template = Template("{% load thread_tags %}<li id='thread_section_{{section.id}}'>{% thread_section_edit section %}</li>")
            context = Context({'section': new_section, 'ltag': ltag})

            new_section_html[prepend_section] = template.render(context)


            course.reset_thread_section_sort_order()
            rerender_thread = False

        
        for section in rerender_sections:
            template = Template("{% load thread_tags %}{% thread_section_edit section %}")
            context = Context({'section': section, 'ltag': ltag})

            replace_section_html[section.id] = template.render(context)
            
            
        if rerender_thread:

            # must reset thread section sort order if changed sections
            # because thread_content ordering depends on thread_sections
            # as a single group being sorted correctly
            course.reset_thread_section_sort_order()

            # generate html for entire thread
            from django.template.loader import render_to_string

            thread_html = render_to_string(
                template_name='micourses/threads/thread_edit_sub.html',
                context = {'course': course, 'ltag': ltag }
            )
        else:
            thread_html = None

        return JsonResponse({'action': action,
                             'section_id': section_id,
                             'course_id': course.id,
                             'thread_html': thread_html,
                             'new_section_html': new_section_html,
                             'replace_section_html': replace_section_html,
                             })

class EditContentView(View):
    """
    Perform one of the following changes to a ThreadContent
    depending on value of POST parameter action:
    - move_up: move content up
    - move_down: move content down
    - delete: delete content
    - edit: edit content attributes
    - insert: insert new content at end of section

    Must be designer of course

    """


    def post(self, request, *args, **kwargs):

        try:
            action = request.POST['action']
            the_id = request.POST['id']
        except KeyError:
            return JsonResponse({})

        form_html=""

        # if action is insert, then the_id must be a valid section_id
        if action=='insert':
            try:
                thread_section = ThreadSection.objects.get(id=the_id)
            except (KeyError, ValueError, ObjectDoesNotExist):
                return JsonResponse({})

            course = thread_section.get_course()
            thread_content=None

        # else, the_id must be a valid content_id
        else:
            try:
                thread_content = ThreadContent.objects.get(id=the_id)
            except (KeyError, ValueError, ObjectDoesNotExist):
                return JsonResponse({})

            course = thread_content.course
            thread_section=thread_content.section

        
        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})


        rerender_sections = []

        # move content up
        if action=="move_up":
            previous_in_section = thread_content.find_previous(in_section=True)
            if previous_in_section:
                if previous_in_section.sort_order == thread_content.sort_order:
                    thread_section.reset_thread_content_sort_order()
                    previous_in_section.refresh_from_db()
                    thread_content.refresh_from_db()
                sort_order = thread_content.sort_order
                thread_content.sort_order = previous_in_section.sort_order
                previous_in_section.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()
                    previous_in_section.save()

                rerender_sections = [thread_section,]

            else:
                # if thread_content is first in section, then move up to
                # end of previous section

                previous_section = thread_section.find_previous()
                try:
                    thread_content.sort_order = previous_section\
                                  .thread_contents.last().sort_order+1
                except AttributeError:
                    thread_content.sort_order = 0
                thread_content.section = previous_section
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()

                rerender_sections = [thread_section, previous_section]

        # move content down
        if action=="move_down":
            next_in_section = thread_content.find_next(in_section=True)
            if next_in_section:
                if next_in_section.sort_order == thread_content.sort_order:
                    thread_section.reset_thread_content_sort_order()
                    next_in_section.refresh_from_db()
                    thread_content.refresh_from_db()
                sort_order = thread_content.sort_order
                thread_content.sort_order = next_in_section.sort_order
                next_in_section.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()
                    next_in_section.save()

                rerender_sections = [thread_section,]

            else:
                # if thread_content is last in section, then move down to
                # beginning of next section

                next_section = thread_section.find_next()
                try:
                    thread_content.sort_order = next_section\
                                  .thread_contents.first().sort_order-1
                except AttributeError:
                    thread_content.sort_order = 0
                thread_content.section = next_section
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()

                rerender_sections = [thread_section, next_section]
        
        # delete content
        elif action=="delete":
            thread_content.mark_deleted()
            rerender_sections = [thread_section,]


        # edit content
        elif action=="edit":
            try:
                content_type = ContentType.objects.get(id=request.POST['content_type'])
                
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({});

            form_identifier = "edit_%s" % the_id

            update_options_command="update_content_options('%s', this.value)"% \
                form_identifier

            form = thread_content_form_factory(
                the_content_type=content_type,
                update_options_command=update_options_command
            )
            form = form(request.POST, instance=thread_content,
                        auto_id="content_form_%s_%%s" % form_identifier,
                    )
            if form.is_valid():
                with transaction.atomic(), reversion.create_revision():
                    form.save()
                rerender_sections = [thread_section,]
            else:
                form_html = form.as_p()


        # insert content
        elif action=="insert":
            try:
                content_type = ContentType.objects.get(id=request.POST['content_type'])
                
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({});

            form_identifier = "insert_%s" % the_id

            update_options_command="update_content_options('%s', this.value)"% \
                form_identifier

            try:
                new_sort_order = thread_section.thread_contents.last()\
                                                              .sort_order+1
            except AttributeError:
                new_sort_order = 0

            initial={'section': thread_section, 
                     'course': thread_section.get_course(),
                     'sort_order': new_sort_order}

            form = thread_content_form_factory(
                the_content_type=content_type,
                update_options_command=update_options_command
            )
            form = form(request.POST,
                        auto_id="content_form_%s_%%s" % form_identifier,
                    )
            if form.is_valid():
                with transaction.atomic(), reversion.create_revision():
                    new_thread_content=form.save(commit=False)
                    new_thread_content.section=thread_section
                    new_thread_content.sort_order = new_sort_order
                    new_thread_content.save()

                rerender_sections = [thread_section,]
            else:
                form_html = form.as_p()



        section_contents={}
        for section in rerender_sections:
            # generate html for thread_content of section
            from django.template.loader import render_to_string

            content_html = render_to_string(
                template_name='micourses/threads/thread_content_edit_container.html',
                context = {'thread_section': section }
            )
            
            section_contents[section.id] = content_html

        return JsonResponse({'section_contents': section_contents,
                             'action': action,
                             'id': the_id,
                             'form_html': form_html,
                             })


class ReturnContentForm(View):
   def post(self, request, *args, **kwargs):

        try:
            form_type = request.POST['form_type']
            the_id = request.POST['id']
        except KeyError:
            return JsonResponse({})

        instance = None
        thread_content=None
        thread_section=None

        # If form type is "edit", then the_id must be 
        # a valid thread_content id.
        # Populate form with instance of that thread_content
        if form_type=="edit":
            try:
                thread_content = ThreadContent.objects.get(id=the_id)
            except (KeyError,ObjectDoesNotExist):
                return JsonResponse({})

            instance = thread_content
            the_content_type = thread_content.content_type

        # If form type is "insert", then the_id must be
        # a valid thread_section id.
        # Create blank form 
        elif form_type=="insert":
            try:
                thread_section = ThreadSection.objects.get(id=the_id)
            except ObjectDoesNotExist:
                return JsonResponse({})
            the_content_type = None


        # else invalid form_type
        else:
            return JsonResponse({})


        # must be designer of course
        if thread_content:
            course=thread_content.course
        else:
            course=thread_section.get_course()
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})


        form_identifier = "%s_%s" % (form_type, the_id)

        update_options_command="update_content_options('%s', this.value, '%s')" % \
            (form_identifier, course.code)

        form = thread_content_form_factory(
            the_content_type=the_content_type,
            update_options_command=update_options_command
        )
        form = form(instance=instance, 
                    auto_id="content_form_%s_%%s" % form_identifier,
        )

        form_html = form.as_p()

        return JsonResponse({'form_type': form_type,
                             'id': the_id,
                             'form_html': form_html})



class ReturnContentOptions(View):

    def post(self, request, *args, **kwargs):
        
        # must be designer of some course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role() 
            if role==DESIGNER_ROLE:
                is_designer=True
        if not is_designer:
            return JsonResponse({})

        try:
            form_id = request.POST['form_id']
            this_content_type = ContentType.objects.get(id=request.POST['option'])
            course_code = request.POST['course_code']
            course = Course.objects.get(code=course_code)
        except (KeyError,ObjectDoesNotExist):
            return JsonResponse({})
            
        content_options = '<option selected="selected" value="">---------</option>\n'

        # for assessment, filter just for course
        if this_content_type.model == 'assessment':
            queryset = this_content_type.model_class().objects.filter(course=course)
        else:
            queryset = this_content_type.model_class().objects.all()
        for item in queryset:
            content_options += "<option value='%s'>%s</option>\n" \
                                    % (item.id, item)

        return JsonResponse({'form_id': form_id, 
                             'content_options': content_options})
