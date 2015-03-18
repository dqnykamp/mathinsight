# customized sympy commands

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import Tuple, sympify, C, S, Float, Matrix, Abs
from mitesting.sympy_customized import bottom_up, customized_sort_key, TupleNoParen
from sympy.logic.boolalg import BooleanFunction

class python_equal_uneval(BooleanFunction):
    nargs=2

    def doit(self, **hints):
        if hints.get('deep', True):
            return self.args[0].doit(**hints) == self.args[1].doit(**hints) 
        else:
            return self.args[0] == self.args[1]
    
    def _latex(self, prtr):
        return "%s == %s" % (prtr._print(self.args[0]), 
                             prtr._print(self.args[1]))
    

class python_not_equal_uneval(BooleanFunction):
    nargs=2

    def doit(self, **hints):
        if hints.get('deep', True):
            return self.args[0].doit(**hints) != self.args[1].doit(**hints) 
        else:
            return self.args[0] != self.args[1]
    
    def _latex(self, prtr):
        return "%s != %s" % (prtr._print(self.args[0]), 
                             prtr._print(self.args[1]))
    

def _initial_evalf(w,n):
    """ 
    Convert every number to float with precision n
    If number ends in 5, convert to high precision Float
    and multiply by 1+epsilon so that it will round up correctly.
    
    """

    if w.is_Number:
        wstr=str(w)
        if "." in wstr:
            wstr = wstr.rstrip('0')
            if wstr[-1]=="5":
                # include extra call to str because bug
                # in sympy where this doesn't work with unicode
                w=Float(str(wstr), n+1)
                one_plus_epsilon = S.One.evalf(n)\
                                   +pow(10,1-n)
                w *= one_plus_epsilon
    try:
        return w.evalf(n)
    except:
        return w

def modified_round(w, p=0):
    """
    sympy expr.round() function modified so that gives extra digits
    in it representation when p <= 0
    """
    try:
        from mpmath.libmp import prec_to_dps
    except ImportError:
        from sympy.mpmath.libmp import prec_to_dps

    from sympy.core.expr import _mag
    from sympy import Pow, Rational, Integer

    x = w
    if not x.is_number:
        raise TypeError('%s is not a number' % type(x))
    if x in (S.NaN, S.Infinity, S.NegativeInfinity, S.ComplexInfinity):
        return x
    if not x.is_real:
        i, r = x.as_real_imag()
        return i.round(p) + S.ImaginaryUnit*r.round(p)
    if not x:
        return x
    p = int(p)

    precs = [f._prec for f in x.atoms(C.Float)]
    dps = prec_to_dps(max(precs)) if precs else None

    mag_first_dig = _mag(x)
    allow = digits_needed = mag_first_dig + p
    if p <= 0:
        allow += 1
        digits_needed += 1
    if dps is not None and allow > dps:
        allow = dps
    mag = Pow(10, p)  # magnitude needed to bring digit p to units place
    xwas = x
    x += 1/(2*mag)  # add the half for rounding
    i10 = 10*mag*x.n((dps if dps is not None else digits_needed) + 1)
    if i10.is_negative:
        x = xwas - 1/(2*mag)  # should have gone the other way
        i10 = 10*mag*x.n((dps if dps is not None else digits_needed) + 1)
        rv = -(Integer(-i10)//10)
    else:
        rv = Integer(i10)//10
    q = 1
    if p > 0:
        q = mag
    elif p < 0:
        rv /= mag
    rv = Rational(rv, q)
    if rv.is_Integer:
        # use str or else it won't be a float
        return C.Float(str(rv), digits_needed)
    else:
        if not allow and rv > w:
            allow += 1
        return C.Float(rv, allow)


def round_expression(expression, n=0, initial_n_digits=100):
    """
    Customized version of round
    Attempts to round expressions to n decimal places in a way to get 
    identical results for two expressions that agree to n decimal places.
    To accomplish, the method performs the following steps
    1.  Traverses expression tree and attempts to call evalf with 
        initial_n_digits precision on every element.
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
    expression =  bottom_up(expression, 
            lambda w: _initial_evalf(w,initial_n_digits), atoms=True)

    # next, round numbers
    if n <= 0:
        from sympy import Integer
        expression =  bottom_up(
            expression,
            lambda w: w if not w.is_Number else Integer(modified_round(w,n)),
            atoms=True)
    else:
        expression =  bottom_up(
            expression,
            lambda w: w if not w.is_Number else Float(str(modified_round(w,n))),
            atoms=True)
        
    return expression


def evalf_expression(expression, n=15):
    """
    Customized version of evalf.
    Attempts to truncate expressions to n digits in a way to get 
    identical results for two expressions that agree to n digits.
    To accomplish, the method performs the following steps
    1.  Traverses expression tree and attempts to call evalf with max(30,n+5)
        precision on every element.
        The first pass puts expression in a consistent form.
    2.  Traverses expression tree, converting each number to a float
        with the precision specified by n.
        For consistency, converts expression to string and back to float
        so that expression loses memory of original value and two
        expression will be the same if their conversion to string is the same.
    """

    expression = sympify(expression)
    initial_n_digits = max(30, n+5)

    # first convert every number to a float with initial_n_digits
    # for consistency
    expression =  bottom_up(expression, 
            lambda w: _initial_evalf(w,initial_n_digits), atoms=True)

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
    expression =  bottom_up(
        expression,
        lambda w: w if not w.is_Float else Float(str(w.evalf(14))),
        atoms=True)
        
    return expression


class MatrixAsVector(Matrix):
    """
    Matrix that prints like a vector with latex.
    Simply outputs all elements, separated by commands and in parentheses.
    Produces reasonable results only for column or row matrices.
    
    """
    def _latex(self, prtr):
        # flattened list of elements
        elts = [item for sublist in self.tolist() for item in sublist] 
        return r"\left ( %s\right )" % \
            r", \quad ".join([ prtr._print(i) for i in elts ])
        

class MatrixFromTuple(object):
    """
    Returns MatrixAsVector from Tuple.

    """
    def __new__(cls, *args, **kwargs):
        return MatrixAsVector(list(args))
        
