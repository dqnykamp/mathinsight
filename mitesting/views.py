from mitesting.models import Question, Assessment, QuestionAnswerOption
from midocs.models import Applet
from micourses.models import QuestionResponse
from django.db import IntegrityError
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponse
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from mitesting.permissions import return_user_assessment_permission_level, user_has_given_assessment_permission_level_decorator, user_has_given_assessment_permission_level, user_can_administer_assessment
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin
from django.template import TemplateSyntaxError
import json 

import logging

logger = logging.getLogger(__name__)


class QuestionView(DetailView):
    """
    View question or question solution by itself on a page

    Checks if logged in user has level 2 permissions.
    If not, redirects to login page.
    If not solution, then shows help and solution buttons, if available.

    Random number seed can be given as a GET parameter;
    otherwise, seed is randomly chosen and stored so can reproduce.

    Add the following to the context:
    - question_data: dictionary returned by render_assessments.render_question.
      This dictionary contains the information about the question that is
      used by the template mitesting/question_body.html
    - show_lists: True, since should show lists of assessments
    - noanalytics: True to indicate shouldn't link to Google analytics


    """

    model = Question
    pk_url_kwarg = 'question_id'
    solution=False

    def render_to_response(self, context, **response_kwargs):
        if self.solution:
            self.template_name = 'mitesting/question_solution.html'

        # determine if user has full permissions on assessments
        # (i.e., permission level 2),
        if not user_has_given_assessment_permission_level(
            self.request.user, 2):
            path = self.request.build_absolute_uri()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path)
        else:
            return super(QuestionView, self)\
                .render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        
        try:
            seed = self.request.GET['seed']
        except:
            seed = None

        # show help if no rendering solution
        show_help = not self.solution
        
        # In question view, there will be only one question on page.
        # Identifier doesn't matter.  Use qv to indiciate from question view.
        identifier = "qv"

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()

        import random
        rng = random.Random()

        context['question_data']= self.object.render(
            rng=rng, seed=seed, user=self.request.user,
            question_identifier=identifier, 
            allow_solution_buttons=True,
            solution=self.solution,
            show_help = show_help,
            auxiliary_data=auxiliary_data,
            show_post_user_errors=True)

        context['_auxiliary_data_'] = auxiliary_data

        context['show_lists']=True

        # no Google analytics for questions
        context['noanalytics']=True

        return context





class GradeQuestionView(SingleObjectMixin, View):
    """
    Grade user responses for computer graded questions.
    Record answer for logged in users, if record_answers for computer_grade_data
    is set.

    Expects the following POST data:
    - cgd: a picked and base64 encoded dictionary of computer_grade_data,
      which is a dictionary containing information about the equation needed
      for computer grading.
      computer_grade_data should contain the following
      - seed: the seed use to used to generate the question
      - identifier: the identifier for the question
      - allow_solution_buttons: if set to true, show a solution  button if
        other criteria are met
      - record_answers: if set to true, record logged in user answers
      - course_code: code of course of assessment
      - assessment_code: code of assessment in which the question was rendered
      - question_set: question_set of this assessment in which question appeared
      - assessment_seed: seed used to generate the assessment
      - answer_info: list of identifiers, codes, points, answer types,
        and groups of answers in question
      - applet_counter: number of applets encountered so far 
        (not sure if need this)
    - number_attempts_[identifier]: the number of previous attempts answering
      the question
    - answer_[answer_identifier]: the response user entered for the answer
       
    Returns a json objects with the following properties
    - identifier: the identifier for the questions
    - correct: true if all answer blanks were answer correctly
    - feedback: message detailing the correctness of the answers
    - answer_correct: an object keyed by answer identifiers,
      where each property is true if the corresponding answer was correct
    - answer_feedback: an object keyed by answer identifiers,
      where each property gives a message about the correctness of the answer
    - number_attempts: the number of attempts answering the question, 
      including the current attempt
    - enable_solution_button: true if should enable the button to reveal
      the solution
    - attempt_credit: fraction question is correct on this attempt

    If record_answers is set to true and user is logged in, then record
    users answers, associating answer with a course if associated with a course
    that is set up for recording answers and assessment not past due

    """
    model = Question
    pk_url_kwarg = 'question_id'

    def post(self, request, *args, **kwargs):

        # Look up the question to grade
        question = self.get_object()
        
        pairs = [s2 for s1 in request.body.split(b'&') for s2 in s1.split(b';')]
        cgd = None
        for name_value in pairs:
            if not name_value:
                continue
            nv = name_value.split(b'=', 1)
            if len(nv) != 2:
                continue
            
            if nv[0]==b'cgd':
                cgd = nv[1]
                break

        import pickle, base64
        computer_grade_data = pickle.loads(
            base64.b64decode(cgd))

        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data['seed']
        
        response_data = request.POST

        answer_info = computer_grade_data['answer_info']
        
        answer_user_responses = []
        for answer_num in range(len(answer_info)):
            answer_identifier = answer_info[answer_num]['identifier']
            answer_user_responses.append({
                'identifier': answer_identifier,
                'code': answer_info[answer_num]['code'],
                'answer': 
                response_data.get('answer_%s' % answer_identifier, "")})
        
        from .grade_question import grade_question
        answer_results=grade_question(question=question,
                question_identifier=question_identifier,
                answer_info=answer_info, 
                answer_user_responses=answer_user_responses, seed=seed)
            
        # determine if question is part of an assessment
        course_code = computer_grade_data.get('course_code')
        assessment_code = computer_grade_data.get('assessment_code')
        assessment_seed = computer_grade_data.get('assessment_seed')
        question_set = computer_grade_data.get('question_set')

        if assessment_code and course_code:
            try:
                assessment = Assessment.objects.get(course__code=course_code,
                                                    code=assessment_code)
            except ObjectDoesNotExist:
                assessment_code = None

        if not assessment_code:
            assessment = None
            question_set = None
            assessment_seed = None


        # increment number of attempts
        try:
            number_attempts = int(response_data['number_attempts_%s' % 
                                                question_identifier])
        except (KeyError, ValueError):
            number_attempts=0

        number_attempts+=1
        answer_results['number_attempts'] = number_attempts
        
        show_solution_button = computer_grade_data.get(
            'show_solution_button', False)

        enable_solution_button = False
        if show_solution_button and \
                question.show_solution_button_after_attempts and \
                number_attempts >= question.show_solution_button_after_attempts:
            enable_solution_button = True

        answer_results['enable_solution_button'] = enable_solution_button
                
        
        # untested with courses
        
        record_answers = computer_grade_data['record_answers'] 

        # if not recording the result of the question,
        # we're finished, so return response with the results
        if not (record_answers and request.user.is_authenticated()):
            return HttpResponse(json.dumps(answer_results),
                                content_type = 'application/json')

        try:
            student = request.user.courseuser
            course = student.return_selected_course()
        except:
            student = None
            course = None

        # check if assessment given by assessment_code is in course
        # if so, will link to latest attempt
        current_attempt = None
        past_due = False
        due_date = None
        solution_viewed = False

        if course and assessment_code:
                        
            assessment_content_type = ContentType.objects.get\
                (model='assessment')

            try:
                content=course.thread_contents.get\
                    (object_id=assessment.id,\
                     content_type=assessment_content_type)

                if not content.record_scores:
                    record_answers = False

            except ObjectDoesNotExist:
                content=None
                record_answers = False

            if record_answers:
                due_date = content.adjusted_due_date(student)
                today = datetime.date.today()
                if due_date and today > due_date:
                    past_due = True
                    record_answers = False

            # if content, get or create attempt by student
            # with same assessment_seed
            # if not record scores, mark attempt as invalid
            if content:
                try:
                    current_attempt = content.studentcontentattempt_set\
                        .filter(student=student, seed=assessment_seed,
                                invalid=not record_answers).latest()
                except ObjectDoesNotExist:
                    current_attempt = content.studentcontentattempt_set\
                        .create(student=student, seed=assessment_seed,
                                invalid=not record_answers)


                # check if student already viewed the solution
                # if so, mark as to not record scores 
                # and get/create invalid attempt
                if current_attempt.studentcontentattemptsolutionview_set\
                        .filter(question_set=question_set).exists():
                    solution_viewed = True
                    record_answers = False

                    try:
                        current_attempt = content.studentcontentattempt_set\
                            .filter(student=student, seed=assessment_seed,
                                    invalid=not record_answers).latest()
                    except ObjectDoesNotExist:
                        current_attempt = content.studentcontentattempt_set\
                            .create(student=student, seed=assessment_seed,
                                    invalid=not record_answers)



        # If have current_attempt, then record answers even if 
        # record_answers is False.
        # Since attempt will be marked as invalid,
        # it won't count toward score and won't be viewable by student
        if current_attempt:
            QuestionResponse.objects.create\
                (user=request.user, question=question, \
                 question_set=question_set,\
                 answer=json.dumps(answer_user_responses),\
                 identifier_in_answer = question_identifier, \
                 seed=seed, credit=answer_results['credit'],\
                 course_content_attempt=current_attempt)

        if past_due:
            feedback_message = "Due date %s of %s is past.<br/>Answer not recorded." % (due_date, assessment)
        elif solution_viewed:
            feedback_message = "Solution for question already viewed for this attempt.<br/>Answer not recorded. <br/>Generate a new attempt to resume recording answers." 
        elif not record_answers:
            feedback_message = "Assessment not set up for recording answers"
        else:
            feedback_message = ""

        if current_attempt and not current_attempt.invalid:
            feedback_message += "Answer recorded for %s<br/>Course: <a href=\"%s\">%s</a>" % (request.user,reverse('micourses:assessmentattempted', kwargs={'pk': content.id} ), course)

            current_credit =current_attempt\
                .get_percent_credit_question_set(question_set)
            answer_results['current_credit']=current_credit


        answer_results['feedback'] += "<p>%s</p>" % feedback_message
        

        data = json.dumps(answer_results)

        return HttpResponse(json.dumps(answer_results),
                            content_type = 'application/json')


class InjectQuestionSolutionView(SingleObjectMixin, View):
    """
    Returns rendered solution of question as json object.
    Record that logged in users have viewed the solution

    Expects the following POST data:
    - cgd: a picked and base64 encoded dictionary of computer_grade_data,
      which is a dictionary containing information about the equation needed
      for computer grading.
      computer_grade_data should contain the following
      - seed: the seed use to used to generate the question
      - identifier: the identifier for the question
      - course_code: code of course of assessment
      - assessment_code: code of assessment in which the question was rendered
      - question_set: question_set of this assessment in which question appeared
      - assessment_seed: seed used to generate the assessment
      - applet_counter: number of applets encountered so far 
        (not sure if need this)

    Returns a json objects with the following properties
    - identifier: the identifier for the questions
    - rendered_solution: the solution rendered via the template
      mitesting/question_solution_body.html
    

    """
    model = Question
    pk_url_kwarg = 'question_id'

    def post(self, request, *args, **kwargs):
        # Look up the question to grade
        question = self.get_object()
        

        pairs = [s2 for s1 in request.body.split(b'&') for s2 in s1.split(b';')]
        cgd = None
        for name_value in pairs:
            if not name_value:
                continue
            nv = name_value.split(b'=', 1)
            if len(nv) != 2:
                continue
            
            if nv[0]==b'cgd':
                cgd = nv[1]
                break

        import pickle, base64, binascii
        try:
            computer_grade_data = pickle.loads(
                base64.b64decode(cgd))
        except (TypeError, IndexError, EOFError, binascii.Error) as exc:
            logger.error("cgd malformed: %s" % exc)
            return HttpResponse("", content_type = 'application/json')

        course_code = computer_grade_data.get('course_code')
        assessment_code = computer_grade_data.get('assessment_code')
        assessment = None
        
        if assessment_code and course_code:
            try:
                assessment = Assessment.objects.get(course__code=course_code,
                                                    code=assessment_code)
            except ObjectDoesNotExist:
                assessment_code = None

        # if user cannot view question solution,
        # or if user cannot view assessment solution (in case question is
        # part of an assessment)
        # then return empty json object
        if not question.user_can_view(request.user, solution=True):
            return HttpResponse("", content_type = 'application/json')
        if assessment:
            if not assessment.user_can_view(request.user, solution=True,
                                            include_questions=False):
                return HttpResponse("", content_type = 'application/json')

        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data['seed']

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()
        auxiliary_data['applet']['suffix'] = "%s_sol" % question_identifier

        import random
        rng=random.Random()

        from mitesting.render_assessments import render_question
        question_data= render_question(
            question=question,
            rng=rng, seed=seed, user=request.user,
            question_identifier="%s_sol" % question_identifier, 
            auxiliary_data = auxiliary_data,
            solution=True,
            show_help = False)

        from django.template.loader import get_template
        question_solution_template = get_template(
            "mitesting/question_solution_body.html")
        rendered_solution = question_solution_template.render(
                {'question_data': question_data})

        rendered_solution = mark_safe("<h4>Solution</h4>" + rendered_solution)
        results = {'rendered_solution': rendered_solution,
                   'identifier': question_identifier,
                   'applet_javascript': auxiliary_data['applet']['javascript'],
                   }


        # if don't have logged in user, then just return results
        if not request.user.is_authenticated():
            return HttpResponse(json.dumps(results),
                                content_type = 'application/json')
            
        # otherwise, first record that user viewed solution

        # this code is untested

        try:
            student = request.user.courseuser
            course = student.return_selected_course()
        except:
            course = None

        # check if assessment given by assessment_code is in course
        # if so, will link to latest attempt
        if course and assessment_code:

            assessment_seed = computer_grade_data.get('assessment_seed')
            question_set = computer_grade_data.get('question_set')

            assessment_content_type = ContentType.objects.get\
                (model='assessment')

            try:
                content=course.thread_contents.get\
                    (object_id=assessment.id,\
                     content_type=assessment_content_type)
            except ObjectDoesNotExist:
                content=None

            # if found course content, get or create attempt by student
            # with same assessment_seed
            if content:
                try:
                    current_attempt = content.studentcontentattempt_set\
                        .filter(student=student, seed=assessment_seed)\
                        .latest()
                except ObjectDoesNotExist:
                    current_attempt = content.studentcontentattempt_set\
                        .create(student=student, seed=assessment_seed)

                # record fact that viewed solution
                # for this content attempt
                # and this question set
                current_attempt.studentcontentattemptsolutionview_set\
                    .create(question_set=question_set)


        return HttpResponse(json.dumps(results),
                            content_type = 'application/json')



class AssessmentView(DetailView):
    """
    View assessment or assessment solution

    Accepts either get or post, with seed given as a parameter.
    Checks if logged in user has required permissions. 
    For solution, checks if logged in user with level 2 permissions.
    If user doesn't have required permissions, redirects to login page.
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

    def render_to_response(self, context, **response_kwargs):

        # determine if user has permission to view assessment or solution
        has_permission=False

        if user_has_given_assessment_permission_level(self.request.user, 2):
            has_permission=True
        elif not self.solution and self.object.user_can_view(
            self.request.user, solution=False):
            has_permission=True
            
        if not has_permission:
            path = self.request.build_absolute_uri()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path)
        else:
            return super(AssessmentView, self)\
                .render_to_response(context, **response_kwargs)


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
            template_names.append("mitesting/%s%s.html" % 
                                  (template_base_name, solution_postfix))
        template_names.append("mitesting/assessment%s.html" % solution_postfix)

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

        from .render_assessments import render_question_list, get_new_seed
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
        
        context['generate_assessment_link'] = False
        context['show_solution_link'] = False
        
        if user_can_administer_assessment(self.request.user):
            context['generate_assessment_link'] = True

        if context['generate_assessment_link']:
            if not self.solution:
                context['show_solution_link'] = True


        context['assessment_name'] = self.assessment.name
        if self.solution:
            context['assessment_name'] += " solution"
        context['assessment_short_name'] = self.assessment.return_short_name()
        if self.solution:
            context['assessment_short_name'] += " sol."

        if self.version_string:
            context['version_string'] = ', version %s' % self.version_string
        else:
            context['version_string'] = ''

        context['course'] = self.assessment.course
        context['thread_content'] = self.thread_content
        context['attempt_number'] = self.attempt_number

        # add attempt url to rendered_list question_data
        if self.thread_content:
            for (ind,q) in enumerate(rendered_list):
                q["question_data"]["attempt_url"] = reverse('micourses:assessmentattemptquestion', kwargs={'pk': self.thread_content.id, 'attempt_number': self.attempt_number, 'question_number': ind+1} )

        # get list of the question numbers in assessment
        # if question_numbers specified in GET parameters
        if kwargs["include_question_numbers"]:
            question_numbers=[]
            for q in rendered_list:
                question_numbers.append(str(q['question'].id))
            question_numbers = ", ".join(question_numbers)
        else:
            question_numbers=None
        context['question_numbers']=question_numbers

        # turn off Google analytics for localhost/development site
        context['noanalytics']=(settings.SITE_ID > 1)

        context['new_seed']=get_new_seed(rng)

        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.model.objects.filter(
            course__code=self.kwargs["course_code"]))
        self.assessment = self.object

        self.determine_version_attempt(
            user=request.user,seed=request.GET.get('seed'),
            question_seeds=request.GET.get('question_seeds'),
            question_ids=request.GET.get('question_ids'),
            question_sets=request.GET.get('question_sets'),
            number_in_thread=request.GET.get('n',1),
        )

        # other data from GET
        current_tz = timezone.get_current_timezone()
        assessment_date = request.GET.get('date',
                current_tz.normalize(timezone.now().astimezone(current_tz))\
                                          .strftime("%B %d, %Y"))
        question_numbers = "question_numbers" in request.GET
        
        context = self.get_context_data(object=self.object, 
                                assessment_date=assessment_date,
                                include_question_numbers=question_numbers)
        return self.render_to_response(context)


    def determine_version_attempt(self, user, seed, 
                                  question_seeds, question_ids, question_sets,
                                  number_in_thread):

        """
        Determine what version of assessment to generate.
        
        For enrolled students, find or create
        content attempts and question attempts.

        Set the following variables that give information about user
        and the assessment's role in course:
        self.current_enrollment
        self.thread_content
        self.attempt_number

        Set the following variables that specify the version of assessment:
        self.assessment_seed
        self.version_string
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
        If seed is in GET
        - use that to generate assessment (even if single version)
        - If GET also contains list of question ids and question seeds,
          then use those ids and question seeds 
          rather than those from assessment.
          (If number of ids and seeds doesn't match assesment
          or ids are invalid,
          then ignore and generate questions from assessment seed.)
        - do not record any responses 
          (not possible anyway as no matching attempts)
        If seed is not in GET, treat as student of course


        """

        # sets the following variables
        self.course_enrollment=None
        self.thread_content=None
        self.assessment_seed= None
        self.version_string = ''
        self.attempt_number=1
        self.question_list = []

        from mitesting.render_assessments import get_question_list
        from micourses.models import INSTRUCTOR_ROLE, NOT_YET_AVAILABLE, \
            NOT_YET_AVAILABLE


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
        if courseuser:
            try:
                self.course_enrollment = self.assessment.course\
                        .courseenrollment_set.get(student=courseuser)
            except ObjectDoesNotExist:
                pass


        ###############################################
        # first, determine thread_content of assessment
        ###############################################

        # only exception where could have no thread content is
        # if assessment is not in thread and number in thread is 1
        try:
            self.thread_content=self.assessment.thread_content_set.all()\
                            [number_in_thread-1]
        except (IndexError, ValueError, AssertionError):
            if number_in_thread==1 and \
               not self.assessment.thread_content_set.all():
                pass
            else:
                raise Http404("No assessment found") 


        
        ########################################################
        # generic behavior if not in course or no thread content
        ########################################################

        
        if not (self.course_enrollment and self.thread_content):
            if self.assessment.single_version:
                self.assessment_seed='1'
                self.version_string = ''
            else:
                if seed is None:
                    self.assessment_seed='1'
                else:
                    self.assessment_seed=seed
                self.version_string = str(self.assessment_seed)


            self.question_list = get_question_list(self.assessment, 
                                                   seed=self.assessment_seed)

            return


        #########################################
        # instructor behavior with seed specified
        #########################################

        if seed is not None and self.course_enrollment.role == INSTRUCTOR_ROLE:
            
            self.assessment_seed = seed

            # If have list of question seeds, ids, and sets
            # then use those for question list
            if question_seed_list and question_id_list and question_set_list:
                question_seed_list = question_seeds.split(",")
                question_id_list = question_ids.split(",")
                question_set_list = question_sets.split(",")
                
                try:
                    from mitesting.render_assessments import \
                        return_question_list_from_specified_data
                    self.question_list = \
                        return_question_list_from_specified_data(
                            assessment=self.assessment, 
                            question_sets=question_set_list,
                            question_seeds=question_seed_list,
                            question_ids=question_id_list,
                            thread_content=self.thread_content)
                except ValueError:
                    pass
                

            # if don't have valid question list, then generate from seed
            if not self.question_list:
                self.question_list = get_question_list(
                    self.assessment, seed=self.assessment_seed,
                    thread_content=self.thread_content)
            
            return


        #########################################
        # enrolled student behavior
        # (also instructor with no seed)
        #########################################

        try:
            student_record = self.thread_content.studentcontentrecord_set\
                                    .get(enrollment = self.course_enrollment)
        except ObjectDoesNotExist:
            student_record = self.thread_content.studentcontentrecord_set\
                                    .create(enrollment = self.course_enrollment)


        assessment_availability = self.thread_content.return_availability(
            student=courseuser)

        self.attempt_number = student_record.attempts.count()

        try:
            latest_attempt = student_record.attempts.latest()
        except ObjectDoesNotExist:
            latest_attempt = None
        else:
            # ignore latest attempt if doesn't match availability of 
            # assessment
            if assessment_availability==NOT_YET_AVAILABLE:
                if latest_attempt.valid:
                    latest_attempt=False
            elif not latest_attempt.valid:
                latest_attempt=False

        current_attempt=None
        if latest_attempt:
            # Ferify latest attempt has the right number of
            # of question sets with question attempts
            # If so, set as current attempt and population
            # question list from that attempt

            question_sets=self.assessment.question_sets()

            ca_qs_list=[]
            total_weight=0
            for ca_question_set in latest_attempt.question_sets.all()\
                            .prefetch_related('question_attempts'):
                try:
                    qa = ca_question_set.question_attempts.latest()
                except ObjectDoesNotExist:
                    ca_qs_list=[]
                    break

                question_set = ca_question_set.question_set

                # find question set detail, if it exists
                try:
                    question_detail=self.assessment.questionsetdetail_set.get(
                        question_set=question_set)
                except ObjectDoesNotExist:
                    question_detail = None

                if question_detail:
                    weight=question_detail.weight
                    group=question_detail.group
                else:
                    weight=1
                    group=""

                total_weight += weight

                self.question_list.append(
                    {'question_set': ca_question_set.question_set,
                     'question': qa.question,
                     'seed': qa.seed,
                     'question_attempt': qa,
                     'relative_weight': weight,
                     'group': group,
                     'previous_same_group': False
                 })

                ca_qs_list.append(ca_question_set.question_set)

            # if question sets don't match, then
            # ignore attempt and treat as not finding a current attempt
            if sorted(ca_qs_list) != sorted(question_sets):
                self.question_list=[]

            # otherwise, use lastest attempt as current attempt
            # and add remaining data to question list
            else:
                current_attempt = latest_attempt
                
                # set assessment seed and version string
                self.assessment_seed = latest_attempt.seed
                self.version_string = str(self.attempt_number)
                if self.thread_content.individualize_by_student:
                    self.version_string = "%s_%s" % \
                        (courseuser.user.username, self.version_string)


                # make weight be relative weight
                # multiply by assessment points to
                # get question_points
                for q_dict in self.question_list:
                    q_dict['relative_weight'] /= total_weight
                    q_dict['points'] = q_dict["relative_weight"]\
                                       *self.thread_content.points

                # treat just like fixed order
                for i in range(1, len(self.question_list)):
                    the_group = self.question_list[i]["group"]
                    # if group is not blank and the same as previous group
                    # mark as belonging to same group as previous question
                    if the_group and \
                       self.question_list[i-1]["group"] == the_group:
                        self.question_list[i]["previous_same_group"] = True


                

        # If didn't find a current attempt to use, generate new attempt
        if not current_attempt:
            
            self.attempt_number +=1
            self.version_string = str(self.attempt_number)
            if self.thread_content.individualize_by_student:
                self.version_string = "%s_%s" % \
                            (courseuser.user.username, self.version_string)
            self.assessment_seed = "sd%s_%s" % (self.thread_content.id, 
                                                self.version_string)
            valid_attempt=assessment_availability==AVAILABLE

            # create the attempt
            current_attempt = student_record.attempts\
                            .create(seed=self.assessment_seed,
                                    valid=valid_attempt)

            self.question_list = get_question_list(
                self.assessment, seed=self.assessment_seed,
                thread_content=self.thread_content)

            # create the content question sets and question attempts
            for (i,q_dict) in enumerate(question_list):
                ca_question_set = current_attempt.question_sets.create(
                    question_number=i+1, question_set=q_dict['question_set'])
                qa=ca_question_set.question_attempts.create(
                    question=q_dict['question'],
                    seed=q_dict['seed'], valid=valid_attempt)
                q_dict['question_attempt'] = qa



class GenerateNewAssessmentAttemptView(SingleObjectMixin, View):
    """
    Generate new assessment attempt then redirect to assessement view.
    Must be a post.


    """

    model = Assessment
    slug_url_kwarg = 'assessment_code'
    slug_field = 'code'

    def post(self, request, *args, **kwargs):
        """
        Through post can generate new attempt.
        Need to test and fix this.
        """

        self.object = self.get_object(queryset=self.model.objects.filter(
            course__code=self.kwargs["course_code"]))

        # First determine if user is enrolled in an course
        try:
            courseuser = request.user.courseuser
            course = courseuser.return_selected_course()
        except (ObjectDoesNotExist, MultipleObjectsReturned, AttributeError):
            # if not in course, just redirect to the assessment url
            return HttpResponseRedirect(reverse('mitesting:assessment',
                            kwargs={'course_code': self.object.course.code,
                                    'assessment_code': self.object.code }))

        assessment_content_type = ContentType.objects.get(model='assessment')

        try:
            # Find the course version of the specific assessment
            course_thread_content=course.thread_contents.get\
                            (object_id=self.object.id,\
                        content_type=assessment_content_type)
        except ObjectDoesNotExist:
            # if can't find, just redirect to the assessment url
            return HttpResponseRedirect(reverse('mitesting:assessment',
                            kwargs={'course_code': self.object.course.code,
                                    'assessment_code': self.object.code }))


        attempts = course_thread_content.studentcontentattempt_set\
                                        .filter(student=courseuser) 

        attempt_number = attempts.count()+1
        version = str(attempt_number)
        if course_thread_content.individualize_by_student:
            version= "%s_%s" % (courseuser.user.username, 
                                version)
        seed = "%s_%s_%s" % (course.code, self.object.id, 
                             version)

        current_attempt = course_thread_content.studentcontentattempt_set\
                                    .create(student=courseuser, seed=seed)

        # redirect to assessment url
        return HttpResponseRedirect(reverse('mitesting:assessment', 
                    kwargs={'course_code': self.object.course.code,
                            'assessment_code': self.object.code }))



def assessment_avoid_question_view(request, course_code, assessment_code):
    
    assessment = get_object_or_404(Assessment, course__code=course_code,
                                   code=assessment_code)
    
    # determine if user has permission to view, given privacy level
    if not assessment.user_can_view(request.user, solution=True):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)
    
    avoid_list= request.GET.get('avoid_list',"")
    seed = request.GET.get('seed')

    assessment_date = request.GET.get('date')
    if not assessment_date:
        assessment_date = datetime.date.today().strftime("%B %d, %Y")

    course = request.GET.get('course',"")
    semester = request.GET.get('semester',"")


    if avoid_list:
        new_seed = assessment.avoid_question_seed(avoid_list, start_seed=seed)
    else:
        new_seed=seed
    
    new_url = "%s?seed=%s&date=%s&course=%s&semester=%s&question_numbers" % \
              (reverse('mitesting:assessment', 
                       kwargs={'course_code': course_code,
                               'assessment_code': assessment_code}),
               new_seed, assessment_date, course, semester)
    

    return HttpResponseRedirect(new_url)


def assessment_overview_view(request, course_code, assessment_code):
    assessment = get_object_or_404(Assessment, course__code=course_code,
                                   code=assessment_code)

    # make link to assessment if 
    # user has permission to view the assessment, given privacy level
    assessment_link = assessment.user_can_view(request.user, solution=False)

    try:
        courseuser = request.user.courseuser
        course = courseuser.return_selected_course()
    except:
        courseuser = None
        course = None

    course_thread_content=None
    # if in the course
    if course:
        assessment_content_type = ContentType.objects.get\
            (model='assessment')
                        
        try:
            course_thread_content=course.thread_contents.get\
                (object_id=assessment.id,\
                     content_type=assessment_content_type)
        except ObjectDoesNotExist:
            course_thread_content=None
            course = None

    generate_assessment_link = False
    if user_can_administer_assessment(request.user):
        generate_assessment_link = True

    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    return render_to_response \
        ('mitesting/assessment_overview.html', 
         {'assessment': assessment,
          'assessment_link': assessment_link,
          'course': course,
          'course_thread_content': course_thread_content,
          'generate_assessment_link': generate_assessment_link,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))
    
    

@user_has_given_assessment_permission_level_decorator(2)
def assessment_list_view(request):

    assessment_list = Assessment.objects.all()

    view_solution = True
    
    # no Google analytics for assessment list
    noanalytics=True

    return render_to_response \
        ('mitesting/assessment_list.html', 
         {'assessment_list': assessment_list,
          'view_solution': view_solution,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@user_has_given_assessment_permission_level_decorator(2)
def question_list_view(request):
    question_list = Question.objects.all()

    # no Google analytics for question list
    noanalytics=True
    
    return render_to_response \
        ('mitesting/question_list.html', {'question_list': question_list,
                                          'noanalytics': noanalytics,
                                          },
         context_instance=RequestContext(request))


def default_sympy_commands(request):
    from mitesting.models import SympyCommandSet
    default_commands = json.dumps(
        [(cmd.pk, cmd.name) for cmd in SympyCommandSet.objects.filter(default=True)])
        
    return HttpResponse(default_commands, content_type = 'application/json')
