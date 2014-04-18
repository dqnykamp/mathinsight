from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import sympify
from sympy import Tuple, Float, Symbol, Rational, Integer, factorial
import re
import keyword

def bottom_up(rv, F, atoms=False, nonbasic=False):
    """Apply ``F`` to all expressions in an expression tree from the
    bottom up. If ``atoms`` is True, apply ``F`` even if there are no args;
    if ``nonbasic`` is True, try to apply ``F`` to non-Basic objects.

    Version customized to 
    1. always call rv=rv.func(*args) even if  args and rv.args
       evaluate to be equal.
    2. call bottom_up on elements of tuples and lists
    3. catch TypeError so that can be called on tuples or lists
       that contain other lists
    """
    try:
        if isinstance(rv, list):
            rv = [bottom_up(a, F, atoms, nonbasic) for a in rv]
        elif isinstance(rv, tuple):
            rv = tuple([bottom_up(a, F, atoms, nonbasic) for a in rv])
        elif rv.args:
            args = tuple([bottom_up(a, F, atoms, nonbasic)
                for a in rv.args])
            rv = rv.func(*args)
            rv = F(rv)
        elif atoms:
            rv = F(rv)
    except AttributeError:
        if nonbasic:
            try:
                rv = F(rv)
            except TypeError:
                pass
    except TypeError:
        pass

    return rv


def parse_expr(s, global_dict=None, local_dict=None, 
               split_symbols=False, evaluate=True):
    """
    Customized version of sympy parse_expr with four modifications.
    1.  Add Integer, Float, Rational, Symbol, and factorial
        to global_dict if not present.  
        (Needed since Symbol could be added by auto_symbol,
        Integer, Float, or Rational could be added by auto_number,
        and factorial could be added by factorial_notation.)
    2.  Use a customized version of the auto_symbol transformation 
        so that python keywords like "lambda", "as" and "if" 
        will be parsed to symbols
    3.  In addition, use auto_number, factorial notation, convert_xor
        and implicit_multiplication transformations by default, 
        and add split_symbols transformation if split_symbols is True.
    4.  Allows substitution of python keywords like 'lambda', 'as", or "if" 
        via local/global_dict.
    5.  Call sympify after parse_expr so that tuples will be 
        converted to Sympy Tuples.  (A bug in parse_expr that this
        doesn't happen automatically?)
    """
    
    from sympy.parsing.sympy_parser import \
        (auto_number, factorial_notation, convert_xor, implicit_multiplication)
    from sympy.parsing.sympy_parser import split_symbols as split_symbols_trans
    from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr

    # Create new global dictionary so modifications don't affect original
    new_global_dict = {}
    if global_dict:
        new_global_dict.update(global_dict)

    # Since Symbol could be added by auto_symbol
    # and Integer, Float, or Rational could be added by auto_number
    # add them to the global dict if not present
    if 'Integer' not in new_global_dict:
        new_global_dict['Integer'] = Integer
    if 'Float' not in new_global_dict:
        new_global_dict['Float'] = Float
    if 'Rational' not in new_global_dict:
        new_global_dict['Rational'] = Rational
    if 'Symbol' not in new_global_dict:
        new_global_dict['Symbol'] = Symbol
    if 'factorial' not in new_global_dict:
        new_global_dict['factorial'] = factorial

    # If evaluate==False, then operators could be included
    # so must add them to global_dict if not present
    if evaluate==False:
        from sympy import Add, Mul, Pow
        if 'Add' not in new_global_dict:
            new_global_dict['Add'] = Add
        if 'Mul' not in new_global_dict:
            new_global_dict['Mul'] = Mul
        if 'Pow' not in new_global_dict:
            new_global_dict['Pow'] = Pow

    # Always include the transformations:
    # auto_symbol: converts undefined variables to symbols
    #   (customized so that lambda is also a symbol)
    # auto_number: converts numbers to sympy numbers (Integer, Float, etc.)
    # factorial_notation: allow standard factorial notation: x!
    # convert_xor: allows use of ^ for exponentiation
    # implicit multiplication: allows use of 5x for 5*x
    # If split_symbols is True, then include split_symbols
    # transformation so that can use xy for x*y
    transformations = (auto_symbol, auto_number, factorial_notation,\
                           convert_xor)
    if split_symbols:
        transformations += (split_symbols_trans, )
    transformations += (implicit_multiplication, )

    # if a python keyword such as "lambda" or "as" is in 
    # the local or global dictionary, we can't use 
    # the standard approach to substitute values. 
    # Instead, we replace keyword with _keyword_ in both the
    # expression and the dictionary keys.
    for kword in keyword.kwlist:
        if kword in new_global_dict:
            new_global_dict['_'+kword+'_'] = new_global_dict[kword]
            del new_global_dict[kword]
            s = re.sub(r'\b'+kword+r'\b', '_'+kword+'_', s)
        if local_dict and kword in local_dict:
            local_dict_old=local_dict
            local_dict = {}
            local_dict.update(local_dict_old)
            local_dict['_'+kword+'_'] = local_dict[kword]
            del local_dict[kword]
            s = re.sub(r'\b'+kword+r'\b', '_'+kword+'_', s)

    
    # call sympify after parse_expr to convert tuples to Tuples
    expr = sympify(sympy_parse_expr(
            s, global_dict=new_global_dict, local_dict=local_dict, 
            transformations=transformations, evaluate=evaluate))

    return expr



def parse_and_process(s, global_dict=None, local_dict=None,
                      split_symbols=False, evaluate_level=None):
    """
    Parse expression and optionally call doit, evaluate_level is full. 
    If evaluate_level = Expression.EVALUATE_NONE, then parse
    with evaluate=False set.
    If evaluate_level = Expression.EVALUATE_FULL or evaluate_level=None,
    then call doit() after parsing.
    """
    
    from mitesting.models import Expression
    if evaluate_level == Expression.EVALUATE_NONE:
        evaluate = False
    else:
        evaluate = True

    expression = parse_expr(s, global_dict=global_dict,
                            local_dict=local_dict,
                            split_symbols=split_symbols,
                            evaluate=evaluate)

    if evaluate_level == Expression.EVALUATE_FULL \
            or evaluate_level is None:
        try: 
            expression=expression.doit()
        except (AttributeError, TypeError):
            pass
        
    return expression


def auto_symbol(tokens, local_dict, global_dict):
    # customized verison of auto symbol
    # only difference is that ignore python keywords 
    # so that the keywords will be turned into a symbol
    from sympy.parsing.sympy_tokenize import NAME, OP
    from sympy.core.basic import Basic


    """Inserts calls to ``Symbol`` for undefined variables."""
    result = []
    prevTok = (None, None)

    tokens.append((None, None))  # so zip traverses all tokens
    for tok, nextTok in zip(tokens, tokens[1:]):
        tokNum, tokVal = tok
        nextTokNum, nextTokVal = nextTok
        if tokNum == NAME:
            name = tokVal

            if (name in ['True', 'False', 'None']
                or name in local_dict
                # Don't convert attribute access
                or (prevTok[0] == OP and prevTok[1] == '.')
                # Don't convert keyword arguments
                or (prevTok[0] == OP and prevTok[1] in ('(', ',')
                    and nextTokNum == OP and nextTokVal == '=')):
                result.append((NAME, name))
                continue
            elif name in global_dict:
                obj = global_dict[name]
                if isinstance(obj, (Basic, type)) or callable(obj):
                    result.append((NAME, name))
                    continue

            result.extend([
                (NAME, 'Symbol'),
                (OP, '('),
                (NAME, repr(str(name))),
                (OP, ')'),
            ])
        else:
            result.append((tokNum, tokVal))

        prevTok = (tokNum, tokVal)

    return result
