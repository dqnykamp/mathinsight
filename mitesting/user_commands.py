# commands that users can use in questions


from sympy import Tuple, Function, Subs, Expr, Abs
from mitesting.sympy_customized import customized_sort_key, TupleNoParen
from sympy.logic.boolalg import BooleanFunction


def return_localized_commands():
    # create a dictionary containing the localized commands

    from mitesting.customized_commands import round_expression, evalf_expression
    from sympy import E, I, re, im
    
    localized_commands = \
        {'roots_tuple': roots_tuple, 
         'real_roots_tuple': real_roots_tuple, 
         'eigenvals_tuple': eigenvals_tuple,
         'eigenvects_tuple': eigenvects_tuple,
         'round': round_expression,
         'smallest_factor': smallest_factor,
         'find_all_roots_numerically': find_all_roots_numerically,
         'e': E,
         'i': I,
         'Re': re,
         'Im': im,
         'max': max_including_tuples,
         'Max': max_including_tuples,
         'min': min_including_tuples,
         'Min': min_including_tuples,
         'abs': Abs,
         'evalf': evalf_expression,
         'index': index,
         'sum': sum,
         'map': listmap,
         'if': iif,
         'len': len_custom,
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
         'cumsum': cumsum,
         'median': median,
         'prime_factors': prime_factors,
         'safe_getitem': safe_getitem,
        }
    
    return localized_commands


def listmap(*args, **kwargs):
    return list(map(*args,**kwargs))


class roots_tuple(Function):
    """
    Finds symbolic roots of a univariate polynomial.
    Returns a TupleNoParen of the sorted roots (using customized_sort_key)
    ignoring multiplicity
    
    """

    @classmethod
    def eval(cls, f, *gens):
        from sympy import roots
        rootslist = list(roots(f, *gens).keys())
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
        rootslist = list(roots(f, *gens, filter='R').keys())
        rootslist.sort(key=customized_sort_key)
        return TupleNoParen(*rootslist)

class eigenvects_tuple(Function):
    """
    Finds eigenvectors of a matrix
    Returns a TupleNoParen of eigenvectors, in same order as eigenvals_tuple
    (sorted according to eigenvalue using customized_sort_key)
    ignoring multiplicity
    
    """

    @classmethod
    def eval(cls, A):
        from .customized_commands import MatrixAsVector
        from numpy import array
        from numpy.linalg import eig
        from sympy.core import sympify
        
        # convert A to a numpy array of type float64
        try:
            A_array = array(A.tolist(), dtype='float64')
        except (TypeError, AttributeError):
            raise ValueError("Argument to eigenvects_tuple must be a matrix of numerical entries")

        [evals,evects] = eig(A_array)

        eigtuplelist = []
        for i in range(evals.size):
            eigtuplelist.append([sympify(evals[i]),
                                 sympify(evects[:,i].tolist())])


        eigtuplelist.sort(key=lambda w: customized_sort_key(w[0]))

        eiglist=[]
        for t in eigtuplelist:
            eiglist.append(MatrixAsVector(t[1]))
        return TupleNoParen(*eiglist)


class eigenvals_tuple(Function):
    """
    Finds eigenvalues of a matrix
    Returns a TupleNoParen of the sorted eigenvalues (using customized_sort_key)
    
    """

    @classmethod
    def eval(cls, A):
        from numpy import array
        from numpy.linalg import eigvals
        from sympy.core import sympify

        # convert A to a numpy array of type float64
        try:
            A_array = array(A.tolist(), dtype='float64')
        except (TypeError, AttributeError):
            raise ValueError("Argument to eigenvals_tuple must be a matrix of numerical entries")

        evals = eigvals(A_array)
        
        eiglist=[]
        for i in range(evals.size):
            eiglist.append(sympify(evals[i]))
        
        eiglist.sort(key=customized_sort_key)

        return TupleNoParen(*eiglist)


class index(Function):
    """
    Returns first index of value for list or Tuple expr.

    Return -1 if value not in list.
    """

    @classmethod
    def eval(cls,expr, value):
        try:
            return expr.index(value)
        except ValueError:
            return(-1)
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
            factorlist=list(factors.keys())
            factorlist.sort()
            return factorlist[0]
        else:
            raise ValueError("Argument to smallest_factor must be an integer")


class prime_factors(Function):
    """
    Find prime factors of expr up to 10000.
    Returns a TupleNoParen of the factors in increasing order, 
    ignoring multiplicity
    """

    @classmethod
    def eval(cls, expr):
        if expr.is_Integer:
            from sympy import primefactors
            return TupleNoParen(*primefactors(expr, limit=10000))
        else:
            raise ValueError("Argument to prime_factors must be an integer")


class max_including_tuples(Function):
    """
    If argument is a single Tuple, then find max over Tuple items.
    Else, find max over arguments.
    """

    @classmethod
    def eval(cls, *args):
        from sympy import Max
        if len(args)==1 and isinstance(args[0],Tuple):
            return Max(*args[0])
        else:
            return Max(*args)


class min_including_tuples(Function):
    """
    If argument is a single Tuple, then find min over Tuple items.
    Else, find min over arguments.
    """

    @classmethod
    def eval(cls, *args):
        from sympy import Min
        if len(args)==1 and isinstance(args[0],Tuple):
            return Min(*args[0])
        else:
            return Min(*args)


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


def safe_getitem(thetuple, n):
    """
    Safe version of thetuple[n] that returns Symbol('???')
    on TypeError or IndexError
    """
    
    try:
        return thetuple[n]
    except (TypeError, IndexError):
        from sympy import Symbol
        return Symbol('???')
    

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
        from sympy import oo, ImmutableMatrix
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
        if not (isinstance(u,Tuple) or isinstance(u,tuple) or \
                isinstance(u,ImmutableMatrix))\
           and not (isinstance(v,Tuple) or isinstance(v,tuple) \
                    or isinstance(v,ImmutableMatrix)):
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
        if isinstance(u,ImmutableMatrix):
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


from sympy import Point as sympy_Point
class Point(sympy_Point):
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
        from mitesting.sympy_customized import AddUnsort
        return AddUnsort(self.sub2.doit(), -self.sub1.doit())

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


class len_custom(BooleanFunction):
    @classmethod
    def eval(cls, arg):
        try:
            return len(arg)
        except TypeError:
            return 0


class find_all_roots_numerically(Function):
    """
    Attempt to find all roots of a function f between a and b
    by marching along at intervals of width 0.1, 
    looking for a change in sign.

    Given this crude stepping algorithm 
    and the large overhead of a parsed_function, 
    the algorithm will be slow if eps is too small compared to b-a.

    """
    @classmethod
    def eval(cls, f, a, b, eps=0.1):
        from scipy.optimize import brentq
        
        def rootsearch(f,a,b,dx):
            x1 = a
            try:
                f1 = f(a).evalf()
            except:
                return None, None
            x2_raw = a + dx
            x2 = min(x2_raw,b)
            try:
                f2 = f(x2).evalf()
            except:
                return None, None
            while f1*f2 > 0.0:
                if x2_raw >= b:
                    return None,None
                x1 = x2; f1 = f2
                x2_raw = x1 + dx
                x2 = min(x2_raw, b)
                try:
                    f2 = f(x2).evalf()
                except:
                    return None, None
            return x1,x2


        a=a.evalf()
        b=b.evalf()

        if a >= b:
            raise ValueError("Endpoints must be increasing. [%s, %s]" % (a,b))
        if eps <= 0:
            raise ValueError("Step size must be positive.  %s" % eps)

        roots=[]
        for i in range(1000):
            x1, x2 = rootsearch(f,a,b,eps)
            if x1 is None:
                break
            a=x2
            roots.append(brentq(f,x1,x2))
        
        return TupleNoParen(*roots)


"""
Turn off automatic evaluation of floats in the following sympy functions.
Functions will still evaluate to floats when .evalf() is called
and will otherwise behave normally.
"""

for cmd in ["log", "exp", "acos", "acosh", "acot", "acoth", "asin", "asinh", "atan", "atan2", "atanh", "cos", "cosh", "cot", "coth", "csc", "sec", "sin", "sinh", "tan", "tanh"]:
    exec("from sympy import %s as sympy_%s" % (cmd,cmd))

class log(sympy_log):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

    @classmethod
    def eval(cls, arg, base=None):
        from sympy.core import sympify
        arg = sympify(arg)

        # don't replace logs of rational with difference of logs
        if arg.is_Number and arg.is_Rational and arg.q != 1:
            return
        else:
            return super(log, cls).eval(arg,base)


class ln(sympy_log):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

    @classmethod
    def eval(cls, arg, base=None):
        from sympy.core import sympify
        arg = sympify(arg)

        # don't replace logs of rational with difference of logs
        if arg.is_Number and arg.is_Rational and arg.q != 1:
            return
        else:
            return super(ln, cls).eval(arg,base)

class exp(sympy_exp):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acos(sympy_acos):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acosh(sympy_acosh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acot(sympy_acot):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class acoth(sympy_acoth):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class asin(sympy_asin):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class asinh(sympy_asinh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atan(sympy_atan):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atan2(sympy_atan2):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class atanh(sympy_atanh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cos(sympy_cos):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cosh(sympy_cosh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class cot(sympy_cot):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class coth(sympy_coth):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class csc(sympy_csc):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sec(sympy_sec):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sin(sympy_sin):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class sinh(sympy_sinh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class tan(sympy_tan):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

class tanh(sympy_tanh):
    @classmethod
    def _should_evalf(cls, arg):
        return -1

def accumu(lis):
    total = 0
    for x in lis:
        total += x
        yield total

class cumsum(Function):
    @classmethod
    def eval(cls, lis):
        return list(accumu(lis))

class median(Function):
    @classmethod
    def eval(cls, lis):
        try:
            lis_sorted = sorted(lis)
        except TypeError:
            if isinstance(lis,list):
                return cls(Tuple(*lis))
            else:
                return None

        n=len(lis)
        index = (n-1) // 2
        if n < 1:
            if isinstance(lis,list):
                return cls(Tuple(*lis))
            else:
                return None
        if n % 2 == 1:
            return lis_sorted[index]
        if len(lis) %2 == 0:
            return (lis_sorted[index]+lis_sorted[index+1])/2
