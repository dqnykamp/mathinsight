# customized sympy commands

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import Tuple, sympify, Function, C, S, Basic, Float, Matrix, Expr, Subs
from mitesting.sympy_customized import bottom_up, customized_sort_key, TupleNoParen
from sympy.logic.boolalg import BooleanFunction


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
    Returns a TupleNoParen of the sorted roots (using customized_sort_key)
    ignoring multiplicity
    
    """

    from sympy import roots
    rootslist = roots(f, *gens, **flags).keys()
    rootslist.sort(key=customized_sort_key)

    return TupleNoParen(*rootslist)

def real_roots_tuple(f, *gens):
    """
    Finds real roots of a univariate polynomial.
    Returns a TupleNoParen of the sorted roots, ignoring multiplicity.
    """
    from sympy import roots
    rootslist = roots(f, *gens, filter='R').keys()
    rootslist.sort(key=customized_sort_key)
    return TupleNoParen(*rootslist)


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
    from sympy import Piecewise
    return Piecewise((result_if_true,cond),(result_if_false,True))


def count(thelist, item):
    """
    Implementation of list count member function as a separate function
    so that works with parse_expr and implicit multiplication transformation.
    """
    return thelist.count(item)

def scalar_multiple_deviation(u,v):
    """
    Return deviation from u and v being scalar multiples of each other,
    where u and v are either matrices or tuples representing vectors

    For each component that is nonzero for both u and v,
    calculate ratio between their components.
    Divide each such ratio by the first ratio
    and add the absolute difference from 1, symmetrized between u and v.
    Return this sum as the deviation.

    Returns 0 if they are perfectly scalar multiples.
    A non-zero number represents an estimate of the fraction they are away
    from being scalar multiples of each other.
    A very small deviation (on order of machine precision) 
    is an indication that u and v may be scalar multiples except for
    differences due to round off error.

    If u and v are both scalars, then consider multiples if both zero
    or if both non-zero and one can take their ratio.

    Returns infinity (oo) if for some component only one of u or v is zero.
    Hence, the zero vector is excluded as being a scalar multiple unless
    both u and v are the zero vector.

    Returns infinity (oo) if u and v are not both tuples/matrices
    of the same size and type.

    Have not implemented for sympy's Vector class.
    """
    
    from sympy import oo

    u = sympify(u)
    v = sympify(v)

    if u == v:
        return 0

    # if u and v are not tuples or Matrices, then
    # - to be consistent, u and v are not multiples if either are zero 
    #   (the case of both zero is accounted for above)
    # - otherwise, attempt to take ratio, 
    #   and consider u and v to be multiples if this ratio can be taken
    if not (isinstance(u,Tuple) or isinstance(u,tuple) or isinstance(u,Matrix))\
       and not (isinstance(v,Tuple) or isinstance(v,tuple) \
                or isinstance(v,Matrix)):
        if u==0 or v==0:
            return oo
        try:
            ratio = u/v
        except AttributeError:
            return oo
        else:
            return 0

    # if not the same type of tuple, then return as non-multiples
    if u.__class__ != v.__class__:
        return oo
    
    if len(u) != len(v):
        return oo

    # if matrices, also demand the same shape
    if isinstance(u,Matrix):
        if u.shape != v.shape:
            return oo

    n = len(u)

    # find indices where both u and v are non-zero
    # if find index where only one of u and v zero, then conclude not multiples
    nonzero_inds=[]
    for i in range(n):
        if u[i]==0:
            if v[i]==0:
                continue
            else:
                return oo
        else:
            if v[i]==0:
                return oo
            else:
                nonzero_inds.append(i)

    # shouldn't encounter no nonzero inds, as two zero vectors
    # should have been caught in first line
    if len(nonzero_inds)==0:
        return 0

    ind1=nonzero_inds[0]

    try:
        base_ratio = u[ind1]/v[ind1]
    except AttributeError:
        # if components are objects that can't be divided, 
        # then u and v aren't scalar multiples
        return oo

    # if just one non-zero component, and we could divide to form base_ratio,
    # then consider scalar multiples
    if len(nonzero_inds)==1:
        return 0
    
    deviation_sum = 0
    for i in range(1, len(nonzero_inds)):
        try:
            ratio_of_ratios = u[nonzero_inds[i]]/v[nonzero_inds[i]]/base_ratio
        except AttributeError:
            # if components are objects that can't be divided, 
            # then u and v aren't scalar multiples
            return oo

        try:
            ratio_of_ratios = ratio_of_ratios.ratsimp()
        except:
            pass

        # symmetrize deviation_sum with respect to u and v
        deviation_sum += (Abs(ratio_of_ratios-1)+Abs(1/ratio_of_ratios-1))/2
        
    if deviation_sum.is_comparable:
        return deviation_sum
    else:
        return oo


class Point(C.Point):
    def evalf(self, prec=None, **options):
        coords = [x.evalf(prec, **options) for x in self.args]
        return type(self)(*coords, evaluate=False)

    def __new__(cls, *args, **kwargs):
        kwargs["evaluate"]=False
        return super(Point, cls).__new__(cls,*args, **kwargs) 


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
        

class DiffSubs(Expr):
    """
    Difference of substituting two different values of variables
    into an expression.
    """

    def __new__(cls, expr, variables, point1, point2, 
                 **assumptions):
        obj = Expr.__new__(cls, expr, variables, point1, point2)
        obj.sub1 = Subs(expr, variables, point1, **assumptions)
        obj.sub2 = Subs(expr, variables, point2, **assumptions)
        return obj

    def doit(self):
        return self.sub2.doit() - self.sub1.doit()

    def as_difference(self):
        from mitesting.sympy_customized import AddUnsortInitial
        return AddUnsortInitial(self.sub2.doit(), -self.sub1.doit())

    def evalf(self, prec=None, **options):
        return self.sub2.doit().evalf(prec, **options)\
            -self.sub1.doit().evalf(prec, **options)

    def _latex(self, prtr):
        expr, old, new1 = self.sub1.args
        latex_expr = prtr._print(expr)
        latex_old = (prtr._print(e) for e in old)
        latex_new1 = (prtr._print(e) for e in new1)
        new2 = self.sub2.args[2]
        latex_new2 = (prtr._print(e) for e in new2)
        latex_subs1 = r'\\ '.join(
            e[0] + '=' + e[1] for e in zip(latex_old, latex_new1))
        latex_old = (prtr._print(e) for e in old)
        latex_subs2 = r'\\ '.join(
            e[0] + '=' + e[1] for e in zip(latex_old, latex_new2))
        return r'\left. %s \vphantom{\Large I} \right|_{\substack{ %s }}^{\substack{ %s }}' % (latex_expr, latex_subs1, latex_subs2)



class IsNumberUneval(BooleanFunction):
    def doit(self, **hints):
        if hints.get('deep', True):
            return self.args[0].doit(**hints).is_number
        else:
            return  self.args[0].is_number


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
