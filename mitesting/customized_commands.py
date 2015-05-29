# customized sympy commands

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import Tuple, sympify, C, S, Float, Matrix, Abs, Gt, Lt, Ge, Le, Function
from mitesting.sympy_customized import bottom_up, customized_sort_key, TupleNoParen, And
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

    Compares as equal to Tuples or tuples.
    
    """
    def _latex(self, prtr):
        # flattened list of elements
        elts = [item for sublist in self.tolist() for item in sublist] 
        return r"\left ( %s\right )" % \
            r", \quad ".join([ prtr._print(i) for i in elts ])
        
    def __eq__(self, other):
        # compare as equal to tuple or Tuple
        if isinstance(other, Tuple) or isinstance(other,tuple):
            n=len(other)
            if not self.shape==(1,n) or self.shape==(n,1):
                return False
            return Tuple(*self)==other

        return super(MatrixAsVector, self).__eq__(other)


class MatrixFromTuple(object):
    """
    Returns MatrixAsVector from Tuple.

    """
    def __new__(cls, *args, **kwargs):
        return MatrixAsVector(list(args))
        

class Gts(BooleanFunction):
    """
    Multiple GreaterThan function for expressions such as a > b >= c.

    First argument is iterable of expressions.
    If two or fewer expressions, return standard Gt or Ge.
    Otherwise, the inequality is unevaluated.

    Second argument, strict, determines if strict inequality.  (Defaults to True.)

    If strict is iterable, then components determine the strictness of
    each inequality.  
    Extra components of strict are ignored.
    If strict has too few components, the last component of applies to 
    remaining inequalities.

    If strict is not iterable, then the truth value of strict applies to
    all inequalities.
    

    """

    def __new__(cls, *args, **kwargs):
        
        if len(args) !=1 and len(args) !=2:
            raise TypeError("Gts must have 1 or 2 arguments (%s given)" % \
                            len(args))
            
        exprs=args[0]
        if len(args) == 2:
           strict=args[1]
        else:
           strict=True
        try:
            nexprs = len(exprs)
        except TypeError:
            raise TypeError("First argument of Gts must have at least 2 elements (1 given)")


        if len(exprs) < 2:
            raise TypeError("First argument of Gts must have at least 2 elements (%s given)"
                            % len(exprs))

        elif len(exprs)==2:
            try:
                strict0=strict[0]
            except TypeError:
                strict0=strict
            if strict0:
                return Gt(exprs[0],exprs[1], **kwargs)
            else:
                return Ge(exprs[0],exprs[1], **kwargs)
        else:
            obj = super(Gts, cls).__new__(cls,*args,**kwargs)
            
            if kwargs.get("evaluate", True):
                obj.normalize_args()
                return obj.doit(deep=False)
            else:
                return obj

    def __init__(self, *args, **kwargs):
        self.normalize_args()

    def normalize_args(self):
        self.exprs = self.args[0]

        if(len(self.args)==2):
           self.strict = self.args[1]
        else:
           self.strict = True

        self.nargs = len(self.exprs)

        try:
            nstrict = len(self.strict)
            self.strict=list(self.strict)
        except TypeError:
            try:
                self.strict=[bool(self.strict)]*(self.nargs-1)
            except TypeError:
                self.strict=[True]*(self.nargs-1)
        else:
            for i in range(min(nstrict,self.nargs-1)):
                try: 
                    self.strict[i] = bool(self.strict[i])
                except TypeError:
                    self.strict[i] = True
            if nstrict < self.nargs-1:
                self.strict += [self.strict[:]]*(self.nargs-1-nstrict)
            elif nstrict > self.nargs-1:
                self.strict = self.strict[:self.nargs-1]
            
        self.strict = tuple(self.strict)

    def _hashable_content(self):
        """
        Use normalized args for hashable content so
        equality doesn't depend original format for strict
        """

        return (self.exprs, self.strict)


    def doit(self, **hints):
        result=True
        if hints.get('deep', True):
            if self.strict[0]:
                result = Gt(self.exprs[0].doit(**hints), 
                            self.exprs[1].doit(**hints))
            else:
                result = Ge(self.exprs[0].doit(**hints), 
                            self.exprs[1].doit(**hints))
            for i in range(1, self.nargs-1):
                if self.strict[i]:
                    result = And(result, Gt(self.exprs[i].doit(**hints), 
                                            self.exprs[i+1].doit(**hints)))
                else:
                    result = And(result, Ge(self.exprs[i].doit(**hints), 
                                            self.exprs[i+1].doit(**hints)))
            return result
        else:
            if self.strict[0]:
                result = Gt(self.exprs[0], self.exprs[1])
            else:
                result = Ge(self.exprs[0], self.exprs[1])
            for i in range(1, self.nargs-1):
                if self.strict[i]:
                    result = And(result, Gt(self.exprs[i], self.exprs[i+1]))
                else:
                    result = And(result, Ge(self.exprs[i], self.exprs[i+1]))
            return result


    def __nonzero__(self):
        return bool(self.doit(deep=False))

    __bool__ = __nonzero__


    def _latex(self, prtr):
        tex = "%s" % prtr._print(self.exprs[0])
        for i in range(self.nargs-1):
            if self.strict[i]:
                tex += " >"
            else:
                tex += " \geq"
            tex += " %s" % prtr._print(self.exprs[i+1])

        return tex




class Lts(BooleanFunction):
    """
    Multiple LessThan function for expressions such as a < b <= c.

    First argument is iterable of expressions.
    If two or fewer expressions, return standard Lt or Le.
    Otherwise, the inequality is unevaluated.

    Second argument, strict, determines if strict inequality.  (Defaults to True.)

    If strict is iterable, then components determine the strictness of
    each inequality.  
    Extra components of strict are ignored.
    If strict has too few components, the last component of applies to 
    remaining inequalities.

    If strict is not iterable, then the truth value of strict applies to
    all inequalities.
    

    """

    def __new__(cls, *args, **kwargs):
        
        if len(args) !=1 and len(args) !=2:
            raise TypeError("Lts must have 1 or 2 arguments (%s given)" % \
                            len(args))
            
        exprs=args[0]
        if len(args) == 2:
           strict=args[1]
        else:
           strict=True
        try:
            nexprs = len(exprs)
        except TypeError:
            raise TypeError("First argument of Lts must have at least 2 elements (1 given)")


        if len(exprs) < 2:
            raise TypeError("First argument of Lts must have at least 2 elements (%s given)"
                            % len(exprs))

        elif len(exprs)==2:
            try:
                strict0=strict[0]
            except TypeError:
                strict0=strict
            if strict0:
                return Lt(exprs[0],exprs[1], **kwargs)
            else:
                return Le(exprs[0],exprs[1], **kwargs)
        else:
            obj = super(Lts, cls).__new__(cls,*args,**kwargs)
            
            if kwargs.get("evaluate", True):
                obj.normalize_args()
                return obj.doit(deep=False)
            else:
                return obj

    def __init__(self, *args, **kwargs):
        self.normalize_args()

    def normalize_args(self):
        self.exprs = self.args[0]

        if(len(self.args)==2):
           self.strict = self.args[1]
        else:
           self.strict = True

        self.nargs = len(self.exprs)

        try:
            nstrict = len(self.strict)
            self.strict=list(self.strict)
        except TypeError:
            try:
                self.strict=[bool(self.strict)]*(self.nargs-1)
            except TypeError:
                self.strict=[True]*(self.nargs-1)
        else:
            for i in range(min(nstrict,self.nargs-1)):
                try: 
                    self.strict[i] = bool(self.strict[i])
                except TypeError:
                    self.strict[i] = True
            if nstrict < self.nargs-1:
                self.strict += [self.strict[:]]*(self.nargs-1-nstrict)
            elif nstrict > self.nargs-1:
                self.strict = self.strict[:self.nargs-1]
            
        self.strict = tuple(self.strict)

    def _hashable_content(self):
        """
        Use normalized args for hashable content so
        equality doesn't depend original format for strict
        """

        return (self.exprs, self.strict)


    def doit(self, **hints):
        result=True
        if hints.get('deep', True):
            if self.strict[0]:
                result = Lt(self.exprs[0].doit(**hints), 
                            self.exprs[1].doit(**hints))
            else:
                result = Le(self.exprs[0].doit(**hints), 
                            self.exprs[1].doit(**hints))
            for i in range(1, self.nargs-1):
                if self.strict[i]:
                    result = And(result, Lt(self.exprs[i].doit(**hints), 
                                            self.exprs[i+1].doit(**hints)))
                else:
                    result = And(result, Le(self.exprs[i].doit(**hints), 
                                            self.exprs[i+1].doit(**hints)))
            return result
        else:
            if self.strict[0]:
                result = Lt(self.exprs[0], self.exprs[1])
            else:
                result = Le(self.exprs[0], self.exprs[1])
            for i in range(1, self.nargs-1):
                if self.strict[i]:
                    result = And(result, Lt(self.exprs[i], self.exprs[i+1]))
                else:
                    result = And(result, Le(self.exprs[i], self.exprs[i+1]))
            return result


    def __nonzero__(self):
        return bool(self.doit(deep=False))

    __bool__ = __nonzero__


    def _latex(self, prtr):
        tex = "%s" % prtr._print(self.exprs[0])
        for i in range(self.nargs-1):
            if self.strict[i]:
                tex += " <"
            else:
                tex += " \leq"
            tex += " %s" % prtr._print(self.exprs[i+1])

        return tex



class subscript_symbol(Function):
    """
    Returns a symbol of the form "a_b" where a and b are latexed arguments.

    If third argument is True, then create real symbol
    
    """

    @classmethod
    def eval(cls, a,b, real=False):

        from mitesting.sympy_customized import Symbol, latex
        symbol_name=''
        if b is None:
            if a is None:
                symbol_name='_'
            else:
                symbol_name='%s_' % latex(a)
        else:
            if a is None:
                symbol_name='_%s' % latex(b)
            else:
                symbol_name='%s_%s' % (latex(a),latex(b))

        if real:
            return Symbol(symbol_name, real=True)
        else:
            return Symbol(symbol_name)
