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
import random
from django.contrib.contenttypes.models import ContentType
import datetime
from mitesting.permissions import return_user_assessment_permission_level, user_has_given_assessment_permission_level_decorator, user_has_given_assessment_permission_level
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

        context['question_data']= self.object.render(
            seed=seed, user=self.request.user,
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
      - answer_info: codes, points and answer type of answers in question
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
        random.seed(seed)
        from .render_assessments import setup_expression_context
        context_results = setup_expression_context(question)

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
        
        points_achieved=0
        total_points=0

        from .sympy_customized import parse_and_process
        from .math_objects import math_object
        answer_results={}

        answer_results['answer_feedback'] = {}
        answer_results['answer_correct'] = {}
        answer_results['identifier']=question_identifier
        answer_results['feedback']=""

        binary_feedback_correct = ' <img src="%sadmin/img/icon-yes.gif" alt="correct" />'\
             % (settings.STATIC_URL)
        binary_feedback_incorrect = ' <img src="%sadmin/img/icon-no.gif" alt="incorrect" />'\
            % (settings.STATIC_URL)

        # check correctness of each answer
        for answer_num in range(len(answer_info)):
            user_response = answer_user_responses[answer_num]["answer"]
            answer_code = answer_info[answer_num]['code']
            answer_points= answer_info[answer_num]['points']
            answer_type = answer_info[answer_num]['type']
            answer_identifier = answer_info[answer_num]['identifier']

            total_points += answer_points
            percent_correct = 0
            feedback = ""

            answer_option_used = None
            
            if answer_type == QuestionAnswerOption.MULTIPLE_CHOICE:
                try:
                    the_answer = question.questionansweroption_set \
                        .get(id = user_response)
                except ObjectDoesNotExist:
                    logger.warning("Multiple choice answer not found")
                    answer_results['answer_feedback'][answer_identifier] \
                        = "Cannot grade due to error in question"
                    answer_results['answer_correct'][answer_identifier]=False
                    continue
                except ValueError:
                    answer_results['answer_feedback'][answer_identifier] \
                        = "No response"
                    answer_results['answer_correct'][answer_identifier]=False
                    continue
                else:
                    percent_correct = the_answer.percent_correct
                    if percent_correct == 100:
                        feedback = "Yes, you are correct"
                    elif percent_correct > 0:
                        feedback = 'Answer is not completely correct' \
                            + ' but earns partial (%s%%) credit.' \
                            % (the_answer.percent_correct)
                    else:
                        feedback = "No, you are incorrect"
                    answer_option_used = the_answer

            elif answer_type == QuestionAnswerOption.EXPRESSION:

                # get rid of any .methods, so can't call commands like
                # .expand() or .factor()
                import re
                user_response = re.sub('\.[a-zA-Z]+', '', user_response)

                near_match_percent_correct = 0
                near_match_feedback=""

                if not user_response:
                    answer_results['answer_feedback'][answer_identifier] \
                        = "No response"
                    answer_results['answer_feedback']\
                        [answer_identifier+"__binary_"] \
                        = binary_feedback_incorrect
                    answer_results['answer_correct'][answer_identifier]=False
                    continue


                # compare with expressions associated with answer_code
                for answer_option in question.questionansweroption_set \
                        .filter(answer_code=answer_code, \
                                    answer_type=QuestionAnswerOption.EXPRESSION):

                    # find the expression associated with answer_option
                    try:
                        valid_answer=expr_context[answer_option.answer]
                    except KeyError:
                        continue

                    # determine level of evaluation of answer_option
                    evaluate_level = valid_answer.return_evaluate_level()

                    try:
                        user_response_parsed = parse_and_process(
                            user_response, global_dict=global_dict, 
                            split_symbols=answer_option
                            .split_symbols_on_compare,
                            evaluate_level=evaluate_level)
                    except Exception as e:
                        feedback = "Sorry.  Unable to understand the answer."
                        break

                    
                    from mitesting.sympy_customized import EVALUATE_NONE
                    user_response_unevaluated =  parse_and_process(
                        user_response, global_dict=global_dict, 
                        split_symbols=answer_option
                        .split_symbols_on_compare,
                        evaluate_level=EVALUATE_NONE)

                    user_response_parsed=math_object(
                        user_response_parsed,
                        tuple_is_unordered=valid_answer.return_if_unordered(),
                        output_no_delimiters= \
                            valid_answer.return_if_output_no_delimiters(),
                        use_ln=valid_answer.return_if_use_ln(),
                        normalize_on_compare=answer_option.normalize_on_compare,
                        evaluate_level=evaluate_level,
                        n_digits = valid_answer.return_n_digits(),
                        round_decimals = valid_answer.return_round_decimals())

                    user_response_unevaluated=math_object(
                        user_response_unevaluated,
                        tuple_is_unordered=valid_answer.return_if_unordered(),
                        output_no_delimiters= \
                            valid_answer.return_if_output_no_delimiters(),
                        use_ln=valid_answer.return_if_use_ln(),
                        normalize_on_compare=answer_option.normalize_on_compare,
                        evaluate_level=EVALUATE_NONE)

                    correctness_of_answer = \
                        user_response_parsed.compare_with_expression( \
                        valid_answer.return_expression())

                    if correctness_of_answer == 1 and \
                            answer_option.percent_correct > percent_correct:
                        if answer_option.percent_correct == 100:
                            feedback = \
                                'Yes, $%s$ is correct.' % \
                                user_response_unevaluated
                        else:
                            feedback = '$%s$ is not completely correct but earns' \
                                ' partial (%s%%) credit.' \
                                % (user_response_unevaluated, 
                                   answer_option.percent_correct)
                        percent_correct = answer_option.percent_correct
                        answer_option_used = answer_option

                    elif correctness_of_answer == -1 and \
                            answer_option.percent_correct >\
                            near_match_percent_correct:
                        near_match_feedback = \
                            " Your answer is mathematically equivalent to " 
                        if answer_option.percent_correct == 100:
                            near_match_feedback += "the correct answer, "
                        else:
                            near_match_feedback  += \
                                "an answer that is %s%% correct, " \
                                % answer_option.percent_correct
                        near_match_feedback += "but this question requires"\
                            " you to write your answer in a different form." 
                        near_match_percent_correct =\
                            answer_option.percent_correct
                        answer_option_used = answer_option
                    if not feedback:
                        feedback = 'No, $%s$ is incorrect.' \
                            % user_response_unevaluated
                        answer_option_used = answer_option

                if percent_correct < 100 and near_match_feedback:
                    feedback += near_match_feedback

            else:
                logger.warning("Unrecognized answer type: %s" % answer_type)
                answer_results['answer_feedback'][answer_identifier] \
                    = "Cannot grade due to error in question"
                answer_results['answer_feedback']\
                    [answer_identifier+"__binary_"] \
                    = binary_feedback_incorrect
                answer_results['answer_correct'][answer_identifier]=False
                continue


            # store (points achieved)*100 as integer for now
            points_achieved += percent_correct * \
                answer_points

            answer_results['answer_feedback'][answer_identifier] \
                = feedback
            if percent_correct == 100:
                answer_results['answer_feedback']\
                    [answer_identifier+"__binary_"] \
                    = binary_feedback_correct
            else:
                answer_results['answer_feedback']\
                    [answer_identifier+"__binary_"] \
                    = binary_feedback_incorrect

            answer_results['answer_correct'][answer_identifier]\
                = (percent_correct == 100)

            # record any feedback from answer option used
            if answer_option_used and answer_option_used.feedback:
                template_string = "{% load testing_tags mi_tags humanize %}"
                template_string += answer_option_used.feedback
                try:
                    t = Template(template_string)
                    rendered_feedback = mark_safe(t.render(expr_context))
                except TemplateSyntaxError as e:
                    logger.warning("Error in feedback for answer option with "
                                   + " code = %s: %s"
                                   % (answer_code, answer_option_used))
                else:
                    answer_results['feedback'] += "<p>%s</p>" %\
                        rendered_feedback

        
        # record if exactly correct, then normalize points achieved
        if total_points:
            answer_correct = (points_achieved == total_points*100)
            points_achieved /= 100.0
            credit = points_achieved/total_points
        else:
            answer_correct = False
            points_achieved /= 100.0
            credit = 0
        answer_results['correct'] = answer_correct
        if total_points == 0:
            total_score_feedback = "<p>No points possible for question</p>"
        elif answer_correct:
            total_score_feedback = "<p>Answer is correct</p>"
        elif points_achieved == 0:
            total_score_feedback = "<p>Answer is incorrect</p>"
        else:
            total_score_feedback = '<p>Answer is %s%% correct'\
                % int(round(credit*100))
        answer_results['feedback'] = total_score_feedback + \
            answer_results['feedback']
            
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
                 seed=seed, credit=credit,\
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

        from mitesting.render_assessments import render_question
        question_data= render_question(
            question=question,
            seed=seed, user=request.user,
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

        context['assessment_date'] = self.request.GET.get\
            ('date', datetime.date.today().strftime("%B %d, %Y"))

        applet_data = Applet.return_initial_applet_data()
        context['applet_data'] = applet_data

        from .render_assessments import render_question_list, get_new_seed
        rendered_list=[]
        (rendered_list,self.seed)=render_question_list(
            self.object, seed=self.seed, user=self.request.user, 
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
        
        if self.request.user.has_perm("mitesting.administer_assessment"):
            context['generate_assessment_link'] = True
        else:
            try:
                if self.request.user.courseuser:
                    if self.request.courseuser.get_current_role() == 'I':
                        context['generate_assessment_link'] = True
            except AttributeError:
                pass

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

        context['course_thread_content'] = self.course_thread_content
        context['attempt_number'] = self.attempt_number

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

        context['new_seed']=get_new_seed()

        return context


    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        seed = request.GET.get('seed')
        self.determine_seed_version(user=request.user,seed=seed)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def post(self, request, *args, **kwargs):
        """
        Through post can generate new attempt.
        Need to test and fix this.
        """
        self.object = self.get_object()
        new_attempt = request.POST.get('new_attempt',False)
        self.determine_seed_version(user=request.user,
                                    new_attempt=new_attempt)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def determine_seed_version(self, user, seed=None, new_attempt=False):
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
            course = courseuser.return_selected_course()
        except (ObjectDoesNotExist, MultipleObjectsReturned, AttributeError):
            courseuser = None
            course = None

        self.current_attempt=None
        self.attempt_number=0
        self.course_thread_content=None


        # if enrolled in the course
        if course:
            assessment_content_type = ContentType.objects.get\
                (model='assessment')

            try:
                self.course_thread_content=course.coursethreadcontent_set.get\
                    (thread_content__object_id=self.object.id,\
                         thread_content__content_type=assessment_content_type)
                # Finds the course version of the specific assessment
            except ObjectDoesNotExist:
                course=None

            if self.course_thread_content:
                attempts = self.course_thread_content.studentcontentattempt_set\
                    .filter(student=courseuser) 
                self.attempt_number = attempts.count()
                # attempts = attempts.filter(score=None) # We do not want to modify attempts where the score has been overitten

                if new_attempt:
                    # if new_attempt, create another attempt
                    self.attempt_number += 1
                    self.version = str(self.attempt_number)
                    if self.course_thread_content.individualize_by_student:
                        self.version= "%s_%s" % (courseuser.user.username, 
                                                 self.version)
                    seed = "%s_%s_%s" % (course.code, self.object.id, 
                                         self.version)

                    try:
                        self.current_attempt = \
                            self.course_thread_content.studentcontentattempt_set\
                            .create(student=courseuser, seed=seed)
                    except IntegrityError:
                        raise 


                # if instructor and seed is set from GET/POST
                # then use that seed and don't link to attempt
                # (i.e., skip this processing)
                elif not (courseuser.get_current_role() == 'I' and \
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
                        seed = "%s_%s_%s" % (course.code, self.object.id, 
                                             self.version)

                        # create the attempt
                        self.current_attempt = \
                            self.course_thread_content.studentcontentattempt_set\
                            .create(student=courseuser, seed=seed)

        self.seed=seed


def assessment_avoid_question_view(request, assessment_code):
    
    assessment = get_object_or_404(Assessment, code=assessment_code)
    
    # determine if user has permission to view, given privacy level
    if not assessment.user_can_view(request.user, solution=True):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)
    
    try:
        avoid_list= request.REQUEST['avoid_list']
    except:
        avoid_list = ""
    try:
        seed = request.REQUEST['seed']
    except:
        seed = None
    try: 
        assessment_date = request.REQUEST['date']
    except:
        assessment_date = datetime.date.today().strftime("%B %d, %Y")
    try: 
        course = request.REQUEST['course']
    except:
        course = ""
    try: 
        semester = request.REQUEST['semester']
    except:
        semester = ""

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
    if request.user.has_perm("mitesting.administer_assessment"):
        generate_assessment_link = True
    else:
        try:
            if self.request.user.courseuser:
                if self.request.courseuser.get_current_role() == 'I':
                    generate_assessment_link = True
        except AttributeError:
            pass

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
