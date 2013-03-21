from mitesting.models import Question, Assessment
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.contrib.auth.decorators import permission_required, user_passes_test
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

    question_context = the_question.setup_context(seed)
    
    # if there was an error, question_context is a string 
    # so just make rendered question text be that string
    if not isinstance(question_context, dict):
        rendered_question = question_context
        rendered_solution = question_context
    else:
        rendered_question = the_question.render_question(question_context, user=request.user)
        rendered_solution = the_question.render_solution(question_context)

    if user_has_given_assessment_permission_level(request.user, 2, solution=True):
        show_lists=True
    else:
        show_lists=False

    # no Google analytics for assessments
    noanalytics=True

    return render_to_response \
        ('mitesting/question.html', {'the_question': the_question, 
                                     'rendered_question': rendered_question,
                                     'rendered_solution': rendered_solution,
                                     'show_lists': show_lists,
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

    question_context = the_question.setup_context(seed)
    
    # if there was an error, question_context is a string string,
    # so just make rendered question text be that string
    if not isinstance(question_context, dict):
        rendered_solution = question_context
    else:
        rendered_solution = the_question.render_solution(question_context)
        
    # no Google analytics for assessments
    noanalytics=True

    return render_to_response \
        ('mitesting/question_solution.html', {'the_question': the_question, 
                                     'rendered_solution': rendered_solution,
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
        assessment_date = datetime.date.today().strftime("%B %m, %Y")
    try: 
        course = request.REQUEST['course']
    except:
        course = ""
    try: 
        semester = request.REQUEST['semester']
    except:
        semester = ""

    try: 
        semester = request.REQUEST['semester']
    except:
        semester = ""



    rendered_question_list=[]
    rendered_solution_list=[]
    if solution:
        rendered_solution_list=the_assessment.render_solution_list(seed)
    else:
        rendered_question_list=the_assessment.render_question_list(seed, user=request.user)


    if "question_numbers" in request.REQUEST:
        if solution:
            the_list=rendered_solution_list
        else:
            the_list=rendered_question_list
            
        question_numbers=[]
        for q in the_list:
            question_numbers.append(str(q['question'].id))
        question_numbers = ",".join(question_numbers)
    else:
        question_numbers=None



    # no Google analytics for assessments
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

    return render_to_response \
        (template, 
         {'the_assessment': the_assessment, 
          'the_assessment_name': the_assessment_name, 
          'question_list': rendered_question_list,
          'solution_list': rendered_solution_list,
          'seed': seed, 'version': version,
          'assessment_date': assessment_date,
          'course': course,
          'semester': semester,
          'question_numbers': question_numbers,
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

    avoid_question_seed = the_assessment.avoid_question_seed(avoid_list)
    
    new_url = "%s?seed=%s" % (reverse('mit-assessment', kwargs={'assessment_code': assessment_code}), avoid_question_seed)
    

    return HttpResponseRedirect(new_url)

@user_has_given_assessment_permission_level_decorator(2, solution=False)
def assessment_list_view(request):

    assessment_list = Assessment.objects.all()

    if return_user_assessment_permission_level(request.user, solution=True) >=2:
        view_solution = True
    else:
        view_solution = False
    
    # no Google analytics for assessments
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

    # no Google analytics for assessments
    noanalytics=True
    
    return render_to_response \
        ('mitesting/question_list.html', {'question_list': question_list,
                                          'noanalytics': noanalytics,
                                          },
         context_instance=RequestContext(request))


def question_figure_view(request, question_id, figure_number):
    from mitesting.figure import linegraph

    the_question = get_object_or_404(Question, id=question_id)
    
    # get functions for figure_number
    the_functions=the_question.function_set.filter(figure=figure_number)
    
    # raise 404 if no such functions
    if len(the_functions)==0:
        raise Http404()

    # check if any of the functions are solution_only
    solution_only=False
    for function in the_functions:
        if function.solution_only:
            solution_only=True
            break

    # determine if user has permission to view, given privacy level
    if not the_question.user_can_view(request.user,solution_only):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)

    # get random number names from question
    the_random_numbers=the_question.randomnumber_set.all()
    
    # for each random number, get value from GET
    random_number_values = {}
    for the_random_number in the_random_numbers:
        try:
            random_number_values[the_random_number.name] = request.GET[the_random_number.name]
            
        except:
            pass

    #make a list of safe functions 
    safe_list = ['arccos', 'arcsin', 'arctan', 'arctan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'piecewise']

    #use the list to filter the local namespace 
    safe_dict = dict([ (k, globals().get(k, None)) for k in safe_list ]) 
    #add any needed builtins back in. 
    safe_dict['__builtins__'] = {}
    safe_dict['abs'] = abs 
    safe_dict['float'] = float 
    safe_dict['int'] = int
    safe_dict['round'] = round

    # process template tags on functions using context of random numbers
    c = Context(random_number_values)
    function_list=[]
    linestyle_list=[]
    linewidth_list=[]
    for (ind,function) in enumerate(the_functions):
        rendered_function_value = Template(function.value).render(c)
        the_variable = function.variable
        function_expression = "lambda %s: %s" % (the_variable, rendered_function_value)

        # Try evaluating function.  Ignore if any errors.
        try:
            f= eval(function_expression,safe_dict)
            function_list.append(f)
            linestyle_list.append(function.linestyle)
            linewidth_list.append(function.linewidth)
        except:
            pass

    # look for graphing parameters from GET
    kwargs={'linestyle': linestyle_list, 'linewidth': linewidth_list}
    try:
        kwargs['xmin'] = float(request.GET['xmin'])
    except:
        pass
    try:
        kwargs['xmax'] = float(request.GET['xmax'])
    except:
        pass
    try:
        kwargs['xlabel'] = request.GET['xlabel']
    except:
        pass
    try:
        kwargs['ylabel'] = request.GET['ylabel']
    except:
        pass

    # convert ymin and ymax to ylim
    try:
        ymin = float(request.GET['ymin'])
    except:
        ymin = None
    try:
        ymax = float(request.GET['ymax'])
    except:
        ymax = None
    if ymin is not None or ymax is not None:
        kwargs['ylim']=[ymin, ymax]
        
    #from midocs.figure import linegraph
    
    return linegraph(f=function_list, **kwargs)
