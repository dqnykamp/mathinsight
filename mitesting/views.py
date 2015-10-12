from mitesting.models import Question
from django.db import transaction
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, JsonResponse
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin
import json 
import reversion

import logging

logger = logging.getLogger(__name__)


class QuestionView(DetailView):
    """
    View question or question solution by itself on a page

    Checks if logged in user has level 3 permissions.
    If not, redirects to forbidden page
    If not solution, then shows help and solution buttons, if available.

    Random number seed can be given as a GET parameter;
    otherwise, seed is randomly chosen and stored so can reproduce.

    Add the following to the context:
    - question_data: dictionary returned by render_questions.render_question.
      This dictionary contains the information about the question that is
      used by the template mitesting/question_body.html
    - show_lists: True, since should show lists of assessments
    - noanalytics: True to indicate shouldn't link to Google analytics


    """

    model = Question
    pk_url_kwarg = 'question_id'
    solution=False



    def get(self, request, *args, **kwargs):
        # determine if user has full permissions on assessments
        # (i.e., permission level 3),
        if not request.user.has_perm('mitesting.administer_question'):
            try:
                from micourses.permissions import user_has_given_assessment_permission_level
                if not user_has_given_assessment_permission_level(
                        request.user, 3):
                    return redirect("mi-forbidden")
            except ImportError:
                return redirect("mi-forbidden")

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_template_names(self):
        if self.solution:
            return ['mitesting/question_solution.html',]
        else:
            return ['mitesting/question_detail.html',]
            

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        
        try:
            seed = self.request.GET['seed']
        except:
            seed = None

        # show help if not rendering solution
        show_help = not self.solution
        
        # In question view, there will be only one question on page.
        # Identifier doesn't matter.  Use qv to indiciate from question view.
        identifier = "qv"

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()

        import random
        rng = random.Random()

        question_dict={'question': self.object,
                       'seed': seed,}
        from mitesting.render_questions import render_question
        context['question_data']= render_question(
            question_dict=question_dict,
            rng=rng,  user=self.request.user,
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
    Record answer for logged in users, if record_response for computer_grade_data
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
      - record_response: if set to true, record logged in user answers
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

    If record_response is set to true and user is logged in, then record
    users answers, associating answer with a course if associated with a course
    that is set up for recording answers and assessment not past due

    """
    model = Question
    pk_url_kwarg = 'question_id'


    # Don't wrap entire request in a single transaction
    # as we are getting transaction deadlocks.
    # Instead, will create transaction when save data
    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(GradeQuestionView, self).dispatch(*args, **kwargs)


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
        
        user_responses = []
        for answer_num in range(len(answer_info)):
            answer_identifier = answer_info[answer_num]['identifier']
            user_responses.append({
                'identifier': answer_identifier,
                'code': answer_info[answer_num]['code'],
                'response': 
                response_data.get('answer_%s' % answer_identifier, "")})

        question_attempt=None
        question_attempt_id = computer_grade_data.get("question_attempt_id")

        if question_attempt_id is not None:
            try:
                from micourses.models import QuestionAttempt
                question_attempt = QuestionAttempt.objects.get(
                    id=question_attempt_id)
            except QuestionAttempt.DoesNotExist:
                pass
        
        from .grade_question import grade_question
        answer_results=grade_question(
            question=question,
            question_identifier=question_identifier,
            question_attempt=question_attempt,
            answer_info=answer_info, 
            user_responses=user_responses, seed=seed)
        
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

        record_response = computer_grade_data['record_response'] 

        # if not recording the result of the question,
        # we're finished, so return response with the results
        if not (record_response and question_attempt):
            return JsonResponse(answer_results)


        content_attempt = question_attempt.content_attempt_question_set\
                         .content_attempt
        content_record=content_attempt.record
        content = content_record.content

        # Verify that logged in user is the student of the content_record.
        # If not, don't record results
        # (Important so instructors viewing student results don't
        # inadvertantly change student's score.)
        if not content_record.enrollment \
               or request.user.courseuser != content_record.enrollment.student:
            return JsonResponse(answer_results)


        # Have question attempt of enrolled student.
        # Possibly situations
        # 1. Content is marked as not recording scores.
        # 2. Content is past due
        # 3. Content is not yet due
        # 4. Solution has been viewed
        # 5. Content is available and solution hasn't been viewed.
        #
        # In cases 1-4, an invalid response will be recorded,
        # and a message will be displayed to indicate the problem.
        # Score totals will not be updated.
        #
        # In case 5, if have an invalid attempt (content or question attempt)
        # then response will still be treated as invalid even though
        # the response itself will be marked as valid.
        # Display a message indicating student should generate a new attempt.
        # Score totals will not be updated
        #
        # In case 5, if have a valid attempt (both content and question attempt)
        # then record valid response and update scores.

        record_valid_response = True

        if not content.record_scores:
            record_valid_response = False

        from micourses.models import AVAILABLE,  NOT_YET_AVAILABLE, PAST_DUE
        
        assessment_availability = content.return_availability(content_record)

        if assessment_availability != AVAILABLE:
            record_valid_response = False

        # check if student already viewed the solution
        # if so, mark as to not record response
        if question_attempt.solution_viewed:
            solution_viewed = True
            record_valid_response = False
        else:
            solution_viewed = False

        # Record response.
        # Invalid responses won't count toward score and 
        # won't be viewable by student
        from micourses.models import QuestionResponse
        from django.db.utils import OperationalError

        # in case get deadlock, try to save answer (and recalculate score)
        # five times
        for trans_i in range(5):
            try:
                with transaction.atomic():
                    QuestionResponse.objects.create(
                        question_attempt=question_attempt,
                        response=json.dumps(user_responses),
                        credit=answer_results['credit'],
                        valid = record_valid_response)
            except OperationalError:
                if trans_i==4:
                    raise
            else:
                break

        # if did not have a valid attempt, treat as though 
        # response were marked as invalid, since it won't count.
        if not (content_attempt.valid and question_attempt.valid):
            record_valid_response = False

        answer_results['record_valid_response'] = record_valid_response

        if not content.record_scores:
            feedback_message = "Assessment not set up for recording answers.<br/>Answer not recorded."
        elif assessment_availability == PAST_DUE:
            current_tz = timezone.get_current_timezone()
            due = content.get_adjusted_due(content_record)
            due = current_tz.normalize(due.astimezone(current_tz))

            from micourses.utils import format_datetime
            feedback_message = "Due date %s of %s is past.<br/>Answer not recorded." % (format_datetime(due), content.get_title())

        elif assessment_availability == NOT_YET_AVAILABLE:
            feedback_message = "Assessment is not yet available. <br/>Answer not recorded."
        elif solution_viewed:
            feedback_message = "Solution for question already viewed for this attempt.<br/>Answer not recorded. <br/>Generate a new attempt to resume recording answers." 
        elif not (content_attempt.valid and question_attempt.valid):
            feedback_message = "The current assessment attempt is not valid.<br/>It might have been started before the assessment was available.<br/>Answer not recorded.<br/>Generate a new attempt or reload page to start recording answers."
        else:
            feedback_message = ""

        if record_valid_response:
            feedback_message += "Answer recorded for %s.<br/>Course: <a href=\"%s\">%s</a>" % (request.user,reverse('micourses:content_record', kwargs={'content_id': content.id, 'course_code': content.course.code} ), content.course)

        answer_results['feedback'] += "<p>%s</p>" % feedback_message


        # if didn't record valid response, don't update scores,
        # so return without setting values
        if not record_valid_response:
            return JsonResponse(answer_results)
            

        from mitesting.utils import round_and_int
        question_attempt.refresh_from_db()
        if question_attempt.credit is None:
            answer_results['current_percent_credit']=0
        else:
            answer_results['current_percent_credit']=round_and_int(
                question_attempt.credit*100,1)

        content_attempt.refresh_from_db()
        if content_attempt.score is None:
            answer_results['attempt_score']=0
        else:
            answer_results['attempt_score']=round_and_int(
                content_attempt.score,1)
        
        content_record.refresh_from_db()
        if content_record.score is None:
            answer_results['content_score']=0
        else:
            answer_results['content_score']=round_and_int(
                content_record.score,1)

        return JsonResponse(answer_results)


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
            return JsonResponse({})

        course_code = computer_grade_data.get('course_code')
        assessment_code = computer_grade_data.get('assessment_code')
        
        assessment = None
        course=None

        if assessment_code and course_code:
            try:
                from micourses.models import Assessment
                assessment = Assessment.objects.get(course__code=course_code,
                                                    code=assessment_code)
                course=assessment.course
            except ObjectDoesNotExist:
                assessment_code = None

        # if user cannot view question solution,
        # or if user cannot view assessment solution (in case question is
        # part of an assessment)
        # then return empty json object
        if not question.user_can_view(request.user, solution=True, 
                                      course=course):
            return JsonResponse({})
        if assessment:
            if not assessment.user_can_view(request.user, solution=True,
                                            include_questions=False):
                return JsonResponse({})


        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data['seed']

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()
        auxiliary_data['applet']['suffix'] = "%s_sol" % question_identifier

        question_attempt=None
        question_attempt_id = computer_grade_data.get("question_attempt_id")
        if question_attempt_id is not None:
            try:
                from micourses.models import QuestionAttempt
                question_attempt = QuestionAttempt.objects.get(
                    id=question_attempt_id)
            except QuestionAttempt.DoesNotExist:
                pass

        import random
        rng=random.Random()

        question_dict={
            'question': question,
            'seed': seed,
            'question_attempt': question_attempt,
         }

        from mitesting.render_questions import render_question
        question_data= render_question(
            question_dict=question_dict,
            rng=rng, user=request.user,
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


        
        # if not from a question attempt, then just return solution
        # and don't record fact
        if not question_attempt:
            return JsonResponse(results)

        
        ce = course.courseenrollment_set.get(student=request.user.courseuser)

        own_attempt = True
        if ce != question_attempt.content_attempt_question_set\
                                 .content_attempt.record.enrollment:
            own_attempt = False
        
        # if not an instructor, then show solution only if question attempt
        # is own attempt
        from micourses.models import INSTRUCTOR_ROLE, DESIGNER_ROLE
        if not (ce.role == INSTRUCTOR_ROLE or ce.role == DESIGNER_ROLE):
            if not own_attempt:
                return JsonResponse({})

        if own_attempt and not question_attempt.solution_viewed:
            # record fact that viewed solution for this question_attempt
            question_attempt.solution_viewed = timezone.now()
            with transaction.atomic(), reversion.create_revision():
                question_attempt.save()

        # return solution
        return JsonResponse(results)


def default_sympy_commands(request):
    from mitesting.models import SympyCommandSet
    default_commands = json.dumps(
        [(cmd.pk, cmd.name) for cmd in SympyCommandSet.objects.filter(default=True)])
        
    return HttpResponse(default_commands, content_type = 'application/json')


