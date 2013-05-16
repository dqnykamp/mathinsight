from mitesting.models import Question, Assessment
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.conf import settings
from django.utils.safestring import mark_safe
import random
from numpy import arccos, arcsin, arctan, arctan2, ceil, cos, cosh, degrees, e, exp, fabs, floor, fmod, frexp, hypot, ldexp, log, log10, modf, pi, radians, sin, sinh, sqrt, tan, tanh, piecewise

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



def assessment_view(request, assessment_code, solution=False):
    
    the_assessment = get_object_or_404(Assessment, code=assessment_code)
    
    # determine if user has permission to view, given privacy level
    if not the_assessment.user_can_view(request.user, solution):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)
    
    try:
        seed = request.REQUEST['seed']
        version = seed
    except:
        seed = None
        version = 'random'
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


    rendered_question_list=[]
    rendered_solution_list=[]
    if solution:
        rendered_solution_list=the_assessment.render_solution_list(seed)
        geogebra_oninit_commands=""
        for sol in rendered_solution_list:
            if geogebra_oninit_commands:
                geogebra_oninit_commands += "\n"
            if sol['geogebra_oninit_commands']:
                geogebra_oninit_commands += sol['geogebra_oninit_commands']
    else:
        rendered_question_list=the_assessment.render_question_list(seed, user=request.user)
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


    if request.user.has_perm("mitesting.administer_assessment"):
        generate_assessment_link = True
    else:
        generate_assessment_link = False


    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2:
        noanalytics=True
    
    solution_postfix=""
    if solution:
        solution_postfix="_solution"
    template="mitesting/assessment"+solution_postfix+".html"
    if the_assessment.assessment_type.code=='in_class_exam':
        template="mitesting/exam"+solution_postfix+".html"
    elif the_assessment.assessment_type.code=='in_class_quiz':
        template="mitesting/quiz"+solution_postfix+".html"

    the_assessment_name = the_assessment.name
    if solution:
        the_assessment_name = the_assessment_name + " solution"
    the_assessment_short_name = the_assessment.return_short_name()
    if solution:
        the_assessment_short_name = the_assessment_short_name + " sol."

    return render_to_response \
        (template, 
         {'the_assessment': the_assessment, 
          'the_assessment_name': the_assessment_name, 
          'the_assessment_short_name': the_assessment_short_name, 
          'question_list': rendered_question_list,
          'solution_list': rendered_solution_list,
          'seed': seed, 'version': version,
          'assessment_date': assessment_date,
          'course': course,
          'semester': semester,
          'question_numbers': question_numbers,
          'generate_assessment_link': generate_assessment_link,
          'geogebra_oninit_commands': geogebra_oninit_commands,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


def assessment_avoid_question_view(request, assessment_code):
    
    the_assessment = get_object_or_404(Assessment, code=assessment_code)
    
    # determine if user has permission to view, given privacy level
    if not the_assessment.user_can_view(request.user, solution=True):
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
        new_seed = the_assessment.avoid_question_seed(avoid_list, start_seed=seed)
    else:
        new_seed=seed
    
    new_url = "%s?seed=%s&date=%s&course=%s&semester=%s&question_numbers" % (reverse('mit-assessment', kwargs={'assessment_code': assessment_code}), new_seed, assessment_date, course, semester)
    

    return HttpResponseRedirect(new_url)

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
