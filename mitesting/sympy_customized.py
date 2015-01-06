from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from sympy import sympify, default_sort_key
from sympy.parsing.sympy_tokenize import NAME, OP
from sympy import Tuple, Float, Symbol, Rational, Integer, factorial
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
    Customized version of sympy parse_expr with the following modifications.
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
    5.  Remove leading 0s from numbers so not interpretted as octal numbers.
    6.  Convert leading 0x to 0*x so not interpreeted as hexadecimal numbers.
    7.  Call sympify after parse_expr so that tuples will be 
        converted to Sympy Tuples.  (A bug in parse_expr that this
        doesn't happen automatically?)
    """
    
    from sympy.parsing.sympy_parser import \
        (auto_number, factorial_notation, convert_xor)
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
        kword_found=False
        if kword in new_global_dict:
            new_global_dict['_'+kword+'_'] = new_global_dict[kword]
            del new_global_dict[kword]
            kword_found=True
        if local_dict and kword in local_dict:
            local_dict_old=local_dict
            local_dict = {}
            local_dict.update(local_dict_old)
            local_dict['_'+kword+'_'] = local_dict[kword]
            del local_dict[kword]
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

    # replace = with __Eq__(lhs,rhs) 
    # and != with __Ne__(lhs,rhs)
    from mitesting.utils import replace_equals
    s=replace_equals(s)

    from sympy import Eq, Ne
    new_global_dict['__Eq__'] = Eq
    new_global_dict['__Ne__'] = Ne
    
    # change !== to !=
    s = re.sub('!==','!=', s)

    # change === to = (so can assign keywords in functions like Interval)
    s = re.sub('===','=', s)
    
    # call sympify after parse_expr to convert tuples to Tuples
    expr = sympify(sympy_parse_expr(
            s, global_dict=new_global_dict, local_dict=local_dict, 
            transformations=transformations, evaluate=evaluate))

    # if expr is a Tuple, but s had implicit parentheses, 
    # then return TupleNoParen
    if isinstance(expr,Tuple):
        ss=s.strip()
        # implicit parens if doesn't start and end with parentheses
        if not (ss.startswith("(") and ss.endswith(")")):
            return TupleNoParen(*expr)

        # implicit parens if initial opening paren doesn't match final closing paren
        parenCtr=0
        for (i,c) in enumerate(ss):
            if c == "(":
                parenCtr +=1
            elif c == ")":
                parenCtr -=1
                if parenCtr == 0 and i != len(ss)-1:
                    return TupleNoParen(*expr)

    return expr



def parse_and_process(s, global_dict=None, local_dict=None,
                      split_symbols=False, evaluate_level=None):
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

    expression = parse_expr(s, global_dict=global_dict,
                            local_dict=local_dict,
                            split_symbols=split_symbols,
                            evaluate=evaluate)

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

            if (name in ['True', 'False', 'and', 'or', 'not']
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


class SymbolCallable(Symbol):
    pass

def _token_callable(token, local_dict, global_dict, nextToken=None):
    """
    Predicate for whether a token name represents a callable function.

    Essentially wraps ``callable``, but looks up the token name in the
    locals and globals.
    """
    func = local_dict.get(token[1])
    if not func:
        func = global_dict.get(token[1])
    return callable(func) and (not isinstance(func, Symbol)
                               or isinstance(func, SymbolCallable))


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
            if not func:
                func = global_dict.get(tok[1])
            if func:
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
    adjacent to and/or/not.

    Cases:

    - Two AppliedFunctions next to each other ("sin(x)cos(x)")

    - AppliedFunction next to an open parenthesis ("sin x (cos x + 1)")

    - A close parenthesis next to an AppliedFunction ("(x+2)sin x")\

    - A close parenthesis next to an open parenthesis ("(x+2)(x+3)")

    - AppliedFunction next to an implicitly applied function ("sin(x)cos x")

    """
    from sympy.parsing.sympy_parser import AppliedFunction
    result = []
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
        elif (isinstance(tok, AppliedFunction) and nextTok[0] == NAME):
            # Applied function followed by implicitly applied function
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              nextTok[0] == OP and nextTok[1] == '('):
            # Constant followed by parenthesis
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              nextTok[0] == NAME and
              not _token_callable(nextTok, local_dict, global_dict)):
            # Constant followed by constant
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              (isinstance(nextTok, AppliedFunction) or nextTok[0] == NAME)):
            # Constant followed by (implicitly applied) function
            result.append((OP, '*'))
    if tokens:
        result.append(tokens[-1])
    return result


def split_symbols_custom(predicate):
    """Creates a transformation that splits symbol names.

    ``predicate`` should return True if the symbol name is to be split.

    For instance, to retain the default behavior but avoid splitting certain
    symbol names, a predicate like this would work:


    >>> from sympy.parsing.sympy_parser import (parse_expr, _token_splittable,
    ... standard_transformations, implicit_multiplication,
    ... split_symbols_custom)
    >>> def can_split(symbol):
    ...     if symbol not in ('list', 'of', 'unsplittable', 'names'):
    ...             return _token_splittable(symbol)
    ...     return False
    ...
    >>> transformation = split_symbols_custom(can_split)
    >>> parse_expr('unsplittable', transformations=standard_transformations +
    ... (transformation, implicit_multiplication))
    unsplittable
    """

    def _split_symbols(tokens, local_dict, global_dict):
        result = []
        split = False
        split_previous=False
        for tok in tokens:
            if split_previous:
                # throw out closing parenthesis of Symbol that was split
                split_previous=False
                continue
            split_previous=False
            if tok[0] == NAME and tok[1] == 'Symbol':
                split = True
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
                            result.extend([(NAME, "'%s'" % char), (OP, ')'),
                                           (NAME, 'Symbol'), (OP, '(')])
                    # Delete the last two tokens: get rid of the extraneous
                    # Symbol( we just added
                    # Also, set split_previous=True so will skip
                    # the closing parenthesis of the original Symbol
                    del result[-2:]
                    split = False
                    split_previous = True
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

