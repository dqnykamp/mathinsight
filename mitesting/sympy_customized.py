from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import sympify
from sympy import Tuple, Float, Symbol, Rational, Integer


def bottom_up(rv, F, atoms=False, nonbasic=False):
    """Apply ``F`` to all expressions in an expression tree from the
    bottom up. If ``atoms`` is True, apply ``F`` even if there are no args;
    if ``nonbasic`` is True, try to apply ``F`` to non-Basic objects.

    Version customized to 
    1. always call rv=rv.func(*args) even if  args and rv.args
       evaluate to be equal.
    2. call bottom_up on elements of tuples and lists
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

    return rv


def parse_expr(s, global_dict=None, local_dict=None, 
               split_symbols=False, evaluate=True):
    """
    Customized version of sympy parse_expr with three modifications.
    1.  Add Integer, Float, Rational, Symbol to global_dict if not 
        not present.  (Needed since  Symbol could be added by auto_symbol
        and Integer, Float, or Rational could be added by auto_number.)
    2.  Use convert_xor and implicit_multiplication transformations
        by default, and add split_symbols transformation if 
        split_symbols is True.
    3.  Call sympify after parse_expr so that tuples will be 
        converted to Sympy Tuples.  (A bug in parse_expr that this
        doesn't happen automatically?)
    """
    
    from sympy.parsing.sympy_parser import \
        (standard_transformations, convert_xor, \
             implicit_multiplication)
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


    # Always include convert_xor and implicit multiplication
    # transformations so that can use ^ for exponentiation
    # and 5x for 5*x
    # If split_symbols is True, then include split_symbols
    # transformation so that can use xy for x*y
    if split_symbols:
        transformations=standard_transformations+(convert_xor, split_symbols_trans, implicit_multiplication)
    else:
        transformations=standard_transformations+(convert_xor, implicit_multiplication)

    # call sympify after parse_expr to convert tuples to Tuples
    expr= sympify(sympy_parse_expr(s, global_dict=new_global_dict, local_dict=local_dict, transformations=transformations, evaluate=evaluate))

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

