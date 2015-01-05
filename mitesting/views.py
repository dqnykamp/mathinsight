from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.models import Question, Assessment, QuestionAnswerOption
from midocs.models import Applet
from micourses.models import QuestionStudentAnswer
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
import datetime
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

        applet_data = Applet.return_initial_applet_data()

        import random
        rng = random.Random()

        context['question_data']= self.object.render(
            rng=rng, seed=seed, user=self.request.user,
            question_identifier=identifier, 
            allow_solution_buttons=True,
            solution=self.solution,
            show_help = show_help,
            applet_data=applet_data)

        context['applet_data'] = applet_data

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
      - assessment_code: code of any assessment in which the question was rendered
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
        
        response_data = request.POST

        import pickle, base64
        try:
            computer_grade_data = pickle.loads(
                base64.b64decode(response_data.get('cgd')))
        except TypeError, IndexError:
            return HttpResponse("", content_type = 'application/json')

        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data['seed']
        # use local random generator to make sure threadsafe
        import random
        rng=random.Random()
        from .render_assessments import setup_expression_context
        context_results = setup_expression_context(question, rng=rng, seed=seed)

        expr_context = context_results['expression_context']

        function_dict = context_results['user_function_dict']
        global_dict = question.return_sympy_global_dict(user_response=True)
        global_dict.update(function_dict)

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
        answer_results=grade_question(question, question_identifier, answer_info, 
                                      answer_user_responses, expr_context, global_dict)
            
        # determine if question is part of an assessment
        assessment_code = computer_grade_data.get('assessment_code')
        assessment_seed = computer_grade_data.get('assessment_seed')
        question_set = computer_grade_data.get('question_set')

        if assessment_code:
            try:
                assessment = Assessment.objects.get(code=assessment_code)
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
                content=course.coursethreadcontent_set.get\
                    (thread_content__object_id=assessment.id,\
                         thread_content__content_type=assessment_content_type)

                # record answer only if assessment_type 
                # specifies recoding online attempts
                if not assessment.assessment_type.record_online_attempts:
                    record_answers = False

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

            # if record scores, get or create attempt by student
            # with same assessment_seed
            if record_answers:
                try:
                    current_attempt = content.studentcontentattempt_set\
                        .filter(student=student, seed=assessment_seed).latest()
                except ObjectDoesNotExist:
                    current_attempt = content.studentcontentattempt_set\
                        .create(student=student, seed=assessment_seed)


                # check if student already viewed the solution
                # if so, clear attempt so not recorded for course
                if current_attempt.studentcontentattemptsolutionview_set\
                        .filter(question_set=question_set).exists():
                    solution_viewed = True
                    current_attempt = None
                    record_answers = False


        # if have current_attempt, don't record assessment,
        # as it would be redundant information
        if current_attempt:
            assessment=None
            assessment_seed = None

        # record attempt, possibly linking to latest content attempt
        # even if record_answers is False, create QuestionStudentAnswer
        # record (just in case), but don't associate it with course
        QuestionStudentAnswer.objects.create\
            (user=request.user, question=question, \
                 question_set=question_set,\
                 answer=json.dumps(answer_user_responses),\
                 identifier_in_answer = question_identifier, \
                 seed=seed, credit=answer_results['credit'],\
                 course_content_attempt=current_attempt,\
                 assessment=assessment, \
                 assessment_seed=assessment_seed)

        if past_due:
            feedback_message = "Due date %s of %s is past.<br/>Answer not recorded." % (due_date, assessment)
        elif solution_viewed:
            feedback_message = "Solution for question already viewed for this attempt.<br/>Answer not recorded. <br/>Generate a new attempt to resume recording answers." 
        elif not record_answers:
            feedback_message = "Assessment not set up for recording answers"
        else:
            feedback_message = ""

        if current_attempt:
            feedback_message += "Answer recorded for %s<br/>Course: <a href=\"%s\">%s</a>" % (request.user,reverse('mic-assessmentattempted', kwargs={'pk': content.id} ), course)

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
      - assessment_code: code of any assessment in which the question was rendered
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
        
        response_data = request.POST

        import pickle, base64
        try:
            computer_grade_data = pickle.loads(
                base64.b64decode(response_data.get('cgd')))
        except (TypeError, IndexError, EOFError) as exc:
            logger.error("cgd malformed: %s" % exc)
            return HttpResponse("", content_type = 'application/json')

        assessment_code = computer_grade_data.get('assessment_code')
        assessment = None
        
        if assessment_code:
            try:
                assessment = Assessment.objects.get(code=assessment_code)
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

        applet_data = Applet.return_initial_applet_data()
        applet_data['suffix'] = "%s_sol" % question_identifier

        import random
        rng=random.Random()

        from mitesting.render_assessments import render_question
        question_data= render_question(
            question=question,
            rng=rng, seed=seed, user=request.user,
            question_identifier=question_identifier, 
            applet_data = applet_data,
            solution=True,
            show_help = False)

        from django.template.loader import get_template
        question_solution_template = get_template(
            "mitesting/question_solution_body.html")
        rendered_solution = question_solution_template.render(Context(
                {'question_data': question_data}))

        rendered_solution = mark_safe("<h4>Solution</h4>" + rendered_solution)
        results = {'rendered_solution': rendered_solution,
                   'identifier': question_identifier,
                   'applet_javascript': applet_data['javascript'],
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
                content=course.coursethreadcontent_set.get\
                    (thread_content__object_id=assessment.id,\
                         thread_content__content_type=\
                         assessment_content_type)
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

        context['assessment_date'] = self.request.GET.get('date')
        if not context['assessment_date']:
            context['assessment_date']  = \
                datetime.date.today().strftime("%B %d, %Y")

        applet_data = Applet.return_initial_applet_data()
        context['applet_data'] = applet_data

        import random
        rng=random.Random()

        from .render_assessments import render_question_list, get_new_seed
        (rendered_list,self.seed)=render_question_list(
            self.object, rng=rng, seed=self.seed, user=self.request.user, 
            solution=self.solution,
            current_attempt=self.current_attempt,
            applet_data = applet_data)

        # if question_only is set, then view only that question
        if self.kwargs.get('question_only'):
            question_only = int(self.kwargs['question_only'])
            rendered_list=rendered_list[question_only-1:question_only]
            context['question_only'] = question_only
        context['rendered_list'] = rendered_list

        context['seed'] = self.seed

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


        context['assessment_name'] = self.object.name
        if self.solution:
            context['assessment_name'] += " solution"
        context['assessment_short_name'] = self.object.return_short_name()
        if self.solution:
            context['assessment_short_name'] += " sol."

        if self.version:
            context['version_string'] = ', version %s' % self.version
        else:
            context['version_string'] = ''

        context['course'] = self.course
        context['course_thread_content'] = self.course_thread_content
        context['attempt_number'] = self.attempt_number

        # add attempt url to rendered_list question_data
        if self.course_thread_content:
            for (ind,q) in enumerate(rendered_list):
                q["question_data"]["attempt_url"] = reverse('mic-assessmentattemptquestion', kwargs={'pk': self.course_thread_content.id, 'attempt_number': self.attempt_number, 'question_number': ind+1} )

        # get list of the question numbers in assessment
        # if question_numbers specified in GET parameters
        if "question_numbers" in self.request.GET:
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
        self.object = self.get_object()
        seed = request.GET.get('seed')
        self.determine_seed_version(user=request.user,seed=seed)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def determine_seed_version(self, user, seed=None):
        """
        
        Need to fix and test this.

        """

        if seed is None:
            seed_from_get_post=False
        else:
            seed_from_get_post=True

        if self.object.nothing_random:
            seed='1'
            self.version = ''
        else:
            if seed is None:
                seed='1'
            self.version = seed
        
        # First determine if user is enrolled in an course
        try:
            courseuser = user.courseuser
            self.course = courseuser.return_selected_course()
        except (ObjectDoesNotExist, MultipleObjectsReturned, AttributeError):
            courseuser = None
            self.course = None

        self.current_attempt=None
        self.attempt_number=0
        self.course_thread_content=None


        # if enrolled in the course
        if self.course:
            assessment_content_type = ContentType.objects.get\
                (model='assessment')

            try:
                self.course_thread_content=self.course.coursethreadcontent_set.get\
                    (thread_content__object_id=self.object.id,\
                         thread_content__content_type=assessment_content_type)
                # Finds the course version of the specific assessment
            except ObjectDoesNotExist:
                self.course=None

            if self.course_thread_content:
                attempts = self.course_thread_content.studentcontentattempt_set\
                    .filter(student=courseuser) 
                self.attempt_number = attempts.count()
                # attempts = attempts.filter(score=None) # We do not want to modify attempts where the score has been overitten



                # if instructor and seed is set from GET/POST
                # then use that seed and don't link to attempt
                # (i.e., skip this processing)
                if not (courseuser.get_current_role() == 'I' and \
                          seed_from_get_post):

                    # else try to find latest attempt
                    try:
                        self.current_attempt = attempts.latest()
                        seed = self.current_attempt.seed
                        self.version = str(self.attempt_number)
                        if self.course_thread_content.individualize_by_student:
                            self.version= "%s_%s" % (courseuser.user.username,
                                                     self.version)

                    except ObjectDoesNotExist:
                        # for seed use course_code, assessment_id, 
                        # and possibly student

                        # if individualize_by_student, add username
                        self.version = "1"
                        if self.course_thread_content.individualize_by_student:
                            self.version= "%s_%s" % (courseuser.user.username, 
                                                     self.version)
                        seed = "%s_%s_%s" % (self.course.code, self.object.id, 
                                             self.version)

                        # create the attempt
                        self.current_attempt = \
                            self.course_thread_content.studentcontentattempt_set\
                            .create(student=courseuser, seed=seed)

        self.seed=seed


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
        self.object = self.get_object()

        # First determine if user is enrolled in an course
        try:
            courseuser = request.user.courseuser
            course = courseuser.return_selected_course()
        except (ObjectDoesNotExist, MultipleObjectsReturned, AttributeError):
            # if not in course, just redirect to the assessment url
            return HttpResponseRedirect(reverse('mit-assessment',
                            kwargs={'assessment_code': self.object.code }))

        assessment_content_type = ContentType.objects.get(model='assessment')

        try:
            # Find the course version of the specific assessment
            course_thread_content=course.coursethreadcontent_set.get\
                            (thread_content__object_id=self.object.id,\
                        thread_content__content_type=assessment_content_type)
        except ObjectDoesNotExist:
            # if can't find, just redirect to the assessment url
            return HttpResponseRedirect(reverse('mit-assessment',
                            kwargs={'assessment_code': self.object.code }))


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
        return HttpResponseRedirect(reverse('mit-assessment', kwargs={'assessment_code': self.object.code }))



def assessment_avoid_question_view(request, assessment_code):
    
    assessment = get_object_or_404(Assessment, code=assessment_code)
    
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
    
    new_url = "%s?seed=%s&date=%s&course=%s&semester=%s&question_numbers" % (reverse('mit-assessment', kwargs={'assessment_code': assessment_code}), new_seed, assessment_date, course, semester)
    

    return HttpResponseRedirect(new_url)


def assessment_overview_view(request, assessment_code):
    assessment = get_object_or_404(Assessment, code=assessment_code)

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
            course_thread_content=course.coursethreadcontent_set.get\
                (thread_content__object_id=assessment.id,\
                     thread_content__content_type=assessment_content_type)
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
