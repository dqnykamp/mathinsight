from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.template import TemplateSyntaxError, Context, Template
from django.utils.safestring import mark_safe
import random

"""
Change to deal with:
Javascript for solution applets not inserted
Multiple choice changed
Identifier changed
Need to ignore question spacing on solutions

"""



def setup_expression_context(question):
    """
    Set up the question context by parsing all expressions for question.
    Returns context that contains all evaluated expressions 
    with keys given by the expression names.

    Before evaluating expressions, initializes global dictionary
    with allowed sympy commands for the question.

    Random expressions are based on state of random.
    Its seed can be set via random.seed(seed).

    Return a dictionary with the following:
    - expression_context: a Context() with mappings from the expressions
    - sympy_global_dict: the final global_dict from all expressions
    - user_function_dict: results of any RANDOM_FUNCTION_NAME expressions
    - error_in_expressions: True if encountered any errors in expressions
    - expression_error: dictionary of all error messages encountered
    - failed_conditions: True if failed conditions for all attempts
    - failed_condition_message: message of which expression last failed
    """


    max_tries=500
    success=False

    from mitesting.utils import return_sympy_global_dict

    failed_condition_message=""
    failed_conditions=True
    for i in range(max_tries):
        expression_context = Context({})
        random_group_indices={}
        error_in_expressions = False
        expression_error = {}
        user_function_dict = {}

        # initialize global dictionary using the comamnds
        # found in allowed_sympy_commands.
        # Also adds standard symbols to dictionary.
        global_dict = return_sympy_global_dict(
            [a.commands for a in question.allowed_sympy_commands.all()])

        try:
            for expression in question.expression_set.all():
                try:
                    expression_evaluated=expression.evaluate(
                        global_dict=global_dict, 
                        user_function_dict=user_function_dict,
                        random_group_indices=random_group_indices)

                # on FailedCondition, reraise to stop evaluating expressions
                except expression.FailedCondition:
                    raise

                # for any other exception, record exception and
                # allow to continue processing expressions
                except Exception as exc:
                    error_in_expressions = True
                    expression_error[expression.name] = exc.args[0]
                    expression_context[expression.name] = '??'

                else:
                    # if random word, add singular and plural to context
                    if expression.expression_type == expression.RANDOM_WORD:
                        expression_context[expression.name] \
                            = expression_evaluated[0]
                        expression_context[expression.name + "_plural"] \
                            = expression_evaluated[1]
                    else:
                        expression_context[expression.name] \
                            = expression_evaluated

            # if make it through all expressions without encountering
            # a failed condition, then record fact and
            # break out of loop
            failed_conditions = False
            break

        # on FailedCondition, continue loop, but record
        # message in case it is final pass through loop
        except expression.FailedCondition as exc:
            failed_condition_message = exc.args[0]



    results = {
        'error_in_expressions': error_in_expressions,
        'expression_error': expression_error,
        'failed_conditions': failed_conditions,
        'failed_condition_message': failed_condition_message,
        'sympy_global_dict': global_dict,
        'user_function_dict': user_function_dict,
        'expression_context': expression_context,
        }


    return results


def render_question_text(question_data, solution=False):

    question = question_data['question']

    expr_context = question_data['expression_context']

    render_results = {}

    template_error=False
    template_string_base = "{% load testing_tags mi_tags humanize %}"
    template_string=template_string_base
    if solution:
        template_string += question.solution_text
    else:
        template_string += question.question_text
    try:
        render_results['rendered_text'] = \
             mark_safe(Template(template_string).render(expr_context))
    except TemplateSyntaxError as e:
        render_results['rendered_text'] = \
            mark_safe("<p>Error in question template: %s</p>" % e)
        template_error = True

    render_results['subparts']=[]
    subparts = question.questionsubpart_set.all()
    for subpart in subparts:
        template_string=template_string_base
        subpart_dict = {'letter': subpart.get_subpart_letter() }
        if solution:
            template_string += subpart.solution_text
        else:
            template_string += subpart.question_text
        try:
            subpart_dict['subpart_text']= \
                mark_safe(Template(template_string).render(expr_context))
        except TemplateSyntaxError as e:
            subpart_dict['subpart_text'] = \
                mark_safe("Error in question subpart template: %s" % e)
            template_error= True
        render_results['subparts'].append(subpart_dict)

    if question_data['show_help']:
        add_help_data(question_data, render_results, subparts)
        
    render_results['render_error'] = template_error

    return render_results




def add_help_data(question_data, render_results, subparts=None):

    question = question_data['question']

    template_string_base = "{% load testing_tags mi_tags humanize %}"
    expr_context = question_data['expression_context']
    hint_template_error=False
   
    # solution is visible if user has permisions for question and, 
    # in the case when the question is part of an assessment, 
    # also has permissions for assessment
    solution_visible = False
    if question_data['user'] and \
            question.user_can_view(question_data['user'],solution=True):
        if question_data['assessment']:
            if question_data['assessment'].user_can_view(user, solution=True):
                solution_visible=True
        else:
            solution_visible=True

    if subparts is None:
        subparts = question.questionsubpart_set.all()

    subparts_present=False
    for (i,subpart) in enumerate(subparts):
        subparts_present=True
        help_available=False
        subpart_dict = render_results['subparts'][i]
        subpart_dict['reference_pages'] = \
            [rpage.page for rpage in question.questionreferencepage_set\
                 .filter(question_subpart=subpart_dict['letter'])]
        if subpart_dict['reference_pages']:
            help_available=True
        if solution_visible and subpart.solution_text:
            subpart_dict['include_solution_link']=True
            help_available=True
        if subpart.hint_text:
            template_string = template_string_base + subpart.hint_text
            try:
                subpart_dict['hint_text'] = \
                    Template(template_string).render(expr_context)
            except TemplateSyntaxError as e:
                subpart_dict['hint_text'] = \
                    'Error in hint text template: %s' % e
                hint_template_error=True
            help_available=True
        subpart_dict['help_available']=help_available

    help_available=False
    if subparts_present:
        render_results['reference_pages'] = \
            [rpage.page for page in question.questionreferencepage_set\
                 .filter(question_subpart=None)]
    else:
        render_results['reference_pages'] = \
            [rpage.page for page in question.questionreferencepage_set.all()]
    if render_results['reference_pages']:
        help_available=True

    if solution_visible and question.solution_text:
        render_results['include_solution_link'] = True
        help_available=True
    if question.hint_text:
        template_string = template_string_base + question.hint_text
        try:
            render_results['hint_text'] = \
                Template(template_string).render(expr_context)
        except TemplateSyntaxError as e:
            render_results['hint_text'] = \
                'Error in hint text template: %s' % e
            hint_template_error=True
        help_available = True
    render_results['help_available'] = help_available

    render_results['hint_template_error'] = hint_template_error


def render_question(question, seed=None, user=None, show_help=True,
                    question_identifier="", 
                    assessment=None, question_set=None, 
                    assessment_seed=None, pre_answers=None, readonly=False,
                    precheck=False, allow_solution_buttons=False,
                    solution=False):

    """
    renders question

    If argument seed is specified, random number generator used for
    randomly generating expressions is initialized to that seed.
    Otherwise a seed is randomly generated (and returned so can
    generate exact version again by passing the seed back in).


    """

    if seed is None:
        seed=question.get_new_seed()

    random.seed(seed)

    # first, setup context due to expressions from question
    context_results = setup_expression_context(question)

    # if failed condition, then don't display the question
    # but instead give message that condition failed
    if context_results['failed_conditions']:
        results = {
            'success': False,
            'error_message': mark_safe(
                '<p>'+context_results['failed_condition_message']+'</p>'),
            'question_text': mark_safe(
                "<p>Question cannot be displayed "
                + " due to failed condition.</p>")
        }
        return results


    question_data = {
        'question': question, 'identifier': question_identifier,
        'seed': seed, 'question_set': question_set,
        'assessment': assessment, 'assessment_seed': assessment_seed,
        'show_help': show_help, 'user': user,
        'readonly': readonly, 'precheck': precheck,
        'pre_answers': pre_answers, 
        'allow_solution_buttons': allow_solution_buttons,
        }

    # applet_data will be used to gather information about applets
    # included in templates.  Applets should add to javascript item
    # with key given by applet code (to avoid collisions)
    # Add to context with key _applet_data_ to avoid overwriting expressions
    applet_data={}
    applet_data['counter']=0
    applet_data['javascript'] = {}
    context_results['expression_context']['_applet_data_'] = \
        applet_data

    # also add to question_data directly to allow easier access
    question_data['applet_data'] = applet_data


    question_data['expression_context'] \
        = context_results['expression_context']

    results = render_question_text(question_data, solution=solution)

    results['seed'] = seed
    results['identifier']= question_identifier
    results['error_message'] = ''

    # If error in expressions or in rendering,
    # still show as much of the question as was processed.
    # However, don't give opportunity to submit answer
    if results['render_error'] \
            or context_results['error_in_expressions']:

        results['success']=False
        if context_results['error_in_expressions']:
            errors = context_results['expression_error']
            for expr in errors.keys():
                results['error_message'] += '<p>' + errors[expr] + '</p>'
        if results['render_errror']:
            results['error_message'] += '<p>Error in rendering template</p>'

        results['error_message'] = mark_safe(results['error_message'])
        return results


    results['success'] = True

    ### TODO: no submit_button on "precheck"


    # if computer, include submit button
    # and show help via buttons (so can record if view hint/solution)
    results['submit_button'] = question.computer_graded
    results['help_as_buttons'] = question.computer_graded
    return results



    # if question.question_type.name=="Multiple choice":
    #     rendered_text = question.render_multiple_choice_question\
    #         (context, identifier=identifier, seed_used=seed_used,
    #          assessment=assessment,
    #          assessment_seed=assessment_seed, question_set=question_set)
    # elif question.question_type.name=="Math write in":
    #     rendered_text= question.render_math_write_in_question\
    #         (context, identifier=identifier, seed_used=seed_used,
    #          assessment=assessment,
    #          assessment_seed=assessment_seed, question_set=question_set,
    #          precheck=precheck)
    # else:


    # return rendered_text

