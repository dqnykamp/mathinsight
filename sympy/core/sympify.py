"""sympify -- convert objects SymPy internal format"""

from inspect import getmro

from core import all_classes as sympy_classes
from sympy.core.compatibility import iterable


class SympifyError(ValueError):
    def __init__(self, expr, base_exc=None):
        self.expr = expr
        self.base_exc = base_exc

    def __str__(self):
        if self.base_exc is None:
            return "SympifyError: %r" % (self.expr,)

        return ("Sympify of expression '%s' failed, because of exception being "
            "raised:\n%s: %s" % (self.expr, self.base_exc.__class__.__name__,
            str(self.base_exc)))

converter = {}  # See sympify docstring.

class CantSympify(object):
    """
    Mix in this trait to a class to disallow sympification of its instances.

    Example
    =======

    >>> from sympy.core.sympify import sympify, CantSympify

    >>> class Something(dict):
    ...     pass
    ...
    >>> sympify(Something())
    {}

    >>> class Something(dict, CantSympify):
    ...     pass
    ...
    >>> sympify(Something())
    Traceback (most recent call last):
    ...
    SympifyError: SympifyError: {}

    """
    pass

def sympify(a, locals=None, convert_xor=True, strict=False, rational=False):
    """
    Converts an arbitrary expression to a type that can be used inside SymPy.

    For example, it will convert Python ints into instance of sympy.Rational,
    floats into instances of sympy.Float, etc. It is also able to coerce symbolic
    expressions which inherit from Basic. This can be useful in cooperation
    with SAGE.

    It currently accepts as arguments:
       - any object defined in sympy
       - standard numeric python types: int, long, float, Decimal
       - strings (like "0.09" or "2e-19")
       - booleans, including ``None`` (will leave them unchanged)
       - lists, sets or tuples containing any of the above

    If the argument is already a type that SymPy understands, it will do
    nothing but return that value. This can be used at the beginning of a
    function to ensure you are working with the correct type.

    >>> from sympy import sympify

    >>> sympify(2).is_integer
    True
    >>> sympify(2).is_real
    True

    >>> sympify(2.0).is_real
    True
    >>> sympify("2.0").is_real
    True
    >>> sympify("2e-45").is_real
    True

    If the expression could not be converted, a SympifyError is raised.

    >>> sympify("x***2")
    Traceback (most recent call last):
    ...
    SympifyError: SympifyError: "could not parse u'x***2'"

    Locals
    ------

    The sympification happens with access to everything that is loaded
    by ``from sympy import *``; anything used in a string that is not
    defined by that import will be converted to a symbol. In the following,
    the ``bitcout`` function is treated as a symbol and the ``O`` is
    interpreted as the Order object (used with series) and it raises
    an error when used improperly:

    >>> s = 'bitcount(42)'
    >>> sympify(s)
    bitcount(42)
    >>> sympify("O(x)")
    O(x)
    >>> sympify("O + 1")
    Traceback (most recent call last):
    ...
    TypeError: unbound method...

    In order to have ``bitcount`` be recognized it can be imported into a
    namespace dictionary and passed as locals:

    >>> ns = {}
    >>> exec 'from sympy.core.evalf import bitcount' in ns
    >>> sympify(s, locals=ns)
    6

    In order to have the ``O`` interpreted as a Symbol, identify it as such
    in the namespace dictionary. This can be done in a variety of ways; all
    three of the following are possibilities:

    >>> from sympy import Symbol
    >>> ns["O"] = Symbol("O")  # method 1
    >>> exec 'from sympy.abc import O' in ns  # method 2
    >>> ns.update(dict(O=Symbol("O")))  # method 3
    >>> sympify("O + 1", locals=ns)
    O + 1

    If you want *all* single-letter and Greek-letter variables to be symbols
    then you can use the clashing-symbols dictionaries that have been defined
    there as private variables: _clash1 (single-letter variables), _clash2
    (the multi-letter Greek names) or _clash (both single and multi-letter
    names that are defined in abc).

    >>> from sympy.abc import _clash1
    >>> _clash1
    {'C': C, 'E': E, 'I': I, 'N': N, 'O': O, 'Q': Q, 'S': S}
    >>> sympify('C & Q', _clash1)
    And(C, Q)

    Strict
    ------

    If the option ``strict`` is set to ``True``, only the types for which an
    explicit conversion has been defined are converted. In the other
    cases, a SympifyError is raised.

    >>> sympify(True)
    True
    >>> sympify(True, strict=True)
    Traceback (most recent call last):
    ...
    SympifyError: SympifyError: True

    Extending
    ---------

    To extend ``sympify`` to convert custom objects (not derived from ``Basic``),
    just define a ``_sympy_`` method to your class. You can do that even to
    classes that you do not own by subclassing or adding the method at runtime.

    >>> from sympy import Matrix
    >>> class MyList1(object):
    ...     def __iter__(self):
    ...         yield 1
    ...         yield 2
    ...         raise StopIteration
    ...     def __getitem__(self, i): return list(self)[i]
    ...     def _sympy_(self): return Matrix(self)
    >>> sympify(MyList1())
    [1]
    [2]

    If you do not have control over the class definition you could also use the
    ``converter`` global dictionary. The key is the class and the value is a
    function that takes a single argument and returns the desired SymPy
    object, e.g. ``converter[MyList] = lambda x: Matrix(x)``.

    >>> class MyList2(object):   # XXX Do not do this if you control the class!
    ...     def __iter__(self):  #     Use _sympy_!
    ...         yield 1
    ...         yield 2
    ...         raise StopIteration
    ...     def __getitem__(self, i): return list(self)[i]
    >>> from sympy.core.sympify import converter
    >>> converter[MyList2] = lambda x: Matrix(x)
    >>> sympify(MyList2())
    [1]
    [2]

    Notes
    =====

    Sometimes autosimplification during sympification results in expressions
    that are very different in structure than what was entered. Until such
    autosimplification is no longer done, the ``kernS`` function might be of
    some use. In the example below you can see how an expression reduces to
    -1 by autosimplification, but does not do so when ``kernS`` is used.

    >>> from sympy.core.sympify import kernS
    >>> from sympy.abc import x
    >>> -1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))
    -1
    >>> sympify('-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))')
    -1
    >>> kernS('-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))')
    -1 + 2*(-x + 1/x)/(x*(x - 1/x)**2) + 2/(x*(x - 1/x))

    In the last expression, the result is not exactly the same as the
    entered string, but it is a lot closer.

    """
    try:
        cls = a.__class__
    except AttributeError:  # a is probably an old-style class object
        cls = type(a)
    if cls in sympy_classes:
        return a
    if cls in (bool, type(None)):
        if strict:
            raise SympifyError(a)
        else:
            return a

    try:
        return converter[cls](a)
    except KeyError:
        for superclass in getmro(cls):
            try:
                return converter[superclass](a)
            except KeyError:
                continue

    if isinstance(a, CantSympify):
        raise SympifyError(a)

    try:
        return a._sympy_()
    except AttributeError:
        pass

    if not isinstance(a, basestring):
        for coerce in (float, int):
            try:
                return sympify(coerce(a))
            except (TypeError, ValueError, AttributeError, SympifyError):
                continue

    if strict:
        raise SympifyError(a)

    if iterable(a):
        try:
            return type(a)([sympify(x, locals=locals, convert_xor=convert_xor,
                rational=rational) for x in a])
        except TypeError:
            # Not all iterables are rebuildable with their type.
            pass
    if isinstance(a, dict):
        try:
            return type(a)([sympify(x, locals=locals, convert_xor=convert_xor,
                rational=rational) for x in a.iteritems()])
        except TypeError:
            # Not all iterables are rebuildable with their type.
            pass

    # At this point we were given an arbitrary expression
    # which does not inherit from Basic and doesn't implement
    # _sympy_ (which is a canonical and robust way to convert
    # anything to SymPy expression).
    #
    # As a last chance, we try to take "a"'s normal form via unicode()
    # and try to parse it. If it fails, then we have no luck and
    # return an exception
    try:
        a = unicode(a)
    except Exception, exc:
        raise SympifyError(a, exc)

    from sympy.parsing.sympy_parser import (parse_expr, TokenError,
                                            standard_transformations)
    from sympy.parsing.sympy_parser import convert_xor as t_convert_xor
    from sympy.parsing.sympy_parser import rationalize as t_rationalize

    transformations = standard_transformations

    if rational:
        transformations += (t_rationalize,)
    if convert_xor:
        transformations += (t_convert_xor,)

    try:
        a = a.replace('\n', '')
        expr = parse_expr(a, local_dict=locals, transformations=transformations)
    except (TokenError, SyntaxError), exc:
        raise SympifyError('could not parse %r' % a, exc)

    return expr


def _sympify(a):
    """Short version of sympify for internal usage for __add__ and __eq__
       methods where it is ok to allow some things (like Python integers
       and floats) in the expression. This excludes things (like strings)
       that are unwise to allow into such an expression.

       >>> from sympy import Integer
       >>> Integer(1) == 1
       True

       >>> Integer(1) == '1'
       False

       >>> from sympy import Symbol
       >>> from sympy.abc import x
       >>> x + 1
       x + 1

       >>> x + '1'
       Traceback (most recent call last):
           ...
       TypeError: unsupported operand type(s) for +: 'Symbol' and 'str'

       see: sympify
    """
    return sympify(a, strict=True)


def kernS(s):
    """Use a hack to try keep autosimplification from joining Integer or
    minus sign into an Add of a Mul; this modification doesn't
    prevent the 2-arg Mul from becoming an Add, however.

    Examples
    ========

    >>> from sympy.core.sympify import kernS
    >>> from sympy.abc import x, y, z

    The 2-arg Mul allows a leading Integer to be distributed and kernS does
    not prevent that:

    >>> 2*(x + y) == kernS('2*(x + y)') == 2*x + 2*y
    True

    But a Mul with more than 2 args need not have the leading Integer
    distributed and the kernS version of S will keep that distribution
    from occuring:

    >>> 2*(x  + y)*z  # the first two arguments undergo the distribution
    z*(2*x + 2*y)
    >>> 2*z*(x + y)  # in this form, the Add is not multiplied by an Integer
    2*z*(x + y)
    >>> kernS('2*(x + y)*z')  # kernS will stop the distribution in this case
    2*z*(x + y)

    >>> kernS('E**-(x)')
    exp(-x)

    If use of the hack fails, the un-hacked string will be passed to sympify...
    and you get what you get.

    XXX This hack should not be necessary once issue 1497 has been resolved.
    """
    import re
    from sympy.core.symbol import Symbol

    hit = False
    if '(' in s:
        if s.count('(') != s.count(")"):
            raise SympifyError('unmatch laft parentheses')

        kern = '_kern'
        while kern in s:
            kern += "_"
        lparen = 'kern_2'
        while lparen in s:
            lparen += "_"
        olds = s
        s = re.sub(r'(\d *\*|-) *\(', r'\1(%s*%s' % (kern, lparen), s)

        hit = kern in s
        if hit:
            # close parentheses after kerns; if this fails there is
            # either an error in this parsing or in the original string
            i = 0
            close = []
            while True:
                i = s.find(kern,  i)
                if i == -1:
                    break
                count = 1  # for the one before the kern
                for j in range(i + 1, len(s)):
                    c = s[j]
                    if c == "(":
                        count += 1
                    elif c == ")":
                        count -= 1
                    else:
                        continue
                    if count == 0:
                        close.append(j)
                        i += len(kern)  # continue from the last kern
                        break
            for i in reversed(close):
                s = ')'.join([s[:i], s[i:]])
            s = s.replace(lparen, "(")

    for i in range(2):
        try:
            expr = sympify(s)
            break
        except:  # the kern might cause unknown errors, so use bare except
            if hit:
                s = olds  # maybe it didn't like the kern; use un-kerned s
                hit = False
                continue
            expr = sympify(s)  # let original error raise

    if not hit:
        return expr

    rep = {Symbol(kern): 1}
    if hasattr(expr, 'xreplace'):
        return expr.xreplace(rep)
    elif isinstance(expr, (list, tuple, set)):
        return type(expr)([_clear(e) for e in expr])
    if hasattr(expr, 'subs'):
        return expr.subs(rep)
    # hope that kern is not there anymore
    return expr
