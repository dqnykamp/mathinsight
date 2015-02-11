from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import sympify, default_sort_key
from sympy.parsing.sympy_tokenize import NAME, OP
from sympy import Tuple, Float, Symbol, Rational, Integer, Pow, factorial, Matrix, Derivative, Expr, Add, Mul, S
from sympy.core.function import UndefinedFunction
from sympy.printing.latex import LatexPrinter as sympy_LatexPrinter

from sympy import Interval as sympy_Interval
from sympy import FiniteSet as sympy_FiniteSet

import re
import keyword

EVALUATE_NONE = 0
EVALUATE_PARTIAL = 1
EVALUATE_FULL = 2

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
        if isinstance(rv, list) or isinstance(rv,tuple):
            rv = rv.__class__(bottom_up(a, F, atoms, nonbasic) for a in rv)
        elif isinstance(rv, Tuple):
            rv = rv.__class__(*[bottom_up(a, F, atoms, nonbasic) for a in rv])
        elif isinstance(rv,Matrix):
            rv = rv.__class__([bottom_up(a, F, atoms, nonbasic) for a in rv.tolist()])
            if nonbasic:
                rv=F(rv)
        elif isinstance(rv, AddUnsort):
            args = tuple([bottom_up(a, F, atoms, nonbasic)
                for a in rv.original_args])
            rv = AddUnsortInitial(*args)
            rv = F(rv)
        elif isinstance(rv, MulUnsort):
            args = tuple([bottom_up(a, F, atoms, nonbasic)
                for a in rv.original_args])
            rv = MulUnsortInitial(*args)
            rv = F(rv)
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
               split_symbols=False, evaluate=True,
               replace_symmetric_intervals=False,
               assume_real_variables=False):
    """
    Customized version of sympy parse_expr with the following modifications.
    1.  Add Integer, Float, Rational, Symbol, and factorial
        to global_dict if not present.  
        (Needed since Symbol could be added by auto_symbol,
        Integer, Float, or Rational could be added by auto_number,
        and factorial could be added by factorial_notation.)
    2.  Use a customized version of the auto_symbol transformation 
        so that python keywords like "lambda", "as" and "if" 
        will be parsed to symbols.
        If assume_real_variables, the symbols created in this way will be real.
    3.  In addition, use auto_number, factorial notation, convert_xor
        and implicit_multiplication transformations by default, 
        and add split_symbols transformation if split_symbols is True.
    4.  Allows substitution of python keywords like 'lambda', 'as", or "if" 
        via local/global_dict.
    5.  Remove leading 0s from numbers so not interpreted as octal numbers.
    6.  Convert leading 0x to 0*x so not interpreeted as hexadecimal numbers.
    7.  Call sympify after parse_expr so that tuples will be 
        converted to Sympy Tuples.  (A bug in parse_expr that this
        doesn't happen automatically?)
    """
    
    from sympy.parsing.sympy_parser import \
        (auto_number, factorial_notation, convert_xor)
    from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr

    # Create new global dictionary so modifications don't affect original
    if global_dict:
        new_global_dict = global_dict.copy()
    else:
        new_global_dict ={}
    if local_dict:
        new_local_dict = local_dict.copy()
    else:
        new_local_dict = {}

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
        if 'Add' not in new_global_dict:
            new_global_dict['Add'] = AddUnsortInitial
        if 'Mul' not in new_global_dict:
            new_global_dict['Mul'] = MulUnsortInitial
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
    if assume_real_variables:
        transformations=(auto_symbol_real,)
    else:
        transformations=(auto_symbol,)
    transformations += (auto_number, factorial_notation, convert_xor)
    if split_symbols:
        transformations += (split_symbols_trans, )
    transformations += (implicit_multiplication, )

    # if a python keyword such as "lambda" or "as" is in 
    # the local or global dictionary, we can't use 
    # the standard approach to substitute values. 
    # Instead, we replace keyword with _keyword_ in both the
    # expression and the dictionary keys.
    for kword in keyword.kwlist:
        kword_found=False
        if kword in new_global_dict:
            new_global_dict['_'+kword+'_'] = new_global_dict[kword]
            del new_global_dict[kword]
            kword_found=True
        if new_local_dict and kword in new_local_dict:
            new_local_dict['_'+kword+'_'] = new_local_dict[kword]
            del new_local_dict[kword]
            kword_found=True
        if kword_found:
            s = re.sub(r'\b'+kword+r'\b', '_'+kword+'_', s)


    # Don't interpret leading 0 in number as indicating octal number
    # To prevent this interpretation, remove leading 0s from numbers
    # Use a lookbehind to make sure the zero does not comes after
    # an alphanumeric character or a period
    s = re.sub(r'(?<![\w\.])0*(\d)', r'\1', s)

    # Don't interpret leading 0x as indicating hexadecimal number
    # To prevent this interpretation, change to 0*x
    s = re.sub(r'\b0x', r'0*x', s)
    
    # Don't interpret integer followed by l or L as a long integer.
    # Instead, make it be a multiplication
    s = re.sub(r'(\d)l', r'\1*l', s)
    s = re.sub(r'(\d)L', r'\1*L', s)

    # replace unicode character for - used in mathjax display with -
    s= re.sub(r'\u2212', r'-', s)

    # replace mathjax character for \times with *
    s = re.sub(r'\xd7', r'*', s)
    
    # replace unicode character for \cdot used in mathjax display with *
    s = re.sub(r'\u22c5', r'*', s)

    from mitesting.utils import replace_simplified_derivatives
    s= replace_simplified_derivatives(
        s, local_dict=new_local_dict, global_dict=new_global_dict, 
        split_symbols=split_symbols,
        assume_real_variables=assume_real_variables)

    # replace
    #      =  with __Eq__(lhs,rhs)
    #      != with __Ne__(lhs,rhs)
    #   and/& with __And__(lhs,rhs)
    #    or/| with __Or__(lhs,rhs)
    #     in  with (rhs).contains(lhs)
    from mitesting.utils import replace_boolean_equals_in, replace_intervals

    s=replace_boolean_equals_in(s, evaluate=evaluate)
    s=replace_intervals(s, replace_symmetric=replace_symmetric_intervals)

    # map those replace booleans and equals to sympy functions
    from sympy import Eq, Ne, And, Or
    new_global_dict['__Eq__'] = Eq
    new_global_dict['__Ne__'] = Ne
    new_global_dict['__And__'] = And
    new_global_dict['__Or__'] = Or
    new_global_dict['__Interval__'] = Interval
    
    # change {} to __FiniteSet__()
    s = re.sub(r'{',r' __FiniteSet__(', s)
    s = re.sub(r'}', r')', s)
    new_global_dict['__FiniteSet__'] = FiniteSet

    # change !== to !=
    s = re.sub('!==','!=', s)

    # change === to = (so can assign keywords in functions like Interval)
    s = re.sub('===','=', s)

    # call sympify after parse_expr to convert tuples to Tuples
    expr = sympify(sympy_parse_expr(
            s, global_dict=new_global_dict, local_dict=new_local_dict, 
            transformations=transformations, evaluate=evaluate))

    # if expr is a Tuple, but s had implicit parentheses, 
    # then return TupleNoParen
    if isinstance(expr,Tuple):
        # implicit parens if there is a comma that is not inside
        # matching parentheses
        parenCtr=0
        for (i,c) in enumerate(s):
            if c == "(":
                parenCtr +=1
            elif c == ")":
                parenCtr -=1
            elif c == ",":
                if parenCtr==0:
                    expr = TupleNoParen(*expr)
                    break

    # if evaluate, then 
    # - replace AddUnsorts with Adds
    # - replace MulUnsorts with Muls
    def replaceUnsorts(w):
        if isinstance(w, AddUnsort):
            return Add(*w.args)
        if isinstance(w, MulUnsort):
            return Mul(*w.args)
        return w

    if evaluate:
        expr=bottom_up(expr, replaceUnsorts)

    return expr



def parse_and_process(s, global_dict=None, local_dict=None,
                      split_symbols=False, evaluate_level=None,
                      replace_symmetric_intervals=False,
                      assume_real_variables=False):
    """
    Parse expression and optionally call doit, evaluate_level is full. 
    If evaluate_level = EVALUATE_NONE, then parse
    with evaluate=False set.
    If evaluate_level = EVALUATE_FULL or evaluate_level=None,
    then call doit() after parsing.
    """
    
    if evaluate_level == EVALUATE_NONE:
        evaluate = False
    else:
        evaluate = True

    expression = parse_expr(
        s, global_dict=global_dict, local_dict=local_dict,
        split_symbols=split_symbols, evaluate=evaluate,
        replace_symmetric_intervals=replace_symmetric_intervals,
        assume_real_variables=assume_real_variables)

    if evaluate_level == EVALUATE_FULL or evaluate_level is None:
        try: 
            expression=expression.doit()
        except (AttributeError, TypeError):
            pass
        
    return expression


def auto_symbol(tokens, local_dict, global_dict):
    """Inserts calls to ``Symbol`` for undefined variables.
    
    Customized verison of auto symbol
    only difference is that ignore python keywords and None
    so that the keywords and None will be turned into a symbol
    """
    from sympy.core.basic import Basic

    result = []
    prevTok = (None, None)

    tokens.append((None, None))  # so zip traverses all tokens
    for tok, nextTok in zip(tokens, tokens[1:]):
        tokNum, tokVal = tok
        nextTokNum, nextTokVal = nextTok
        if tokNum == NAME:
            name = tokVal

            if (name in ['True', 'False', 'and', 'or', 'not', 'in']
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

def auto_symbol_real(tokens, local_dict, global_dict):
    """Inserts calls to ``Symbol`` for undefined variables,
    designating them as real

    Customized verison of auto symbol
    only other difference is that ignore python keywords and None
    so that the keywords and None will be turned into a symbol
    """
    from sympy.core.basic import Basic

    result = []
    prevTok = (None, None)

    tokens.append((None, None))  # so zip traverses all tokens
    for tok, nextTok in zip(tokens, tokens[1:]):
        tokNum, tokVal = tok
        nextTokNum, nextTokVal = nextTok
        if tokNum == NAME:
            name = tokVal

            if (name in ['True', 'False', 'and', 'or', 'not', 'in']
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
                (OP, ','),
                (NAME, 'real'),
                (OP, '='),
                (NAME, 'True'),
                (OP, ')'),
            ])
        else:
            result.append((tokNum, tokVal))

        prevTok = (tokNum, tokVal)

    return result


class SymbolCallable(Symbol):
    pass

def _token_callable(token, local_dict, global_dict, nextToken=None, 
                    include_symbol_callable=True):
    """
    Predicate for whether a token name represents a callable function.

    Essentially wraps ``callable``, but looks up the token name in the
    locals and globals.
    """
    func = local_dict.get(token[1])
    if func is None:
        func = global_dict.get(token[1])
    return callable(func) and (not isinstance(func, Symbol)
            or (include_symbol_callable and isinstance(func, SymbolCallable)))


def implicit_multiplication(result, local_dict, global_dict):
    """Makes the multiplication operator optional in most cases.

    Customized version: 
    1. don't add multiplication adjacent to and/or/not.
    2. treat as SymbolCallable as callable

    Use this before :func:`implicit_application`, otherwise expressions like
    ``sin 2x`` will be parsed as ``x * sin(2)`` rather than ``sin(2*x)``.

    Example:

    >>> from sympy.parsing.sympy_parser import (parse_expr,
    ... standard_transformations, implicit_multiplication)
    >>> transformations = standard_transformations + (implicit_multiplication,)
    >>> parse_expr('3 x y', transformations=transformations)
    3*x*y
    """
    # These are interdependent steps, so we don't expose them separately
    from sympy.parsing.sympy_parser import _group_parentheses, \
        _flatten
    for step in (_group_parentheses(implicit_multiplication),
                 _apply_functions,
                 _implicit_multiplication):
        result = step(result, local_dict, global_dict)

    result = _flatten(result)
    return result


def _apply_functions(tokens, local_dict, global_dict):
    """Convert a NAME token + ParenthesisGroup into an AppliedFunction.

    Note that ParenthesisGroups, if not applied to any function, are
    converted back into lists of tokens.

    Customized version that adds .default to end of ParsedFunctions
    if they are not followed by a ParenthesisGroup.
    In this way, a Function will behave like an Expression if
    it is not followed by an argument.
    """

    from sympy.parsing.sympy_parser import ParenthesisGroup, AppliedFunction
    from .utils import ParsedFunction

    result = []
    symbol = None
    parsed_function = False
    for tok in tokens:
        if tok[0] == NAME:
            symbol = tok
            result.append(tok)

            # check if tok represent a ParsedFunction
            func = local_dict.get(tok[1])
            if func is None:
                func = global_dict.get(tok[1])
            if func is not None:
                try:
                    if issubclass(func, ParsedFunction):
                        parsed_function=True
                except TypeError:
                    pass
        elif isinstance(tok, ParenthesisGroup):
            if symbol and _token_callable(symbol, local_dict, global_dict):
                result[-1] = AppliedFunction(symbol, tok)
                symbol = None
            else:
                result.extend(tok)
            parsed_function=False
        else:
            if parsed_function:
                # if found parsed function not followed by ParenthesisGroup,
                # then append .default
                result[-1] = (NAME, "%s.default" % symbol[1])
                parsed_function=False
            symbol = None
            result.append(tok)
    return result


def _implicit_multiplication(tokens, local_dict, global_dict):
    """Implicitly adds '*' tokens.

    Customized version: only difference is don't add multiplication
    adjacent to and/or/not and don't include SymbolCallable as callable
    except before parentheses.

    Cases:

    - Two AppliedFunctions next to each other ("sin(x)cos(x)")

    - AppliedFunction next to an open parenthesis ("sin x (cos x + 1)")

    - A close parenthesis next to an AppliedFunction ("(x+2)sin x")\

    - A close parenthesis next to an open parenthesis ("(x+2)(x+3)")

    - AppliedFunction next to an implicitly applied function ("sin(x)cos x")

    """
    from sympy.parsing.sympy_parser import AppliedFunction
    result = []
    prevTok = (None, None)
    for tok, nextTok in zip(tokens, tokens[1:]):
        result.append(tok)
        # only change from standard: ignore and/or/not
        if ((tok[0] == NAME and tok[1] in ("and", "or", "not")) or
            (nextTok[0] == NAME and nextTok[1] in ("and", "or", "not"))):
            continue
        elif (isinstance(tok, AppliedFunction) and
              isinstance(nextTok, AppliedFunction)):
            result.append((OP, '*'))
        elif (isinstance(tok, AppliedFunction) and
              nextTok[0] == OP and nextTok[1] == '('):
            # Applied function followed by an open parenthesis
            result.append((OP, '*'))
        elif (tok[0] == OP and tok[1] == ')' and
              isinstance(nextTok, AppliedFunction)):
            # Close parenthesis followed by an applied function
            result.append((OP, '*'))
        elif (tok[0] == OP and tok[1] == ')' and
              nextTok[0] == NAME):
            # Close parenthesis followed by an implicitly applied function
            result.append((OP, '*'))
        elif (tok[0] == nextTok[0] == OP
              and tok[1] == ')' and nextTok[1] == '('):
            # Close parenthesis followed by an open parenthesis
            result.append((OP, '*'))
        elif (isinstance(tok, AppliedFunction) and nextTok[0] == NAME and
              nextTok[1] not in ['and', 'or', 'not', 'in']):
            # Applied function followed by implicitly applied function
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              not (prevTok[0] == OP and prevTok[1] == '.') and
              nextTok[0] == OP and nextTok[1] == '('):
            # Constant followed by parenthesis
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict,
                                  include_symbol_callable=False) and
              tok[1] not in ['and', 'or', 'not', 'in'] and
              nextTok[0] == NAME and
              not _token_callable(nextTok, local_dict, global_dict, 
                                  include_symbol_callable=False) and
              nextTok[1] not in ['and', 'or', 'not', 'in']):
            # Constant followed by constant
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict, 
                                  include_symbol_callable=False) and
              tok[1] not in ['and', 'or', 'not', 'in'] and
              (isinstance(nextTok, AppliedFunction) or nextTok[0] == NAME)):
            # Constant followed by (implicitly applied) function
            result.append((OP, '*'))
        prevTok=tok
    if tokens:
        result.append(tokens[-1])
    return result


def split_symbols_custom(predicate):
    """Creates a transformation that splits symbol names.

    ``predicate`` should return True if the symbol name is to be split.

    Modified from sympy to check if Symbol is specified to be real,
    so that Symbol('xy',real=True) splits to 
    Symbol('x',real=True)Symbol('y',real=True)

    """

    def _split_symbols(tokens, local_dict, global_dict):
        result = []
        split = False
        split_previous=0
        splitting_real = False
        for (i,tok) in enumerate(tokens):
            if split_previous:
                # throw out closing parenthesis of Symbol that was split
                split_previous-=1
                continue
            split_previous=False
            if tok[0] == NAME and tok[1] == 'Symbol':
                split = True
                # check if real=True
                splitting_real=False
                try:
                    if tokens[i+3][0] == OP and tokens[i+3][1] == "," \
                       and tokens[i+4][0] == NAME and tokens[i+4][1] == "real" \
                       and tokens[i+5][0] == OP and tokens[i+5][1] == "=" \
                       and tokens[i+6][0] == NAME and tokens[i+6][1] == "True":
                        splitting_real=True
                except IndexError:
                    pass

            elif split and tok[0] == NAME:
                symbol = tok[1][1:-1]
                if predicate(symbol):
                    for char in symbol:
                        if char in local_dict or char in global_dict:
                            # Get rid of the call to Symbol
                            del result[-2:]
                            result.extend([(NAME, "%s" % char),
                                           (NAME, 'Symbol'), (OP, '(')])
                        else:
                            if splitting_real:
                                result.extend([(NAME, "'%s'" % char), (OP, ','),
                                               (NAME, 'real'), (OP, '='),
                                               (NAME, 'True'), (OP, ')'),
                                               (NAME, 'Symbol'), (OP, '(')])
                            else:
                                result.extend([(NAME, "'%s'" % char), (OP, ')'),
                                               (NAME, 'Symbol'), (OP, '(')])
                    # Delete the last two tokens: get rid of the extraneous
                    # Symbol( we just added
                    # Also, set split_previous so will skip
                    # the closing parenthesis (and possibly, real=True)
                    # of the original Symbol
                    del result[-2:]
                    split = False
                    if splitting_real:
                        split_previous=5
                    else:
                        split_previous=1
                    continue
                else:
                    split = False
            result.append(tok)

        return result
    return _split_symbols



#: Splits symbol names for implicit multiplication.
#:
#: Intended to let expressions like ``xyz`` be parsed as ``x*y*z``. Does not
#: split Greek character names, so ``theta`` will *not* become
#: ``t*h*e*t*a``. Generally this should be used with
#: ``implicit_multiplication``.
from sympy.parsing.sympy_parser import _token_splittable
split_symbols_trans = split_symbols_custom(_token_splittable)


def customized_sort_key(item, order=None):
    """
    Customized version of the sympy default_sort_key, modified so that
    all expressions that are real numbers use the sort key for plain numbers.
    In this way, numerical expressions are sorted in numerical order.
    """
    try:
        x=sympify(item)
    except:
        pass
    else:
        if x.is_comparable:
            # return sympy sort key for a number, where x is the coefficient
            return  ((1, 0, 'Number'), (0, ()), (), x)

    # otherwise return the default sympy sort key
    return default_sort_key(item, order)


# Tuple but with no parentheses when printing with latex
class TupleNoParen(Tuple):
    def _latex(self, prtr):
        return r", \quad ".join([ prtr._print(i) for i in self ])

    def __getitem__(self,key):
        result = super(TupleNoParen,self).__getitem__(key)
        # convert slice back to TupleNoParen
        if isinstance(key,slice):
            return self.__class__(*result)
        else:
            return result

class DerivativePrimeSimple(Derivative):
    def _latex(self, prtr):
        # if is a derivative of a single variable
        # of a single function of that variable
        # then latex using prime notation
        if len(self.variables)==1:
            variable = self.variables[0]
            expr = self.expr
            fn = expr.func

            if isinstance(fn,Symbol) or isinstance(fn,UndefinedFunction):
                if len(expr.args)==1 and expr.args[0]==variable:
                    return "%s'(%s)" % (fn, variable)

        return prtr._print_Derivative(self)
            

class DerivativePrimeNotation(Expr):
    def __new__(cls, fn, argument, dummy_variable='x'):
        if not (isinstance(fn,Symbol) or isinstance(fn,UndefinedFunction)):
            raise ValueError('Prime notation for derivative can only be use for undefined functions')
        
        if argument._diff_wrt:
            return DerivativePrimeSimple(fn(argument),argument)

        return super(DerivativePrimeNotation,cls)\
            .__new__(cls, fn,argument, dummy_variable)

    def __init__(self, fn, argument, dummy_variable='x'):
        self.fn=fn
        self.argument=argument
        self.dummy_variable = sympify(dummy_variable)

    def _latex(self, prtr):
        return r"%s'\left(%s\right)" % (self.fn, prtr._print(self.argument))

    def doit(self, **hints):
        from sympy import Subs
        xx=self.dummy_variable
        return Subs(Derivative(self.fn(xx),xx), xx, self.argument).doit(**hints)

    def _hashable_content(self):
        # don't include dummy_variable when determining equality
        return (self.fn, self.argument)
            
class DerivativeSimplifiedNotation(Derivative):
    def _latex(self, prtr):
        # if is a derivative with respect to a single variable
        # of a single function of that variable
        # then latex using simplified notation
        if len(self.variables)==1:
            variable = self.variables[0]
            expr = self.expr
            fn = expr.func

            from sympy.core.function import UndefinedFunction
            if isinstance(fn,Symbol) or isinstance(fn,UndefinedFunction):
                if len(expr.args)==1 and expr.args[0]==variable:
                    return "\\frac{d %s}{d %s}" % (fn, variable)

        return prtr._print_Derivative(self)
            
    def doit(self, **hints):
        # Special case of dx/dx is represented as Derivative(x(x),x).
        # Should simplify to 1 on doit
        if len(self.variables)==1:
            variable = self.variables[0]
            expr = self.expr
            fn = expr.func
            
            from sympy.core.function import UndefinedFunction
            if isinstance(fn,Symbol) or isinstance(fn,UndefinedFunction):
                if len(expr.args)==1 and expr.args[0]==variable:
                    if str(fn)==str(variable):
                        return 1

        return super(DerivativeSimplifiedNotation,self).doit(**hints)

class AddUnsortInitial(Expr):
    """
    returns an unevaluated AddUnsort with 0 terms included
    """
    def __new__(cls, *args, **options):
        # always set evaluate to false
        options['evaluate']=False
        original_args = sympify(args)
        new_args=[]
        zero_placeholder=Symbol('_0_')
        for w in args:
            if w==0:
                new_args.append(zero_placeholder)
            else:
                new_args.append(w)
        args= tuple(sympify(new_args))

        obj=AddUnsort(*args, **options)
        
        if obj.is_Add:
            obj.original_args=original_args
            obj._args=original_args
        return obj


def _get_coeff(a):
    # Get first argument from Mul.
    # Handle nested Muls and use original_args for MulUnsort.
    while a.is_Mul:
        if isinstance(a,MulUnsort):
            a=a.original_args[0]
        else:
            a=a.args[0]
    return a

def _coeff_isneg(a):
    # modified from sympy to handle nested Muls
    # and use original_args for MulUnsort
    a=_get_coeff(a)
    return a.is_Number and a.is_negative

def fraction_MulUnsort(expr, exact=False):
    # modified from sympy fraction to return MulUnsort
    # not put extra 1's in the denominator
    expr = sympify(expr)
    numer, denom = [], []

    from sympy.functions import exp

    for term in MulUnsort.make_args(expr):
        if term.is_commutative and (term.is_Pow or term.func is exp):
            b, ex = term.as_base_exp()
            if ex.is_negative:
                if ex is S.NegativeOne:
                    denom.append(b)
                else:
                    denom.append(Pow(b, -ex))
            elif ex.is_positive:
                numer.append(term)
            elif not exact and ex.is_Mul:
                n, d = term.as_numer_denom()
                numer.append(n)
                denom.append(d)
            else:
                numer.append(term)
        elif term.is_Rational:
            n, d = term.as_numer_denom()
            numer.append(n)
            if d !=1:
                denom.append(d)
        else:
            numer.append(term)

    return MulUnsortInitial(*numer), MulUnsortInitial(*denom)


class AddUnsort(Add):
    """
    An Add object that displays terms in original order entered.
    Even if not created with evaluate=False, will show original args.
    """

    def __init__(self, *args, **options):
        self.original_args = sympify(args)
        super(AddUnsort,self).__init__()

    def doit(self, **hints):
        return Add(*self.args)

    def __eq__(self, other):
        # For AddUnsort, original args must be the same
        if isinstance(other, AddUnsort):
            if self.original_args == other.original_args:
                return True
            else:
                return False

        # For Add, equal if the sorted/combined args are equal to original_args
        if isinstance(other,Add):
            if list(self.original_args) == other.as_ordered_terms():
                return True
            else:
                return False
        return super(AddUnsort, self).__eq__(other)

    def __neg__(self):
        # create a MulUnsort with an initial factor of -1 set to not
        # be displayed
        obj= MulUnsortInitial(S.NegativeOne, self)
        obj.display_initial_negative_one=False
        return obj

    def _latex(self, prtr):
        # identical to _print_Add from latex.py with self=prtr and expr=self
        # except get terqms from original_args
        # and use customized _coeff_isneg

        terms = list(self.original_args)

        tex = prtr._print(terms[0])

        for term in terms[1:]:
            if not _coeff_isneg(term):
                tex += " + " + prtr._print(term)
            else:
                tex += " - " + prtr._print(-term)

        return tex

    def _sympystr(self, prtr):
        # identical to _print_Add from str.py with self=prtr and expr=self
        # except set terms from original_args
        from sympy.printing.precedence import precedence
        terms = list(self.original_args)

        PREC = precedence(self)
        l = []
        for term in terms:
            t = prtr._print(term)
            if t.startswith('-'):
                sign = "-"
                t = t[1:]
            else:
                sign = "+"
            if precedence(term) < PREC:
                l.extend([sign, "(%s)" % t])
            else:
                l.extend([sign, t])
        sign = l.pop(0)
        if sign == '+':
            sign = ""
        return sign + ' '.join(l)


class MulUnsortInitial(Expr):
    """
    returns an unevaluated MulUnsort with 1 factors included
    """
    def __new__(cls, *args, **options):
        # always set evaluate to false
        options['evaluate']=False
        original_args = sympify(args)
        if len(original_args)==1:
            return original_args[0]

        new_args=[]
        one_placeholder=Symbol('_1_')
        for w in args:
            if w==1:
                new_args.append(one_placeholder)
            else:
                new_args.append(w)
        args= tuple(sympify(new_args))

        obj=MulUnsort(*args, **options)
        
        if obj.is_Mul:
            obj.original_args=original_args
            obj._args=original_args
        return obj


class MulUnsort(Mul):
    """
    A Mul object that displays factors in original order entered.
    Even if not created with evaluate=False, will show original args.
    """

    def __init__(self, *args, **options):
        self.original_args = sympify(args)
        self.display_initial_negative_one = True
        super(MulUnsort,self).__init__()

    def doit(self, **hints):
        return Mul(*self.args)

    def __eq__(self, other):
        # For MulUnsort, original args must be the same
        if isinstance(other, MulUnsort):
            if self.original_args == other.original_args:
                return True
            else:
                return False

        # For Mul, equal if the sorted/combined args are equal to original_args
        if isinstance(other,Mul):
            if list(self.original_args) == other.as_ordered_factors():
                return True
            else:
                return False
        return super(MulUnsort, self).__eq__(other)

    def __neg__(self):
        # keep track if an initial factor of -1 was originally added, 
        # and should be displayed
        # or was just added to switch the sign, and should not be displayed
        if not self.display_initial_negative_one and self.original_args[0]==-1:
            return MulUnsortInitial(*self.original_args[1:])
        arg0=_get_coeff(self)
        if arg0.is_Number and arg0.is_negative:
            return MulUnsortInitial(-self.original_args[0], 
                                    *self.original_args[1:])
        obj= MulUnsortInitial(S.NegativeOne, *self.original_args)
        obj.display_initial_negative_one=False
        return obj

    def _latex(self,prtr):
        """
        based on _print_Mul from latex.py with self=prtr and expr=self
        
        Differences
        - set args = original_args 
        - create MulUnsort when construction fractions
        - wrap negative number factors in parentheses
        - display initial factor of -1 if didn't come from negation
        - don't break apart large fractions
        """

        tex = ""

        # don't display the initial factor of negative one 
        # if just came from negation
        if not self.display_initial_negative_one and self.original_args[0]==-1:
            tex = "-"
            self = MulUnsortInitial(*self.original_args[1:])

            if not self.is_Mul:
                return tex + prtr._print(self)

        numer, denom = fraction_MulUnsort(self, exact=True)
        separator = prtr._settings['mul_symbol_latex']
        numbersep = prtr._settings['mul_symbol_latex_numbers']


        def _needs_mul_brackets(expr, first=False, last=False):
            """
            Returns True if the expression needs to be wrapped in brackets when
            printed as part of a Mul, False otherwise. This is True for Add,
            but also for some container objects that would not need brackets
            when appearing last in a Mul, e.g. an Integral. ``last=True``
            specifies that this expr is the last to appear in a Mul.
            ``first=True`` specifies that this expr is the first to appear in a Mul.
            """
            from sympy import Integral, Piecewise, Product, Sum

            if expr.is_Add:
                return True
            elif expr.is_Relational:
                return True
            elif expr.is_Mul:
                if not first and _coeff_isneg(expr):
                    return True
            elif expr.is_Number:
                if not first and expr < 0:
                    return True

            if (not last and
                any([expr.has(x) for x in (Integral, Piecewise, Product, Sum)])):
                return True

            return False



        def convert(self):
            if not self.is_Mul:
                return str(prtr._print(self))
            else:
                _tex = last_term_tex = ""

                args=self.original_args
                for i, term in enumerate(args):
                    term_tex = prtr._print(term)

                    if _needs_mul_brackets(term, first=(i == 0),
                                                last=(i == len(args) - 1)):
                        term_tex = r"\left(%s\right)" % term_tex

                    if re.search("[0-9][} ]*$", last_term_tex) and \
                            re.match("[{ ]*[-+0-9]", term_tex):
                        # between two numbers
                        _tex += numbersep
                    elif _tex:
                        _tex += separator

                    _tex += term_tex
                    last_term_tex = term_tex
                return _tex
        

        if denom is S.One:
            # use the original expression here, since fraction() may have
            # altered it when producing numer and denom
            tex += convert(self)
        else:
            snumer = convert(numer)
            sdenom = convert(denom)
            ldenom = len(sdenom.split())
            if prtr._settings['fold_short_frac'] \
                    and ldenom <= 2 and not "^" in sdenom:
                # handle short fractions
                if _needs_mul_brackets(numer, last=False):
                    tex += r"\left(%s\right) / %s" % (snumer, sdenom)
                else:
                    tex += r"%s / %s" % (snumer, sdenom)
            else:
                tex += r"\frac{%s}{%s}" % (snumer, sdenom)

        return tex

    def _sympystr(self, prtr):
        """
        identical to _print_Mul from str.py with self=prtr and expr=self except
        - set args = original_args 
        - create MulUnsort when have leading negative
        - display initial factor of -1 if didn't come from negation
        """

        if not isinstance(self,MulUnsort):
            return prtr._print_Mul(self)

        from sympy.printing.precedence import precedence

        prec = precedence(self)

        coeff = self.original_args[0]
        
        if not coeff.is_negative:
            sign = ""
        else:
            # don't display the initial factor of negative one 
            # if just came from negation
            if not self.display_initial_negative_one and coeff==-1:
                new_args=[]
            else:
                new_args=[-coeff]
            new_args.extend(self.original_args[1:])
            self = MulUnsortInitial(*new_args)
            sign = "-"
            if not self.is_Mul:
                return "-" + prtr._print(self)

        a = []  # items in the numerator
        b = []  # items that are in the denominator (if any)

        args = self.original_args

        # Gather args for numerator/denominator
        for item in args:
            if item.is_commutative and item.is_Pow and item.exp.is_Rational and item.exp.is_negative:
                if item.exp != -1:
                    b.append(Pow(item.base, -item.exp, evaluate=False))
                else:
                    b.append(Pow(item.base, -item.exp))
            elif item.is_Rational and item is not S.Infinity:
                #if item.p != 1:
                a.append(Rational(item.p))
                if item.q != 1:
                    b.append(Rational(item.q))
            else:
                a.append(item)

        a = a or [S.One]

        a_str = list(map(lambda x: prtr.parenthesize(x, prec), a))
        b_str = list(map(lambda x: prtr.parenthesize(x, prec), b))

        if len(b) == 0:
            return sign + '*'.join(a_str)
        elif len(b) == 1:
            return sign + '*'.join(a_str) + "/" + b_str[0]
        else:
            return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)

    @classmethod
    def make_args(cls, expr):
        if isinstance(expr, cls):
            return expr.original_args
        else:
            return (expr,)


class LatexPrinter(sympy_LatexPrinter):
    def _print_And(self, e):
        args = sorted(e.args, key=default_sort_key)
        return self._print_LogOp(args, r"~\text{and}~")

    def _print_Or(self, e):
        args = sorted(e.args, key=default_sort_key)
        return self._print_LogOp(args, r"~\text{or}~")


def latex(expr, **settings):
    return LatexPrinter(settings).doprint(expr)


class Interval(sympy_Interval):
    def contains(self, other, evaluate=True):
        if evaluate:
            return super(Interval,self).contains(other)
        else:
            from sympy import Contains
            return Contains(other, self, evaluate=False)

class FiniteSet(sympy_FiniteSet):
    def contains(self, other, evaluate=True):
        if evaluate:
            return super(FiniteSet,self).contains(other)
        else:
            from sympy import Contains
            return Contains(other, self, evaluate=False)
