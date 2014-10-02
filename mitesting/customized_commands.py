# customized sympy commands

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import Tuple, sympify, Function, C, S
from mitesting.sympy_customized import bottom_up

class Abs(C.Abs):
    """
    customized version of sympy Abs function that
    evaluates the derivative assuming that the argument is real
    """
    def _eval_derivative(self, x):
        from sympy.core.function import Derivative
        from sympy.functions import sign
        return Derivative(self.args[0], x, **{'evaluate': True}) \
            * sign(self.args[0])
    
def roots_tuple(f, *gens, **flags):
    """
    Finds symbolic roots of a univariate polynomial.
    Returns a Tuple of the sorted roots (using sympify.sort_key)
    ignoring multiplicity
    
    """

    from sympy import roots
    rootslist = roots(f, *gens, **flags).keys()
    rootslist = sorted(rootslist, key=lambda x: sympify(x).sort_key())

    return Tuple(*rootslist)

def real_roots_tuple(f, *gens):
    """
    Finds real roots of a univariate polynomial.
    Returns a Tuple of the sorted roots, ignoring multiplicity.
    """
    from sympy import roots
    rootslist = roots(f, *gens, filter='R').keys()
    rootslist.sort()
    return Tuple(*rootslist)


def round_expression(expression, n=0, initial_n_digits=100):
    """
    Customized version of round
    Attempts to round expressions to n decimal places in a way to get 
    identical results for two expressions that agree to n decimal places.
    To accomplish, the method performs the following steps
    1.  Traverses expression tree to call evalf with initial_n_digits
        precision on every number or numbersymbol (like pi).
        The first pass puts expression in a consistent form.
    2.  Traverses expression tree, converting each number to a float
        with the number of decimal places specified by n n.
        For consistency, converts expression to string and back to float
        so that expression loses memory of original value and two
        expression will be the same if their conversion to string is the same.
        If n is 0 or smaller, then converts to integer rather than float.

    """
    
    expression = sympify(expression)
    # first convert every number to a float with initial_n_digits
    # for consistency
    expression =  bottom_up(
        expression,
        lambda w: w if not (w.is_Number or w.is_NumberSymbol) else w.evalf(initial_n_digits),
        atoms=True)

    # next, round numbers
    if n <= 0:
        from sympy import Integer
        expression =  bottom_up(
            expression,
            lambda w: w if not w.is_Number else Integer(round(w,n)),
            atoms=True)
    else:
        from sympy import Float
        expression =  bottom_up(
            expression,
            lambda w: w if not w.is_Number else Float(str(round(w,n))),
            atoms=True)
        
    return expression


def evalf_expression(expression, n=15):
    """
    Customized version of evalf.
    Attempts to truncate expressions to n digits in a way to get 
    identical results for two expressions that agree to n digits.
    To accomplish, the method performs the following steps
    1.  Traverses expression tree to call evalf with max(30,n+5)
        precision on every number or numbersymbol (like pi).
        The first pass puts expression in a consistent form.
    2.  Traverses expression tree, converting each number to a float
        with the precision specified by n.
        For consistency, converts expression to string and back to float
        so that expression loses memory of original value and two
        expression will be the same if their conversion to string is the same.
    """

    expression = sympify(expression)
    initial_n_digits = max(30, n+5)
    
    def initial_evalf(w):
        try:
            return w.evalf(initial_n_digits)
        except:
            return w


    # first convert every number to a float with initial_n_digits
    # for consistency
    expression =  bottom_up(expression, initial_evalf, atoms=True)

    from sympy import Float
    expression =  bottom_up(
        expression,
        lambda w: w if not w.is_Number else Float(str(w.evalf(n))),
        atoms=True)

    return expression


def normalize_floats(expression):
    """
    To ensure consistency of expression with floats in presence of
    machine precision errors, round all floats to 14 digits,
    converting expression to string and back to lose memory
    of original value and ensure two expression will be the same 
    if their conversion to string is the same
    """
    expression = sympify(expression)
    from sympy import Float
    expression =  bottom_up(
        expression,
        lambda w: w if not w.is_Float else Float(str(w.evalf(14))),
        atoms=True)
        
    return expression


def index(expr, value):
    """
    Returns first index of value for list or Tuple expr.
    Return empty string if not list or Tuple or value is not present.
    """
    try:
        return expr.index(value)
    except:
        return ""


def smallest_factor(expr):
    """
    Find smallest factor of absolute value of expr up to 10000.
    Return empty string on error or if not integer.
    Assumes expr is a sympy integer, not a Python integer
    """
    try:
        if expr.is_Integer:
            from sympy import factorint
            factors = factorint(Abs(expr), limit=10000)
            factorlist=factors.keys()
            factorlist.sort()
            return factorlist[0]
        else:
            return ""
    except:
        return ""

def max_including_tuples(*args):
    """
    If argument is a single Tuple, then find max over Tuple items.
    Else, find max over arguments.
    Return empty string on error.
    """
    try:
        if len(args)==1 and isinstance(args[0],Tuple):
            return C.Max(*args[0])
        else:
            return C.Max(*args)
    except:
        return ""


def min_including_tuples(*args):
    """
    If argument is a single Tuple, then find min over Tuple items.
    Else, find min over arguments.
    Return empty string on error.
    """
    try:
        if len(args)==1 and isinstance(args[0],Tuple):
            return C.Min(*args[0])
        else:
            return C.Min(*args)
    except:
        return ""

def iif(cond, result_if_true, result_if_false):
    """
    Inline if statement
    """
    try:
        if(cond):
            return result_if_true
        else:
            return result_if_false
    except:
        return ""
      

"""
Turn off automatic evaluation of floats in the following sympy functions.
Functions will still evaluate to floats when .evalf() is called
and will otherwise behave normally.
"""

class log(C.log):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class ln(C.log):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class exp(C.exp):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acosh(C.acosh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acos(C.acos):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acosh(C.acosh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acot(C.acot):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acoth(C.acoth):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class asin(C.asin):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class asinh(C.asinh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atan(C.atan):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atan2(C.atan2):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atanh(C.atanh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cos(C.cos):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cosh(C.cosh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cot(C.cot):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class coth(C.coth):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class csc(C.csc):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sec(C.sec):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sin(C.sin):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sinh(C.sinh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class tan(C.tan):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class tanh(C.tanh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1
