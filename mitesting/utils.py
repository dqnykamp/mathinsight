
from mitesting.sympy_customized import parse_and_process, bottom_up, customized_sort_key, SymbolCallable, TupleNoParen
from sympy import Tuple, Function, sympify, Symbol
from sympy.parsing.sympy_tokenize import TokenError
import six
import re

def get_new_seed(rng=None, seed=None):
    if not rng:
        import random
        rng=random.Random()

    if seed is not None:
        rng.seed(seed)

    return str(rng.randint(0,1E8))

def return_sympy_local_dict(allowed_sympy_commands=[]):
    """
    Make a whitelist of allowed commands sympy and customized commands.
    Argument allowed_sympy_commands is an iterable containing
    strings of comma separated commands names.
    Returns a dictionary where keys are the command names and 
    values are the corresponding function or sympy expression.
    The local dictionary contains
    1.  the allowed sympy_commands that match localized commands
    2.  the allowed sympy_commands that match standard sympy commands.
    Command names that don't match either customized or sympy commands
    are ignored.
    """

    from mitesting.user_commands import return_localized_commands
    localized_commands = return_localized_commands()

    # create a set of allowed commands containing all comma-separated
    # strings from allowed_sympy_commands
    allowed_commands = set()
    for commandstring in allowed_sympy_commands:
        allowed_commands=allowed_commands.union(
            [item.strip() for item in commandstring.split(",")])

    # create a dictionary containing all sympy commands
    all_sympy_commands = {}
    exec("from sympy import *", all_sympy_commands)

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



def return_random_number_sample(expression, rng, local_dict=None, index=None):
    """
    Returns a randomly generated number based on string, along with the
    index chosen from list of all possibilities
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
        raise ValueError("Invalid format for random number: " + expression + "<br/>Required format: (minval, maxval, [increment])")

    if not isinstance(number_params, Tuple) or len(number_params) < 2 \
            or len(number_params) > 3: 
        raise ValueError("Invalid format for random number: " + expression + "<br/>Required format: (minval, maxval, [increment])")
    
    min_value = number_params[0]
    max_value = number_params[1]
    if(len(number_params) >= 3):
        increment = number_params[2]
    else:
        increment = 1

    from math import floor
    try:
        if min_value > max_value:
            raise ValueError("In expression defining random number, require minval <= maxval.  However, %s > %s." % (min_value, max_value)  + "<br/>Required format: (minval, maxval, [increment])")
        
        # multiply by 1+1E-10 before rounding down to integer
        # so small floating point errors don't bring it down to next integer
        num_possibilities = 1+int(floor((max_value-min_value)/increment) \
                                      *(1+1E-10))
    except TypeError:
        raise TypeError("Expression defining random number must contain numbers: " + str(number_params) + "<br/>Required format: (minval, maxval, [increment])")

    choices=[min_value+n*increment for n in range(num_possibilities)]

    if index is not None:
        if index < 0 or index >= num_possibilities:
            index=None
    if index is None:
        #index = int(rng.random() * num_possibilities)  # like python 2.7 choice
        index = rng.randrange(num_possibilities)

    the_num = choices[index]

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
                
    return sympify(the_num), index


def return_random_word_and_plural(expression_list, rng, index=None,
                                  allow_index_resample=False):
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

    If allow_index_resample, then resample randomly if index is invalid.
    Otherwise, raise IndexError if index is invalid

    Returns a tuple containing the word, its plural, and the
    index of word from the list.
    """
    
    required_format_text = "Required format: w1, w2, ...<br/>" \
        + "where each w could be of the following forms:<br/>" \
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
                         + "<br/>" + required_format_text)

    
    # check if parsed the whole selection and if have only one level of 
    # recursion.
    expr_split=expression_list.split(",")
    last_expr = expr_split[-1].strip()
    if last_expr=="":
        try:
            last_expr = expr_split[-2].strip()
        except IndexError:
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "<br/>" + required_format_text)
        if last_expr == "":
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "<br/>" + required_format_text)
    if last_expr[-1]==")":
        last_expr = last_expr[:-1].strip()
        if parsed_expression[-1][-1] != last_expr:
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "<br/>" + required_format_text)

    else:
        if parsed_expression[-1] != last_expr:
            raise ValueError("Invalid format for random word: "+ expression_list
                             + "<br/>" + required_format_text)
        
    for expr in parsed_expression:
        if isinstance(expr, list):
            if len(expr) > 2:
                raise ValueError("Invalid format for random word: "
                                 + expression_list
                                 + "<br/>" + required_format_text)

            for expr2 in expr:
                if isinstance(expr2, list):
                    raise ValueError("Invalid format for random word: "
                                     + expression_list
                                     + "<br/>" + required_format_text)
                
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

    try:
        the_word=option_list[index]
        the_plural=plural_list[index]
    except IndexError:
        if allow_index_resample:
            # resample and try again
            index = rng.randrange(len(option_list))
            the_word=option_list[index]
            the_plural=plural_list[index]
        else:
            raise

    return (the_word, the_plural, index)


def return_random_expression(expression_list, rng, index=None, 
                             local_dict=None, evaluate_level=None,
                             assume_real_variables=False,
                             parse_subscripts=False,
                             allow_index_resample=False):
    """
    Return an expression from a string containing comma-separated list.
    Expression_list is first parsed with sympy using local_dict, if given.
    If index is given, that item from the list is returned.
    If index is none, items is chosen randomly and uniformly from
    all entries.

    If allow_index_resample, then resample randomly if index is invalid.
    Otherwise, raise IndexError if index is invalid

    Returns a tuple containing the expression 
    and the index of the expression from the list.
    """
    
    try:
        parsed_list = parse_and_process(
            expression_list, local_dict=local_dict,
            evaluate_level=evaluate_level,
            assume_real_variables=assume_real_variables,
            parse_subscripts=parse_subscripts)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for random expression: "
                         + expression_list
                         + "<br/>Required format: expr1, expr2, ...")
    

    
    the_expression=None

    # if expression isn't a list 
    # but index is zero or unspecified or allow_index_resample is True
    # then use whole expresion
    try:
        n = len(parsed_list)
    except TypeError:
        if index is None or index==0 or allow_index_resample:
            the_expression=parsed_list
            index=0
        else:
            raise IndexError("Nonzero index specified and expression is not a list")

    # if expression is list
    if the_expression is None:
        
        # if index isn't prescribed, generate randomly
        if index is None:
            index = rng.randrange(n)

        try:
            the_expression = parsed_list[index]
        except TypeError:
            raise ValueError("Invalid format for random expression: "
                             + expression_list
                             + "<br/>Required format: expr1, expr2, ...")
        except IndexError:
            if allow_index_resample:
                # resample and try again
                index = rng.randrange(n)
                the_expression = parsed_list[index]
            else:
                raise
    
    return (the_expression, index)


class ParsedFunction(Function):
    pass

def return_parsed_function(expression, function_inputs, name,
                           local_dict=None, 
                           evaluate_level=None,
                           assume_real_variables=False,
                           parse_subscripts=False):
    """
    Parse expression into function of function_inputs,
    a subclass of ParsedFunction.

    The expression field must be a mathematical expression
    and the function inputs field must be a tuple of symbols.
    The expression will be then viewed as a function of the
    function input symbol(s). 
    Substitutions from local_dict will be made in expression
    except values from function_inputs will be ignored.

    """

    from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL,\
        EVALUATE_FULL

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

    # initially parse with no evaluation so functions are not evaluated
    # until after inputs are substituted
    try:
        expr2= parse_and_process(expression, local_dict=local_dict_sub,
                                 evaluate_level=EVALUATE_NONE,
                                 assume_real_variables=assume_real_variables,
                                 parse_subscripts=parse_subscripts)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for function: " + expression)

    # parsed_function is a class that stores the expression
    # and the input list, substituting the function arguments
    # for the input_list symbols on evaluation
    class _parsed_function(ParsedFunction):
        # Store information for evaluation
        # On evaluation, it must take the number of arguments in input_list
        the_input_list = input_list
        nargs = len(input_list)

        expression=expr2
        eval_level = evaluate_level

        # on evaluation replace any occurences of inputs in expression
        # with the values from the arguments
        @classmethod
        def eval(cls, *args):
            expr_sub=cls.expression

            # can't use nargs here as it is converted to a set
            # so instead use len(input_list)
            replace_dict={}
            for i in range(len(cls.the_input_list)):
                if assume_real_variables:
                    input_symbol=Symbol(cls.the_input_list[i],real=True)
                else:
                    input_symbol=Symbol(cls.the_input_list[i])
                replace_dict[input_symbol] =  args[i]

            if cls.eval_level == EVALUATE_NONE:
                expr_sub=bottom_up(expr_sub,
                    lambda w: w if w not in replace_dict else replace_dict[w],
                                   atoms=True, evaluate=False)
            else:
                # if evaluated, then replace unevaluated commands at same time
                # as substitute in the input values so that function is 
                # calculated based on its evaluated input
                expr_sub = replace_unevaluated_commands(
                    expr_sub, replace_dict=replace_dict)

            if cls.eval_level == EVALUATE_FULL or cls.eval_level is None:
                try: 
                    expr_sub=expr_sub.doit()
                except (AttributeError, TypeError):
                    pass

            return expr_sub


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
                             split_symbols=None, assume_real_variables=False,
                             parse_subscripts=False):

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
                            assume_real_variables=assume_real_variables,
                            parse_subscripts=parse_subscripts)

    # If expression was a Matrix already, then have a 1x1 matrix
    # whose only element is a matrix.
    # In that case, return just the inner matrix
    if expr.rows==1 and expr.cols==1:
        if isinstance(expr[0,0], Matrix):
            expr=expr[0,0]
    
    return expr
    


def replace_absolute_value(expression):
    """
    Look for combinations of | expr |
    in nesting group of parenthesis, braces, or brackets
    (treating all opening (, [, or { as equivalent
    and all closing ), ], or } as equivalent).

    Ignore case if expr is empty

    If find combination, replace with __Abs__(...)


    returns 
    - string with __Abs__()

    """

    paren_stack = []
    bar_ind = None
    left_inds=[]
    right_inds=[]
    
    for (i,char) in enumerate(expression):
        if char=='(' or char== "[" or char=="{":
            paren_stack.append(bar_ind)
            bar_ind = None
        elif char==')' or char=="]" or char=="}":
            try:
                bar_ind = paren_stack.pop()
            except IndexError:
                # unmatched parens.  
                # Just return expression without modification.
                return expression

        elif char=="|":
            if bar_ind is None:
                bar_ind = i
            elif i > bar_ind+1:
                left_inds.append(bar_ind)
                right_inds.append(i)
                bar_ind = None
            else:
                # ignore ||
                bar_ind = None
    
    if len(paren_stack):
        # unmatched parens.  
        # Just return expression without modification.
        return expression


    # replace all right_inds with )
    new_expr_sub=expression
    for ind in right_inds:
        new_expr_sub = new_expr_sub[:ind] + ")" + new_expr_sub[ind+1:]


    last_ind=0
    new_expr=""
    
    left_inds.sort()
    for ind in left_inds:
        new_expr += new_expr_sub[last_ind:ind]

        new_expr += " __Abs__("

        last_ind=ind+1

    new_expr += new_expr_sub[last_ind:]

    return new_expr


def replace_bar_boolean_equals_in(s, evaluate=True):
    """
    Replace |, and/&, or, =, != and "in" contain in s
    with operators to be parsed by sympy
    

    1. Replace matching |arg| within same nesting level of parentheses
    (or brackets or braces) with __Abs__(arg)

    2. Replace remaining | (not ||) with __cond_prob__(lhs,rhs)

    3. Replace 
       - and with &
       - or with |
       - in with placeholder symbol

    4. Replace = (not an == or preceded by <, >, or !) with __Eq__(lhs,rhs)
    then replace != (not !==) with __Ne__(lhs,rhs)
    If evaluate=False, add evaluate=False

    5. Replace in placeholder with (rhs).contains(lhs),
    If evaluate=False, add evaluate=False
   
    6. Replace & (not an &&) with __And__(lhs,rhs), 
    then replace | (not ||) with __Or__(lhs,rhs).

    7. If evaluate=False, replace == with __python_Eq__(lhs,rhs)
    and !== with __python__Ne__(lhs,rhs)
    
    8. Replace expressions such as a <= b < c < d
    with __Lts__((a,b,c,d), (False, True, True))
    If evaluate=False, add evaluate=False.
    Second argument is a tuple specifying which inequalities are strict.

    9. Replace expressions such as a >= b > c > d
    with __Gts__((a,b,c,d), (False, True, True))
    If evaluate=False, add evaluate=False.
    Second argument is a tuple specifying which inequalities are strict.

    __Eq__, __Ne__, __And__, __Or___ must then be mapped to sympy 
    Eq, Ne, And, and Or when parsing.  (Actually use customized And, Or.)

    __Lts__ and __Gts__ must be mapped to custom functions Lts and Gts
    when parsing.

    If evaluate=False, then __python_Eq__ and __python_Ne__ must be
    mapped to python_equal_uneval and python_not_equal_uneval when parsing
    
    To find lhs and rhs, looks for unmatched parentheses 
    or the presence of certain characters no in parentheses

    Repeats the procedure until can't find more =, !=, &, |, or in
    or until lhs or rhs is blank

    Step 1 is a separate loop, as it is in different form.
    Call replace_absolute_value

    Step 9 is a separate loop, as it involves multiple arguments.


    """

    import re

    
    s = replace_absolute_value(s)


    #####################################
    # replace commands with two arguments
    #####################################
    for i in range(9):
        if i==0:
            pattern = re.compile('[^\|](\|)[^\|]')
            len_op=1
            new_op='__cond_prob__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars="|" 

        elif i==1:

            # replace and/or with &/|
            s=re.sub(r'\band\b',r'&', s)
            s=re.sub(r'\bor\b',r'|', s)

            # replace in with __in_op_pl__
            s=re.sub(r'\bin\b', r'___in_op_pl___', s)
            
            continue
            
        elif i==2:
            pattern = re.compile('[^<>!=](=)[^=]')
            len_op=1
            if evaluate:
                new_op='__Eq__(%s,%s)'
            else:
                new_op='__Eq__(%s,%s, evaluate===False)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==3:
            pattern = re.compile('[^<>!=](!=)[^=]')
            len_op=2
            if evaluate:
                new_op='__Ne__(%s,%s)'
            else:
                new_op='__Ne__(%s,%s, evaluate===False)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==4:
            pattern = re.compile('(___in_op_pl___)')
            len_op=14
            if evaluate:
                new_op='(%s).contains(%s)'
            else:
                new_op='(%s).contains(%s, evaluate===False)'
            reverse_arguments=True
            replace_rhs_intervals=True
            # characters captured in pattern to left of operator
            loffset=0
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==5:
            pattern = re.compile('[^&](&)[^&]')
            len_op=1
            new_op='__And__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
        elif i==6:
            pattern = re.compile('[^\|](\|)[^\|]')
            len_op=1
            new_op='__Or__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|" 
        elif i==7:
            if evaluate:
                continue
            pattern = re.compile('[^<>!=](==)[^=]')
            len_op=2
            new_op='__python_Eq__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==8:
            if evaluate:
                continue
            pattern = re.compile('[^<>!=](!==)[^=]')
            len_op=3
            new_op='__python_Ne__(%s,%s)'
            reverse_arguments=False
            replace_rhs_intervals=False
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
            
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



    #####################
    # replace Gts and Lts
    #####################
    for i in range(2):
        if i==0:
            pattern = re.compile('[^!](<)')
            op_char="<"
            new_op='__Lts__'
            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
        elif i==1:
            pattern = re.compile('[^!](>)')
            op_char=">"
            new_op='__Gts__'

            # characters captured in pattern to left of operator
            loffset=1
            # characters that signal end of expression if not in ()
            break_chars=",&|!=<>" 
            
        while True:
            mo= pattern.search(s)
            if not mo:
                break
            ind = mo.start(0)+loffset

            strict=[s[ind+1]!="=",]
            if strict[0]:
                len_op=1
            else:
                len_op=2

            
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

            args = [s[begin_pos:ind].strip(),]

            while True:
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

                args += [s[ind+len_op:end_pos].strip(),]

                if end_pos==len(s) or s[end_pos] != op_char:
                    break
                
                next_strict = s[end_pos+1] != "="
                strict += [next_strict,]
                if next_strict:
                    len_op=1
                else:
                    len_op=2
            

                ind = end_pos
                


            # stop if an argument is just spaces
            if "" in args:
                break
            else:
                if evaluate:
                    new_command_string = "%s((%s),%s)"\
                                         % (new_op, ",".join(args), tuple(strict))
                else:
                    new_command_string = "%s((%s),%s, evaluate===False)"\
                                         % (new_op, ",".join(args), tuple(strict))

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

    unsplit_symbols = []
    if split_symbols and local_dict:
        unsplit_symbols = list(local_dict.keys())

    pattern=re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)'\ *\(")

    while True:
        mo= pattern.search(s)
        if not mo:
            break
        funname_begin = mo.start(1)
        funname_end = mo.end(1)

        funname = s[funname_begin:funname_end]

        # if split symbols, narrow to just last letter, unless in local_dict
        if split_symbols:
            if not funname in unsplit_symbols:
                funname_begin=funname_end-1
                funname=s[funname_begin:funname_end]
                # if last character isn't letter, skip
                if not funname.isalpha():
                    s = s[:funname_end] + '__tempprimesymbol__' + \
                        s[funname_end+1:]
                    continue

        match_end = mo.end(0)
        s = s[:funname_begin] + ' __DerivativePrimeNotation__(' + funname + \
            "," + s[match_end:]


    s=re.sub("__tempprimesymbol__", "'", s)


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
                # if not differentiating with respect to callable
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
                        local_dict=None, user_dict=None,
                        random_group_indices=None,
                        new_alternate_dicts=[],
                        new_alternate_exprs=[],
                        random_outcomes={}):

    from sympy.core.function import UndefinedFunction
    from mitesting.math_objects import math_object

    # if randomly selecting from a list,
    # determine if the index for random_list_group was chosen already
    if the_expr.expression_type in [the_expr.RANDOM_WORD,
                                the_expr.RANDOM_EXPRESSION,
                                the_expr.RANDOM_FUNCTION_NAME]:

        # try selecting index from group
        if the_expr.random_list_group:
            try:
                index = random_group_indices.get(\
                                        the_expr.random_list_group)
            except AttributeError:
                index = None
        else:
            index = None

        # if didn't obtain index from group, try from random outcomes
        allow_index_resample=False
        if index is None:
            index = random_outcomes.get(str(the_expr.id))
            allow_index_resample=True

        # treat RANDOM_WORD as special case
        # as it involves two outputs and hasn't been
        # parsed by sympy
        # Complete all processing and return
        if the_expr.expression_type == the_expr.RANDOM_WORD:
            try:
                result = return_random_word_and_plural( 
                    the_expr.expression, index=index, rng=rng,
                    allow_index_resample=allow_index_resample)
            except IndexError:
                raise IndexError("Insufficient entries for random list group: "\
                                     + the_expr.random_list_group)

            # record index chosen for random list group, if group exist
            if the_expr.random_list_group:
                try:
                    random_group_indices[the_expr.random_list_group]\
                        =result[2]
                except TypeError:
                    pass

            # record index chosen for random outcomes
            random_outcomes[str(the_expr.id)] = result[2]

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
                the_expr.expression, index=index,
                local_dict=local_dict,
                evaluate_level = the_expr.evaluate_level, rng=rng,
                assume_real_variables=the_expr.real_variables,
                parse_subscripts=the_expr.parse_subscripts,
                allow_index_resample=allow_index_resample)
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


            # turn to SymbolCallable and add to user_dict
            # should use:
            # function_text = six.text_type(math_expr)
            # but sympy doesn't yet accept unicode for function name
            function_text = str(math_expr)
            if the_expr.real_variables:
                math_expr = SymbolCallable(function_text, real=True)
            else:
                math_expr = SymbolCallable(function_text)
            try:
                user_dict[function_text] = math_expr
            except TypeError:
                pass


        # record index chosen for random list group, if group exists
        if the_expr.random_list_group:
            try:
                random_group_indices[the_expr.random_list_group]=index
            except TypeError:
                pass

        # record index chosen for random outcomes
        random_outcomes[str(the_expr.id)] = index


    elif the_expr.expression_type == the_expr.RANDOM_NUMBER:
        # try obtaining index from random outcomes
        index = random_outcomes.get(str(the_expr.id))

        math_expr, index = return_random_number_sample(
            the_expr.expression, local_dict=local_dict, rng=rng, index=index)
        
        random_outcomes[str(the_expr.id)] = index

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
                    assume_real_variables=the_expr.real_variables,
                    parse_subscripts=the_expr.parse_subscripts)

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
                    assume_real_variables = the_expr.real_variables,
                    parse_subscripts=the_expr.parse_subscripts)
            except ValueError as e:
                raise ValueError("Invalid format for matrix<br/>%s" % e.args[0])
            except (TypeError, NotImplementedError, SyntaxError, TokenError):
                raise ValueError("Invalid format for matrix")
        try:
            if math_expr is None:
                math_expr = parse_and_process(
                    expression, local_dict=local_dict,
                    evaluate_level = the_expr.evaluate_level,
                    assume_real_variables = the_expr.real_variables,
                    parse_subscripts=the_expr.parse_subscripts)
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
                    message += "<br/>Comparison != returns truth value only for numerical values.  Use !== to compare if two symbolic expressions are not identical."
                if re.search('[^<>!=]=[^=]',the_expr.expression):
                    message += "<br/>Comparison = returns truth value only for numerical values.  Use == to compare if two symbolic expressions are identical."
                raise TypeError(message)


        if the_expr.expression_type == the_expr.RANDOM_ORDER_TUPLE:
            shuffle_indices = random_outcomes.get(str(the_expr.id))

            try:
                if sorted(shuffle_indices) != list(range(len(math_expr))):
                    shuffle_indices=None
            except TypeError:
                shuffle_indices = None

            if shuffle_indices is None:
                shuffle_indices = list(range(len(math_expr)))
                rng.shuffle(shuffle_indices)

            if isinstance(math_expr,list):
                math_expr=[math_expr[i] for i in shuffle_indices]
            elif isinstance(math_expr, Tuple):
                the_class=math_expr.__class__
                math_expr = list(math_expr)
                math_expr=[math_expr[i] for i in shuffle_indices]
                math_expr = the_class(*math_expr)
                
            random_outcomes[str(the_expr.id)] = shuffle_indices

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


            # turn to SymbolCallable and add to user_dict
            function_text = str(math_expr)
            if the_expr.real_variables:
                math_expr = SymbolCallable(function_text,real=True)
            else:
                math_expr = SymbolCallable(function_text)
            try:
                user_dict[function_text] = math_expr
            except TypeError:
                pass

        if the_expr.expression_type == the_expr.UNSPLIT_SYMBOL:
            # math_expr should be a Symbol
            if not isinstance(math_expr,Symbol):
                raise ValueError("Invalid unsplit symbol: %s " \
                                 % math_expr)


            # add to user_dict
            symbol_text = str(math_expr)
            try:
                user_dict[symbol_text] = math_expr
            except TypeError:
                pass


        if the_expr.expression_type == the_expr.FUNCTION:
            parsed_function = return_parsed_function(
                the_expr.expression, function_inputs=the_expr.function_inputs,
                name = the_expr.name, local_dict=local_dict,
                evaluate_level = the_expr.evaluate_level,
                assume_real_variables = the_expr.real_variables,
                parse_subscripts=the_expr.parse_subscripts)

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



def mark_commands_no_evaluate(s, global_dict={}, local_dict={}):
    """
    For every sympy Function f in global_dict or local_dict,
    replace in string s any calls "f(...)" with "f(..., evaluate=False)"
    as long as does not have an evaluate keyword already specified.
    Exception: don't mark ParsedFunctions
    """
    
    from sympy.core.function import Application

    combined_dict=global_dict.copy()
    combined_dict.update(local_dict)

    evaluate_pattern = re.compile('evaluate *=')

    for cmd in combined_dict:
        try:
            if not issubclass(combined_dict[cmd], Application) or \
               issubclass(combined_dict[cmd],ParsedFunction):
                continue
        except TypeError:
            continue
            
        pattern = re.compile(r'\b%s *\(' % cmd)
        start_ind=0

        while True:
            mo= pattern.search(s[start_ind:])
            if not mo:
                break

            start_ind = mo.end(0)+start_ind

            # search for any instances of evaluate=,
            # that aren't surrounded by parentheses
            last_ind_outside_parens=start_ind
            n_parens=0
            for (j,c) in enumerate(s[start_ind:]):
                if c=="(":
                    if n_parens==0:
                        mo= evaluate_pattern.search(\
                                        s[last_ind_outside_parens:start_ind+j])

                        # if found evaluate, continue to next instance 
                        if mo:
                            break

                    n_parens += 1

                if c==")":
                    if n_parens==0:
                        mo= evaluate_pattern.search(\
                                        s[last_ind_outside_parens:start_ind+j])

                        # if found evaluate, continue to next instance
                        if mo:
                            break
                        
                        # found closing paren to command with not evaluate
                        # so add evaluate=False
                        s=s[:start_ind+j] + ", evaluate=False" + \
                           s[start_ind+j:]
                        
                        # continue to next instance
                        break
                    elif n_parens==1:
                        # dropped out of last parentheses inside command
                        last_ind_outside_parens=start_ind+j

                    n_parens-=1
    return s


def replace_unevaluated_commands(expr, replace_dict={}):
    """
    replace AddUnsorts with Adds
    replace MulUnsorts with Muls
    replace python_equal_uneval with ==
    replace python_not_equal_uneval with !=
    all other unevaluated commands replaced with evaluated versions

    In addition, make replacement from replace_dict, if given

    """

    def replaceUnsortsPythonEquals(w):
        from mitesting.sympy_customized import AddUnsort, MulUnsort
        from mitesting.customized_commands import python_equal_uneval, \
            python_not_equal_uneval, Gts, Lts
        from sympy import Add, Mul

        if w in replace_dict:
            return replace_dict[w]
        if isinstance(w, AddUnsort):
            return Add(*w.args)
        if isinstance(w, MulUnsort):
            return Mul(*w.args)
        if isinstance(w, python_equal_uneval):
            return w.args[0] == w.args[1]
        if isinstance(w, python_not_equal_uneval):
            return w.args[0] != w.args[1]
        if isinstance(w, Gts) or isinstance(w,Lts):
            return w.doit(deep=False)

  
        return w

    # other unevaluated commands get replaced with evaluated versions
    # during bottom_up
    # use atoms only if there is a replace_dict
    return bottom_up(expr, replaceUnsortsPythonEquals, atoms=bool(replace_dict))



def replace_subscripts(s, split_symbols=False, assume_real_variables=False,
                       local_dict=None):
    """
    Replace any instances of x_y with __subscriptsymbol__(x,y) in string s.

    If split symbols, x can be only one letter, or a combination of numbers or
    letters, beginning with a letter, that is a key in local_dict.
    Otherwise, x can be any combination of numbers or letters
    but must begin with a letter.

    If split_symbols, then y can be only one character unless it is 
    a number, a key in local_dict, or in parentheses.
    Otherwise, y can be any combination of numbers or letters.
    If the first character of y is "(", then y continues until matching ")".

    For split_symbols, exclude keys in local_dict that include a _

    If assume_real_variables, add third argument of True to command

    If x_y is in local_dict, then don't replace with subscript_command

    """

    unsplit_symbols = []
    if split_symbols and local_dict:
        for sym in local_dict.keys():
            if not '_' in sym:
                unsplit_symbols.append(sym)

    pattern = re.compile(r"([a-zA-Z][a-zA-Z0-9]*)_[^_]")

    while True:
        mo= pattern.search(s)
        if not mo:
            break
        base_begin = mo.start(0)
        base_end = mo.end(0)-1

        base = s[base_begin:base_end-1]



        sub_begin=base_end
        sub_end=len(s)
        sub_skipafter=0
        used_parens=False

        # if next character after "_" is "(", then find matching )
        if s[base_end]=="(":
            used_parens=True
            sub_begin+=1
            n_openpar=0
            for (j,c) in enumerate(s[base_end:]):
                if c=="(":
                    n_openpar+=1
                elif c==")":
                    n_openpar-=1
                    if n_openpar == 0:
                        sub_end=base_end+j
                        sub_skipafter=1
                        break
            subscript = s[sub_begin:sub_end]

        else:
            for (j,c) in enumerate(s[base_end:]): 
                if not c.isalnum():
                    sub_end=base_end+j
                    break

            subscript = s[sub_begin:sub_end]
            
        # if captured pattern is in local_dict,
        # will leave subscripts unmodified
        if s[base_begin:sub_end+sub_skipafter] in local_dict:
            s = s[:base_begin] + \
                re.sub('_','__notasubscriptsymbol__',
                        s[base_begin:sub_end+sub_skipafter]) \
                + s[sub_end+sub_skipafter:]
            continue
            
        # If split symbols then
        # (a) shorten base to last letter unless in unsplit_symbols, and
        # (b) shorten subscript to number or first letter
        #     unless used parenthesis or is in unsplit_symbols

        if split_symbols:
            # narrow base to last letter unless in unsplit_symbols
            if not base in unsplit_symbols:
                base_begin=base_end-2
                base=s[base_begin:base_end-1]
                # if last character isn't letter, skip
                if not base.isalpha():
                    s = s[:base_end-1] + '__notasubscriptsymbol__' + \
                        s[base_end:]
                    continue


            # if subscript is not in unsplit symbols and didn't user parens
            # then change to be number or the first letter
            if split_symbols and not used_parens and \
               subscript not in unsplit_symbols:
                if s[base_end].isdigit():
                    for (j,c) in enumerate(s[base_end:]):
                        if not c.isdigit():
                            sub_end=base_end+j
                            break
                else:
                    sub_end=base_end+1

                subscript = s[sub_begin:sub_end]

            # Check if newly shortened pattern is in local_dict.
            # If so, will leave subscripts unmodified
            # Also add a space before and after the pattern,
            # so it won't get turned into a symbol by the parser
            # and will instead get mapped by local_dict.
            # (Parser won't split symbols that contain a _.)
            if s[base_begin:sub_end+sub_skipafter] in local_dict:
                s = s[:base_begin] + ' ' + \
                    re.sub('_','__notasubscriptsymbol__',
                            s[base_begin:sub_end+sub_skipafter]) \
                    + ' ' + s[sub_end+sub_skipafter:]
                continue


        if assume_real_variables:
            subscript_command_string = " __subscriptsymbol__(%s,%s, True) " % \
                                       (base,subscript)
        else:
            subscript_command_string = " __subscriptsymbol__(%s,%s) " % \
                                       (base,subscript)
        s = s[:base_begin] + subscript_command_string \
            + s[sub_end+sub_skipafter:]

    s=re.sub('__notasubscriptsymbol__', '_', s)

    return s


def round_and_int(number, ndigits=0):
    """
    Round number to ndigits of accuracy.
    If result is an integer, convert to integer to remove trailing zero.

    If number is None, return None

    """

    if number is None:
        return None

    number = round(number,ndigits)
    
    if round(number)==number:
        number=int(number)

    return number

