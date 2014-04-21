from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.models import Question, Assessment, QuestionAnswerOption
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
from django.core.exceptions import ObjectDoesNotExist
import random
from django.contrib.contenttypes.models import ContentType
import datetime
from mitesting.permissions import return_user_assessment_permission_level, user_has_given_assessment_permission_level_decorator, user_has_given_assessment_permission_level
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin
import json 

class QuestionView(DetailView):
    """
    
    """

    model = Question
    pk_url_kwarg = 'question_id'

    def render_to_response(self, context, **response_kwargs):
        # determine if user has permission to view question,
        # given privacy level
        if not self.object.user_can_view(self.request.user,
                                         solution=context['solution']):
            path = self.request.build_absolute_uri()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path)
        else:
            return super(QuestionView, self)\
                .render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        
        if self.request.method == 'GET':
            try:
                seed = self.request.GET['seed']
            except:
                seed = None
        else:
            try:
                seed = self.request.POST['seed']
            except:
                seed = None
                
        # determine if rendering solution.
        solution=kwargs.get('solution',False)
        context['solution'] = solution

        show_help = not solution and not self.object.computer_graded
        
        # In question view, there will be only one question on page.
        # Identifier doesn't matter.  Use qv to indiciate from question view.
        identifier = "qv"
        from mitesting.render_assessments import render_question
        context['question_data']= render_question(
            question=self.object,
            seed=seed, user=self.request.user,
            question_identifier=identifier, 
            allow_solution_buttons=True,
            solution=solution,
            show_help = show_help)


        # if users has full permissions on assessments
        # (i.e., permission level 2 for solutions),
        # then show lists of assessments
        if user_has_given_assessment_permission_level(self.request.user, 2, 
                                                      solution=True):
            context['show_lists']=True
        else:
            context['show_lists']=False

        # no Google analytics for questions
        context['noanalytics']=True

        return context

class QuestionSolutionView(QuestionView):
    template_name = 'mitesting/question_solution.html'

    def get_context_data(self, **kwargs):
        kwargs['solution']=True
        return super(QuestionSolutionView, self).get_context_data(**kwargs)


class GradeQuestionView(SingleObjectMixin, View):
    model = Question
    pk_url_kwarg = 'question_id'

    def post(self, request, *args, **kwargs):
        # Look up the question to grade
        question = self.get_object()
        
        response_data = request.POST

        import pickle
        import base64
        computer_grade_data = pickle.loads(
            base64.b64decode(response_data.get('cgd')))

        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data.get('seed')
        random.seed(seed)
        from .render_assessments import setup_expression_context
        context_results = setup_expression_context(question)

        expr_context = context_results['expression_context']

        function_dict = context_results['user_function_dict']
        global_dict = question.return_sympy_global_dict(user_response=True)
        global_dict.update(function_dict)

        answer_blank_codes = computer_grade_data['answer_blank_codes']
        answer_blank_points = computer_grade_data['answer_blank_points']
        
        answer_blank_user_responses = {}
        for answer_identifier in answer_blank_codes.keys():
            answer_blank_user_responses[answer_identifier] = \
                response_data['answer_%s' % answer_identifier]


        points_achieved=0
        total_points=0

        from .sympy_customized import parse_and_process
        from .math_objects import math_object
        answer_results={}

        answer_results['answer_blank_feedback'] = {}
        answer_results['answer_blank_correct'] = {}
        answer_results['identifier']=question_identifier

        # check correctness of each answer
        for answer_identifier in answer_blank_codes.keys():
            user_response = answer_blank_user_responses[answer_identifier]
            answer_code = answer_blank_codes[answer_identifier]
            answer_points = answer_blank_points[answer_identifier]

            total_points += answer_points

            # get rid of any .methods, so can't call commands like
            # .expand() or .factor()
            import re
            user_response = re.sub('\.[a-zA-Z]+', '', user_response)
            
            percent_correct = 0
            near_match_percent_correct = 0

            if not user_response:
                answer_results['answer_blank_feedback'][answer_identifier] \
                    = "No response"
                answer_results['answer_blank_correct'][answer_identifier]=0
                continue
            
            feedback=""
               
            # compare with expressions associated with answer_code
            for answer_option in question.questionansweroption_set \
                    .filter(answer_code=answer_code, \
                                answer_type=QuestionAnswerOption.EXPRESSION):
                
                # find the expression associated with answer_option
                try:
                    valid_answer=expr_context[answer_option.answer]
                except KeyError:
                    continue

                split_symbols=answer_option.split_symbols_on_compare
                
                try:
                    user_response_parsed = parse_and_process(
                        user_response, global_dict=global_dict, 
                        split_symbols=split_symbols)
                except Exception as e:
                    feedback = "Sorry.  Unable to understand the answer."
                    break

                user_response_parsed=math_object(
                    user_response_parsed,
                    tuple_is_unordered=valid_answer.return_if_unordered(),
                    output_no_delimiters= \
                        valid_answer.return_if_output_no_delimiters(),
                    use_ln=valid_answer.return_if_use_ln())


                correctness_of_answer = valid_answer.compare_with_expression \
                    (user_response_parsed.return_expression())

                if correctness_of_answer == 1:
                    if answer_option.percent_correct > percent_correct:
                        if answer_option.percent_correct == 100:
                            feedback = \
                                'Yes, $%s$ is correct.' % user_response_parsed
                        else:
                            feedback = \
                                '$%s$ is partially correct (%s%% credit).'\
                                % (user_response_parsed, 
                                   answer_option.percent_correct)
                        percent_correct = answer_option.percent_correct
                        
                elif correctness_of_answer == -1 and percent_correct==0:
                    if answer_option.percent_correct >\
                            near_match_percent_correct:
                        feedback = "No, $%s$ is not correct. " \
                            % user_response_parsed
                        feedback += " You are close as your "\
                            + "answer is mathematically equivalent to " 
                        if answer_option.percent_correct == 100:
                            feedback += "the correct answer, "
                        else:
                            feedback += "an answer that is %s%% correct, " \
                                % answer_option.percent_correct
                        feedback += "but this question requires"\
                            " you to write your answer in a different form." 
                elif not feedback:
                    feedback = 'No, $%s$ is incorrect.  Try again.' \
                        % user_response_parsed


            # store (points achieved)*100 as integer for now
            points_achieved += percent_correct * \
                answer_blank_points[answer_identifier]

            answer_results['answer_blank_feedback'][answer_identifier] \
                = feedback
            answer_results['answer_blank_correct'][answer_identifier]\
                = percent_correct

        
        # record if exactly correct, then normalize points achieved
        answer_correct = (points_achieved == total_points*100)
        points_achieved /= 100.0
        credit = points_achieved/total_points
        answer_results['correct'] = answer_correct
        if answer_correct:
            answer_results['feedback'] = "<p>Answer is correct</p>"
        elif points_achieved == 0:
            answer_results['feedback'] = "<p>Answer is incorrect</p>"
        else:
            answer_results['feedback'] = '<p>Answer is %s%% correct'\
                % round(credit*100) 

        # increment number of attempts
        try:
            number_attempts = int(response_data['number_attempts_%s' % 
                                                question_identifier])
        except (KeyError, ValueError):
            number_attempts=0

        number_attempts+=1
        answer_results['number_attempts'] = number_attempts

        show_solution_button = False
        allow_solution_buttons = computer_grade_data.get(
            'allow_solution_buttons', False)

        if allow_solution_buttons and \
                question.show_solution_button_after_attempts and \
                number_attempts >= \
                question.show_solution_button_after_attempts and \
                question.user_can_view(request.user, solution=True):

            # check if solution exists for question or subpart
            solution_exists = False
            if question.solution_text:
                solution_exists = True
            else:
                for question_subpart in question.questionsubpart_set.all():
                    if question_subpart.solution_text:
                        solution_exists = True
                        break

            if solution_exists:
                show_solution_button = True
                inject_solution_url = reverse('mit-injectquestionsolution',
                                      kwargs={'question_id': question.id})
                show_solution_command = \
                    '$.post("%s", "cgd=%s", process_solution_inject);' \
                    % (inject_solution_url, response_data.get('cgd'))
                
                solution_button_html = \
                    "<input type='button' class='mi_show_solution' value='Show solution' onclick='%s'>" % (show_solution_command)

                answer_results['solution_button_html'] = \
                    solution_button_html

                

        answer_results['show_solution_button'] = show_solution_button

        
        # untested with courses
        
        # if not recording the result of the question,
        # we're finished, so return response with the results
        if not (computer_grade_data['record'] 
                and request.user.is_authenticated()):
            return HttpResponse(json.dumps(answer_results),
                                content_type = 'application/json')
            
        
        assessment_code = computer_grade_data.get('assessment_code')
        assessment_seed = computer_grade_data.get('assessment_seed')
        if assessment_code:
            assessment = Assessment.objects.get(code=assessment_code)
        else:
            assessment = None
            question_set = None
            assessment_seed = None

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
        record_scores = True

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
                    record_scores = False

                if not content.record_scores:
                    record_scores = False

            except ObjectDoesNotExist:
                content=None
                record_scores = False

            if record_scores:
                due_date = content.adjusted_due_date(student)
                today = datetime.date.today()
                if due_date and today > due_date:
                    past_due = True
                    record_scores = False

            # if record scores, get or create attempt by student
            # with same assessment_seed
            if record_scores:
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
                    record_scores = False


        # if have current_attempt, don't record assessment,
        # as it would be redundant information
        if current_attempt:
            assessment=None
            assessment_seed = None

        # record attempt, possibly linking to latest content attempt
        # even if record_scores is False, create QuestionStudentAnswer
        # record (just in case), but don't associate it with course
        import json
        QuestionStudentAnswer.objects.create\
            (user=request.user, question=question, \
                 question_set=question_set,\
                 answer=json.dumps(answer_blank_user_responses),\
                 identifier_in_answer = question_identifier, \
                 seed=seed, credit=credit,\
                 course_content_attempt=current_attempt,\
                 assessment=assessment, \
                 assessment_seed=assessment_seed)

        if past_due:
            feedback_message = "Due date %s of %s is past.<br/>Answer not recorded." % (due_date, assessment)
        elif solution_viewed:
            feedback_message = "Solution for question already viewed for this attempt.<br/>Answer not recorded. <br/>Generate a new attempt to resume recording answers." 
        elif not record_scores:
            feedback_message = "Assessment not set up for recording answers"
        else:
            feedback_message = ""

        if current_attempt:
            feedback_message += "Answer recorded for %s<br/>Course: <a href=\"%s\">%s</a>" % (request.user,reverse('mic-assessmentattempted', kwargs={'pk': content.id} ), course)


        answer_results['feedback_message']=feedback_message
        

        data = json.dumps(answer_results)

        return HttpResponse(json.dumps(answer_results),
                            content_type = 'application/json')


class InjectQuestionSolutionView(SingleObjectMixin, View):
    model = Question
    pk_url_kwarg = 'question_id'

    def post(self, request, *args, **kwargs):
        # Look up the question to grade
        question = self.get_object()
        
        if not question.user_can_view(request.user, True):
            return HttpResponse("", content_type = 'application/json')

        response_data = request.POST

        import pickle
        import base64
        computer_grade_data = pickle.loads(
            base64.b64decode(response_data.get('cgd')))

        question_identifier = computer_grade_data['identifier']

        # set up context from question expressions
        seed = computer_grade_data.get('seed')

        from mitesting.render_assessments import render_question
        question_data= render_question(
            question=question,
            seed=seed, user=request.user,
            question_identifier=question_identifier, 
            applet_counter = computer_grade_data["applet_counter"],
            solution=True,
            show_help = False)

        from django.template.loader import get_template
        question_solution_template = get_template(
            "mitesting/question_solution_body.html")
        rendered_solution = question_solution_template.render(Context(
                {'question_data': question_data}))

        rendered_solution = mark_safe("<h4>Solution</h4>" + rendered_solution)
        results = {'rendered_solution': rendered_solution,
                   'identifier': question_identifier
                   }

        # record that viewed solution
        # if record is true

        # this code is untested

        # record fact that user viewed solution
        if computer_grade_data['record'] and request.user.is_authenticated():
            assessment_code = computer_grade_data.get('assessment_code')
            assessment_seed = computer_grade_data.get('assessment_seed')
            if assessment_code:
                assessment = Assessment.objects.get(code=assessment_code)
            else:
                assessment = None

            try:
                student = request.user.courseuser
                course = student.return_selected_course()
            except:
                course = None
                    
            # check if assessment given by assessment_code is in course
            # if so, will link to latest attempt
            if course and assessment_code:
                    
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



def assessment_view(request, assessment_code, solution=False, question_only=None):
    
    # if question_only is set, then view only that question
    if question_only:
        question_only = int(question_only)

    assessment = get_object_or_404(Assessment, code=assessment_code)
    
    # determine if user has permission to view, given privacy level
    if not assessment.user_can_view(request.user, solution):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)

    seed = None
    version = ''
    
    if request.method == 'POST':
        new_attempt = request.POST['new_attempt']
    else:
        new_attempt = False
        seed = request.REQUEST.get('seed', None)
        """
        This is possibly not a correct comment.
        If the user is anonymous, the seed is available in _GET.
        However, users in courses have seeds passed through the database and this will be set to None, to be overwritten later.
        """
        version = seed
        if not version:
            if assessment.nothing_random:
                version = ''
            else:
                version='random'

    assessment_date = request.REQUEST.get\
        ('date', datetime.date.today().strftime("%B %d, %Y"))


    try:
        courseuser = request.user.courseuser
        course = courseuser.return_selected_course()
    except:
        courseuser = None
        course = None

    current_attempt=None
    attempt_number=0
    course_thread_content=None

    # if student in the course
    if course:
        assessment_content_type = ContentType.objects.get\
            (model='assessment')
                        
        try:
            course_thread_content=course.coursethreadcontent_set.get\
                (thread_content__object_id=assessment.id,\
                     thread_content__content_type=assessment_content_type)
            # Finds the course version of the specific assessment
        except ObjectDoesNotExist:
            course=None

        if course_thread_content:
            attempts = course_thread_content.studentcontentattempt_set\
                .filter(student=courseuser) 
            attempt_number = attempts.count()
            # attempts = attempts.filter(score=None) # We do not want to modify attempts where the score has been overitten
            
            if new_attempt:
                # if new_attempt, create another attempt
                attempt_number += 1
                version = str(attempt_number)
                if course_thread_content.individualize_by_student:
                    version= "%s_%s" % (courseuser.user.username, version)
                seed = "%s_%s_%s" % (course.code, assessment.id, version)

                try:
                    current_attempt = \
                        course_thread_content.studentcontentattempt_set\
                        .create(student=courseuser, seed=seed)
                except IntegrityError:
                    raise 
                    

            # if instructor and seed is set (from GET)
            # then use that seed and don't link to attempt
            # (i.e., skip this processing)
            elif not (courseuser.role == 'I' and seed is not None):
                
                # else try to find latest attempt
                try:
                    current_attempt = attempts.latest()
                    seed = current_attempt.seed
                    version = str(attempt_number)
                    if course_thread_content.individualize_by_student:
                        version= "%s_%s" % (courseuser.user.username, version)

                except ObjectDoesNotExist:
                    # for seed use course_code, assessment_id, 
                    # and possibly student

                    # if individualize_by_student, add username
                    version = "1"
                    if course_thread_content.individualize_by_student:
                        version= "%s_%s" % (courseuser.user.username, version)
                    seed = "%s_%s_%s" % (course.code, assessment.id, version)

                    # create the attempt
                    current_attempt = \
                        course_thread_content.studentcontentattempt_set\
                        .create(student=courseuser, seed=seed)
                

    rendered_question_list=[]
    rendered_solution_list=[]
    if solution:
        rendered_solution_list=assessment.render_solution_list(seed)
        if question_only:
            try:
                rendered_solution_list=rendered_solution_list[question_only-1:question_only]
            except:
                pass

        geogebra_oninit_commands=""
        for sol in rendered_solution_list:
            if geogebra_oninit_commands:
                geogebra_oninit_commands += "\n"
            if sol['geogebra_oninit_commands']:
                geogebra_oninit_commands += sol['geogebra_oninit_commands']

                        
    else:
        rendered_question_list=assessment.render_question_list(seed, user=request.user, current_attempt=current_attempt)
        if question_only:
            try:
                rendered_question_list = rendered_question_list[question_only-1:question_only]
            except:
                raise#  pass

        geogebra_oninit_commands=""
        for ques in rendered_question_list:
            if geogebra_oninit_commands:
                geogebra_oninit_commands += "\n"
            if ques['geogebra_oninit_commands']:
                geogebra_oninit_commands += ques['geogebra_oninit_commands']

        
        
    geogebra_oninit_commands = mark_safe(geogebra_oninit_commands)

    if "question_numbers" in request.REQUEST:
        if solution:
            the_list=rendered_solution_list
        else:
            the_list=rendered_question_list
            
        question_numbers=[]
        for q in the_list:
            question_numbers.append(str(q['question'].id))
        question_numbers = ", ".join(question_numbers)
    else:
        question_numbers=None


    generate_assessment_link = False
    show_solution_link = False
    if request.user.has_perm("mitesting.administer_assessment"):
        generate_assessment_link = True
        if not solution:
            show_solution_link = True


    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    template_names = []
    solution_postfix=""
    if solution:
        solution_postfix="_solution"
    template_base_name = assessment.assessment_type.template_base_name
    if template_base_name:
        template_names.append("mitesting/%s%s.html" % (template_base_name, solution_postfix))
    template_names.append("mitesting/assessment%s.html" % solution_postfix)


    assessment_name = assessment.name
    if solution:
        assessment_name = assessment_name + " solution"
    assessment_short_name = assessment.return_short_name()
    if solution:
        assessment_short_name = assessment_short_name + " sol."

    if version:
        version_string = ', version %s' % version
    else:
        version_string = ''
    return render_to_response \
        (template_names, 
         {'assessment': assessment, 
          'assessment_name': assessment_name, 
          'assessment_short_name': assessment_short_name, 
          'question_list': rendered_question_list,
          'solution_list': rendered_solution_list,
          'seed': seed, 'version_string': version_string,
          'assessment_date': assessment_date,
          'course': course,
          'course_thread_content': course_thread_content,
          'attempt_number': attempt_number,
          'question_numbers': question_numbers,
          'generate_assessment_link': generate_assessment_link,
          'show_solution_link': show_solution_link,
          'question_only': question_only,
          'geogebra_oninit_commands': geogebra_oninit_commands,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


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

    if request.user.has_perm("mitesting.administer_assessment"):
        generate_assessment_link = True
    else:
        generate_assessment_link = False

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
    
    

@user_has_given_assessment_permission_level_decorator(2, solution=False)
def assessment_list_view(request):

    assessment_list = Assessment.objects.all()

    if return_user_assessment_permission_level(request.user, solution=True) >=2:
        view_solution = True
    else:
        view_solution = False
    
    # no Google analytics for assessment list
    noanalytics=True

    return render_to_response \
        ('mitesting/assessment_list.html', 
         {'assessment_list': assessment_list,
          'view_solution': view_solution,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@user_has_given_assessment_permission_level_decorator(2, solution=True)
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
