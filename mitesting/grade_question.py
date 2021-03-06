from django.conf import settings
from mitesting.models import QuestionAnswerOption, Expression
from django.core.exceptions import ObjectDoesNotExist
from sympy.parsing.sympy_tokenize import TokenError
import json

import logging

logger = logging.getLogger(__name__)


def check_function_answer(f,user_response_parsed):

    f_float=None
    try:
        f=f(user_response_parsed)
    except Exception as e:
        return 0
    else:
        # try performing doit() on function in case has unevaluated functions
        try:
            f=f.doit()
        except (AttributeError, TypeError):
            pass

        # before attempting to convert to float,
        # check if f returns a boolean, 
        # in which case mark as completely correct or incorrect
        from sympy import S
        if f is S.BooleanTrue:
            return 1
        elif f is S.BooleanFalse:
            return 0

        try:
            f_float = float(f)
        except (TypeError, AttributeError):
            # try converting Eq and Ne to regular python functions
            # that demand exact equality of expressions
            from sympy import Eq, Ne
            try:
                f=f.replace(Eq, lambda x,y: x==y)
                f=f.replace(Ne, lambda x,y: x!=y)
                
                # again check if Boolean before attempting to convert to float
                if f is S.BooleanTrue:
                    return 1
                elif f is S.BooleanFalse:
                    return 0

                f_float = float(f)
            except (TypeError, AttributeError):
                return 0
                
    return max(0,min(1,f_float))


def compare_response_with_answer_code(user_response, the_answer_info, question,
                                      expr_context, local_dict,
                                      show_correctness=True):

    answer_code = the_answer_info['code']
    answer_type = the_answer_info['type']

    binary_feedback_correct = ' <img src="%sadmin/img/icon-yes.gif" alt="correct" />'\
         % (settings.STATIC_URL)
    binary_feedback_incorrect = ' <img src="%sadmin/img/icon-no.gif" alt="incorrect" />'\
        % (settings.STATIC_URL)

    answer_result = {'percent_correct': 0, 'answer_correct': False,
                     'received_response': False}
    
    if answer_type == QuestionAnswerOption.MULTIPLE_CHOICE:
        try:
            the_answer = question.questionansweroption_set \
                .get(id = user_response)
        except ObjectDoesNotExist:
            logger.warning("Multiple choice answer not found")
            answer_result['answer_feedback'] \
                = "Cannot grade due to error in question"
            return answer_result
        except ValueError:
            answer_result['answer_feedback'] \
                = "No response"
            return answer_result
        except TypeError:
            logger.warning("Invalid option for multiple choice answer")
            answer_result['answer_feedback'] \
                = "Cannot grade due to error in question"
            return answer_result
        else:
        
            # if multiple choice doesn't match given code
            # then something is wrong
            if the_answer.answer_code != answer_code:
                logger.warning("Multiple choice answer answer code does not match")
                answer_result['answer_feedback'] \
                    = "Cannot grade due to error in question"
                return answer_result

            percent_correct = the_answer.percent_correct
            if show_correctness:
                if percent_correct == 100:
                    feedback = "Yes, you are correct."
                elif percent_correct > 0:
                    feedback = 'Answer is not completely correct' \
                        + ' but earns partial (%s%%) credit.' \
                        % (the_answer.percent_correct)
                else:
                    feedback = "No, you are incorrect."
            else:
                feedback = "Answered"

            answer_result['received_response']=True

        # record any feedback from answer option used
        try:
            feedback += " " +  the_answer.render_feedback(expr_context)
        except:
            pass

    elif answer_type == QuestionAnswerOption.TEXT:
        percent_correct=0
        if(user_response):
            feedback = "Answer to be manually graded."
            answer_result['received_response']=True
        else:
            feedback = "No response"

    # if either EXPRESSION or FUNCTION, then use all options 
    # that are EXPRESSION or FUNCTION
    elif answer_type == QuestionAnswerOption.EXPRESSION or \
         answer_type == QuestionAnswerOption.FUNCTION:

        # get rid of any .methods, so can't call commands like
        # .expand() or .factor()
        import re
        user_response = re.sub('\.[a-zA-Z]+', '', user_response)


        if not user_response:
            answer_result['answer_feedback'] \
                = "No response"
            answer_result['answer_feedback_binary'] \
                = binary_feedback_incorrect
            return answer_result


        # start with negative percent_correct so that will get 
        # feedback from matched answers with 0 percent correct
        percent_correct=-1

        round_level_required = None
        round_level_used = None
        round_absolute = None
        n_sign_errors = 0
        n_constant_factor_errors = 0
        n_constant_term_errors = 0
        near_match_percent_correct = 0
        near_match_feedback=""
        answer_option_used = None
        user_response_string=""
        feedback=""

        from .sympy_customized import parse_and_process
        from .math_objects import math_object
        from sympy import sympify
        from django.db.models import Q
        answer_options=question.questionansweroption_set \
                .filter(answer_code=answer_code) \
                .filter(Q(answer_type=QuestionAnswerOption.EXPRESSION)
                        | Q(answer_type=QuestionAnswerOption.FUNCTION))

        if(len(answer_options)==0):
            logger.warning("Expression answer found with no matching options")
            answer_result['answer_feedback'] \
                = "Cannot grade due to error in question"
            return answer_result
            

        # compare with expressions associated with answer_code
        for answer_option in answer_options:

            # find the expression associated with answer_option
            try:
                valid_answer=expr_context[answer_option.answer]
            except KeyError:
                continue
            try:
                valid_alternates = expr_context['_alternate_exprs_'] \
                                   [answer_option.answer]
            except KeyError:
                valid_alternates = []

            # determine level of evaluation of answer_option
            try:
                evaluate_level = valid_answer.return_evaluate_level()
            except AttributeError:
                continue

            # determine if should assume real variables when parsing
            try:
                assume_real_variables \
                    = valid_answer.return_assume_real_variables()
            except AttributeError:
                continue

            # determine if have partial credit for less rounding
            round_partial_credit_digits=0
            round_partial_credit_percent=0
            if answer_option.round_partial_credit_digits:
                round_partial_credit_digits = \
                        answer_option.round_partial_credit_digits
            if answer_option.round_partial_credit_percent:
                round_partial_credit_percent = \
                        answer_option.round_partial_credit_percent

            # determine if have partial credit for sign errors
            sign_error_partial_credit = answer_option.sign_error_partial_credit
            sign_error_partial_credit_percent=0
            if answer_option.sign_error_partial_credit_percent:
                sign_error_partial_credit_percent = \
                        answer_option.sign_error_partial_credit_percent

            # determine if have partial credit for constant term errors
            constant_term_error_partial_credit = \
                    answer_option.constant_term_error_partial_credit
            constant_term_error_partial_credit_percent=0
            if answer_option.constant_term_error_partial_credit_percent:
                constant_term_error_partial_credit_percent = \
                    answer_option.constant_term_error_partial_credit_percent

            # determine if have partial credit for constant factor errors
            constant_factor_error_partial_credit = \
                    answer_option.constant_factor_error_partial_credit
            constant_factor_error_partial_credit_percent=0
            if answer_option.constant_factor_error_partial_credit_percent:
                constant_factor_error_partial_credit_percent = \
                    answer_option.constant_factor_error_partial_credit_percent

            user_response_parsed=None
            
            expression_type = the_answer_info.get('expression_type')

            try:
                if expression_type == Expression.MATRIX:
                    from mitesting.utils import return_matrix_expression
                    try:
                        user_response_parsed =return_matrix_expression(
                            user_response, local_dict=local_dict, 
                            split_symbols=answer_option
                            .split_symbols_on_compare,
                            evaluate_level=evaluate_level,
                            assume_real_variables=assume_real_variables,
                            parse_subscripts=True)
                    except ValueError as e:
                        feedback = "Invalid matrix: %s" % e.args[0]
                        break
                elif expression_type == Expression.INTERVAL:
                    try:
                        user_response_parsed =parse_and_process(
                            user_response, local_dict=local_dict, 
                            split_symbols=answer_option
                            .split_symbols_on_compare,
                            evaluate_level=evaluate_level,
                            replace_symmetric_intervals=True,
                            assume_real_variables=assume_real_variables,
                            parse_subscripts=True)
                    except (TypeError, NotImplementedError, SyntaxError, TokenError):
                        pass
                    except ValueError as e:
                        if "real intervals" in e.args[0]:
                            feedback="Cannot evaluate answer; variables used in intervals must be real."
                            break
                            
                if user_response_parsed is None:
                    user_response_parsed = parse_and_process(
                        user_response, local_dict=local_dict, 
                        split_symbols=answer_option
                        .split_symbols_on_compare,
                        evaluate_level=evaluate_level,
                        assume_real_variables=assume_real_variables,
                        parse_subscripts=True)
            except ValueError as e:
                try:
                    if "real intervals" in e.args[0]:
                        feedback="Cannot evaluate answer; variables used in intervals must be real."
                        break
                except:
                    pass
                feedback = "Sorry.  Unable to understand the answer."
                break
            except Exception as e:
                feedback = "Sorry.  Unable to understand the answer."
                break

            # if VECTOR, convert Tuples to column MatrixAsVector
            # which latexs as a vector
            if expression_type == Expression.VECTOR:
                from mitesting.customized_commands import \
                    MatrixFromTuple
                from mitesting.sympy_customized import TupleNoParen
                from sympy import Tuple

                if isinstance(user_response_parsed, Tuple) and \
                   not isinstance(user_response_parsed, TupleNoParen):
                    user_response_parsed = MatrixFromTuple(
                        *user_response_parsed)
                    
            # If a set and didn't include braces, will be a TupleNoParen.
            # In that case, convert to set and back to remove duplicates
            elif expression_type == Expression.SET:
                from mitesting.sympy_customized import TupleNoParen
                if isinstance(user_response_parsed, TupleNoParen):
                    user_response_parsed = TupleNoParen(*set(user_response_parsed))
                
            
            user_response_parsed=math_object(
                user_response_parsed,
                tuple_is_unordered=valid_answer.return_if_unordered(),
                round_on_compare=answer_option.round_on_compare,
                round_absolute=answer_option.round_absolute,
                round_partial_credit_digits=round_partial_credit_digits,
                round_partial_credit_percent=round_partial_credit_percent,
                sign_error_partial_credit=sign_error_partial_credit,
                sign_error_partial_credit_percent=
                sign_error_partial_credit_percent,
                constant_term_error_partial_credit=
                constant_term_error_partial_credit,
                constant_term_error_partial_credit_percent=
                constant_term_error_partial_credit_percent,
                constant_factor_error_partial_credit=
                constant_factor_error_partial_credit,
                constant_factor_error_partial_credit_percent=
                constant_factor_error_partial_credit_percent,
                normalize_on_compare=answer_option.normalize_on_compare,
                match_partial_on_compare= 
                answer_option.match_partial_on_compare,
                evaluate_level=evaluate_level)


            user_response_string=""
            user_response_unevaluated=None
            from mitesting.sympy_customized import EVALUATE_NONE
            try:
                if expression_type == Expression.MATRIX:
                    from mitesting.utils import return_matrix_expression
                    user_response_unevaluated =return_matrix_expression(
                        user_response, local_dict=local_dict, 
                        split_symbols=answer_option
                        .split_symbols_on_compare,
                        evaluate_level=EVALUATE_NONE,
                        assume_real_variables=assume_real_variables,
                        parse_subscripts=True)
                elif expression_type == Expression.INTERVAL:
                    try:
                        user_response_unevaluated = parse_and_process(
                            user_response, local_dict=local_dict, 
                            split_symbols=answer_option
                            .split_symbols_on_compare,
                            evaluate_level=EVALUATE_NONE,
                            replace_symmetric_intervals=True,
                            assume_real_variables=assume_real_variables,
                            parse_subscripts=True)
                    except (TypeError, NotImplementedError, SyntaxError, TokenError):
                        pass
                    except ValueError as e:
                        if "real intervals" in e.args[0]:
                            feedback="Variables used in intervals must be real"
                            break
                            
                if user_response_unevaluated is None:
                    user_response_unevaluated =  parse_and_process(
                        user_response, local_dict=local_dict, 
                        split_symbols=answer_option
                        .split_symbols_on_compare,
                        evaluate_level=EVALUATE_NONE,
                        assume_real_variables=assume_real_variables,
                        parse_subscripts=True)

                user_response_unevaluated=math_object(
                    user_response_unevaluated,
                    evaluate_level=EVALUATE_NONE)
                user_response_string = str(user_response_unevaluated)
            except:
                pass

            if not user_response_string:
                try:
                    user_response_string = str(user_response_parsed)
                except:
                    user_response_string = "[error displaying answer]"


            if answer_option.answer_type == QuestionAnswerOption.FUNCTION:
                f_options = [expr_context['_sympy_local_dict_']\
                             [answer_option.answer],]
                try:
                    f_options.extend(expr_context['_alternate_funcs_']\
                                     [answer_option.answer])
                except KeyError:
                    pass

                fraction_equal=0
                for f in f_options:
                    fraction_equal = max(fraction_equal,
                                         check_function_answer(
                                             f, user_response_parsed))
                

                answer_results = {'fraction_equal': fraction_equal,
                                  'fraction_equal_on_normalize': 0,
                                  'round_level_used': 0,
                                  'round_level_required': 0,
                                  'round_absolute': False,
                                  'n_sign_errors': 0,
                                  'n_constant_term_errors': 0,
                                  'n_constant_factor_errors': 0}
            else:
                answer_options=[valid_answer,]
                answer_options.extend(valid_alternates)
                fraction_equal=-1
                fraction_equal_on_normalize=-1
                answer_results={}
                for ao in answer_options:
                    results=user_response_parsed.compare_with_expression( 
                        ao.return_expression())
                    if results['fraction_equal'] > fraction_equal \
                       or (results['fraction_equal'] == fraction_equal \
                           and results['fraction_equal_on_normalize']  \
                           >= fraction_equal_on_normalize):
                        answer_results=results
                        fraction_equal=results['fraction_equal']
                        fraction_equal_on_normalize\
                            =results['fraction_equal_on_normalize']
            this_percent_correct = \
                answer_option.percent_correct\
                *answer_results['fraction_equal']
            this_near_match_percent_correct = \
                        answer_option.percent_correct\
                        *answer_results['fraction_equal_on_normalize']

            # Use feedback from this answer option if
            # (1) percent correct increases
            #     (it starts negative so zero increases it the first time,
            #     allowing the possibility for feedback even if
            #     no credit is assigned, as outlined next)
            #     and
            # (2) either
            #     (a) the response was marked as at least partially equal
            #         (which occurrs even if the answer option is
            #         listed as 0% correct, so that can give feedback for
            #         matching wrong answers)
            #     (b) answer matched at a lower numerical precision
            #         than required (so that can give feedback that the answer
            #         is close to a the required precision even if giving
            #         no credit for being close)
            #         or
            #     (c) the answer matched after taking into account certain
            #         errors (so that can give feedback about sign errors
            #         or constant term/factor errors even if not giving credit
            #         for matching after accounting for these errors)
            if (answer_results['fraction_equal'] > 0 or \
                (answer_results['round_level_used'] is not None
                 and answer_results['round_level_required'] is not None
                 and answer_results['round_level_used'] < \
                 answer_results['round_level_required']) or \
                answer_results['n_sign_errors'] > 0 or \
                answer_results['n_constant_term_errors'] > 0 or \
                answer_results['n_constant_factor_errors'] > 0) \
                and this_percent_correct  > percent_correct:
                if show_correctness:
                    if this_percent_correct == 100:
                        feedback = \
                            'Yes, $%s$ is correct.' % \
                            user_response_string
                    elif this_percent_correct > 0:
                        feedback = '$%s$ is not completely correct but earns' \
                            ' partial (%i%%) credit.' \
                            % (user_response_string, 
                               round(this_percent_correct))
                else:
                    feedback = 'Answer understood as: $%s$.' % user_response_string

                percent_correct = this_percent_correct
                answer_option_used = answer_option
                round_level_required = answer_results['round_level_required']
                round_level_used = answer_results['round_level_used']
                round_absolute = answer_results['round_absolute']
                n_sign_errors = answer_results['n_sign_errors']
                n_constant_term_errors = \
                            answer_results['n_constant_term_errors']
                n_constant_factor_errors = \
                            answer_results['n_constant_factor_errors']
                
            if this_near_match_percent_correct  > \
                 max(near_match_percent_correct,percent_correct):
                near_match_percent_correct =\
                    this_near_match_percent_correct
                near_match_feedback = \
                    "<br><small>(Your answer is mathematically equivalent to " 
                if near_match_percent_correct == 100:
                    near_match_feedback += "the correct answer, "
                else:
                    near_match_feedback  += \
                        "an answer that is %i%% correct, " \
                        % round(near_match_percent_correct)
                near_match_feedback += "but "\
                    " you must write your answer in a different form.)</small>" 
            if not feedback:
                if show_correctness:
                    feedback = 'No, $%s$ is incorrect.' \
                        % user_response_string
                else:
                    feedback = 'Answer understood as: $%s$.' \
                               % user_response_string

            answer_result['received_response']=True

        # since started with negative percent_correct
        # make it zero if no matches
        percent_correct = max(0, percent_correct)

        # additional feedback if show_correctness is True
        if show_correctness:

            # record any feedback from answer option used
            try:
                feedback += " " + \
                            answer_option_used.render_feedback(expr_context)
            except:
                pass

            # record any feedback about rounding
            if round_level_used is not None \
               and round_level_required is not None \
               and round_level_used < round_level_required:
                if round_absolute:
                    round_place_used = pow(10,-round_level_used)
                    round_place_required = pow(10,-round_level_required)
                    if round_place_used >=1:
                        round_place_used = int(round_place_used)
                        if round_place_required >=1:
                            round_place_required = int(round_place_required)
                    feedback += " Answer matched to the nearest %s's place but matching to the %s's place is required." % (round_place_used, round_place_required)
                else:
                    feedback += " Answer matched to %s significant digits but %s significant digits are required." % (round_level_used, round_level_required)


            # record any feedback about sign errors or constant term/factor errors

            if near_match_percent_correct != 100:
                # However, don't show feedback message if the answer
                # is mathematically equivalent to a 100% correct answer.
                # (In this case, the calculation error calculation probably
                # just effectively normalized the answer)
                if n_sign_errors == 1:
                    feedback += " Answer appears to have a sign error."
                elif n_sign_errors > 1:
                    feedback += " Answer appears to have around %s sign errors." % n_sign_errors
                if n_constant_term_errors == 1:
                    feedback += " Answer appears to have a place where you added or subtracted by the wrong number."
                elif n_constant_term_errors > 1:
                    feedback += " Answer appears to have around %s places where you added or subtracted by the wrong number." % n_constant_term_errors
                if n_constant_factor_errors == 1:
                    feedback += " Answer appears to have a place where you multiplied or divided by the wrong number."
                elif n_constant_factor_errors > 1:
                    feedback += " Answer appears to have around %s places where you multiplied or divided by the wrong number." % n_constant_factor_errors

                    
            if percent_correct < 100 and \
               near_match_percent_correct > percent_correct:
                feedback += near_match_feedback



    else:
        logger.warning("Unrecognized answer type: %s" % answer_type)
        answer_result['answer_feedback'] \
            = "Cannot grade due to error in question"
        answer_result['answer_feedback_binary']\
            = binary_feedback_incorrect
        return answer_result

    answer_result['percent_correct'] = percent_correct

    answer_result['answer_feedback'] = feedback


    if show_correctness:
        if percent_correct == 100:
            answer_result['answer_feedback_binary'] = binary_feedback_correct
        elif percent_correct > 0:
            answer_result['answer_feedback_binary']\
                = ' <small>(%s%%)</small>' % int(round(percent_correct))
        else:
            answer_result['answer_feedback_binary']\
                = binary_feedback_incorrect
    else:
        answer_result['answer_feedback_binary'] = ""
        
    answer_result['answer_correct'] = (percent_correct == 100)

    return answer_result


def index_convert(i, removed_indices):
    # compute index of original array from index of array with removed entries

    # removed_indices is a list of entries removed from original array

    # assume removed_indices is small so just do linear search
    
    for ind in sorted(removed_indices):
        if i >= ind:
            i += 1
        else:
            return i
    return i


def match_max_ones(A):
    """
    Find elements (i,j) of matrix A, maximizing number of 1's under
    condition that each i and each j are used at most once

    Assume A is a matrix of 1's and 0's. 
    
    Returns a list of tuples of form (i,j), where each i and j in range of 
    column and row indicies, respectively, and each i and j appear at most once.
    
    """
    index_list = []
    removed_rows = []
    removed_cols = []
    
    # find any rows that have exactly one 1
    
    while True:
        removed_nonzero_items=False

        rows_to_remove = []
        for row_ind in range(A.rows):
            the_row=list(A[row_ind,:])
            if sum(the_row) == 1:
                col_ind= the_row.index(1)
                index_list.append((index_convert(row_ind,removed_rows), 
                                   index_convert(col_ind,removed_cols)))
                # remove row later
                rows_to_remove.append(row_ind)

                # remove column right away
                removed_cols.append(index_convert(col_ind,removed_cols))
                A.col_del(col_ind)

                removed_nonzero_items=True
            elif sum(the_row)==0:
                rows_to_remove.append(row_ind)
        
        rows_to_remove_converted = []
        rows_to_keep=list(range(A.rows))

        for row_ind in rows_to_remove:
            rows_to_remove_converted.append(index_convert(row_ind,removed_rows))
            rows_to_keep.remove(row_ind)

        removed_rows.extend(rows_to_remove_converted)

        A=A[rows_to_keep, :]


        cols_to_remove = []
        for col_ind in range(A.cols):
            the_col=list(A[:,col_ind])
            if sum(the_col) == 1:
                row_ind= the_col.index(1)
                index_list.append((index_convert(row_ind,removed_rows), 
                                   index_convert(col_ind,removed_cols)))

                # remove column later
                cols_to_remove.append(col_ind)

                # remove row right away
                removed_rows.append(index_convert(row_ind,removed_rows))
                A.row_del(row_ind)

                removed_nonzero_items=True
            elif sum(the_col)==0:
                cols_to_remove.append(col_ind)
        
        cols_to_remove_converted = []
        cols_to_keep=list(range(A.cols))

        for col_ind in cols_to_remove:
            cols_to_remove_converted.append(index_convert(col_ind,removed_cols))
            cols_to_keep.remove(col_ind)

        removed_cols.extend(cols_to_remove_converted)

        A=A[:, cols_to_keep]

        if not removed_nonzero_items:
            break

    # if removed all rows or columns of A, then we are done
    if(A.rows*A.cols==0):
        return index_list

    # in the remaining matrix A, each row and each column has at least two 1s.
    # Take the first row of A, match it in turn with each column with a 1,
    # compute the index_list from the remaining submatrix
    # Choose the alternative where index list is the largest


    index_sublists = []
    len_sublists=[]
    for col in range(A.cols):
        if A[0,col]==0:
            index_sublists.append(None)
            len_sublists.append(-1)
        else:
            index_sublists.append(match_max_ones(A.minorMatrix(0,col)))
            len_sublists.append(len(index_sublists[col]))

    best_col = len_sublists.index(max(len_sublists))

    row = index_convert(0,removed_rows)
    col = index_convert(best_col,removed_cols)
    index_list.append((row,col))
    removed_rows.append(row)
    removed_cols.append(col)

    for pair in index_sublists[best_col]:
        row =index_convert(pair[0],removed_rows)
        col =index_convert(pair[1],removed_cols)
        index_list.append((row,col))

    return index_list

    
def grade_question_group(group_list, user_responses, answer_info, question,
                         expr_context, local_dict, answer_results,
                         show_correctness=True):
    """
    Grade a group of answers, where responses could match answers
    in any sequence.

    First, match as many answers with responses that get full credit.
    Then, match answers with responses in order of decreasing percent credit.

    Inputs:
    - group_list: list of answer numbers in the given group
    - user_responses: list identifiers, codes and answers giving user's
      response to questions
    - answer_info: list of identifiers, codes, points, answer types,
      and groups of answers in question
    - question: the question in which answers are contained
    - expr_context: the rendered expression context for the question
    - local_dict: global dictionary to be used to parse user's responses
    - answer_results: dictionary that records results of answers
      (not just the ones from this group).  
    - show_correctness: True if feedback should reveal if response is correct

    Return a dictionary containing:
    - points_achieved_times_100: the points achieved for this group,
      multipled by 100
    - points_answered: total points of questions that have an answer
      in this group

    """


    from sympy import zeros

    n_answers=len(group_list)

    answer_array = []

    for (i,response_num) in enumerate(group_list):
        answer_array.append([])
        user_response = user_responses[response_num]["response"]
        for answer_num in group_list:
            the_answer_info = answer_info[answer_num]

            try:
                answer_array[i].append(\
                    compare_response_with_answer_code \
                    (user_response=user_response, 
                     the_answer_info=the_answer_info,
                     question=question, expr_context=expr_context,
                     local_dict=local_dict,
                     show_correctness=show_correctness)
                )
            except Exception as e:
                logger.error("Unexpected error when comparing answer:\n%s: %s" \
                             % (e.__class__.__name__, e))
                answer_array[i].append({
                    'percent_correct': 0, 'answer_correct': False,
                    'received_response': False,
                    'answer_feedback': 'Sorry.  Unable to understand the answer.  Possibly, a server error occured.'})


    correct_matrix = zeros(n_answers, n_answers)
    for response_num in range(n_answers):
        for answer_num in range(n_answers):
            if answer_array[response_num][answer_num]['answer_correct']:
                correct_matrix[response_num,answer_num] = 1

                
    # match as many as possible answers with full credit
    answer_matches = match_max_ones(correct_matrix)
    n_matches = len(answer_matches)
    n_answers_left = n_answers-n_matches

    if n_answers_left > 0:

        # for remaining responses and answers match starting with the 
        # largest partial credit
        responses_used = []
        answers_used = []
        for match in answer_matches:
            responses_used.append(match[0])
            answers_used.append(match[1])

        # partial credit matrix
        P = zeros(n_answers_left, n_answers_left)

        row=-1
        for response_num in range(n_answers):
            if response_num in responses_used:
                continue
            row +=1
            col=-1
            for answer_num in range(n_answers):
                if answer_num in answers_used:
                    continue
                col+=1
                P[row,col] = \
                    answer_array[response_num][answer_num]['percent_correct']

        while P.rows > 0:
            max_credit = max(P)
            for row in range(P.rows):
                try:
                    col = list(P[row,:]).index(max_credit)
                except ValueError:
                    continue
                actual_response=index_convert(row,responses_used)
                actual_answer=index_convert(col,answers_used)
                answer_matches.append((actual_response,actual_answer))
                responses_used.append(actual_response)
                answers_used.append(actual_answer)
                P.row_del(row)
                P.col_del(col)
                break

    # record answers in answer_results
    points_achieved_times_100=0
    points_answered=0;
    for match in answer_matches:
        answer_identifier = answer_info[group_list[match[0]]]['identifier']
        answer_results["answers"][answer_identifier] = \
                        answer_array[match[0]][match[1]]
                                                       
        answer_points = answer_info[group_list[match[0]]]['points']
        points_achieved_times_100 += answer_points*\
                answer_results['answers'][answer_identifier]['percent_correct']
        if answer_results['answers'][answer_identifier]['received_response']:
            points_answered += answer_points

    return {'points_achieved_times_100': points_achieved_times_100,
            'points_answered': points_answered }


def grade_question(question, question_identifier, answer_info, 
                   question_attempt,
                   user_responses, seed,
                   show_correctness=True,
                   no_links=False):

    # use local random generator to make sure threadsafe
    import random
    rng=random.Random()

    random_outcomes={}
    if question_attempt:
        if question_attempt.random_outcomes:
            random_outcomes = json.loads(question_attempt.random_outcomes)

    from .render_questions import setup_expression_context

    # first obtain context from just the normal expressions
    context_results = setup_expression_context(question, rng=rng, seed=seed,
                                user_responses = user_responses,
                                random_outcomes=random_outcomes,
                                )
    expr_context=context_results['expression_context']
    user_dict = expr_context['_user_dict_']


    # render any dynamic text from question
    from dynamictext.models import DynamicText
    num_dts = DynamicText.return_number_for_object(question)
    dynamictext_html=[]
    for i in range(num_dts):
        dt = DynamicText.return_dynamictext(question,i)
        rendered_text=dt.render(context=expr_context, 
                                instance_identifier=question_identifier)
        function_name = "%s_dynamictext_update" % \
                        dt.return_identifier(question_identifier)
        dynamictext_html.append((function_name,rendered_text))
        

    points_achieved=0
    points_answered=0
    total_points=0
    
    answer_results={}

    answer_results['identifier']=question_identifier
    answer_results['feedback']=""
    answer_results['answers'] = {}
    answer_results['dynamictext'] = dynamictext_html
    question_groups = {}

    # check correctness of each answer
    for answer_num in range(len(answer_info)):
        answer_type = answer_info[answer_num]['type']

        # if answer_type is None ignore
        # (used for state variables from applets and if answer_code is None)
        if answer_type is None:
            continue

        user_response = user_responses[answer_num]["response"]
        answer_code = answer_info[answer_num]['code']
        answer_points= answer_info[answer_num]['points']
        answer_identifier = answer_info[answer_num]['identifier']
        answer_group = answer_info[answer_num]['group']
        
        the_answer_info = answer_info[answer_num]

        total_points += answer_points
        
        if answer_group is None:
            try:
                answer_results['answers'][answer_identifier] = \
                    compare_response_with_answer_code \
                    (user_response=user_response,
                     the_answer_info=the_answer_info,
                     question=question, expr_context=expr_context,
                     local_dict=user_dict,
                     show_correctness=show_correctness)

            except Exception as e:
                logger.error("Unexpected error when comparing answer:\n%s: %s" \
                             % (e.__class__.__name__, e))
                answer_results['answers'][answer_identifier] = {
                    'percent_correct': 0, 'answer_correct': False,
                    'received_response': False,
                    'answer_feedback': 'Sorry.  Unable to understand the answer.  Possibly, a server error occured.'}
                
            points_achieved += answer_points*\
                answer_results['answers'][answer_identifier]['percent_correct']
            
            if answer_results['answers'][answer_identifier]['received_response']:
                points_answered += answer_points

        else:
            try:
                group_list = question_groups[answer_group]
            except KeyError:
                group_list = []
                question_groups[answer_group]=group_list
            group_list.append(answer_num)


    for group in question_groups.keys():
        group_results = grade_question_group(
            group_list=question_groups[group], 
            user_responses=user_responses,
            answer_info=answer_info, question=question,
            expr_context=expr_context, local_dict=user_dict,
            answer_results=answer_results,
            show_correctness=show_correctness)

        points_achieved += group_results['points_achieved_times_100']
        points_answered += group_results['points_answered']
        
    # record if exactly correct, then normalize points achieved
    if total_points:
        answer_correct = (points_achieved == total_points*100)
        points_achieved /= 100.0
        credit = points_achieved/total_points
        fraction_answered = points_answered/total_points
    else:
        answer_correct = False
        points_achieved /= 100.0
        credit = 0
        fraction_answered = 0

    answer_results['correct'] = answer_correct
    if show_correctness:
        if total_points == 0:
            total_score_feedback = "<p>No points possible for question</p>"
        elif answer_correct:
            total_score_feedback = "<p>Answer is correct</p>"
        elif points_achieved == 0:
            total_score_feedback = "<p>Answer is incorrect</p>"
        else:
            total_score_feedback = '<p>Answer is %s%% correct</p>'\
                % int(round(credit*100))
    else:
        if total_points == 0:
            total_score_feedback = "<p>No points possible for question</p>"
        elif int(round(fraction_answered*10000)) == 10000:
            total_score_feedback = '<p>Received response for entire question.</p>'
        elif points_answered == 0:
            total_score_feedback = '<p>No response received for question.</p>'
        else:
            total_score_feedback = '<p>Received response for %s%% of question.</p>'\
                % int(round(fraction_answered*100))


    answer_results['feedback'] = total_score_feedback + \
        answer_results['feedback']

    answer_results['credit']=credit
    answer_results['fraction_answered']=fraction_answered

    return answer_results
