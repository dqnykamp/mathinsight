from micourses.models import Assessment, ThreadContent, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from micourses.permissions import user_has_given_assessment_permission_level, user_can_administer_assessment
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView, View, FormView
from django.views.generic.detail import SingleObjectMixin
from django.http import Http404
from django.utils.decorators import method_decorator
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django import forms
from micourses.forms import GenerateCourseAttemptForm
import reversion


class AssessmentView(DetailView):
    """
    View assessment or assessment solution

    Accepts either get or post, with seed given as a parameter.
    Checks if logged in uscter has required permissions. 
    For solution, checks if logged in user with level 2 permissions.
    If user doesn't have required permissions, redirects to forbidden page
    If not solution, then shows help and solution buttons, if available.

    Add the following to the context:
    - question_data: dictionary returned by render_assessments.render_question.
      This dictionary contains the information about the question that is
      used by the template mitesting/question_body.html
    - show_lists: True if should show lists of assessments
    - noanalytics: True to indicate shouldn't link to Google analytics
    """

    model = Assessment
    slug_url_kwarg = 'assessment_code'
    slug_field = 'code'
    solution=False


    def get_template_names(self):
        """
        Returns a list of template names to be used for the request.
        Called by based implementation of render_to_response.

        If template base name is defined in assessment type,
        makes that name be the primary name, with fallback to assessment.html.
        Appends _solution if rendering solution
        """
        template_names = []
        solution_postfix=""
        if self.solution:
            solution_postfix="_solution"
        template_base_name = self.object.assessment_type.template_base_name
        if template_base_name:
            template_names.append("micourses/assessments/%s%s.html" % 
                                  (template_base_name, solution_postfix))
        template_names.append("micourses/assessments/assessment%s.html" % solution_postfix)

        return template_names


    def get_context_data(self, **kwargs):
        context = super(AssessmentView, self).get_context_data(**kwargs)

        context['assessment_date'] = kwargs['assessment_date']

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()
        context['_auxiliary_data_'] = auxiliary_data

        import random
        rng=random.Random()

        # show post user response errors only if instructor permissions
        if user_has_given_assessment_permission_level(
                self.request.user, 2):
            show_post_user_errors=True
        else:
            show_post_user_errors=False

        from micourses.render_assessments import render_question_list
        rendered_list=render_question_list(
            self.assessment, self.question_list, rng=rng, 
            assessment_seed=self.assessment_seed, 
            user=self.request.user, 
            solution=self.solution,
            auxiliary_data = auxiliary_data,
            show_post_user_errors=show_post_user_errors)

        # if question_only is set, then view only that question
        if self.kwargs.get('question_only'):
            question_only = int(self.kwargs['question_only'])
            rendered_list=rendered_list[question_only-1:question_only]
            context['question_only'] = question_only
        context['rendered_list'] = rendered_list

        context['seed'] = self.assessment_seed

        # determine if there were any errors
        success=True
        question_errors=[]
        for (ind,q) in enumerate(rendered_list):
            if not q["question_data"]["success"]:
                success=False
                question_errors.append(str(ind+1))
        if not success:
            context['error_message'] = \
                "Errors occurred in the following questions: %s" %\
                ", ".join(question_errors)

        context['success'] = success
        
        context['generate_course_attempt_link'] = False
        context['show_solution_link'] = False
        
        if user_can_administer_assessment(self.request.user, 
                                          course=self.object.course):
            if self.thread_content:
                context['generate_course_attempt_link'] = True
            if not self.solution:
                context['show_solution_link'] = True

        if self.thread_content:
            context['assessment_name'] = self.thread_content.get_title()
        else:
            context['assessment_name'] = self.assessment.name
        if self.solution:
            context['assessment_name'] += " solution"
        context['assessment_short_name'] = self.assessment.return_short_name()
        if self.solution:
            context['assessment_short_name'] += " sol."

        if self.version:
            context['version'] =  self.version
            context['assessment_name_with_version'] = "%s, version %s" % \
                        (context['assessment_name'], context['version'])
            context['assessment_short_name_with_version'] = "%s, version %s" % \
                        (context['assessment_short_name'], context['version'])
        else:
            context['version'] = ''
            context['assessment_name_with_version'] = context['assessment_name']
            context['assessment_short_name_with_version'] \
                = context['assessment_short_name']

        context['course'] = self.assessment.course
        context['thread_content'] = self.thread_content
        context['number_in_thread'] = self.number_in_thread
        context['current_attempt'] = self.current_attempt

        context['users attempt'] = False
        context['multiple_attempts'] = False
        context['attempt_url']=None
        context['record_url']=None

        # Check if have current attempt that belongs to user
        # (so can show score)
        # Create links to record and attempts (if valid)

        if self.current_attempt and \
           self.current_attempt.record.enrollment == self.course_enrollment:

            context['users_attempt'] = True

            valid_attempt_list = list(
                self.current_attempt.record.attempts.filter(valid=True))
            context['multiple_attempts'] = len(valid_attempt_list)>1

            context['record_url'] = reverse(
                'micourses:content_record',
                kwargs={'course_code': self.assessment.course.code,
                        'content_id': self.thread_content.id})

            if self.current_attempt.valid:
                attempt_number = valid_attempt_list.index(self.current_attempt)\
                                 +1
                context['attempt_url'] = reverse(
                    'micourses:content_attempt', 
                    kwargs={'course_code': self.assessment.course.code,
                            'content_id': self.thread_content.id,
                            'attempt_number': attempt_number})

                # add question attempt urls to rendered_list question_data
                for (ind,q) in enumerate(rendered_list):
                    q["question_data"]["attempt_url"] = reverse(
                        'micourses:question_attempts', 
                        kwargs={'course_code': self.assessment.course.code, 
                                'content_id': self.thread_content.id, 
                                'attempt_number': attempt_number, 
                                'question_number': ind+1} )



        from mitesting.utils import round_and_int
        if self.thread_content:
            context['thread_content_points'] = round_and_int(
                self.thread_content.points)
        if self.current_attempt is None or self.current_attempt.score is None:
            context['attempt_score']=0
        else:
            context['attempt_score']=round_and_int(
                self.current_attempt.score,1)
        
        if self.current_attempt is None or \
           self.current_attempt.record.score is None:
            context['content_score']=0
        else:
            context['content_score']=round_and_int(
                self.current_attempt.record.score,1)


        # get list of the question numbers in assessment
        # if instructor or designer in course
        if user_can_administer_assessment(self.request.user,
                                          course=self.object.course):
            question_numbers=[]
            for q in rendered_list:
                question_numbers.append(str(q['question'].id))
            question_numbers = ", ".join(question_numbers)
        else:
            question_numbers=None
        context['question_numbers']=question_numbers

        # turn off Google analytics for localhost/development site
        context['noanalytics']=(settings.SITE_ID > 1)

        from mitesting.utils import get_new_seed
        context['new_seed']=get_new_seed(rng)

        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.model.objects.filter(
            course__code=self.kwargs["course_code"]))
        self.assessment = self.object


        # Determine if user has permission to view assessment or solution.
        # Only users with administer privileges can view solution this way.
        # All others can view solution only through injecting 
        # solution of individual questions via the "show solution" button
        # (where solution views are tracked).

        has_permission=False
        if  user_can_administer_assessment(request.user, 
                                           course=self.object.course):
            has_permission=True
        elif not self.solution and self.object.user_can_view(
                request.user, solution=False):
            has_permission=True
        if not has_permission:
            return redirect("mi-forbidden")

        try:
            self.number_in_thread=int(request.GET.get('n',1))
        except TypeError:
            self.number_in_thread=1

        try:
            self.determine_version_attempt(
                user=request.user,seed=request.GET.get('seed'),
                content_attempt_id = request.GET.get('content_attempt'),
                question_attempt_ids = request.GET.get('question_attempts'),
            )
        except ValueError as e:
            from django.template import Template, Context
            template_string = "{% extends 'base.html' %}{% block content %}"
            template_string += "<p>%s</p>" % e
            template_string += "{% endblock %}"
            context = Context({'STATIC_URL': settings.STATIC_URL})
            return HttpResponse(Template(template_string).render(context))

        # update selected course for course users
        # self.course_enrollment set by determine_version_attempt
        if self.course_enrollment \
           and self.course_enrollment != \
                    request.user.courseuser.selected_course_enrollment:
            request.user.courseuser.selected_course_enrollment =\
                                                    self.course_enrollment
            request.user.courseuser.save()

        # update session with last course viewed
        request.session['last_course_viewed'] = self.object.course.id

        # other data from GET
        current_tz = timezone.get_current_timezone()
        assessment_date = request.GET.get('date',
                current_tz.normalize(timezone.now().astimezone(current_tz))\
                                          .strftime("%B %d, %Y"))
        
        context = self.get_context_data(object=self.object, 
                                assessment_date=assessment_date)
        return self.render_to_response(context)


    def determine_version_attempt(self, user, seed, content_attempt_id, 
                                  question_attempt_ids):

        """
        Determine what version of assessment to generate.
        
        For enrolled students, find or create
        content attempts and question attempts.

        Set the following variables that give information about user
        and the assessment's role in course:
        self.course_enrollment
        self.thread_content
        self.current_attempt
        
        Set the following variables that specify the version of assessment:
        self.assessment_seed
        self.version
        self.question_list

        question_list is a list of dictionaries with the following info 
        about each question
        - question: the question chosen for the question_set
        - seed: the seed for the question
        - question_set (optional): the question set from which the question
          was chosen
        - question_attempt (optional): the question attempt in which
          to record responses.


        ------------------
        
        Behavior based on status of user as follows.

        Anonymous user behavior:
        just set seed via GET.  If seed is not specified, use seed=1.
        If single version, ignore seed from GET and use seed=1.
        Generate new seed and make link at bottom.
        Even if resample question sets, reloading page will reset with questions
        from that given assessment seed.

        Logged in user who isn't in course: 
        same as anonymous user behavior

        Logged in user who is an active student of course:
        If assessment is not in course thread, same as anonymous user behavior
        Otherwise
        - Ignore seed from GET
        - Determine availability of content 
        - Find latest content attempt
          If content attempt validity does not match, 
          treat as no matching attempt (available=valid)
          Obtain
          * assessment seed from content attempt 
          * list of questions sets in order (from content attempt question sets)
          * the latest question attempt for each question set
          * from each question attempt, determine
            + question
            + seed 
            + whether or not solution viewed
          If missing data (e.g., assessment seed or question attempts),
          then treat as though don't have content attempt and create new one
        - If no matching content attempt, 
          then create new content attempt and question attempts.
          Generate assessment seed as follows:
          * If not yet released, set seed to be attempt number.
          * Otherwise, create assessment seed from 
            + thread content id and attempt number
            + plus username if assessment is individualized by student
            Exception: set seed=1 if assessment marked as single version
          Use assessment seed to generate
          * list of question sets in order
          * question and seed
          Save 
          * assessment seed to content attempt
          * list of question sets in order to content attempt question sets
          * questions and their seeds to question attempt
          If not yet released or past due, mark content attempt
          and question attempts as invalid.


        Logged in user who is a withdrawn student of course:
        Treat like active student, only mark as withdrawn so can
        display message when submitting responses.


        Looged in user who is instructor of course:
        If assessment is not in course thread, same as anonymous user behavior
        Otherwise:
        If content_attempt id is in GET
        - generate assessment based on that content attempt,
          using the latest question attempts for each question set
        - if, in addition, GET contains list of question attempt ids, 
          then use those instead, assuming have one for each question set
          (if don't have one for each question set or question attempts don't
          belong to content attempt, then ignore and use latest question attempts.)
        - if content attempt doesn't have associated question attempts for
          all question sets, then ignore content_attempt id
        If no valid content_attempt id, but seed is in GET
        - use that to generate assessment (even if single version)
        Do not record any responses if generated from content attempt id or seed
        If no valid content attempt id and  seed is not in GET, 
        then treat as student of course


        """

        # sets the following variables
        self.course_enrollment=None
        self.thread_content=None
        self.assessment_seed= None
        self.version = ''
        self.current_attempt=None
        self.question_list = []

        from micourses.render_assessments import get_question_list
        from micourses.models import AVAILABLE,  NOT_YET_AVAILABLE


        #################################
        # first, determine status of user
        #################################

        # if course user doesn't exist, then is anonymous user
        # as logged in users should have a courseuser
        try:
            courseuser = user.courseuser
        except AttributeError:
            courseuser = None

        # check if enrolled in course
        current_role=None
        if courseuser:
            try:
                self.course_enrollment = self.assessment.course\
                        .courseenrollment_set.get(student=courseuser)
            except ObjectDoesNotExist:
                pass
            else:
                current_role = courseuser.get_current_role(course=self.assessment.course)

        ###############################################
        # first, determine thread_content of assessment
        ###############################################

        # thread_content will be None
        # if assessment is not in thread and number in thread is 1
        try:
            self.thread_content=self.assessment.determine_thread_content(
                self.number_in_thread)
        except ObjectDoesNotExist:
            raise Http404("No assessment found") 

        
        ########################################################
        # generic behavior if not in course or no thread content
        ########################################################

        
        if not (self.course_enrollment and self.thread_content):
            if self.assessment.single_version:
                self.assessment_seed='1'
                self.version = ''
            else:
                if seed is None:
                    self.assessment_seed='1'
                else:
                    self.assessment_seed=seed
                self.version = str(self.assessment_seed)[-4:]


            self.question_list = get_question_list(self.assessment, 
                                                   seed=self.assessment_seed)

            return


        #########################################
        # instructor behavior with content attempt or seed specified
        #########################################

        if current_role == INSTRUCTOR_ROLE or current_role == DESIGNER_ROLE:

            content_attempt=None
            if content_attempt_id is not None:
                from micourses.models import ContentAttempt
                try:
                    content_attempt = ContentAttempt.objects.get(
                        id=content_attempt_id)
                except ObjectDoesNotExist:
                    pass
                else:
                    if content_attempt.record.content != self.thread_content:
                        content_attempt=None
                if content_attempt is None:
                    raise ValueError("Content attempt %s does not exist for %s." % \
                        (content_attempt_id, self.thread_content.get_title()))

            # if found valid content attempt, 
            # attempt to find valid question attempts
            if content_attempt:
                question_attempts = []

                if question_attempt_ids:
                    question_attempt_id_list = question_attempt_ids.split(",")

                    from micourses.models import QuestionAttempt

                    for qa_id in question_attempt_id_list:
                        try:
                            qa=QuestionAttempt.objects.get(id=qa_id.strip())
                        except QuestionAttempt.DoesNotExist:
                            question_attempts=[]
                            break
                        else:
                            question_attempts.append(qa)

                from micourses.render_assessments import get_question_list_from_attempt

                self.question_list = get_question_list_from_attempt(
                    assessment=self.assessment, content_attempt=content_attempt,
                    question_attempts=question_attempts)
                            
                if self.question_list:
                    self.current_attempt=content_attempt

                    # set assessment seed and version string
                    self.assessment_seed = self.current_attempt.seed
                    self.version = self.current_attempt.version

                    return
                else:
                    raise ValueError("Invalid content attempt %s for %s.<br/>Question attempts don't match." % \
                        (content_attempt_id, self.thread_content.get_title()))


            # if don't have valid question list, then generate from seed, if set
            if seed is not None:
                self.assessment_seed = seed
                self.question_list = get_question_list(
                    self.assessment, seed=self.assessment_seed,
                    thread_content=self.thread_content)
                self.version=str(seed)

                return


        #########################################
        # enrolled student behavior
        # (also instructor with no seed or content attempt)
        #########################################

        try:
            student_record = self.thread_content.contentrecord_set\
                                    .get(enrollment = self.course_enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                student_record = self.thread_content.contentrecord_set\
                                    .create(enrollment = self.course_enrollment)

        assessment_availability = self.thread_content.return_availability(
            student=courseuser)

        try:
            latest_attempt = student_record.attempts.latest()
        except ObjectDoesNotExist:
            latest_attempt = None
        else:
            # will use the latest attempt in the following cases
            # 1. assessment is not yet available and attempt is not valid
            # 2. assessment is available and the attempt is valid
            # 3. assessment is past due (OK for valid or invalid attempt)

            # This means that invalid past due responses will be added
            # to a valid attempt.
            # However, to prevent free practice on an attempt before it
            # becomes available,
            # if an assessment is changed
            # to become not yet available after an valid attempt has begun,
            # then create a new, invalid, attempt.
            # This algorithm will make the original valid
            # attempt no longer available, even when the assessment
            # becomes available again.
            # (This situation is not foolproof, as one could get this
            # free practice if the assessment was not reloaded.)
        
            if assessment_availability==NOT_YET_AVAILABLE:
                if latest_attempt.valid:
                    latest_attempt=False
            elif assessment_availability==AVAILABLE:
                if not latest_attempt.valid:
                    latest_attempt=False

        self.current_attempt=None
        if latest_attempt:
            # Verify latest attempt has the right number of
            # of question sets with question attempts
            # If so, set as current attempt and populate
            # question list from that attempt
            
            from micourses.render_assessments import get_question_list_from_attempt
            self.question_list = get_question_list_from_attempt(
                assessment=self.assessment, 
                content_attempt=latest_attempt)

            # if found question_list, use latest attempt as current attempt
            if self.question_list:
                self.current_attempt = latest_attempt
                
                # set assessment seed and version string
                self.assessment_seed = latest_attempt.seed
                self.version = latest_attempt.version

                return
                
        # If didn't find a current attempt to use, generate new attempt
        if not self.current_attempt:

            from micourses.utils import create_new_assessment_attempt
            new_attempt_info = create_new_assessment_attempt(
                assessment=self.assessment, thread_content=self.thread_content,
                courseuser = courseuser,
                student_record = student_record)

            self.current_attempt = new_attempt_info['new_attempt']
            self.question_list = new_attempt_info['question_list']
            self.assessment_seed = new_attempt_info['assessment_seed']
            self.version = new_attempt_info['version']



class AssessmentOverview(DetailView):
    model = Assessment
    slug_url_kwarg = 'assessment_code'
    slug_field = 'code'
    template_name='micourses/assessments/assessment_overview.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.model.objects.filter(
            course__code=self.kwargs["course_code"]))
        self.assessment = self.object
        self.user = request.user
        try:
            self.number_in_thread=int(request.GET.get('n',1))
        except TypeError:
            self.number_in_thread=1
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)



    def get_context_data(self, **kwargs):
        context = super(AssessmentOverview, self).get_context_data(**kwargs)

        # thread_content will be None
        # if assessment is not in thread and number in thread is 1
        try:
            thread_content = self.assessment.determine_thread_content(
                self.number_in_thread)
        except ObjectDoesNotExist:
            raise Http404("No assessment found") 
            
        context['thread_content']=thread_content
        context['number_in_thread'] = self.number_in_thread
            
        if thread_content:
            context['assessment_name'] = thread_content.get_title()
        else:
            context['assessment_name'] = self.assessment.name

        # user has permission to view the assessment, given privacy level
        if self.assessment.user_can_view(self.user, solution=False):
            if self.number_in_thread > 1:
                get_string = "n=%s" % self.number_in_thread
            else:
                get_string=""

            if thread_content.substitute_title:
                context['assessment_link'] = self.assessment.return_direct_link(
                    link_text=thread_content.substitute_title,
                    get_string=get_string)
            else:
                context['assessment_link'] = self.assessment.return_direct_link(
                    get_string=get_string)
        else:
            context['assessment_link'] = None

        # generate assessment link if can administer and thread content exists
        if thread_content and user_can_administer_assessment(
                self.user, course=self.object.course):
            context['generate_course_attempt_link'] = True
        else:
            context['generate_course_attempt_link'] = False


        # turn off google analytics for localhost
        if settings.SITE_ID==2 or settings.SITE_ID==3:
            context['noanalytics']=True
        else:
            context['noanalytics']=False
            
        return context
    


class GenerateNewAttempt(SingleObjectMixin, View):
    """
    Generate new assessment attempt then redirect to assessement view.
    Must be a post.


    """

    model = ThreadContent
    pk_url_kwarg = 'content_id'

    def post(self, request, *args, **kwargs):
        """
        Through post can generate new attempt.
        """

        thread_content = self.get_object()

        # if content object isn't an assessment, then return 404
        assessment_content_type = ContentType.objects.get(app_label="micourses",
                                                          model='assessment')
        if thread_content.content_type != assessment_content_type:
            raise Http404("No assessment found") 
                        
        assessment=thread_content.content_object
        course=thread_content.course

        if thread_content.n_of_object != 1:
            get_string = "?n=%s" % thread_content.n_of_object
        else:
            get_string = ""

        # determine if user is enrolled in class
        try:
            enrollment = course.courseenrollment_set.get(
                student=request.user.courseuser)
        except (ObjectDoesNotExist, AttributeError):
            # if not in course, just redirect to the assessment url
            return HttpResponseRedirect(reverse('miassess:assessment',
                            kwargs={'course_code': course.code,
                                    'assessment_code': assessment.code })\
                                        + get_string)

        # get or create content record for user
        try:
            student_record = thread_content.contentrecord_set.get(
                enrollment=enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                student_record = thread_content.contentrecord_set.create(
                    enrollment=enrollment)


        attempts = student_record.attempts.all()

        from micourses.utils import create_new_assessment_attempt
        create_new_assessment_attempt(
            assessment=assessment, thread_content=thread_content,
            courseuser = request.user.courseuser,
            student_record = student_record)

        # redirect to assessment url
        return HttpResponseRedirect(reverse('miassess:assessment', 
                    kwargs={'course_code': course.code,
                            'assessment_code': assessment.code })\
                                    + get_string)




class GenerateCourseAttempt(SingleObjectMixin, FormView):
    model = ThreadContent
    pk_url_kwarg = 'content_id'
    template_name = "micourses/assessments/generate_course_attempt.html"
    form_class=GenerateCourseAttemptForm


    def get_object_thread_content(self):

        self.object = self.get_object()
        self.thread_content = self.object

        # if content object isn't an assessment, then return 404
        assessment_content_type = ContentType.objects.get(app_label="micourses",
                                                          model='assessment')
        if self.thread_content.content_type != assessment_content_type:
            raise Http404("No assessment found") 
        
        self.assessment=self.thread_content.content_object
        self.course=self.thread_content.course




    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        self.get_object_thread_content()
        try:
            self.number_in_thread=int(request.GET.get('n',1))
        except TypeError:
            self.number_in_thread=1

        # determine if user has instructor or designer access
        if not user_can_administer_assessment(request.user, course=self.course):
            return redirect("mi-forbidden")

        self.coursewide_attempts_selected = []

        form = self.get_form()

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        self.get_object_thread_content()
        try:
            self.number_in_thread=int(request.GET.get('n',1))
        except TypeError:
            self.number_in_thread=1

        # determine if user has instructor or designer access
        if not user_can_administer_assessment(request.user, course=self.course):
            return redirect("mi-forbidden")

        form = self.get_form()

        self.coursewide_attempts_selected = request.POST.getlist("cca_ids")

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        avoid_list= form.cleaned_data['avoid_list']
        seed = form.cleaned_data['seed']
        version = form.cleaned_data['version_description']

        if seed == "":
            seed = str(timezone.now())

        assessment_datetime = form.cleaned_data['assessment_datetime']

        current_tz = timezone.get_current_timezone()
        assessment_datetime = current_tz.normalize(
            assessment_datetime.astimezone(current_tz))
        assessment_date = assessment_datetime.date()

        
        avoid_dict={}
        if avoid_list:
            for item in avoid_list.split(","):
                ind = int(item)
                avoid_dict[ind] = avoid_dict.get(ind,0)+1

        from micourses.models import ContentAttempt
                
        for cca_id in self.coursewide_attempts_selected:
            try:
                cca = ContentAttempt.objects.get(id=cca_id)
            except ContentAttempt.DoesNotExist:
                continue

            if cca.record.content != self.thread_content:
                continue

            for qs in cca.question_sets.all():
                try:
                    qa = qs.question_attempts.latest()
                except ObjectDoesNotExist:
                    continue
                ind = qa.question.id
                avoid_dict[ind] = avoid_dict.get(ind,0)+1


        if avoid_dict:
            new_seed = self.assessment.avoid_question_seed(avoid_dict, start_seed=seed)
        else:
            from mitesting.utils import get_new_seed
            new_seed=get_new_seed(seed=seed)


        if not version:
            version = new_seed[-3:]

        try:
            course_record = self.thread_content.contentrecord_set\
                                    .get(enrollment = None)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                course_record = self.thread_content.contentrecord_set\
                                    .create(enrollment = None)

        # create new course attempt
        with transaction.atomic(), reversion.create_revision():
            course_attempt = course_record.attempts\
                                    .create(seed=new_seed, valid=True,
                                            attempt_began = assessment_datetime,
                                            version=version)

            from micourses.render_assessments import get_question_list
            question_list = get_question_list(
                self.assessment, seed=new_seed,
                thread_content=self.thread_content)

            # create the content question sets and question attempts
            with transaction.atomic(), reversion.create_revision():
                for (i,q_dict) in enumerate(question_list):
                    ca_question_set = course_attempt.question_sets.create(
                        question_number=i+1, question_set=q_dict['question_set'])
                    qa=ca_question_set.question_attempts.create(
                        question=q_dict['question'],
                        seed=q_dict['seed'])
                    q_dict['question_attempt'] = qa
        

        new_url = "%s?content_attempt=%s&date=%s" % \
                  (reverse('miassess:assessment', 
                           kwargs={'course_code': self.course.code,
                                   'assessment_code': self.assessment.code}),
                   course_attempt.id, assessment_datetime)


        return HttpResponseRedirect(new_url)


    def get_context_data(self, **kwargs):
        context = super(GenerateCourseAttempt, self).get_context_data(**kwargs)

        context['the_assessment_name'] = self.thread_content.get_title()
        
        context['assessment'] = self.thread_content.content_object

        try:
            coursewide_record = self.thread_content.contentrecord_set.get(enrollment=None)
        except ObjectDoesNotExist:
            coursewide_record = None


        cca_dicts = []
        if coursewide_record:
            for cca in coursewide_record.attempts.filter(valid=True):
                selected = str(cca.id) in self.coursewide_attempts_selected
                question_numbers=[]
                for qs in cca.question_sets.all():
                    try:
                        qa = qs.question_attempts.latest()
                    except ObjectDoesNotExist:
                        continue
                    question_numbers.append(str(qa.question.id))
                question_numbers = ", ".join(question_numbers)
                cca_dicts.append({'cca': cca, 'selected': selected,
                                  'question_numbers': question_numbers})
        context['course_content_attempts'] = cca_dicts


        context['now'] = timezone.now()

        return context

