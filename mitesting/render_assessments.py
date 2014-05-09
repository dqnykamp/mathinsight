from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.template import TemplateSyntaxError, Context, Template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
import random
import json 
import re
import sys

"""
Change to deal with:
Javascript for solution applets not inserted
Multiple choice changed
Identifier changed

"""

def get_new_seed():
    return str(random.randint(0,1E8))

 
def setup_expression_context(question):
    """
    Set up the question context by parsing all expressions for question.
    Returns context that contains all evaluated expressions 
    with keys given by the expression names.

    Before evaluating expressions, initializes global dictionary
    with allowed sympy commands for the question.

    Random expressions are based on state of random.
    Its state can be set via random.seed(seed).

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


def return_valid_answer_codes(question, expression_context): 
    """
    Return a dictionary of all the valid answer codes from the answer options.
    of question.  For an expression to valid, it must be in expression_context.

    If an answer code appears multiple times, the last instances
    takes precedence.

    Also, returns list of expressions not found in expression context
    """
    
    from mitesting.models import QuestionAnswerOption

    valid_answer_codes = {}
    invalid_answers = []
    for option in question.questionansweroption_set.all():

        if option.answer_type==QuestionAnswerOption.EXPRESSION and \
                option.answer not in expression_context:
            invalid_answers.append(
                "(%s, %s)" % (option.answer_code, option.answer))
        else:
            valid_answer_codes[option.answer_code] = option.answer_type

    if invalid_answers:
        if len(invalid_answers) > 1:
            invalid_answers = ["Invalid answer codes: " + \
                                   ", ".join(invalid_answers),]
        else:
            invalid_answers = ["Invalid answer code: " +  invalid_answers[0],]

    return (valid_answer_codes, invalid_answers)


def render_question_text(render_data, solution=False):
    """
    Render the question text and subparts as Django templates.
    Use context specified by expression context and load in custom tags
    Optionally render "need help" information.

    Input question data is a dictionary with the following keys
    - question: the question to be rendered
    - expression_context: the template context used to render the text
    - show_help (optional): if true, render the "need help" information
    
    Return render_results dictionary with the following:
    - question: the question that was rendered
    - rendered_text: the results from rendering the main question text 
    - render_error: exists and true on error rendering the template
    - subparts: a list of dictionaries of results from rendering subparts
      Each dictionary has the following keys:
      - letter: the letter assigned to the supart
      - rendered_text: the results from rendering the subpart text
      - render_error: exists and true on error rendering the template
    If show_help is true, then render_results also contains;
    - reference_pages: a list of pages relevant to the question
    - hint_text: rendered hint text
    - help_available: true if there is help (hint or links to pages)
    - hint_template_error: true if error rendering hint text
    - to each subpart dicionary, the following are added:
      - reference_pages: a list of pages relevant to the subpart
      - hint_text: rendered hint text
      - help_available: true if there is help for subpart
    """

    question = render_data['question']
    expr_context = render_data['expression_context']

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
            if isinstance(e,TemplateSyntaxError):
                message = str(e)
            else:
                message = "%s: %s" % (type(e).__name__, e)
            if solution:
                render_results['rendered_text'] = \
                    mark_safe("<p>Error in solution</p>")
                render_results['render_error_messages'].append(
                    mark_safe("Error in solution template: %s" % message))
            else:
                render_results['rendered_text'] = \
                    mark_safe("<p>Error in question</p>")
                render_results['render_error_messages'].append(
                    mark_safe("Error in question template: %s" % message))
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
                subpart_dict['rendered_text'] = \
                    mark_safe(Template(template_string).render(expr_context))
            except Exception as e:
                if solution:
                    subpart_dict['rendered_text'] = \
                        mark_safe("Error in solution subpart")
                    render_results['render_error_messages'].append(
                        mark_safe("Error in solution subpart %s template: %s" 
                                  % (subpart_dict["letter"],e)))
                else:
                    subpart_dict['rendered_text'] = \
                        mark_safe("Error in question subpart")
                    render_results['render_error_messages'].append(
                        mark_safe("Error in question subpart %s template: %s" 
                                  % (subpart_dict["letter"],e)))
                render_results['render_error'] = True
        else:
            subpart_dict["rendered_text"] = ""
                
        render_results['subparts'].append(subpart_dict)

    # add help data to render_results
    # if show_help is set to true and not solution
    if render_data.get('show_help') and not solution:
        add_help_data(render_data, render_results, subparts)

    return render_results


def add_help_data(render_data, render_results, subparts=None):
    """
    Add hints and references pages to render_results
    
    Input render_data is a dictionary with the following keys
    - question: the question to be rendered
    - expression_context: the template context used to render the text

    Input render_results is a dictionary.
    If question contains subparts, then
    render_results['subparts'][i]
    is a dictionary for each i that enumerates subparts

    If input subparts is defined, then it should contain queryset of 
    question subparts (used to avoid repeating database query).
    Otherwise, a database query is made to determine question subparts

    Modifies render_results to add the following to the dictionary
    - reference_pages: a list of pages relevant to the question
    - hint_text: rendered hint text.
    - help_available: true if there is help (hint or links to page)
    - hint_template_error: true if error rendering hint text of either
      main part of question or any subparts.
    - to each subpart dicionary, render_results['subparts'][i]
      the following are added:
      - reference_pages: a list of pages relevant to the subpart
      - hint_text: rendered hint text
      - help_available: true if there is help for subpart

    """
    question = render_data['question']

    template_string_base = "{% load testing_tags mi_tags humanize %}"
    expr_context = render_data['expression_context']
    hint_template_error=False
   

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
                    question_identifier="",
                    user=None, show_help=True,
                    assessment=None, question_set=None, 
                    assessment_seed=None, 
                    prefilled_answers=None, 
                    readonly=False, auto_submit=False, 
                    record_answers=True,
                    allow_solution_buttons=False,
                    applet_counter=0):

    """
    Render question or solution by compiling text in expression context

    The rendering of the question is done in three steps
    1.  Evaluate all expressions to create the expression context
    2.  Render templates of question or solution text, including subparts
    3.  If question is computer graded, set up conditions for submitting
        and recording answer.

    Input arguments
    - question: the Question instance to be rendered
    - seed: the random generator seed
      Used for setting up the expression context.
      If seed is none, then randomly generate a seed, recording the new
      seed so that exact version can be reproduced by passing seed in
    - solution: if true, generate the solution.  Else generate the question.
    - question_identifier: should be a string that uniquely identifies
      this particular question among any others on the page
    - user: a User instance.  Used to determine if solution is viewable
      and for recording answers of computer graded questions
    - show_help: if true, show help (hints and reference pages).
    - assessment: if not None, indicates the Assessment instance
      in which question is being rendered.  Used to determine if solution is
      visible and for recording answers of computer graded questions
    - question_set: which assessment question_set the question belongs to.
      Used for recording answers of computer graded questions
    - assessment_seed: which assessment seed was used to generate assessment.
      Used for recording answers of computer graded questions
    - prefilled_answers: a list containing answers for answer blanks.
      Useful for redisplaying student answers
    - readonly: if true, then all answer blanks are readonly.
      Useful with prefilled answers.
    - auto_submit: automatically submit answers (instead of submit button)
      Useful with prefilled answers
    - record_answers: if true, record answer upon submit
    - allow_solution_buttons: if true, allow a solution button to be displayed
      on computer graded questions
    - applet_counter: still need to see how this is needed

    The output is a question_data dictionary.  With the exception of
    question, success, rendered_text, and error_message, all entries
    are optional.  The entries are
    - question: the question that was rendered
    - success: true if question rendered without errors.
      If false, rendered text will still show as much of the question
      as was processed, but submit_button will not be set
    - error_message: text explaining all errors encountered
    - rendered_text: the results from rendering the main question text 
    - subparts: a list of dictionaries of results from rendering subparts
      Each dictionary has the following keys:
      - letter: the letter assigned to the supart
      - rendered_text: the results from rendering the subpart text
      - help_available: true if there is help for subpart
      - reference_pages: a list of pages relevant to the subpart
      - hint_text: rendered hint text
   - help_available: true if there is help (hint or links to pages).
      If help_available, then the following
      - reference_pages: a list of pages relevant to the question
      - hint_text: rendered hint text
      - hint_template_error: true if error rendering hint text
    - applet_data: dictionary of information about applets embedded in text
    - identifier: the passed in string to identify the question
    - seed: the random number generator seed used to generate question
    - auto_submit: if true, automatically submit answers upon page load
    - submit_button: if true, include button to submit for computer grading
    - show_solution_button: if exists and set to true, then display a
      button to show the solution.  For show_solution_button to be true, 
      allow_solution_button must be true, the user must have permission 
      to view solution of question, and a solution must exist.
      In addition, if assessment is specified, then user must also have
      permission to view solution of assessment for show_solution_button
      to be set to true.
    - enable_solution_button: true if solution button should be enabled
      at the outset.  (Set true if not computer graded.)
    - inject_solution_url: url from which to retrieve solution
    - computer_grade_data: a pickled and base64 encoded dictionary of 
      information about the question to be sent to server with submission
      of results for computer grading.  Some entries are identical to above:
      - seed
      - identifier
      - show_solution_button
      - record_answers
      - question_set
      - assessment_seed
      - assessment_code (of assessment from input)
      - answer_data: codes, points, and answer type of the answers in question
      - applet_counter: number of applets encountered so far 
        (not sure if need this)
   """

    if seed is None:
        seed=get_new_seed()

    random.seed(seed)

    # first, setup context due to expressions from question
    context_results = setup_expression_context(question)

    # if failed condition, then don't display the question
    # but instead give message that condition failed
    if context_results.get('failed_conditions'):
        question_data = {
            'question': question,
            'success': False,
            'error_message': mark_safe(
                '<p>'+context_results['failed_condition_message']+'</p>'),
            'rendered_text': mark_safe(
                "<p>Question cannot be displayed"
                + " due to failed condition.</p>")
        }
        return results

    render_data = {
        'question': question, 'show_help': show_help, 
        'expression_context': context_results['expression_context'],
        'user': user, 'assessment': assessment
        }

    # applet_data will be used to gather information about applets
    # included in templates.  Applets should add to javascript item
    # with key given by applet code (to avoid collisions)
    # Add to context with key _applet_data_ to avoid overwriting expressions
    applet_data={}
    applet_data['counter']=applet_counter
    applet_data['javascript'] = {}
    render_data['expression_context']['_applet_data_'] = applet_data

    # answer data to keep track of
    # 1. possible answer_codes that are valid
    # 2. the answer_codes that actually appear in the question
    # 3. the multiple choices that actually appear in the question
    (valid_answer_codes, invalid_answers) = return_valid_answer_codes(
        question, render_data['expression_context'])

    answer_data = { 'valid_answer_codes': valid_answer_codes,
                    'answer_data': {},
                    'question': question,
                    'question_identifier': question_identifier,
                    'prefilled_answers': prefilled_answers,
                    'readonly': readonly,
                    'error': bool(invalid_answers),
                    'answer_errors': invalid_answers,
                    }

    render_data['expression_context']['_answer_data_']= answer_data

    question_data = render_question_text(render_data, solution=solution)

    question_data.update({
            'applet_data': applet_data,
            'identifier': question_identifier,
            'seed': seed,
            'auto_submit': auto_submit,
            })

    # if have prefilled answers, check to see that the number matches the
    # number of answer blanks (template tag already checked if
    # the answer_codes matched for those answers that were found)
    if prefilled_answers:
        if len(prefilled_answers) != len(answer_data["answer_data"]):
            answer_data["error"]=True
            answer_data["answer_errors"].append(
                "Invalid number of previous answers")
    

    # If render or expression error, combine all error messages
    # for display in question template.
    question_data['error_message'] = ''

    if question_data.get('render_error') \
            or context_results.get('error_in_expressions')\
            or answer_data.get('error'):

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
            del question_data['render_error']
        if answer_data.get('error'):
            for error_message in answer_data['answer_errors']:
                question_data['error_message'] += \
                    '<li>%s</li>' % error_message

        question_data['error_message'] = mark_safe(\
            "<ul>" + question_data['error_message'] + "</ul>")

    else:
        question_data['success'] = True



    # if allow_solution_buttons is true, then determine if
    # solution is visible to user (ie. user has permissions)
    # and solution exists
    
    # solution is visible if user has permisions for question and, 
    # in the case when the question is part of an assessment, 
    # also has permissions for assessment 
    # (not adjusted for privacy of other questions)

    show_solution_button = False
    if allow_solution_buttons:
    
        solution_visible = False
        if render_data.get('user') and \
                question.user_can_view(user=render_data['user'],solution=True):
            if render_data.get('assessment'):
                if render_data['assessment'].user_can_view(
                    user=render_data['user'], solution=True,
                    include_questions=False):
                    solution_visible=True
            else:
                solution_visible=True

        if solution_visible:
            # check if solution text exists in question or a subpart
            solution_exists=bool(question.solution_text)
            if not solution_exists:
                for subpart in question.questionsubpart_set.all():
                    if subpart.solution_text:
                        solution_exists = True
                        break

            if solution_exists:
                show_solution_button=True

    question_data['show_solution_button']=show_solution_button
    if show_solution_button:
        question_data['inject_solution_url'] = reverse(
            'mit-injectquestionsolution', kwargs={'question_id': question.id})
        question_data['enable_solution_button'] = not question.computer_graded

    # if error or rendering a solution 
    # return without adding computer grading data
    if not question_data['success'] or solution:
        return question_data
    
    # if computer graded and answer data available,
    # add submit button (unless auto_submit)
    question_data['submit_button'] = question.computer_graded and\
        answer_data['answer_data'] and (not auto_submit)

    # set up computer grade data to be sent back to server on submit
    # computer grade data contains
    # - information about question (seed, identifier)
    # - information on grading (record answer and allow solution buttons)
    # - information about assessment (code, seed, and question_set)
    # - information about answer blanks found in template (codes and points)
    # - number of applets encountered so far (not sure if need this)

    computer_grade_data = {'seed': seed, 'identifier': question_identifier, 
                           'record_answers': record_answers,
                           'show_solution_button': show_solution_button}
    if assessment:
        computer_grade_data['assessment_code'] = assessment.code
        computer_grade_data['assessment_seed'] = assessment_seed
        if question_set is not None:
            computer_grade_data['question_set'] = question_set

    if answer_data['answer_data']:
        computer_grade_data['answer_data'] \
            = answer_data['answer_data']

    computer_grade_data['applet_counter'] = applet_data["counter"]

    # serialize and encode computer grade data to facilitate appending
    # to post data of http request sent when submitting answers
    import pickle, base64
    question_data['computer_grade_data'] = \
        base64.b64encode(pickle.dumps(computer_grade_data))

    return question_data



def get_question_list(assessment):
    """
    Return list of questions for assessment, one for each question_set.
    Questions are chosen randomly based on state of random.
    Its state can be set via random.seed(seed).

    Each question is randomly assigned a seed, which is to be used
    generate the question and/or solution, ensuring that question
    and solution will match.

    Return a list of dictionaries, one for each question. 
    Each dictionary contains the following:
    - question_set: the question_set from which the question was drawn
    - question: the question chosen
    - points: the number of points the question set is worth
    - seed: the seed to use to render the question
    """

    question_list = []

    for question_set in assessment.question_sets():
        questions_in_set = assessment.questionassigned_set.filter(
            question_set=question_set)

        the_question=random.choice(questions_in_set).question

        # generate a seed for the question
        # so that can have link to this version of question and solution
        question_seed=get_new_seed()
        the_points = assessment.points_of_question_set(question_set)
        if the_points is None:
            the_points = ""    
        question_list.append({'question_set': question_set,
                              'question': the_question,
                              'points': the_points,
                              'seed': question_seed}
                             )

    return question_list
            


def render_question_list(assessment, seed=None, user=None, solution=False,
                         current_attempt=None):
    """
    Generate list of rendered questions or solutions for assessment.

    After initializing random number generator with seed
    (or generating a new seed if seed was None),
    from each question set, randomly pick a question and a question seed,
    render the question, determine score on this attempt of assessment,
    and determine question group.  If assessment is not set to fixed order,
    randomly order the chosen assessments, keeping questions in the same
    group together.
    

    Inputs:
    - assessment: the assessment to be rendered
    - seed: random number generator seed to generate assesment and questions
    - user: the logged in user
    - solution: True if rendering solution
    - current_attempt: information about score so far on computer scored
      assessments (need to fix and test)

    Outputs:
    - seed that used to generate assessment (the input seed unless it was None)
    - question_list.  List of dictionaries, one per question, giving
      information about the question.  Each dictionary contains:
      - question_set: the question_set from which the question was drawn
      - question: the question chosen
      - points: the number of points the question set is worth
      - seed: the seed to use to render the question
      - question_data: dictionary containing the information needed to
        display the question with question_body.html template.
        This dictionary is what is returned by render_question.
      - current_credit: the percent credit achieved in current attempt
      - current_score: the score (points) achieved in the current attempt
      - group: the group the question set belongs to
      - previous_same_group: true if the previous question if from the
        same question group as the current question
        (Used as indicator for templates that questions belong together.)
    """

    if seed is None:
        seed=get_new_seed()
        
    random.seed(seed)
    question_list = get_question_list(assessment)

    applet_counter=0
    for (i, question_dict) in enumerate(question_list):

        # use qa for identifier since coming from assessment
        identifier="qa%s" % i

        question = question_dict['question']
        question_set = question_dict['question_set']

        question_data = render_question(
            question, seed=question_dict["seed"],solution=solution,
                question_identifier=identifier,
                user=user, show_help=not solution,
                assessment=assessment, question_set=question_set,
                assessment_seed=seed, 
                record_answers=True,
                allow_solution_buttons=assessment.allow_solution_buttons,
                applet_counter=applet_counter)
        applet_counter = question_data['applet_data']['counter']
        
        question_dict['question_data']=question_data

        # if have a latest attempt, look for maximum score on question_set
        current_score=None
        if current_attempt:
            try:
                current_credit =current_attempt\
                    .get_percent_credit_question_set(question_set)
                if question_dict['points']:
                    current_score = current_credit\
                        *question_dict['points']/100
                else:
                    current_score=0
            except ObjectDoesNotExist:
                current_credit = None
        else:
            current_credit = None

        question_dict['current_score']=current_score
        question_dict['current_credit']=current_credit

        try:
            question_group = assessment.questionsetdetail_set.get\
                (question_set=question_set).group
        except ObjectDoesNotExist:
            question_group = ''
        
        question_dict["group"] = question_group
        question_dict["previous_same_group"] = False


    if assessment.fixed_order:
        for i in range(1, len(question_list)):
            the_group = question_list[i]["group"]
            # if group is not blank and the same as previous group
            # make as belonging to same group as previous question
            if the_group and question_list[i-1]["group"] == the_group:
                    question_list[i]["previous_same_group"] = True
        return question_list, seed

    # if not fixed order randomly shuffle questions
    # keep questions with same group together
    # i.e., first random shuffle groups, 
    # then randomly shuffle questions within each group
    # set 'previous_same_group' if previous question is from the same group

    # create list of the groups, 
    # adding unique groups to questions with no group
    question_set_groups = {}
    for (ind,q) in enumerate(question_list):
        question_group = q['group']
        if question_group in question_set_groups:
            question_set_groups[question_group].append(ind)
        elif question_group:
            question_set_groups[question_group] = [ind]
        else:
            unique_no_group_name = '_no_group_%s' % ind
            question_set_groups[unique_no_group_name] = [ind]
            q['group']=unique_no_group_name

    # create list of randomly shuffled groups
    groups = question_set_groups.keys()
    random.shuffle(groups)

    # for each group, shuffle questions,
    # creating cummulative list of the resulting question index order
    question_order =[]
    for group in groups:
        group_indices=question_set_groups[group]
        random.shuffle(group_indices)
        question_order += group_indices

    # shuffle questions based on that order
    # also check if previous question is from same group
    question_list_shuffled =[]
    previous_group = 0
    for i in question_order:
        q=question_list[i]
        this_group = q['group']
        if this_group == previous_group:
            previous_same_group = True
        else:
            previous_same_group = False
        q['previous_same_group'] = previous_same_group
        previous_group = this_group
        question_list_shuffled.append(q)

    return question_list_shuffled, seed

