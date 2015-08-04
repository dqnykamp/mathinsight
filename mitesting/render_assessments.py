from django.template import TemplateSyntaxError, Context, Template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
import json 
import re
import sys
import logging

logger = logging.getLogger(__name__)

"""
Change to deal with:
Javascript for solution applets not inserted
Multiple choice changed
Identifier changed

"""

def get_new_seed(rng):
    return str(rng.randint(0,1E8))

 
def setup_expression_context(question, rng, seed=None, user_responses=None):
    """
    Set up the question context by parsing all expressions for question.
    Returns context that contains all evaluated expressions 
    with keys given by the expression names.

    Before evaluating expressions, initializes global dictionary
    with allowed sympy commands for the question.

    Random expressions are based on state of random instance rng set by seed.
    If multiple attempts are required to meet all conditions,
    new values of seed are randomly generated for each attempt.
    The successful seed is returned.

    The first step is to evaluate normal expressions, i.e., those that
    have not been flagged as post user response.

    user_responses is a list of dictionaries of user responses to answers
    embedded in the question.  If any answers have been marked to be
    asssigned to expressions, the second step is to parse those responses
    using user_function_dict for local_dict and assign the result
    to the corresponding expression.

    The third step is to evaluate any expressions flagged as being 
    post user response.

    Both the local_dict and user_function_dict are added to the
    expression context.

    In addition, if some expressions were EXPRESSION_WITH_ALTERNATES,
    then the following are created:
    - alternate_dicts: a list of local_dicts with different alternates
    - alternate_exprs: a dictionary indexed by expression name, where each
      entry is a list of alternate versions of the expression.  This will 
      be created starting with the first EXPRESSION_WITH_ALTERNATES,
      and will continue being created for all subsequent expressions. 
    - alternate_funcs: a dictionary indexed by expression name, where each
      entry is a list of alternate versions of a FUNCTION.  This will be
      created for all FUNCTIONS once the first EXPRESSION_WITH_ALTERNATES
      is encountered.
    These lists and dictionaries are added to the expression context.

    Return a dictionary with the following:
    - expression_context: a Context() with mappings from the expressions
    - error_in_expressions: True if encountered any errors in normal expressions
    - error_in_expressions_post_user: the same but for post user expressions
    - expression_error: dictionary of error messages from normal expressions
    - expression_error_post_user: the same but for post user expressions
    - failed_conditions: True if failed conditions for all attempts
    - failed_condition_message: message of which expression last failed
    - seed: seed used in last attempt to generate contenxt

    """

    if seed is None:
        seed=get_new_seed(rng)

    rng.seed(seed)

    max_tries=500
    success=False

    failed_condition_message=""
    failed_conditions=True

    for i in range(max_tries):

        if i>0:
            seed=get_new_seed(rng)
            rng.seed(seed)

        expression_context = Context({})
        random_group_indices={}
        error_in_expressions = False
        expression_error = {}

        # initialize global dictionary using the comamnds
        # found in allowed_sympy_commands.
        # Also adds standard symbols to dictionary.
        local_dict = question.return_sympy_local_dict()
        user_function_dict = question.return_sympy_local_dict(
            user_response=True)
        alternate_dicts = []
        alternate_exprs = {}
        alternate_funcs = {}
        try:

            from mitesting.models import Expression
            # first processes the expressions that aren't flagged
            # as post user response
            for expression in question.expression_set\
                                      .filter(post_user_response=False):
                try:
                    evaluate_results=expression.evaluate(
                        local_dict=local_dict, 
                        user_function_dict=user_function_dict,
                        alternate_dicts = alternate_dicts, 
                        random_group_indices=random_group_indices,
                        rng=rng)

                # on FailedCondition, reraise to stop evaluating expressions
                except Expression.FailedCondition:
                    raise

                # for any other exception, record exception and
                # allow to continue processing expressions
                except Exception as exc:
                    error_in_expressions = True
                    expression_error[expression.name] = str(exc)
                    expression_context[expression.name] = '??'
                else:
                    # if random word, add singular and plural to context
                    if expression.expression_type == expression.RANDOM_WORD:
                        expression_evaluated\
                            =evaluate_results['expression_evaluated']
                        expression_context[expression.name] \
                            = expression_evaluated[0]
                        expression_context[expression.name + "_plural"] \
                            = expression_evaluated[1]
                    else:
                        expression_context[expression.name] \
                            = evaluate_results['expression_evaluated']
                        # the following lists will be empty until the
                        # first EXPRESSION_WITH_ALTERNATES is encountered
                        alternate_exprs[expression.name] \
                            = evaluate_results['alternate_exprs']
                        alternate_funcs[expression.name] \
                            = evaluate_results['alternate_funcs']

                        the_expr = expression_context[expression.name]


            # if make it through all expressions without encountering
            # a failed condition, then record fact and
            # break out of loop
            failed_conditions = False
            break

        # on FailedCondition, continue loop, but record
        # message in case it is final pass through loop
        except Expression.FailedCondition as exc:
            failed_condition_message = exc.args[0]

    # add state to expression context as convenience to 
    # reset state if not generating regular expression
    # Also, sympy global dict is accessed from template tags
    expression_context['_sympy_local_dict_'] = local_dict
    expression_context['_user_function_dict_'] = user_function_dict
    expression_context['_alternate_dicts_'] = alternate_dicts
    expression_context['_alternate_exprs_'] = alternate_exprs
    expression_context['_alternate_funcs_'] = alternate_funcs

    error_in_expressions_post_user = False
    expression_error_post_user = {}

    # if haven't failed conditions, process user responses and 
    # expressions flagged as post user response
    if not failed_conditions:
        # next processes any user responses
        # that are assigned to expressions
        from mitesting.sympy_customized import EVALUATE_NONE
        from mitesting.math_objects import math_object
        from mitesting.sympy_customized import parse_and_process
        from sympy import Symbol, Dummy

        from mitesting.models import QuestionAnswerOption
        import pickle, base64

        # ExpressionFromAnswer contains information about any
        # answers that were assigned to expressions
        for expression in question.expressionfromanswer_set.all():
            # will assign Dummy(default_value) if no response given for answer
            # or if error in parsing respons
            default_value= re.sub('_long_underscore_', '\uff3f',
                                  expression.default_value)

            math_expr= Dummy(default_value)

            answer_number=expression.answer_number
            try:
                response=user_responses[answer_number-1]
            except (IndexError, TypeError):
                pass
            else:
                if response['code']==expression.answer_code:
                    if expression.answer_type==\
                       QuestionAnswerOption.MULTIPLE_CHOICE:
                        mc_dict=pickle.loads(base64.b64decode(expression.answer_data))
                        try:
                            response_text=mc_dict[int(response['answer'])]
                        except (ValueError, KeyError):
                            response_text=default_value
                        math_expr=Symbol(response_text)
                    else:
                        try:
                            math_expr =  parse_and_process(
                                response['answer'], 
                                local_dict=user_function_dict, 
                                split_symbols=\
                                expression.split_symbols_on_compare,
                                evaluate_level=EVALUATE_NONE,
                                assume_real_variables=expression.real_variables,
                                parse_subscripts = expression.parse_subscripts
                            )
                        except:
                            pass
            # add expression to local_dict and any alternate_dicts
            # that may have been created.
            local_dict[expression.name]=math_expr
            for alt_dict in alternate_dicts:
                alt_dict[expression.name]=math_expr
            # add to context 
            expression_context[expression.name] = \
                math_object(math_expr, evaluate_level=EVALUATE_NONE)

        # last, process expressions flagged as post user response
        for (i, expression) in enumerate(question.expression_set\
                                  .filter(post_user_response=True)):
            try:
                evaluate_results=expression.evaluate(
                    local_dict=local_dict, 
                    user_function_dict=user_function_dict,
                    alternate_dicts=alternate_dicts,
                    random_group_indices=random_group_indices,
                    rng=rng)

            # record exception and allow to continue processing expressions
            except Exception as exc:
                error_in_expressions_post_user = True
                expression_error_post_user[expression.name] = str(exc)
                expression_context[expression.name] = '??'
            else:
                expression_context[expression.name] \
                    = evaluate_results['expression_evaluated']
                # the following lists will be empty until the
                # first EXPRESSION_WITH_ALTERNATES is encountered
                alternate_exprs[expression.name] \
                    = evaluate_results['alternate_exprs']
                alternate_funcs[expression.name] \
                    = evaluate_results['alternate_funcs']


    results = {
        'error_in_expressions': error_in_expressions,
        'expression_error': expression_error,
        'error_in_expressions_post_user': error_in_expressions_post_user,
        'expression_error_post_user': expression_error_post_user,
        'failed_conditions': failed_conditions,
        'failed_condition_message': failed_condition_message,
        'expression_context': expression_context,
        'seed': seed,
        }


    return results


def return_valid_answer_codes(question, expression_context): 
    """
    For question and expression_content, determine valid answer codes 
    and their answer types (where type is from last instance of answer code).
    Also determine any invalid answer options
    
    Returns a tuple with the following three components:

    1. A dictionary of all the valid answer codes 
       from the answer options of question.  
       The dictionary keys are the answer_codes and
       the values are a dictionary of the answer_types, split symbols,
       and expression_type.

       In the case that the answer is a QuestionAnswerOption.EXPRESSION, 
       it must be in expression_context.
       In the case that the answer is a QuesitonAnswerOption.FUNCTION,
       the answer in expression_context must be a Expression.FUNCTION

    2. A list of tuples (answer_codes, answer) from any invalid answer options

    3. A list error messages for any invalid answer options
 

    """
    
    from mitesting.models import QuestionAnswerOption, Expression
    from mitesting.utils import ParsedFunction
    valid_answer_codes = {}
    invalid_answers = []
    invalid_answer_messages = []
    for option in question.questionansweroption_set.all():

        answer_valid=True
        if option.answer_type==QuestionAnswerOption.EXPRESSION:
            if option.answer not in expression_context:
                answer_valid=False
                error_message =  "Invalid answer option of expression type with code <tt>%s</tt>: " % option.answer_code
                error_message += "answer <tt>%s</tt> is not the name of an expression." % option.answer

        elif option.answer_type==QuestionAnswerOption.FUNCTION:
            try:
                expression = expression_context['_sympy_local_dict_']\
                             [option.answer]
            except KeyError:
                answer_valid=False
                error_message =  "Invalid answer option of function type with code <tt>%s</tt>: " % option.answer_code
                error_message += "answer <tt>%s</tt> is not the name of an expression." % option.answer
            else:
                try:
                    is_function=issubclass(expression, ParsedFunction)
                except TypeError:
                    is_function=False
                if not is_function:
                    answer_valid=False
                    error_message =  "Invalid answer option of function type with code <tt>%s</tt>: " % option.answer_code
                    error_message += "expression <tt>%s</tt> is not a function." % option.answer
           
        if answer_valid:
            if option.answer_code not in valid_answer_codes:
                valid_answer_codes[option.answer_code] = \
                    {'answer_type': option.answer_type,
                     'split_symbols_on_compare': option.split_symbols_on_compare }
                try:
                    expression_type=expression_context[option.answer]\
                        .return_expression_type()
                except (KeyError,AttributeError):
                    pass
                else:
                    valid_answer_codes[option.answer_code]['expression_type'] \
                        = expression_type
        else:
            invalid_answers.append((option.answer_code, option.answer))
            invalid_answer_messages.append(error_message)

    return (valid_answer_codes, invalid_answers, invalid_answer_messages)

def return_new_answer_data(rng=None):
    if not rng:
        import random
        rng=random.Random()
        
    return { 'valid_answer_codes': {},
                    'answer_info': [],
                    'question': None,
                    'question_identifier': "",
                    'prefilled_responses': [],
                    'error': False,
                    'answer_errors': [],
                    'readonly': False,
                    'rng': rng,
         }


def process_expressions_from_answers(question):

    # update expression from answers from question text and subparts
    # update dynamic text from question and solution text and subparts

    # just assume every answer code is valid 
    valid_answer_codes = {}
    for ao in question.questionansweroption_set.all():
        answer_dict = {'answer_type': ao.answer_type,
                       'split_symbols_on_compare':
                       ao.split_symbols_on_compare
        }
        valid_answer_codes[ao.answer_code]=answer_dict


    import random
    rng=random.Random()

    answer_data = return_new_answer_data(rng)
    answer_data['valid_answer_codes'] = valid_answer_codes
    answer_data['question']=question

    from midocs.functions import return_new_auxiliary_data
    auxiliary_data =  return_new_auxiliary_data()

    update_context = Context({'question': question, 
                              '_process_dynamictext': True,
                              '_dynamictext_object': question,
                              '_process_expressions_from_answers': True,
                              '_answer_data_': answer_data,
                              '_sympy_local_dict_': {},
                              '_auxiliary_data_': auxiliary_data,
                          })


    from dynamictext.models import DynamicText
    DynamicText.initialize(question)
    question.expressionfromanswer_set.all().delete()
    render_results=render_question_text(
        {'question': question, 'show_help': True,
         'expression_context': update_context,
     })


def render_question_text(render_data, solution=False):
    """
    Render the question text and subparts as Django templates.
    Use context specified by expression context and load in custom tags
    Optionally render "need help" information.

    Input render_data is a dictionary with the following keys
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
    template_string_base = "{% load testing_tags mi_tags dynamictext humanize %}"


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
        subpart_dict = {'letter': subpart.get_subpart_letter(), 'subpart': subpart }
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

    template_string_base = "{% load testing_tags mi_tags dynamictext humanize %}"
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

    # If subparts are present, then only pages with no single character subpart
    # listed are added to main reference_pages list.
    # (References pages marked with non-existent subpart are not visible)
    if subparts_present:
        render_results['reference_pages'] = \
            [rpage.page for rpage in question.questionreferencepage_set\
                 .exclude(question_subpart__range=("a","z"))]

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


def render_question(question, rng, seed=None, solution=False, 
                    question_identifier="",
                    user=None, show_help=True,
                    assessment=None, question_set=None, 
                    assessment_seed=None, 
                    prefilled_responses=None, 
                    readonly=False, auto_submit=False, 
                    record_answers=True,
                    allow_solution_buttons=False,
                    auxiliary_data=None,
                    show_post_user_errors=False,
                ):

    """
    Render question or solution by compiling text in expression context

    The rendering of the question is done in three steps
    1.  Evaluate all expressions to create the expression context
    2.  Render templates of question or solution text, including subparts
    3.  If question is computer graded, set up conditions for submitting
        and recording answer.

    Input arguments
    - question: the Question instance to be rendered
    - rng: the random number generator instance to use
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
    - prefilled_responses: a list containing respones for answer blanks.
      Useful for redisplaying student answers
    - readonly: if true, then all answer blanks are readonly.
      Useful with prefilled answers.
    - auto_submit: automatically submit answers (instead of submit button)
      Useful with prefilled answers
    - record_answers: if true, record answer upon submit
    - allow_solution_buttons: if true, allow a solution button to be displayed
      on computer graded questions
    - auxiliary_data: dictionary for information that should be accessible 
      between questions or outside questions.  Used, for example, 
      for information about applets and hidden sections embedded in text
    - show_post_user_errors: if true, display errors when evaluating
      expressions flagged as being post user response.  Even if showing
      errors, such an error does not cause the rendering success to be False

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
      - course_code (of assessment from input)
      - assessment_code (of assessment from input)
      - answer_info: list of codes, points, answer type, identifier, 
        group, assigned expression, prefilled answer, and expression type
        of the answers in question
      - applet_counter: number of applets encountered so far 
        (not sure if need this)
   """

    if seed is None:
        seed=get_new_seed(rng)

    rng.seed(seed)

    # first, setup context due to expressions from question.
    # include any prefilled responses to answers
    context_results = setup_expression_context(question, rng=rng, seed=seed,
                                        user_responses=prefilled_responses)

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
                + " due to failed condition.</p>"),
            'seed': seed,
        }
        return question_data

    # set seed to be successful seed from rendering context
    seed = context_results['seed']

    render_data = {
        'question': question, 'show_help': show_help, 
        'expression_context': context_results['expression_context'],
        'user': user, 'assessment': assessment
        }

    # Add auxiliary_data to context with key _auxiliary_data_
    # to avoid overwriting expressions
    render_data['expression_context']['_auxiliary_data_'] = auxiliary_data

    # set up dynamic text
    # context variables used for dynamic text tags
    from dynamictext.models import DynamicText
    render_data['expression_context']['_dynamictext_object']=question
    render_data['expression_context']['_dynamictext_instance_identifier']\
        = question_identifier
    # javascript used to update dynamic text
    num_dts = DynamicText.return_number_for_object(question)
    dynamictext_javascript=""
    for i in range(num_dts):
        dt = DynamicText.return_dynamictext(question,i)
        javascript_function=dt.return_javascript_render_function(
            mathjax=True, instance_identifier=question_identifier)
        dynamictext_javascript += "%s_dynamictext_update= %s\n" % \
                                  (dt.return_identifier(question_identifier),
                                   javascript_function)
    if dynamictext_javascript:
        dynamictext_javascript = mark_safe("\n<script>\n%s</script>\n" % \
                                           dynamictext_javascript)
        
    # answer data to keep track of
    # 1. possible answer_codes that are valid
    # 2. the answer_codes that actually appear in the question
    # 3. the multiple choices that actually appear in the question
    (valid_answer_codes, invalid_answers, invalid_answer_messages) =\
        return_valid_answer_codes(question, render_data['expression_context'])

    answer_data = { 'valid_answer_codes': valid_answer_codes,
                    'answer_info': [],
                    'question': question,
                    'question_identifier': question_identifier,
                    'prefilled_responses': prefilled_responses,
                    'readonly': readonly,
                    'error': bool(invalid_answers),
                    'answer_errors': invalid_answer_messages,
                    'rng': rng
                    }

    render_data['expression_context']['_answer_data_']= answer_data

    question_data = render_question_text(render_data, solution=solution)

    question_data.update({
        'identifier': question_identifier,
        'auto_submit': auto_submit,
        'seed': seed,
        'dynamictext_javascript': dynamictext_javascript,
    })

    # if have prefilled answers, check to see that the number matches the
    # number of answer blanks (template tag already checked if
    # the answer_codes matched for those answers that were found)
    # If so, log warning but otherwise ignore.
    if prefilled_responses:
        if len(prefilled_responses) != len(answer_data["answer_info"]):
            message = "Invalid number of previous responses.\nQuestion: %s"\
                      % question
            if assessment:
                message += "\nAssessment: %s" % assessment
            logger.warning(message)
    

    # If render or expression error, combine all error messages
    # for display in question template.
    question_data['error_message'] = ''

    question_data['success'] = True

    # errors from post user expression don't cause success to be marked as false
    # so that one can still submit new responses
    if (context_results.get('error_in_expressions_post_user')
        and show_post_user_errors):
        errors = context_results['expression_error_post_user']
        for expr in errors.keys():
            question_data['error_message'] += '<li>' + \
                    re.sub(r"\n", r"<br/>", errors[expr]) + '</li>'

    if question_data.get('render_error') \
            or context_results.get('error_in_expressions')\
            or answer_data.get('error'):
        # any other error trigger failure
        # which prevents responses from being submitted
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

    if question_data['error_message']:
        question_data['error_message'] = mark_safe(\
            "<ul>" + question_data['error_message'] + "</ul>")



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
            'mitesting:injectquestionsolution', kwargs={'question_id': question.id})
        question_data['enable_solution_button'] = not question.computer_graded \
                        or  (question.show_solution_button_after_attempts == 0)

    # if rendering a solution 
    # return without adding computer grading data
    if solution:
        return question_data
    
    # if computer graded and answer data available,
    # add submit button (unless auto_submit or error)
    question_data['submit_button'] = question.computer_graded and\
        answer_data['answer_info'] and (not auto_submit) and\
        question_data['success']

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
        computer_grade_data['course_code'] = assessment.course.code
        computer_grade_data['assessment_code'] = assessment.code
        computer_grade_data['assessment_seed'] = assessment_seed
        if question_set is not None:
            computer_grade_data['question_set'] = question_set

    if answer_data['answer_info']:
        computer_grade_data['answer_info'] \
            = answer_data['answer_info']

    # serialize and encode computer grade data to facilitate appending
    # to post data of http request sent when submitting answers
    import pickle, base64
    question_data['computer_grade_data'] = \
        base64.b64encode(pickle.dumps(computer_grade_data))

    return question_data



def get_question_list(assessment, seed, rng=None, thread_content=None):
    """
    Return list of questions for assessment, one for each question_set,
    along with additional information about each question.

    After initializing random number generator with seed
    randomly pick a question and determine question group.  
    If assessment is not set to fixed order,
    randomly order the chosen assessments, keeping questions in the same
    group together.

    Each question is randomly assigned a seed, which is to be used
    generate the question and/or solution, ensuring that question
    and solution will match.


    Return a list of dictionaries, one for each question. 
    Each dictionary contains the following:
    - question_set: the question_set from which the question was drawn
    - question: the question chosen
    - seed: the seed to use to render the question
    - relative_weight: the relative weight of the question
    - points: if have thread_content, then convert weight to points
    - group: the group of the question, if specified
    - previous_same_group: True if group is same as that of previous question
    """

    if not rng:
        import random
        rng=random.Random()
        
    rng.seed(seed)

    question_list = []
    
    total_weight = 0

    for question_set in assessment.question_sets():
        questions_in_set = assessment.questionassigned_set.filter(
            question_set=question_set)

        the_question=rng.choice(questions_in_set).question

        # generate a seed for the question
        # so that can have link to this version of question and solution
        question_seed=get_new_seed(rng)

        # find question set detail, if it exists
        try:
            question_detail=assessment.questionsetdetail_set.get(
                question_set=question_set)
        except ObjectDoesNotExist:
            question_detail = None
        
        if question_detail:
            weight=question_detail.weight
            group=question_detail.group
        else:
            weight=1
            group=""

        total_weight += weight

        question_list.append({'question_set': question_set,
                              'question': the_question,
                              'seed': question_seed,
                              'relative_weight': weight,
                              'group': group,
                              'previous_same_group': False
        })

    # make weight be relative weight
    # if have thread_content, then multiply by assessment points to
    # get question_points
    for q_dict in question_list:
        q_dict['relative_weight'] /= total_weight
        if thread_content:
            q_dict['points'] = q_dict["relative_weight"]*thread_content.points

    if assessment.fixed_order:
        for i in range(1, len(question_list)):
            the_group = question_list[i]["group"]
            # if group is not blank and the same as previous group
            # mark as belonging to same group as previous question
            if the_group and question_list[i-1]["group"] == the_group:
                    question_list[i]["previous_same_group"] = True
        return question_list

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
    groups = list(question_set_groups.keys())
    rng.shuffle(groups)

    # for each group, shuffle questions,
    # creating cummulative list of the resulting question index order
    question_order =[]
    for group in groups:
        group_indices=question_set_groups[group]
        rng.shuffle(group_indices)
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

    return question_list_shuffled

    
def return_question_list_from_specified_data(
        assessment, question_sets, question_seeds, question_ids,
        thread_content=None):

    """
    Attempt to populate question list from specified data.

    Inputs: 
    question_sets: as list of question sets
    question_seeds: a list of seeds to use for each question
    question_ids: a list of question ids

    To be valid, each question set from assessment must appear once in list.
    The question ids must be valid and the questions must belong to course,
    but the questions are not verified to be part of the specified question set
    If not valid, then raise ValueError.

    If valid, then return a question list of same format as
    get_question_list().
    
    """

    # verify that question sets are valid
    if sorted(question_sets) != sorted(assessment.question_sets):
        raise ValueError("Invalid questions sets for assessment")

    if len(question_seeds) != len(question_sets) or  \
       len(question_ids) != len(question_sets):
        raise ValueError("Invalid number of question seeds or ids")


    question_list = []
    total_weight=0

    for (ind,question_set) in enumerate(question_sets):
        try:
            question=Question.objects.get(course=assessment.course,
                                          id=question_ids[ind])
        except Question.DoesNotExist:
            raise ValueError("Question not found in assessment")

        # find question set detail, if it exists
        try:
            question_detail=assessment.questionsetdetail_set.get(
                question_set=question_set)
        except ObjectDoesNotExist:
            question_detail = None
        
        if question_detail:
            weight=question_detail.weight
            group=question_detail.group
        else:
            weight=1
            group=""

        total_weight += weight

        question_list.append({'question_set': question_set,
                              'question': question,
                              'seed': question_seeds[ind],
                              'relative_weight': weight,
                              'group': group,
                              'previous_same_group': False
        })

    # make weight be relative weight
    # if have thread_content, then multiply by assessment points to
    # get question_points
    for q_dict in question_list:
        q_dict['relative_weight'] /= total_weight
        if thread_content:
            q_dict['points'] = q_dict["relative_weight"]*thread_content.points

    # treat just like fixed order
    for i in range(1, len(question_list)):
        the_group = question_list[i]["group"]
        # if group is not blank and the same as previous group
        # mark as belonging to same group as previous question
        if the_group and question_list[i-1]["group"] == the_group:
                question_list[i]["previous_same_group"] = True
    return question_list



def render_question_list(assessment, question_list, assessment_seed, rng=None,
                         user=None, solution=False,
                         auxiliary_data=None,
                         show_post_user_errors=False):
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
    - rng: instance of random number generator to use
    - seed: random number generator seed to generate assesment and questions
    - user: the logged in user
    - solution: True if rendering solution
    - current_attempt: information about score so far on computer scored
      assessments (need to fix and test)
    - auxiliary_data: dictionary for information that should be accessible 
      between questions or outside questions.  Used, for example, 
      for information about applets and hidden sections embedded in text
    - show_post_user_errors: if true, show errors in expressions that are
      flagged as post user response

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
        This dictionary is what is returned by render_question, supplemented by
        - points: copy of above points
        - current_credit: the percent credit achieved in current attempt
        - current_score: the score (points) achieved in the current attempt
        - attempt_url: url to current attempt for the question
      - group: the group the question set belongs to
      - previous_same_group: true if the previous question if from the
        same question group as the current question
        (Used as indicator for templates that questions belong together.)
    """

    if not rng:
        import random
        rng=random.Random()

    for (i, question_dict) in enumerate(question_list):

        # use qa for identifier since coming from assessment
        identifier="qa%s" % i

        question = question_dict['question']
        question_set = question_dict['question_set']
        question_seed = question_dict["seed"]
        question_attempt = question_dict.get("question_attempt")

        prefilled_responses=None

        # if have question attempt, load latest responses from that attempt
        if question_attempt:
            try:
                latest_response=question_attempt.responses\
                    .filter(valid=True).latest()
            except ObjectDoesNotExist:
                latest_response=None

            if latest_response:
                import json
                prefilled_responses = json.loads(latest_response.response)

        question_data = render_question(
            question, rng=rng, seed=question_seed, solution=solution,
            question_identifier=identifier,
            user=user, show_help=not solution,
            assessment=assessment, question_set=question_set,
            assessment_seed=assessment_seed, 
            record_answers=True,
            allow_solution_buttons=assessment.allow_solution_buttons,
            auxiliary_data=auxiliary_data,
            prefilled_responses=prefilled_responses,
            show_post_user_errors=show_post_user_errors)
        
        question_dict['question_data']=question_data

        # if question seed changed 
        # (from resampling question expressions until valid combination found)
        if question_seed != question_data["seed"]:
            # if initial question seed matched that from question_attempt,
            # then record updated seed to reduce future resampling
            if question_attempt and question_seed==question_attempt.seed:
                question_attempt.seed = question_data["seed"]
                question_attempt.save()

            # record actual seed used in question_dict
            # so resampling not needed when checking correctness of reponses
            question_dict['seed']=question_data['seed']

        # if have a latest attempt, look for maximum score on question_set
        current_score=None
        if question_attempt:
            current_credit = question_attempt.credit
            if question_dict.get('points'):
                current_score = current_credit\
                    *question_dict['points']
            else:
                current_score=0
        else:
            current_credit = None

        # record information about score and points in question_data
        # so is available in question_body.html template
        question_data['points']=question_dict.get('points')
        question_data['current_score']=current_score
        question_data['current_credit']=current_credit


    return question_list
