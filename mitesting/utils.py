from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.customized_commands import *
from mitesting.sympy_customized import parse_and_process
from sympy import Tuple, Function, Symbol
from sympy.parsing.sympy_tokenize import TokenError
import six


def return_sympy_local_dict(allowed_sympy_commands=[]):
    """
    Make a whitelist of allowed commands sympy and customized commands.
    Argument allowed_sympy_commands is an iterable containing
    strings of comma separated commands names.
    Returns a dictionary where keys are the command names and 
    values are the corresponding function or sympy expression.
    The local dictionary contains
    1.  all greek symbols from create_greek_dict()
    2.  the allowed sympy_commands that match localized commands
    3.  the allowed sympy_commands that match standard sympy commands.
    Command names that don't match either customized or sympy commands
    are ignored.
    """

    # create a dictionary containing all sympy commands
    all_sympy_commands = {}
    exec "from sympy import *" in all_sympy_commands

    # create a dictionary containing the localized commands
    localized_commands = \
        {'roots_tuple': roots_tuple, 
         'real_roots_tuple': real_roots_tuple, 
         'round': round_expression,
         'smallest_factor': smallest_factor,
         'e': all_sympy_commands['E'], 
         'max': max_including_tuples,
         'Max': max_including_tuples,
         'min': min_including_tuples,
         'Min': min_including_tuples,
         'abs': Abs,
         'evalf': evalf_expression,
         'index': index,
         'sum': sum,
         'if': iif,
         'len': len,
         'log': log, 'ln': ln, 'exp': exp, 
         'count': count,
         'Point': Point,
         'acosh': acosh, 'acos': acos, 'acosh': acosh, 
         'acot': acot, 'acoth': acoth, 'asin': asin, 'asinh': asinh, 
         'atan': atan, 'atan2': atan2, 'atanh': atanh, 
         'cos': cos, 'cosh': cosh, 'cot': cot, 'coth': coth, 'csc': csc, 
         'sec': sec, 'sin': sin, 'sinh': sinh, 'tan': tan, 'tanh': tanh, 
        }
    
    # create a set of allowed commands containing all comma-separated
    # strings from allowed_sympy_commands
    allowed_commands = set()
    for commandstring in allowed_sympy_commands:
        allowed_commands=allowed_commands.union(
            [item.strip() for item in commandstring.split(",")])

    # create the dictionary
    local_dict = {}

    for command in allowed_commands:
        try:
            # attempt to match command with localized command
            local_dict[str(command)]=localized_commands[command]
        except KeyError:
            try:
                # if command isn't found in localized command
                # then attempt to match with standard sympy command
                local_dict[str(command)]=all_sympy_commands[command]
            except KeyError:
                pass

    return local_dict



def return_random_number_sample(expression, rng, local_dict=None):
    """
    Returns a randomly generated number based on string.
    Expression is first parsed via sympy using local_dict, if specified.
    Resulting expression should be a tuple: (minval, maxval, [increment])
    If increment is omitted, set it to 1.
    Result will be number generated uniformly from numbers
    of the form: expr = minval + i * increment
    where i is a non-negative integer and expr <= maxval.
    """
    
    try:
        number_params = parse_and_process(expression, 
                                          local_dict=local_dict)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for random number: " + expression + "\nRequired format: (minval, maxval, [increment])")

    if not isinstance(number_params, Tuple) or len(number_params) < 2 \
            or len(number_params) > 3: 
        raise ValueError("Invalid format for random number: " + expression + "\nRequired format: (minval, maxval, [increment])")
    
    min_value = number_params[0]
    max_value = number_params[1]
    if(len(number_params) >= 3):
        increment = number_params[2]
    else:
        increment = 1

    from math import floor
    try:
        if min_value > max_value:
            raise ValueError("In expression defining random number, require minval <= maxval.  However, %s > %s." % (min_value, max_value)  + "\nRequired format: (minval, maxval, [increment])")
        
        # multiply by 1+1E-10 before rounding down to integer
        # so small floating point errors don't bring it down to next integer
        num_possibilities = 1+int(floor((max_value-min_value)/increment) \
                                      *(1+1E-10))
    except TypeError:
        raise TypeError("Expression defining random number must contain numbers: " + str(number_params) + "\nRequired format: (minval, maxval, [increment])")
    choices=[min_value+n*increment for n in range(num_possibilities)]
    the_num = rng.choice(choices)

    # if the_num is an integer, convert to integer so don't have decimal
    if int(the_num)==the_num:
        the_num = int(the_num)
    else:
        # try to round the answer to the same number of decimal places
        # as the input values
        # seems to help with rounding error with the float arithmetic
        for i in range(1,11):
            if(round(min_value*pow(10,i)) == min_value*pow(10,i)
               and round(max_value*pow(10,i)) == max_value*pow(10,i)
               and round(increment*pow(10,i)) == increment*pow(10,i)):
                the_num = round(the_num,i)
                break
                
    return sympify(the_num)


def return_random_word_and_plural(expression_list, rng, index=None):
    """
    Return word and its plural chosen from string.
    Expression_list is a command separated list of tuples.
    The first element of the tuple is the singular form
    and the second element is the plural form.
    Each element can be either a word or a quoted string.
    If the plural is just the singular form appended with an s,
    the tuple can be replaced a singleton element of the sinular form.

    If index is given, that item from the list is returned.
    If index is none, items is chosen randomly and uniformly from
    all entries.

    Returns a tuple containing the word, its plural, and the
    index of word from the list.
    """
    
    required_format_text = "Required format: w1, w2, ...\n" \
        + "where each w could be of the following forms:\n" \
        + "word, (word, plural), \"a phrase\", " \
        + "or (\"a phrase\", \"a plural phrase\")"

    # define pyparsing syntax to parse nested tuples
    from pyparsing import Literal, Word, quotedString, Forward, \
        Group, ZeroOrMore, alphanums
    allowedchars = alphanums+"!#$%&*+-.:;<=>?@^_|~"
    def Syntax():
        op = Literal(',').suppress()
        lpar  = Literal( '(' ).suppress()
        rpar  = Literal( ')' ).suppress()
        word = Word(allowedchars) | quotedString
        expr = Forward()
        atom = word | Group( lpar + expr + rpar )
        expr <<= atom + ZeroOrMore( op + expr )
        return expr

    def remove_quotes(expression):
        if (expression[0]=='"' and expression[-1]=='"') \
                or (expression[0]=="'" and expression[-1]=="'"):
            return expression[1:-1]
        return expression

    parser = Syntax()
    try:
        parsed_expression = parser.parseString(expression_list).asList()
    except:
        raise ValueError("Invalid format for random word: "+ expression_list
                         + "\n" + required_format_text)

        
    # check if parsed the whole selection and if have only one level of 
    # recursion.
    last_expr = expression_list.split(",")[-1].strip()
    if last_expr[-1]==")":
        last_expr = last_expr[:-1].strip()
        if parsed_expression[-1][-1] != last_expr:
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "\n" + required_format_text)

    else:
        if parsed_expression[-1] != last_expr:
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "\n" + required_format_text)
        
    for expr in parsed_expression:
        if isinstance(expr, list):
            if len(expr) > 2:
                raise ValueError("Invalid format for random word: "
                                 + expression_list
                                 + "\n" + required_format_text)

            for expr2 in expr:
                if isinstance(expr2, list):
                    raise ValueError("Invalid format for random word: "
                                     + expression_list
                                     + "\n" + required_format_text)
                
    option_list=[]
    plural_list=[]
    for item in parsed_expression:
        if isinstance(item,list):
            option_list.append(remove_quotes(item[0]))
            plural_list.append(remove_quotes(item[1]))
        else:
            item = remove_quotes(item)
            option_list.append(item)
            plural_list.append(item + "s")

    # if index isn't prescribed, generate randomly
    if index is None:
        index = rng.randrange(len(option_list))

    the_word=option_list[index]
    the_plural=plural_list[index]

    return (the_word, the_plural, index)


def return_random_expression(expression_list, rng, index=None, 
                             local_dict=None, evaluate_level=None):
    """
    Return an expression from a string containing comma-separated list.
    Expression_list is first parsed with sympy using local_dict, if given.
    If index is given, that item from the list is returned.
    If index is none, items is chosen randomly and uniformly from
    all entries.

    Returns a tuple containing the expression 
    and the index of the expression from the list.
    """
    
    try:
        parsed_list = parse_and_process(expression_list, 
                                        local_dict=local_dict,
                                        evaluate_level=evaluate_level)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for random expression: "
                         + expression_list
                         + "\nRequired format: expr1, expr2, ...")
    

    
    the_expression=None
    # if index isn't prescribed, generate randomly
    if index is None:
        try:
            index = rng.randrange(len(parsed_list))
        except TypeError:
            # if didn't specify index and parsed_list isn't a list,
            # then use whole expression for function name
            the_expression=parsed_list
            index=0

    # if didn't chose expression yet, get entry specified by index
    if the_expression is None:
        try:
            the_expression = parsed_list[index]
        except TypeError:
            raise ValueError("Invalid format for random expression: "
                             + expression_list
                             + "\nRequired format: expr1, expr2, ...")
    
    return (the_expression, index)


class ParsedFunction(Function):
    pass

def return_parsed_function(expression, function_inputs, name,
                           local_dict=None, 
                           default_value=None):
    """
    Parse expression into function of function_inputs,
    a subclass of ParsedFunction.

    The expression field must be a mathematical expression
    and the function inputs field must be a tuple of symbols.
    The expression will be then viewed as a function of the
    function input symbol(s). 
    Substitutions from local_dict will be made in expression
    except values from function_inputs will be ignored.

    The .default argument returns default_value, if exists.
    Else .default will be set to expression parsed with all
    substitutions from local_dict.
    """

    input_list = [six.text_type(item.strip())
                  for item in function_inputs.split(",")]
    # if no inputs, make empty list so function with no arguments
    if input_list == ['']:
        input_list = []

    # if any input variables are in local_dict,
    # remove them from local_dict so they will not be substituted
    if local_dict:
        local_dict_sub = dict((key, local_dict[key]) 
                               for key in local_dict.keys()
                               if key not in input_list)
    else:
        local_dict_sub = None

    try:
        expr2= parse_and_process(expression, local_dict=local_dict_sub)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for function: " + expression)

    if default_value is None:
        default_value = parse_and_process(expression, local_dict=local_dict)

    
    # parsed_function is a class that stores the expression
    # and the input list, substituting the function arguments
    # for the input_list symbols on evaluation
    class _parsed_function(ParsedFunction):
        # Store information for evaluation
        # On evaluation, it must take the number of arguments in input_list
        the_input_list = input_list
        nargs = len(input_list)

        expression = expr2

        default=default_value

        # on evaluation replace any occurences of inputs in expression
        # with the values from the arguments
        @classmethod
        def eval(cls, *args):
            expr_sub=cls.expression
            # can't use nargs here as it is converted to a set
            # so instead use len(input_list)
            replace_dict={}
            for i in range(len(cls.the_input_list)):
                replace_dict[Symbol(cls.the_input_list[i])] =  args[i]
            expr_sub=expr_sub.xreplace(replace_dict)
            return expr_sub


    # must assign to __name__ outside class definition 
    # so it overwrites default name
    _parsed_function.__name__ = str(name)

    return _parsed_function


def return_interval_expression(expression, local_dict=None, evaluate_level=None,
                               split_symbols=None):
    """
    Look for combinations of opening ( or [, comma, and closing ) or ].
    If find both, them replace with 
    Interval(... , left_open===True/False, right_open===True/False)
    and attempt to parse

    With nested combinations of this pattern,
    only the inner combination is converted to an Interval

    returns 
    - expression parsed with intervals

    raises value error if interval limit is not real

    """

    left_inds=[]
    left_opens=[]
    n_commas=[]
    intervals_contained=[]
    found_combinations=[]
    
    for (i,char) in enumerate(expression):
        if char=='(' or char== "[":
            left_opens.append(char=="(")
            left_inds.append(i)
            n_commas.append(0)
            intervals_contained.append(False)
        elif char==',':
            if len(n_commas)>0:
                n_commas[-1] += 1
        elif char==')' or char=="]":
            if len(left_opens)>0:
                found_interval = (n_commas.pop()==1)
                interval_inside = intervals_contained.pop()
                # only add interval if found command and 
                # there is no interval contained inside
                if found_interval:
                    if not interval_inside:
                        found_combinations.append({
                            'left_open': left_opens.pop(),
                            'left_ind': left_inds.pop(),
                            'right_open': (char==")"), 'right_ind': i})
                    # record fact that have interval inside parent
                    if len(intervals_contained) >0:
                        intervals_contained[-1]=True
                else:
                    left_opens.pop()
                    left_inds.pop()
                    if len(intervals_contained) > 0:
                        # propogate presence of interval to parent
                        intervals_contained[-1]=interval_inside

    last_ind=0
    expr_interval=""
    for interval in found_combinations:
        left_ind=interval['left_ind']
        right_ind=interval['right_ind']
        left_open=interval['left_open']
        right_open=interval['right_open']

        expr_interval += expression[last_ind:left_ind]

        # have to use === to specify keywords since 
        # customized parse_expr convert = to Eq
        expr_interval += " Interval(%s,left_open===%s, right_open===%s)" % \
                 (expression[left_ind+1:right_ind],
                  left_open, right_open)

        last_ind=right_ind+1
    expr_interval += expression[last_ind:]

    new_local_dict = {}
    if local_dict:
        new_local_dict.update(local_dict)
    from sympy import Interval
    new_local_dict['Interval'] = Interval

    return parse_and_process(expr_interval, local_dict=new_local_dict,
                             evaluate_level = evaluate_level,
                             split_symbols=split_symbols)


def return_matrix_expression(expression, local_dict=None, evaluate_level=None,
                             split_symbols=None):

    import re
    
    expr_matrix=re.sub(r" *\n *", "],[", expression.strip())
    expr_matrix="Matrix([[" + re.sub(r" +", ",", expr_matrix)+"]])"
    
    new_local_dict = {}
    if local_dict:
        new_local_dict.update(local_dict)
    from sympy import Matrix
    new_local_dict['Matrix'] = Matrix

    expr= parse_and_process(expr_matrix, local_dict=new_local_dict,
                             evaluate_level = evaluate_level,
                             split_symbols=split_symbols)

    # If expression was a Matrix already, then have a 1x1 matrix
    # whose only element is a matrix.
    # In that case, return just the inner matrix
    if expr.rows==1 and expr.cols==1:
        if isinstance(expr[0,0], Matrix):
            expr=expr[0,0]
    
    return expr
    

def replace_boolean_equals(s):
    """
    Replace and/&, or/|, =, and != in s with symbols to be parsed by sympy

    1. Replace and with & and or with |
    
    2. replace = (not an == or preceded by <, >, or !) with __Eq__(lhs,rhs)
    then replace != (not !==) with __Ne__(lhs,rhs)

    3. replace & (not an &&) with __And__(lhs,rhs), 
    then replace | (not ||) with __Or__(lhs,rhs).

    __Eq__, __Ne__, __And__, __Or___ must then be mapped to sympy 
    Eq, Ne, And, and Or when parsing
    
    To find lhs and rhs, looks for unmatched parentheses 
    or the presence of certain characters no in parentheses

    Repeats the procedure until can't find more =, !=, &, or |
    or until lhs or rhs is blank



    """

    import re

    # replace and/or with &/|
    s=re.sub(r'\band\b',r'&', s)
    s=re.sub(r'\bor\b',r'|', s)

    for i in range(4):
        if i==0:
            pattern = re.compile('[^<>!=](=)[^=]')
            len_op=1
            new_op='__Eq__(%s,%s)'
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==1:
            pattern = re.compile('[^<>!=](!=)[^=]')
            len_op=2
            new_op='__Ne__(%s,%s)'
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==2:
            pattern = re.compile('[^&](&)[^&]')
            len_op=1
            new_op='__And__(%s,%s)'
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
        elif i==3:
            pattern = re.compile('[^\|](\|)[^\|]')
            len_op=1
            new_op='__Or__(%s,%s)'
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
            
        while True:
            mo= pattern.search(s)
            if not mo:
                break
            ind = mo.start(0)+1

            # find location of first ( before ind not matched by )
            # or at a comma not enclosed in ()
            n_closepar=0
            begin_pos=0
            for (j,c) in enumerate(s[ind-1::-1]):
                if c==")":
                    n_closepar+=1
                elif c=="(":
                    n_closepar-=1
                    if n_closepar ==-1:
                        begin_pos=ind-j
                        break
                elif c in break_chars and n_closepar==0:
                    begin_pos=ind-j
                    break

            lhs = s[begin_pos:ind]
            lhs =lhs.strip()

            n_openpar=0
            end_pos=len(s)
            for (j,c) in enumerate(s[ind+len_op:]):
                if c=="(":
                    n_openpar+= 1
                elif c==")":
                    n_openpar-=1
                    if n_openpar==-1:
                        end_pos=ind+j+len_op
                        break
                elif c in break_chars and n_openpar==0:
                    end_pos=ind+j+len_op
                    break

            rhs = s[ind+len_op:end_pos]
            rhs = rhs.strip()

            # stop if lhs or rhs are just spaces
            if lhs=="" or rhs=="":
                break
            else:
                s = s[:begin_pos] + (new_op % (lhs,rhs)) + s[end_pos:]

    return s
