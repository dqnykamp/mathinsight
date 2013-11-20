from mitesting.models import Question, Assessment
from django.db import IntegrityError
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
import random
from django.contrib.contenttypes.models import ContentType
import datetime
from mitesting.permissions import return_user_assessment_permission_level, user_has_given_assessment_permission_level_decorator, user_has_given_assessment_permission_level


def question_view(request, question_id):
    the_question = get_object_or_404(Question, id=question_id)
    
    # determine if user has permission to view, given privacy level
    # solution permission required, since shows solution
    if not the_question.user_can_view(request.user, solution=True):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)

    if request.method == 'GET':
        try:
            seed = request.GET['seed']
        except:
            seed = None
    else:
        try:
            seed = request.POST['seed']
        except:
            seed = None

    # use qv in identifier since coming from question view
    identifier = "qv"
    question_context = the_question.setup_context(identifier=identifier,
                                                  seed=seed, 
                                                  allow_solution_buttons=True)
    
    # if there was an error, question_context is a string 
    # so just make rendered question text be that string
    if not isinstance(question_context, Context):
        rendered_question = question_context
        rendered_solution = question_context
        geogebra_oninit_commands=""
    else:
        rendered_question = the_question.render_question(question_context, 
                                                         identifier=identifier,
                                                         user=request.user)
        rendered_solution = the_question.render_solution(question_context,
                                                         identifier=identifier)
        geogebra_oninit_commands=question_context.get('geogebra_oninit_commands')
        #geogebra_oninit_commands=the_question.render_javascript_commands(question_context, question=True, solution=True)

        # n_geogebra_web_applets = question_context.get('n_geogebra_web_applets', 0)
        # if n_geogebra_web_applets>0:
        #     html_string = "napplets++;\nif(napplets == %i) {\n%s\n}" \
        #         % (n_geogebra_web_applets, html_string)


    if user_has_given_assessment_permission_level(request.user, 2, solution=True):
        show_lists=True
    else:
        show_lists=False

    # no Google analytics for questions
    noanalytics=True

    return render_to_response \
        ('mitesting/question.html', {'the_question': the_question, 
                                     'rendered_question': rendered_question,
                                     'rendered_solution': rendered_solution,
                                     'show_lists': show_lists,
                                     'geogebra_oninit_commands': geogebra_oninit_commands,
                                     'noanalytics': noanalytics,
                                     },
         context_instance=RequestContext(request))


def question_solution_view(request, question_id):
    the_question = get_object_or_404(Question, id=question_id)
    
    # determine if user has permission to view, given privacy level
    if not the_question.user_can_view(request.user, solution=True):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)

    if request.method == 'GET':
        try:
            seed = request.GET['seed']
        except:
            seed = None
    else:
        try:
            seed = request.POST['seed']
        except:
            seed = None

    # use qsv in identifier since coming from question solution view
    identifier = "qsv"
    question_context = the_question.setup_context(identifier=identifier,
                                                  seed=seed, 
                                                  allow_solution_buttons=True)
    
    # if there was an error, question_context is a string string,
    # so just make rendered question text be that string
    if not isinstance(question_context, Context):
        rendered_solution = question_context
        geogebra_oninit_commands=""
    else:
        rendered_solution = the_question.render_solution(question_context,
                                                         identifier=identifier)

        geogebra_oninit_commands=question_context.get('geogebra_oninit_commands')
        #geogebra_oninit_commands=the_question.render_javascript_commands(question_context, question=False, solution=True)

    # no Google analytics for questions
    noanalytics=True

    return render_to_response \
        ('mitesting/question_solution.html', {'the_question': the_question, 
                                     'rendered_solution': rendered_solution,
                                     'geogebra_oninit_commands': geogebra_oninit_commands,
                                     'noanalytics': noanalytics,
                                     },
         context_instance=RequestContext(request))



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
