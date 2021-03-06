from django.template import TemplateSyntaxError, Context, Template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.utils import OperationalError
import json 
import re
import sys
import logging
import reversion

logger = logging.getLogger(__name__)

"""
Change to deal with:
Javascript for solution applets not inserted
Multiple choice changed
Identifier changed

"""

 
def setup_expression_context(question, rng, seed, user_responses=None,
                             random_outcomes={}):
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
    using user_dict for local_dict and assign the result
    to the corresponding expression.

    The third step is to evaluate any expressions flagged as being 
    post user response.

    Both the local_dict and user_dict are added to the
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

    rng.seed(seed)

    max_tries=500
    success=False

    failed_condition_message=""
    failed_conditions=True

    from mitesting.utils import get_new_seed

    for i in range(max_tries):

        if i>0:
            seed=get_new_seed(rng)
            rng.seed(seed)

            # remove any specifications for random outcomes
            # since they caused a failed condition
            random_outcomes.clear()

        expression_context = Context({})
        random_group_indices={}
        error_in_expressions = False
        expression_error = {}

        # initialize global dictionary using the comamnds
        # found in allowed_sympy_commands.
        # Also adds standard symbols to dictionary.
        local_dict = question.return_sympy_local_dict()
        user_dict = question.return_sympy_local_dict(
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
                        user_dict=user_dict,
                        alternate_dicts = alternate_dicts, 
                        random_group_indices=random_group_indices,
                        rng=rng, random_outcomes=random_outcomes)
                # on FailedCondition, reraise to stop evaluating expressions
                except Expression.FailedCondition:
                    raise

                # for any other exception, record exception and
                # allow to continue processing expressions
                except Exception as exc:
                    error_in_expressions = True
                    expression_error[expression.name] = str(exc)
                    expression_context[expression.name] = '??'
                    if expression.expression_type == expression.RANDOM_WORD:
                        expression_context[expression.name + "_plural"] = "??"
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
    expression_context['_user_dict_'] = user_dict
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
                            response_text=mc_dict[int(response['response'])]
                        except (ValueError, KeyError):
                            response_text=default_value
                        math_expr=Symbol(response_text)
                    else:
                        try:
                            math_expr =  parse_and_process(
                                response['response'], 
                                local_dict=user_dict, 
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
        for expression in question.expression_set\
                                  .filter(post_user_response=True):

            try:
                evaluate_results=expression.evaluate(
                    local_dict=local_dict, 
                    user_dict=user_dict,
                    alternate_dicts=alternate_dicts,
                    random_group_indices=random_group_indices,
                    rng=rng, random_outcomes=random_outcomes)

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



def render_question_text(render_data, solution=False, no_links=False):
    """
    Render the question text and subparts as Django templates.
    Use context specified by expression context and load in custom tags
    Optionally render "need help" information.

    Input render_data is a dictionary with the following keys
    - question: the question to be rendered
    - expression_context: the template context used to render the text
    - show_help (optional): if true, render the "need help" information

    If no_links, then remove linkes from text and hint text,
    as well as don't show links to reference pages
    
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
    template_string_base = "{% load question_tags mi_tags dynamictext humanize %}"


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
            if no_links:
                remove_links_pattern =r'<(a|/a).*?>'
                render_results['rendered_text'] = mark_safe(re.sub(
                    remove_links_pattern, '', render_results['rendered_text']))
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
                if no_links:
                    remove_links_pattern =r'<(a|/a).*?>'
                    subpart_dict['rendered_text'] = mark_safe(re.sub(
                        remove_links_pattern, '', subpart_dict['rendered_text']))

        else:
            subpart_dict["rendered_text"] = ""
                
        render_results['subparts'].append(subpart_dict)

    # add help data to render_results
    # if show_help is set to true and not solution
    if render_data.get('show_help') and not solution:
        add_help_data(render_data, render_results, subparts, no_links=no_links)

    return render_results


def add_help_data(render_data, render_results, subparts=None,
                  no_links=False):
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

    If no_links is True, does not add links to reference pages.
    Also, removes any <a> or </a> tags in hints (leaving the link text in place)
    
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

    template_string_base = "{% load question_tags mi_tags dynamictext humanize %}"
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
        if not no_links:
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

            if no_links:
                remove_links_pattern =r'<(a|/a).*?>'
                subpart_dict['hint_text'] = mark_safe(re.sub(
                    remove_links_pattern, '', subpart_dict['hint_text']))

        subpart_dict['help_available']=help_available

    help_available=False

    # If subparts are present, then only pages with no single character subpart
    # listed are added to main reference_pages list.
    # (References pages marked with non-existent subpart are not visible)
    if not no_links:
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

        if no_links:
            remove_links_pattern =r'<(a|/a).*?>'
            render_results['hint_text'] = mark_safe(re.sub(
                remove_links_pattern, '', render_results['hint_text']))

    render_results['help_available'] = help_available

    render_results['hint_template_error'] = hint_template_error


def render_question(question_dict, rng, solution=False, 
                    question_identifier="",
                    user=None, show_help=True,
                    assessment=None, 
                    assessment_seed=None, 
                    readonly=False, auto_submit=False, 
                    record_response=True,
                    allow_solution_buttons=False,
                    auxiliary_data=None,
                    show_post_user_errors=False,
                    show_correctness=True,
                    no_links=False,
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
    - record_response: if true, record answer upon submit
    - allow_solution_buttons: if true, allow a solution button to be displayed
      on computer graded questions
    - auxiliary_data: dictionary for information that should be accessible 
      between questions or outside questions.  Used, for example, 
      for information about applets and hidden sections embedded in text
    - show_post_user_errors: if true, display errors when evaluating
      expressions flagged as being post user response.  Even if showing
      errors, such an error does not cause the rendering success to be False
    - show_correctness: if True, then should display correctness of response
      upon its submission
    - no_links: if True, then should suppress links in feedback to responses

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
      - record_response
      - question_set
      - assessment_seed
      - course_code (of assessment from input)
      - assessment_code (of assessment from input)
      - answer_info: list of codes, points, answer type, identifier, 
        group, assigned expression, prefilled answer, and expression type
        of the answers in question
      - applet_counter: number of applets encountered so far 
        (not sure if need this)
      - show_correctness
      - no_links
   """


    question = question_dict['question']
    question_set = question_dict.get('question_set')
    seed = question_dict.get("seed")
    question_attempt = question_dict.get("question_attempt")
    response = question_dict.get("response")

    if seed is None:
        from mitesting.utils import get_new_seed
        seed=get_new_seed(rng)

    rng.seed(seed)


    # dictionary keyed by expression id that specify
    # the random results should obtain.  If valid and no failed condition, 
    # then random number generator is not used.
    random_outcomes={}

    # if have question attempt, load random outcomes and
    # latest responses from that attempt
    if question_attempt:
        if question_attempt.random_outcomes:
            random_outcomes = json.loads(question_attempt.random_outcomes)

    # if have response, load to be prefilled
    if response:
        prefilled_responses = json.loads(response.response)
    else:
        prefilled_responses = None


    # first, setup context due to expressions from question.
    # include any prefilled responses to answers
    context_results = setup_expression_context(question, rng=rng, seed=seed,
                                            user_responses=prefilled_responses,
                                            random_outcomes=random_outcomes)


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
        
        # save new seed to question attempt so on next reload,
        # a new seed will be tried.
        if question_attempt and seed==question_attempt.seed:
            question_attempt.seed = context_results["seed"]

            # repeat so that can retry if get transaction deadlock
            for trans_i in range(5):
                try:
                    with transaction.atomic(), reversion.create_revision():
                        question_attempt.save()
                except OperationalError:
                    if trans_i==4:
                        raise
                else:
                    break
            
        return question_data


    # if seed changed from resampling to avoid failed expression conditions
    if seed != context_results["seed"]:
        # if initial question seed matched that from question_attempt,
        # then record updated seed to reduce future resampling
        if question_attempt and seed==question_attempt.seed:
            question_attempt.seed = context_results["seed"]
            # will save changes below

    # set seed to be successful seed from rendering context
    seed = context_results['seed']

    # if have question attempt, save random_outcomes, if changed
    if question_attempt:
        ro_json = json.dumps(random_outcomes)
        if question_attempt.random_outcomes != ro_json:
            question_attempt.random_outcomes = ro_json
            # repeat so that can retry if get transaction deadlock
            for trans_i in range(5):
                try:
                    with transaction.atomic(), reversion.create_revision():
                        question_attempt.save()
                except OperationalError:
                    if trans_i==4:
                        raise
                else:
                    break
    

    # record actual seed used in question_dict
    # not sure if need this
    question_dict['seed']=seed

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

    question_data = render_question_text(render_data, solution=solution,
                                        no_links=no_links)

    question_data.update({
        'identifier': question_identifier,
        'auto_submit': auto_submit,
        'seed': seed,
        'dynamictext_javascript': dynamictext_javascript,
    })

    # if have prefilled responses, check to see that the number matches the
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


    # if rendering a solution 
    # return without adding computer grading data or solution buttons
    if solution:
        return question_data
    

    # if have a question attempt, determine credit
    # also score if question_dict contains points for question set
    current_score=None
    if question_attempt:
        from mitesting.utils import round_and_int
        if question_attempt.credit is None:
            current_percent_credit=None
            current_score=0
        else:
            current_percent_credit = round_and_int(question_attempt.credit*100,1)
            current_score = round_and_int(question_attempt.credit*question_dict.get('points',0),2)

    else:
        current_percent_credit = None

    # record information about score and points in question_data
    # so is available in question_body.html template
    question_data['points']=question_dict.get('points')
    question_data['current_score']=current_score
    question_data['current_percent_credit']=current_percent_credit


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
            'miquestion:injectquestionsolution', kwargs={'question_id': question.id})
        question_data['enable_solution_button'] = not question.computer_graded \
                        or  (question.show_solution_button_after_attempts == 0)

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
                           'record_response': record_response,
                           'show_solution_button': show_solution_button,
                           'show_correctness': show_correctness,
                           'no_links': no_links}
    if assessment:
        computer_grade_data['course_code'] = assessment.course.code
        computer_grade_data['assessment_code'] = assessment.code
        computer_grade_data['assessment_seed'] = assessment_seed
        if question_set is not None:
            computer_grade_data['question_set'] = question_set

    if question_attempt:
        computer_grade_data['question_attempt_id'] = question_attempt.id
        
    if answer_data['answer_info']:
        computer_grade_data['answer_info'] \
            = answer_data['answer_info']

    # serialize and encode computer grade data to facilitate appending
    # to post data of http request sent when submitting answers
    import pickle, base64
    question_data['computer_grade_data'] = \
        base64.b64encode(pickle.dumps(computer_grade_data))

    return question_data

