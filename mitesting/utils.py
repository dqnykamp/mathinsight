from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mitesting.customized_commands import *
from mitesting.sympy_customized import parse_and_process
from sympy import Tuple, Function, Symbol
from sympy.parsing.sympy_tokenize import TokenError
import six


def return_sympy_global_dict(allowed_sympy_commands=[]):
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
    global_dict = {}

    for command in allowed_commands:
        try:
            # attempt to match command with localized command
            global_dict[str(command)]=localized_commands[command]
        except KeyError:
            try:
                # if command isn't found in localized command
                # then attempt to match with standard sympy command
                global_dict[str(command)]=all_sympy_commands[command]
            except KeyError:
                pass

    return global_dict



def return_random_number_sample(expression, rng, global_dict=None):
    """
    Returns a randomly generated number based on string.
    Expression is first parsed via sympy using global_dict, if specified.
    Resulting expression should be a tuple: (minval, maxval, [increment])
    If increment is omitted, set it to 1.
    Result will be number generated uniformly from numbers
    of the form: expr = minval + i * increment
    where i is a non-negative integer and expr <= maxval.
    """
    
    try:
        number_params = parse_and_process(expression, 
                                          global_dict=global_dict)
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
                             global_dict=None, evaluate_level=None):
    """
    Return an expression from a string containing comma-separated list.
    Expression_list is first parsed with sympy using global_dict, if given.
    If index is given, that item from the list is returned.
    If index is none, items is chosen randomly and uniformly from
    all entries.

    Returns a tuple containing the expression 
    and the index of the expression from the list.
    """
    
    try:
        parsed_list = parse_and_process(expression_list, 
                                        global_dict=global_dict,
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
                           global_dict=None, expand=False, 
                           default_value=None):
    """
    Parse expression into function of function_inputs,
    a subclass of ParsedFunction.

    The expression field must be a mathematical expression
    and the function inputs field must be a tuple of symbols.
    The expression will be then viewed as a function of the
    function input symbol(s). 
    Substitutions from global_dict will be made in expression
    except values from function_inputs will be ignored.
    If expand is true, expression will be expanded.

    The .default argument returns default_value, if exists.
    Else .default will be set to expression parsed with all
    substitutions from global_dict.
    """

    input_list = [six.text_type(item.strip())
                  for item in function_inputs.split(",")]
    # if no inputs, make empty list so function with no arguments
    if input_list == ['']:
        input_list = []

    # if any input variables are in global_dict,
    # remove them from global_dict so they will not be substituted
    if global_dict:
        global_dict_sub = dict((key, global_dict[key]) 
                               for key in global_dict.keys()
                               if key not in input_list)
    else:
        global_dict_sub = None

    try:
        expr2= parse_and_process(expression, global_dict=global_dict_sub)
    except (TokenError, SyntaxError, TypeError, AttributeError):
        raise ValueError("Invalid format for function: " + expression)

    if expand:
        from sympy import expand as sympy_expand
        expr2 = bottom_up(expr2, sympy_expand)

    if default_value is None:
        default_value = parse_and_process(expression, global_dict=global_dict)

    
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
