# commands that users can use in questions

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import Tuple, Function, C,  Subs, Expr, Abs
from mitesting.sympy_customized import customized_sort_key, TupleNoParen
from sympy.logic.boolalg import BooleanFunction


def return_localized_commands():
    # create a dictionary containing the localized commands

    from mitesting.customized_commands import round_expression, evalf_expression
    from sympy import E
    
    localized_commands = \
        {'roots_tuple': roots_tuple, 
         'real_roots_tuple': real_roots_tuple, 
         'round': round_expression,
         'smallest_factor': smallest_factor,
         'e': E,
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
         'is_number': is_number,
         'acosh': acosh, 'acos': acos, 'acosh': acosh, 
         'acot': acot, 'acoth': acoth, 'asin': asin, 'asinh': asinh, 
         'atan': atan, 'atan2': atan2, 'atanh': atanh, 
         'cos': cos, 'cosh': cosh, 'cot': cot, 'coth': coth, 'csc': csc, 
         'sec': sec, 'sin': sin, 'sinh': sinh, 'tan': tan, 'tanh': tanh, 
         'scalar_multiple_deviation': scalar_multiple_deviation,
        }
    
    return localized_commands


class roots_tuple(Function):
    """
    Finds symbolic roots of a univariate polynomial.
    Returns a TupleNoParen of the sorted roots (using customized_sort_key)
    ignoring multiplicity
    
    """

    @classmethod
    def eval(cls, f, *gens):
        from sympy import roots
        rootslist = roots(f, *gens).keys()
        rootslist.sort(key=customized_sort_key)

        return TupleNoParen(*rootslist)


class real_roots_tuple(Function):
    """
    Finds real roots of a univariate polynomial.
    Returns a TupleNoParen of the sorted roots, ignoring multiplicity.
    """

    @classmethod
    def eval(cls, f, *gens):
        from sympy import roots
        rootslist = roots(f, *gens, filter='R').keys()
        rootslist.sort(key=customized_sort_key)
        return TupleNoParen(*rootslist)


class index(Function):
    """
    Returns first index of value for list or Tuple expr.
    """

    @classmethod
    def eval(cls,expr, value):
        try:
            return expr.index(value)
        except ValueError:
            if isinstance(expr,Tuple) or isinstance(expr,tuple):
                group_type = "tuple"
            else:
                group_type = expr.__class__.__name__
            raise ValueError("%s is not in %s" % (value, group_type))
        except AttributeError:
            raise ValueError("First argument of index must be a list or tuple")

    # override so never evaluates as float
    # (default sympy _should_evalf fails if arg is a list)
    @classmethod
    def _should_evalf(cls, arg):
        return -1


class smallest_factor(Function):
    """
    Find smallest factor of absolute value of expr up to 10000.
    Assumes expr is a sympy integer, not a Python integer
    """

    @classmethod
    def eval(cls, expr):
        if expr.is_Integer:
            from sympy import factorint
            factors = factorint(Abs(expr), limit=10000)
            factorlist=factors.keys()
            factorlist.sort()
            return factorlist[0]
        else:
            raise ValueError("Argument to smallest_factor must be an integer")


class max_including_tuples(Function):
    """
    If argument is a single Tuple, then find max over Tuple items.
    Else, find max over arguments.
    """

    @classmethod
    def eval(cls, *args):
        if len(args)==1 and isinstance(args[0],Tuple):
            return C.Max(*args[0])
        else:
            return C.Max(*args)


class min_including_tuples(Function):
    """
    If argument is a single Tuple, then find min over Tuple items.
    Else, find min over arguments.
    """

    @classmethod
    def eval(cls, *args):
        if len(args)==1 and isinstance(args[0],Tuple):
            return C.Min(*args[0])
        else:
            return C.Min(*args)


def iif(cond, result_if_true, result_if_false):
    """
    Inline if statement
    """
    from sympy import Piecewise
    return Piecewise((result_if_true,cond),(result_if_false,True))


def count(thelist, item):
    """
    Implementation of list count member function as a separate function.
    """
    return thelist.count(item)


class scalar_multiple_deviation(Function):
    """
    Inputs: u, v
    two tuples (representing vectors) or two matrices,

    Returns a number that represents how far u and v are from being
    scalar multiples of each other:
    - 0:  if u and v are exactly scalar multiples of each other
    - positive number: an estimate of the fraction they are away
      from being scalar multiples of each other.
    - infinity (oo): if u and v are definitely not scalar multiples.

    A very small deviation (on order of machine precision) 
    is an indication that u and v may be scalar multiples except for
    differences due to round off error.

    If u and v are both scalars, then consider u and v multiples of each other
    if both u and v are zero
    or if both u and v are non-zero and their ratio is defined.

    Returns infinity (oo) if for some component only one of u or v is zero.
    Hence, the zero vector is excluded as being a scalar multiple unless
    both u and v are the zero vector.

    Returns infinity (oo) if u and v are not both tuples/matrices
    of the same size and type. 
    Exception is that row or column MatrixAsVectors are turned into Tuples

    Algorithm:
    For each component that is nonzero for both u and v,
    calculate ratio between their components.
    Divide each such ratio by the first ratio
    and add the absolute difference from 1, symmetrized between u and v.
    If the result is a number, return this sum, otherwise return oo.

    Have not implemented for sympy's Vector class.
    """

    nargs=2

    @classmethod
    def eval(cls, u,v):
        from sympy import oo, Matrix
        from mitesting.customized_commands import MatrixAsVector

        # if u or v are MatrixAsVectors (row or column), convert to Tuples
        if isinstance(u,MatrixAsVector) and (u.cols==1 or u.rows==1):
            u = Tuple(*[elt for elt in u])
        if isinstance(v,MatrixAsVector) and (v.cols==1 or v.rows==1):
            v = Tuple(*[elt for elt in v])

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



class is_number(BooleanFunction):
    @classmethod
    def eval(cls, arg):
        return arg.is_number


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
