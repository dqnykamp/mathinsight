from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.customized_commands import *
from mitesting.sympy_customized import parse_and_process, bottom_up, customized_sort_key, SymbolCallable, TupleNoParen, Symbol
from sympy import Tuple, Function
from sympy.parsing.sympy_tokenize import TokenError
import six
import re

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
         'DiffSubs': DiffSubs,
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
                             local_dict=None, evaluate_level=None,
                             assume_real_variables=False):
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
        parsed_list = parse_and_process(
            expression_list, local_dict=local_dict,
            evaluate_level=evaluate_level,
            assume_real_variables=assume_real_variables)
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
                           default_value=None, evaluate_level=None,
                           assume_real_variables=False):
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
        local_dict_sub = {}

    # test evaluate with the local_dict_sub to check for errors in format
    try:
        expr2= parse_and_process(expression, local_dict=local_dict_sub,
                                 evaluate_level=evaluate_level,
                                 assume_real_variables=assume_real_variables)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for function: " + expression)

    if default_value is None:
        default_value = parse_and_process(
            expression, local_dict=local_dict, evaluate_level=evaluate_level,
            assume_real_variables=assume_real_variables)

    expression_string=expression
    
    # parsed_function is a class that stores the expression string
    # and the input list, substitutes the function arguments
    # for the input_list symbols, and then parses with the resulting local_dict
    class _parsed_function(ParsedFunction):
        # Store information for evaluation
        # On evaluation, it must take the number of arguments in input_list
        the_input_list = input_list
        nargs = len(input_list)

        unparsed_expression = expression_string
        local_dict = local_dict_sub
        the_evaluate_level = evaluate_level
        real_variables = assume_real_variables

        default=default_value

        # on evaluation replace any occurences of inputs in expression
        # with the values from the arguments
        @classmethod
        def eval(cls, *args):
            eval_local_dict=cls.local_dict.copy()

            # can't use nargs here as it is converted to a set
            # so instead use len(input_list)
            for i in range(len(cls.the_input_list)):
                eval_local_dict[cls.the_input_list[i]] = args[i]

            return parse_and_process(cls.unparsed_expression,
                                     local_dict=eval_local_dict,
                                     evaluate_level=cls.the_evaluate_level,
                                     assume_real_variables=cls.real_variables)

    # must assign to __name__ outside class definition 
    # so it overwrites default name
    _parsed_function.__name__ = str(name)

    return _parsed_function


def replace_intervals(expression, replace_symmetric=True):
    """
    Look for combinations of opening ( or [, comma, and closing ) or ].
    If find both, them replace with 
    __Interval__(... , left_open===True/False, right_open===True/False).

    With nested combinations of this pattern,
    only the inner combination is converted to an Interval

    If replace_symmetric=True, then open intervals of form (1,2) 
    and closed intervals of form [1,2] are converted.
    Otherwise, only half-open intervals are converted,
    and open/closed intervals are untouched.

    returns 
    - string with __Intervals__()

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

        if not replace_symmetric and left_open==right_open:
            continue

        expr_interval += expression[last_ind:left_ind]

        # have to use === to specify keywords since 
        # customized parse_expr converts = to Eq
        expr_interval += " __Interval__(%s,left_open===%s, right_open===%s)" % \
                 (expression[left_ind+1:right_ind],
                  left_open, right_open)

        last_ind=right_ind+1
    expr_interval += expression[last_ind:]

    return expr_interval


def return_matrix_expression(expression, local_dict=None, evaluate_level=None,
                             split_symbols=None, assume_real_variables=False):

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
                            split_symbols=split_symbols,
                            assume_real_variables=assume_real_variables)

    # If expression was a Matrix already, then have a 1x1 matrix
    # whose only element is a matrix.
    # In that case, return just the inner matrix
    if expr.rows==1 and expr.cols==1:
        if isinstance(expr[0,0], Matrix):
            expr=expr[0,0]
    
    return expr
    

def replace_boolean_equals_in(s, evaluate=True):
    """
    Replace and/&, or/|, =, != and "in" contain in s
    with operators to be parsed by sympy
    
    1. Replace 
       - and with &
       - or with |
       - in with placeholder symbole

    2. replace = (not an == or preceded by <, >, or !) with __Eq__(lhs,rhs)
    then replace != (not !==) with __Ne__(lhs,rhs)

    3. replace in placeholder with (rhs).contains(lhs),
       or, if evaluate=False, with (rhs).contains(lhs, evaluate=False)

   
    4. replace & (not an &&) with __And__(lhs,rhs), 
    then replace | (not ||) with __Or__(lhs,rhs).

    __Eq__, __Ne__, __And__, __Or___ must then be mapped to sympy 
    Eq, Ne, And, and Or when parsing
    
    To find lhs and rhs, looks for unmatched parentheses 
    or the presence of certain characters no in parentheses

    Repeats the procedure until can't find more =, !=, &, |, or in
    or until lhs or rhs is blank



    """

    import re

    # replace and/or with &/|
    s=re.sub(r'\band\b',r'&', s)
    s=re.sub(r'\bor\b',r'|', s)

    # replace in with __in_op_pl__
    s=re.sub(r'\bin\b', r'___in_op_pl___', s)

    for i in range(5):
        if i==0:
            pattern = re.compile('[^<>!=](=)[^=]')
            len_op=1
            new_op='__Eq__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==1:
            pattern = re.compile('[^<>!=](!=)[^=]')
            len_op=2
            new_op='__Ne__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==2:
            pattern = re.compile('(___in_op_pl___)')
            len_op=14
            if evaluate:
                new_op='(%s).contains(%s)'
            else:
                new_op='(%s).contains(%s, evaluate=False)'
            reverse_arguments=True
            replace_rhs_intervals=True
            # characters captured in pattern to left of operator
            loffset=0
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==3:
            pattern = re.compile('[^&](&)[^&]')
            len_op=1
            new_op='__And__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
        elif i==4:
            pattern = re.compile('[^\|](\|)[^\|]')
            len_op=1
            new_op='__Or__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
            
        while True:
            mo= pattern.search(s)
            if not mo:
                break
            ind = mo.start(0)+loffset

            # find location of first ( before and not matched by )
            # or at a comma not enclosed in ()
            # count braces and brackets as parens, don't track them separately
            n_closepar=0
            begin_pos=0
            for (j,c) in enumerate(s[ind-1::-1]):
                if c==")" or c=="}" or c=="]":
                    n_closepar+=1
                elif c=="(" or c=="{" or c=="[":
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
                if c=="(" or c=="{" or c=="[":
                    n_openpar+= 1
                elif c==")" or c=="}" or c=="]":
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
                if replace_rhs_intervals:
                    rhs = replace_intervals(rhs, replace_symmetric=True)
                if reverse_arguments:
                    new_command_string = new_op % (rhs,lhs)
                else:
                    new_command_string = new_op % (lhs,rhs)
                s = s[:begin_pos] + new_command_string + s[end_pos:]

    return s



def replace_simplified_derivatives(s, local_dict, global_dict, 
                                   split_symbols=False,
                                   assume_real_variables=False):
    """
    Convert expressions such as f'(x) to DerivativePrimeNotation
    and expressions such as df/dx to DerivativeSimplifiedNotation

    If for df/dx, f is not in the local/global dict,
    or it is in the dicts as a Symbol,
    then f is converted to __f_for_deriv__ which is mapped in local_dict
    to SymbolCallable('f')
    If, on the other hand, f is in the local/global dict as
    an object that it not callable, then df/dx is replaced 
    with Derivative(f,x)
    
    Derivatives are converted to __DerivativePrimeNotation__.
    __DerivativeSimplfiedNotation__, and __Derivative__
    which are mapped via global_dict

    """

    from mitesting.sympy_customized import DerivativePrimeNotation, \
        DerivativeSimplifiedNotation

    # replace f'(x) with DerivativePrimeNotation(f(x),x)
    if split_symbols:
        pattern=r"([a-zA-Z])'\ *\("
    else:
        pattern=r"([a-zA-Z_][a-zA-Z0-9_]*)'\ *\("
    s = re.sub(pattern, r' __DerivativePrimeNotation__(\1,', s)

    global_dict['__DerivativePrimeNotation__'] = DerivativePrimeNotation
 


    functions_differentiated = set()
    functions_differentiated_dvar = {}
    # replace df/dx with DerivativeSimplifiedNotation(f(x),x)
    if split_symbols:
        pattern = r"d([a-zA-Z]) */ *d([a-zA-Z])"  # single letter like dx/dt
        # first find all matches and record functions differentiated
        for match in re.findall(pattern, s):
            functions_differentiated.add(match[0])
            dvars=functions_differentiated_dvar.get(match[0], set())
            dvars.add(match[1])
            functions_differentiated_dvar[match[0]]=dvars
        # then substitute
        s = re.sub(pattern, r' __DerivativeSimplifiedNotation__(\1(\2),\2)', s)
    else:
        # possibly multiple letter pattern like dabc/dxyz
        pattern = r"\bd([a-zA-Z_][a-zA-Z0-9_]*) */ *d([a-zA-Z_][a-zA-Z0-9_]*)"
        # first find all matches and record functions differentiated
        for match in re.findall(pattern, s):
            functions_differentiated.add(match[0])
            dvars=functions_differentiated_dvar.get(match[0], set())
            dvars.add(match[1])
            functions_differentiated_dvar[match[0]]=dvars
        s = re.sub(pattern, r' __DerivativeSimplifiedNotation__(\1(\2),\2)', s)

        # possibly multiple letter pattern with number like 10dabc/dxyz
        pattern = r"([0-9])d([a-zA-Z_][a-zA-Z0-9_]*) */ *d([a-zA-Z_][a-zA-Z0-9_]*)"
        # first find all matches and record functions differentiated
        for match in re.findall(pattern, s):
            functions_differentiated.add(match[1])
            dvars=functions_differentiated_dvar.get(match[1], set())
            dvars.add(match[2])
            functions_differentiated_dvar[match[1]]=dvars
        s = re.sub(pattern, r'\1 __DerivativeSimplifiedNotation__(\2(\3),\3)', s)

    global_dict['__DerivativeSimplifiedNotation__'] = DerivativeSimplifiedNotation


    # if functions aren't in local/global dict,
    # or they are in dicts as symbols,
    # then create a SymbolCallable version
    # so that Derivative(x(t),t) does not become Derivative(x*t,t)
    # with implicit multiplication transformation
    for fun in functions_differentiated:
        fun_mapped=None
        new_symbol=None
        if fun in local_dict:
            fun_mapped=local_dict[fun]
        elif fun in global_dict:
            fun_mapped=global_dict[fun]

        if fun_mapped is None:
            if assume_real_variables:
                new_symbol = SymbolCallable(str(fun), real=True)
            else:
                new_symbol = SymbolCallable(str(fun))
        else:
            try:
                if fun_mapped.__class__ == Symbol:
                    if assume_real_variables:
                        new_symbol=SymbolCallable(str(fun_mapped), real=True)
                    else:
                        new_symbol=SymbolCallable(str(fun_mapped))
            except AttributeError:
                pass

        if new_symbol is None:
            if not callable(fun_mapped):
                # if not differentiating with response to callable
                # convert to regular derivative and don't attempt
                # to evaluate at the variable of differentiation
                for dvar in functions_differentiated_dvar[fun]:
                    s=re.sub(r'__DerivativeSimplifiedNotation__\(%s\(%s\)' \
                             % (fun, dvar),
                             r'__Derivative__('+fun, s)

                from sympy import Derivative
                global_dict['__Derivative__'] = Derivative

        else:
            fun_obscured = "__%s_for_deriv__" % fun
            s=re.sub(r'__DerivativeSimplifiedNotation__\('+fun, 
                      r'__DerivativeSimplifiedNotation__('+fun_obscured, s)
            local_dict[fun_obscured]=new_symbol
    return s



def evaluate_expression(the_expr, rng, 
                        local_dict=None, user_function_dict=None,
                        random_group_indices=None,
                        new_alternate_dicts=[],
                        new_alternate_exprs=[]):

    from sympy.core.function import UndefinedFunction
    from mitesting.math_objects import math_object

    # if randomly selecting from a list,
    # determine if the index for random_list_group was chosen already
    if the_expr.expression_type in [the_expr.RANDOM_WORD,
                                the_expr.RANDOM_EXPRESSION,
                                the_expr.RANDOM_FUNCTION_NAME]:

        if the_expr.random_list_group:
            try:
                group_index = random_group_indices.get(\
                                        the_expr.random_list_group)
            except AttributeError:
                group_index = None
        else:
            group_index = None

        # treat RANDOM_WORD as special case
        # as it involves two outputs and hasn't been
        # parsed by sympy
        # Complete all processing and return
        if the_expr.expression_type == the_expr.RANDOM_WORD:
            try:
                result = return_random_word_and_plural( 
                    the_expr.expression, index=group_index, rng=rng)
            except IndexError:
                raise IndexError("Insufficient entries for random list group: " \
                                     + the_expr.random_list_group)

            # record index chosen for random list group, if group exist
            if the_expr.random_list_group:
                try:
                    random_group_indices[the_expr.random_list_group]\
                        =result[2]
                except TypeError:
                    pass

            # attempt to add word to local dictionary
            word_text=re.sub(' ', '_', result[0])
            sympy_word = Symbol(word_text)
            try:
                local_dict[the_expr.name]=sympy_word
            except TypeError:
                pass

            return (result[0], result[1])

        try:
            (math_expr, index) = return_random_expression(
                the_expr.expression, index=group_index,
                local_dict=local_dict,
                evaluate_level = the_expr.evaluate_level, rng=rng,
                assume_real_variables=the_expr.real_variables)
        except IndexError:
            raise IndexError("Insufficient entries for random list group: " \
                                     + the_expr.random_list_group)

        if the_expr.expression_type == the_expr.RANDOM_FUNCTION_NAME:

            # math_expr should be a Symbol or an UndefinedFunction
            # otherwise not a valid function name
            if not (isinstance(math_expr,Symbol) or
                    isinstance(math_expr,UndefinedFunction)):
                raise ValueError("Invalid function name: %s " \
                                 % math_expr)


            # turn to SymbolCallable and add to user_function_dict
            # should use:
            # function_text = six.text_type(math_expr)
            # but sympy doesn't yet accept unicode for function name
            function_text = str(math_expr)
            if the_expr.real_variables:
                math_expr = SymbolCallable(function_text, real=True)
            else:
                math_expr = SymbolCallable(function_text)
            try:
                user_function_dict[function_text] = math_expr
            except TypeError:
                pass


        # record index chosen for random list group, if group exists
        if the_expr.random_list_group:
            try:
                random_group_indices[the_expr.random_list_group]=index
            except TypeError:
                pass

    elif the_expr.expression_type == the_expr.RANDOM_NUMBER:
        math_expr = return_random_number_sample(
            the_expr.expression, local_dict=local_dict, rng=rng)

    # if not randomly generating
    else:

        math_expr = None
        expression = the_expr.expression

        # if interval, try replacing opening and closing parens with interval
        if the_expr.expression_type == the_expr.INTERVAL:
            try:
                math_expr = parse_and_process(
                    expression, local_dict=local_dict,
                    evaluate_level = the_expr.evaluate_level,
                    replace_symmetric_intervals=True,
                    assume_real_variables=the_expr.real_variables)

            except (TypeError, NotImplementedError, SyntaxError, TokenError):
                math_expr=None
            except ValueError as e:
                if "real intervals" in e.args[0]:
                    raise ValueError("Variables used in intervals must be real")
                else:
                    math_expr=None

        elif the_expr.expression_type == the_expr.MATRIX:
            try:
                math_expr = return_matrix_expression(
                    expression, local_dict=local_dict, 
                    evaluate_level = the_expr.evaluate_level,
                    assume_real_variables = the_expr.real_variables)
            except ValueError as e:
                raise ValueError("Invalid format for matrix\n%s" % e.args[0])
            except (TypeError, NotImplementedError, SyntaxError, TokenError):
                raise ValueError("Invalid format for matrix")
        try:
            if math_expr is None:
                math_expr = parse_and_process(
                    expression, local_dict=local_dict,
                    evaluate_level = the_expr.evaluate_level,
                    assume_real_variables = the_expr.real_variables)
        except (TokenError, SyntaxError, TypeError, AttributeError):
            if the_expr.expression_type in [
                the_expr.RANDOM_ORDER_TUPLE,
                the_expr.UNORDERED_TUPLE, the_expr.SORTED_TUPLE]:
                et = "tuple"
            elif the_expr.expression_type == the_expr.SET:
                et = "set"
            elif the_expr.expression_type == the_expr.INTERVAL:
                et = "interval"
            elif the_expr.expression_type == the_expr.CONDITION:
                et = "condition"
            elif the_expr.expression_type == the_expr.FUNCTION:
                et = "function"
            elif the_expr.expression_type == the_expr.EXPRESSION_WITH_ALTERNATES:
                et = "expression with alternates"
            else:
                et = "expression"
            raise ValueError("Invalid format for %s: %s" \
                                 % (et, the_expr.expression))
        except ValueError as e:
            if "real intervals" in e.args[0]:
                raise ValueError("Variables used in intervals must be real")
            else:
                raise

        # If a set and didn't include braces, will be a TupleNoParen.
        # In that case, convert to set and back to remove duplicates
        if the_expr.expression_type == the_expr.SET and \
           isinstance(math_expr, TupleNoParen):
            math_expr = TupleNoParen(*set(math_expr))


        # if VECTOR, convert Tuples to column matrices
        # and convert column and row matrices to MatrixAsVector
        # which latexs as a vector
        if the_expr.expression_type == the_expr.VECTOR:
            from mitesting.customized_commands import \
                MatrixFromTuple, MatrixAsVector
            from sympy import Matrix

            math_expr = math_expr.replace(Tuple,MatrixFromTuple)

            def to_matrix_as_vector(w):
                if isinstance(w,Matrix) and (w.cols==1 or w.rows==1):
                    return MatrixAsVector(w)
                return w

            math_expr=bottom_up(math_expr,to_matrix_as_vector,
                                nonbasic=True)


        # if CONDITION is not met, raise exception
        if the_expr.expression_type == the_expr.CONDITION:
            try:
                if not math_expr:
                    from mitesting.models import Expression
                    raise Expression.FailedCondition(
                        "Condition %s was not met" % the_expr.name)
            except TypeError:
                # symbolic will raise type error.  Consider test failed.
                message= "Could not determine truth value of required condition %s, evaluated as: %s" % (the_expr.expression, math_expr)
                if re.search('!=[^=]',the_expr.expression):
                    message += "\nComparison != returns truth value only for numerical values.  Use !== to compare if two symbolic expressions are not identical."
                if re.search('[^<>!=]=[^=]',the_expr.expression):
                    message += "\nComparison = returns truth value only for numerical values.  Use == to compare if two symbolic expressions are identical."
                raise TypeError(message)


        if the_expr.expression_type == the_expr.RANDOM_ORDER_TUPLE:
            if isinstance(math_expr,list):
                rng.shuffle(math_expr)
            elif isinstance(math_expr, Tuple):
                the_class=math_expr.__class__
                math_expr = list(math_expr)
                rng.shuffle(math_expr)
                math_expr = the_class(*math_expr)
        elif the_expr.expression_type == the_expr.SORTED_TUPLE:
            if isinstance(math_expr,list):
                math_expr.sort(key=customized_sort_key)
            elif isinstance(math_expr, Tuple):
                the_class=math_expr.__class__
                math_expr = list(math_expr)
                math_expr.sort(key=customized_sort_key)
                math_expr = the_class(*math_expr)

        if the_expr.expression_type == the_expr.FUNCTION_NAME:
            # math_expr should be a Symbol or an UndefinedFunction
            # otherwise not a valid function name
            if not (isinstance(math_expr,Symbol) or
                    isinstance(math_expr,UndefinedFunction)):
                raise ValueError("Invalid function name: %s " \
                                 % math_expr)


            # turn to SymbolCallable and add to user_function_dict
            # should use:
            # function_text = six.text_type(math_expr)
            # but sympy doesn't yet accept unicode for function name
            function_text = str(math_expr)
            if the_expr.real_variables:
                math_expr = SymbolCallable(function_text,real=True)
            else:
                math_expr = SymbolCallable(function_text)
            try:
                user_function_dict[function_text] = math_expr
            except TypeError:
                pass


        if the_expr.expression_type == the_expr.FUNCTION:
            parsed_function = return_parsed_function(
                the_expr.expression, function_inputs=the_expr.function_inputs,
                name = the_expr.name, local_dict=local_dict,
                default_value=math_expr, 
                evaluate_level = the_expr.evaluate_level,
                assume_real_variables = the_expr.real_variables)

            # for FUNCTION, add parsed_function rather than
            # math_expr to local dict
            try:
                local_dict[the_expr.name] = parsed_function   
            except TypeError:
                pass

        # if EXPRESSION_WITH_ALTERNATES and is TupleNoParen,
        # then add all but first entry to new_alternates_[dicts/exprs]
        # and let math_expr be the first entry
        if the_expr.expression_type == the_expr.EXPRESSION_WITH_ALTERNATES:
            if isinstance(math_expr, TupleNoParen):
                for e in math_expr[1:]:
                    alt_dict = local_dict.copy()
                    alt_dict[the_expr.name] = e
                    new_alternate_dicts.append(alt_dict)
                    new_alternate_exprs.append(math_object(
                        e, name=the_expr.name,
                        evaluate_level = the_expr.evaluate_level,
                        expression_type=the_expr.expression_type,
                        assume_real_variables = the_expr.real_variables))
                math_expr=math_expr[0]

    # for all expression_types except FUNCTION (and RANDOM WORD)
    # add math_expr to local dict
    if not the_expr.expression_type == the_expr.FUNCTION:
        try:
            # convert list to Tuple
            if isinstance(math_expr,list):
                local_dict[the_expr.name] = Tuple(*math_expr)
            # for boolean, convert to sympy integer
            elif isinstance(math_expr,bool):
                local_dict[the_expr.name] = sympify(int(math_expr))
            else:
                local_dict[the_expr.name] = math_expr
        except TypeError:
            pass

    # for all expression_types (except RANDOM WORD)
    # return math_object of math_expr to context
    return math_object(
        math_expr, name=the_expr.name,
        evaluate_level = the_expr.evaluate_level,
        tuple_is_unordered=(the_expr.expression_type==the_expr.UNORDERED_TUPLE
                            or the_expr.expression_type==the_expr.SET),
        expression_type=the_expr.expression_type,
        assume_real_variables = the_expr.real_variables)
