from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.template import TemplateSyntaxError, Context, Template
from django.utils.safestring import mark_safe
import random
import json 
import re

"""
Change to deal with:
Javascript for solution applets not inserted
Multiple choice changed
Identifier changed

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
        global_dict = question.return_sympy_global_dict()
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


def answer_code_list(question): 
    """
    Return a list of all the unique answer codes from the answer options
    of question that are expressions.
    """
    
    from mitesting.models import QuestionAnswerOption

    answer_code_list = []
    for option in question.questionansweroption_set.filter(
        answer_type=QuestionAnswerOption.EXPRESSION):
        
        if option.answer_code not in answer_code_list:
            answer_code_list.append(option.answer_code)
    
    return answer_code_list


def render_question_text(question_data, solution=False):
    """
    Render the question text and subparts as Django templates.
    Use context specified by expression context and load in custom tags
    Optionally render "need help" information.

    Input question data is a dictionary with the following keys
    - question: the question to be rendered
    - expression_context: the template context used to render the text
    - show_help (optional): if true, render the "need help" information
    If show_help is true, then question_data should also include:
    - user: the logged in user
    - assessment: any assessment for which the question belongs
    (These are used to determine if solution link should be included.)
    
    Return render_results dictionary with the following:
    - question: the quesiton that was rendered
    - rendered_text: the results from rendering the main question text
    - render_error: exists and true on error rendering the template
    - subparts: a list of dictionaries of results from rendering subparts
      Each dictionary has the following keys:
      - letter: the letter assigned to the supart
      - subpart_text: the results from rendering the subpart text
      - render_error: exists and true on error rendering the template
    If show_help is true, then render_results also contains;
    - reference_pages: a list of pages relevant to the question
    - hint_text: rendered hint text
    - include_solution_link: exists and true if should include link to solution
    - help_available: true if there is help (hint or links to page/solution)
    - hint_template_error: true if error rendering hint text
    - to each subpart dicionary, the following are added:
      - reference_pages: a list of pages relevant to the subpart
      - hint_text: rendered hint text
      - include_solution_link: exists and is true if should include 
        link to solution
      - help_available: true if there is help for subpart
    """

    question = question_data['question']
    expr_context = question_data['expression_context']

    render_results = {'question': question, 'render_error_messages': [] }
    template_string_base = "{% load testing_tags mi_tags humanize %}"


    # render solution or question, recording any error in rendering template
    if solution:
        the_text = question.solution_text
    else:
        the_text = question.question_text
    if the_text:
        template_string=template_string_base + the_text
        try:
            render_results['rendered_text'] = \
                mark_safe(Template(template_string).render(expr_context))
        except Exception as e:
            if solution:
                render_results['rendered_text'] = \
                    mark_safe("<p>Error in solution</p>")
                render_results['render_error_messages'].append(
                    mark_safe("Error in solution template: %s" % e))
            else:
                render_results['rendered_text'] = \
                    mark_safe("<p>Error in question</p>")
                render_results['render_error_messages'].append(
                    mark_safe("Error in question template: %s" % e))
            render_results['render_error'] = True
    else:
        render_results['rendered_text'] = ""
        
    # for each subpart, render solution or question, 
    # recording any error in rendering template
    render_results['subparts']=[]
    subparts = question.questionsubpart_set.all()
    for subpart in subparts:
        template_string=template_string_base
        subpart_dict = {'letter': subpart.get_subpart_letter() }
        if solution:
            the_text = subpart.solution_text
        else:
            the_text = subpart.question_text
        if the_text:
            template_string=template_string_base + the_text
            try:
                subpart_dict['subpart_text'] = \
                    mark_safe(Template(template_string).render(expr_context))
            except Exception as e:
                if solution:
                    subpart_dict['subpart_text'] = \
                        mark_safe("Error in solution subpart")
                    render_results['render_error_messages'].append(
                        mark_safe("Error in solution subpart %s template: %s" 
                                  % (subpart_dict["letter"],e)))
                else:
                    subpart_dict['subpart_text'] = \
                        mark_safe("Error in question subpart")
                    render_results['render_error_messages'].append(
                        mark_safe("Error in question subpart %s template: %s" 
                                  % (subpart_dict["letter"],e)))
                render_results['render_error'] = True
        else:
            subpart_dict["subpart_text"] = ""
                
        render_results['subparts'].append(subpart_dict)

    # add help data to render_results, if show_help is set to true
    if question_data.get('show_help'):
        add_help_data(question_data, render_results, subparts)

    return render_results


def add_help_data(question_data, render_results, subparts=None):
    """
    Add hints, references pages, and solution availability to render_results
    
    Input question_data is a dictionary with the following keys
    - question: the question to be rendered
    - expression_context: the template context used to render the text
    - user: the logged in user
    - assessment: any assessment for which the question belongs

    Input render_results is a dictionary.
    If question contains subparts, then
    render_results['subparts'][i]
    is a dictionary for each i that enumerates subparts

    If input subparts is defined, then it should contain queryset of 
    question subparts (used to avoid repeating database query).
    Otherwise, a database query is made to determine question subparts

    Modifies render_results to add the following to the dictionary
    - include_solution_link: if exists and set to true, then user
      has permission to view solution of question and a solution exists.   
      In addition, if assessment is specified, then user must also have
      permission to view solution of assessment for include_solution_link
      to be set to true.
    - reference_pages: a list of pages relevant to the question
    - hint_text: rendered hint text.
    - help_available: true if there is help (hint or links to page/solution)
    - hint_template_error: true if error rendering hint text of either
      main part of question or any subparts.
    - to each subpart dicionary, render_results['subparts'][i]
      the following are added:
      - reference_pages: a list of pages relevant to the subpart
      - hint_text: rendered hint text
      - include_solution_link: exists and is true if user has permission to
        view solution (see above) and solution to subpart exists.
      - help_available: true if there is help for subpart

    """
    question = question_data['question']

    template_string_base = "{% load testing_tags mi_tags humanize %}"
    expr_context = question_data['expression_context']
    hint_template_error=False
   
    # solution is visible if user has permisions for question and, 
    # in the case when the question is part of an assessment, 
    # also has permissions for assessment
    solution_visible = False
    if question_data.get('user') and \
            question.user_can_view(question_data['user'],solution=True):
        if question_data.get('assessment'):
            if question_data['assessment'].user_can_view(question_data['user'],
                                                         solution=True):
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

        # reference page is considered for subpart if it matches 
        # the subpart letter
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
            except Exception as e:
                subpart_dict['hint_text'] = \
                    'Error in hint text template: %s' % e
                hint_template_error=True
            help_available=True
        subpart_dict['help_available']=help_available

    help_available=False

    # If subparts are present, then only pages with no subpart listed
    # are added to main reference_pages list.
    # (References pages marked with non-existent subpart are not visible)
    if subparts_present:
        render_results['reference_pages'] = \
            [rpage.page for rpage in question.questionreferencepage_set\
                 .filter(question_subpart=None)]

    # If question does not contain subparts, then show all reference_pages
    # in the main list, regardless of any marking for a particular subpart
    else:
        render_results['reference_pages'] = \
            [rpage.page for rpage in question.questionreferencepage_set.all()]
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


def render_question(question, seed=None, solution=False, 
                    question_identifier="",  question_set=None, 
                    user=None, show_help=True,
                    assessment=None, assessment_seed=None, 
                    pre_answers=None, readonly=False, auto_submit=False, 
                    allow_solution_buttons=False,
                    applet_counter=0):

    """
    Render question or solution by compiling text in expression context

    The rendering of the question is done in three steps
    1.  Evaluate all expressions to create the expression context
    2.  Render templates of question or solution text, including subparts
    3.  If question is computer graded, set up conditions for submitting
        and recording answer.

    

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
    if context_results.get('failed_conditions'):
        results = {
            'success': False,
            'error_message': mark_safe(
                '<p>'+context_results['failed_condition_message']+'</p>'),
            'question_text': mark_safe(
                "<p>Question cannot be displayed"
                + " due to failed condition.</p>")
        }
        return results

    # probably can remove some of these from question_data
    # if only need to put into the html for computer grading
    question_data = {
        'question': question, 'identifier': question_identifier,
        'seed': seed, 'question_set': question_set,
        'show_help': show_help, 'user': user,
        'readonly': readonly, 'precheck': precheck,
        'pre_answers': pre_answers, 
        'expression_context': context_results['expression_context'],
        }

    # applet_data will be used to gather information about applets
    # included in templates.  Applets should add to javascript item
    # with key given by applet code (to avoid collisions)
    # Add to context with key _applet_data_ to avoid overwriting expressions
    applet_data={}
    applet_data['counter']=applet_counter
    applet_data['javascript'] = {}
    question_data['expression_context']['_applet_data_'] = applet_data
    question_data['applet_data']=applet_data

    # answer data to keep track of
    # 1. possible answer_codes that are valid
    # 2. the answer_codes that actually appear in the question
    # 3. the multiple choices that actually appear in the question
    answer_data = { 'answer_codes': answer_code_list(question),
                    'answer_blank_codes': {},
                    'answer_blank_points': {},
                    'multiple_choice_in_question': [],
                    'question_identifier': question_identifier,
                    }

    question_data['expression_context']['_answer_data_']= answer_data

    results = render_question_text(question_data, solution=solution)

    question_data.update(results)

    question_data['error_message'] = ''

    # If error in expressions or in rendering,
    # still show as much of the question as was processed.
    # However, don't give opportunity to submit answer
    if question_data.get('render_error') \
            or context_results.get('error_in_expressions'):

        question_data['success']=False
        if context_results.get('error_in_expressions'):
            errors = context_results['expression_error']
            for expr in errors.keys():
                question_data['error_message'] += '<li>' + \
                    re.sub(r"\n", r"<br/>", errors[expr]) + '</li>'
        if question_data.get('render_error'):
            for error_message in question_data["render_error_messages"]:
                question_data['error_message'] += \
                    '<li>%s</li>' % error_message

        question_data['error_message'] = mark_safe(\
            "<ul>" + question_data['error_message'] + "</ul>")
        return question_data

    question_data['success'] = True

    # if computer graded, then,
    # - add submit button and show help via buttons (unless auto_submit)
    # - set up computer grade data, which
    if question.computer_graded:

        # if computer, include submit button
        # and show help via buttons (so can record if view hint/solution)
        question_data['submit_button'] = question.computer_graded and not precheck
        question_data['help_as_buttons'] = question.computer_graded

        assessment_code = assessment.code if assessment else None

        computer_grade_data = {'seed': seed, 'identifier': question_identifier, 
                               'record': not precheck, 
                               'allow_solution_buttons': allow_solution_buttons}
        if assessment:
            computer_grade_data['assessment_code'] = assessment.code
            computer_grade_data['assessment_seed'] = assessment_seed,
        if question_set is not None:
            computer_grade_data['question_set'] = question_set

        computer_grade_data['answer_blank_codes'] \
            = answer_data['answer_blank_codes']
        computer_grade_data['answer_blank_points'] \
            = answer_data['answer_blank_points']
        computer_grade_data['applet_counter'] = applet_data["counter"]

        # convert data to url parameter format so can append to the 
        # serialized form output
        import pickle
        import base64
        question_data['computer_grade_data'] = \
            base64.b64encode(pickle.dumps(computer_grade_data))

    return question_data

