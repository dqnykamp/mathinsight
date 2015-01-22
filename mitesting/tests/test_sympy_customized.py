from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import SimpleTestCase
from mitesting.sympy_customized import bottom_up, parse_expr, \
    parse_and_process, EVALUATE_NONE, EVALUATE_PARTIAL, EVALUATE_FULL
from mitesting.customized_commands import normalize_floats
from sympy import Symbol, diff, Tuple, sympify, Integer

class BottomUpTests(SimpleTestCase):
    
    def test_rounds_numbers_to_integers(self):
        expr = bottom_up(sympify("2.0*x"), lambda w: w if not w.is_Number else Integer(w.round()), atoms=True)
        self.assertEqual(str(expr), "2*x")

    def test_evalf_accepted_each_atom(self):
        expr = bottom_up(sympify("sin(x/3)"), lambda w: w if not w.is_Number else w.evalf(4), atoms=True)
        self.assertEqual(str(expr), "sin(0.3333*x)")


class ParseExprTests(SimpleTestCase):


    def test_basics_with_empty_local_dict(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("5x", local_dict={}), 5*x)
        local_dict = {}
        self.assertEqual(parse_expr("3y^2", local_dict=local_dict),
                          3*y**2)
        # verify local_dict is still empty
        self.assertEqual(local_dict, {})
        self.assertEqual(parse_expr("log(x)", local_dict={}),
                          Symbol('log')*x)

    def test_basics_with_no_local_dict(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("5x"), 5*x)
        self.assertEqual(parse_expr("3x^2"), 3*x**2)
        self.assertEqual(parse_expr("log(x)"), Symbol('log')*x)
        
    def test_implicit_convert_xor(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("3x^2/5", local_dict={}), 
                          sympify("3*x**2/5"))
        self.assertEqual(
            normalize_floats(parse_expr("3x^2/5.", local_dict={})), 
            normalize_floats(0.6*x**2))

    def test_implicit_multiplication(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("5x"), 5*x)
        self.assertEqual(parse_expr("5 x"), 5*x)
        self.assertEqual(parse_expr("5*x"), 5*x)
        self.assertEqual(parse_expr("5 x y"), 5*x*y)

    def test_split_symbols(self):
        x = Symbol('x')
        y = Symbol('y')
        xy = Symbol('xy')
        self.assertEqual(parse_expr("5xy"), 5*xy)
        self.assertEqual(parse_expr("5xy", split_symbols=False), 5*xy)
        self.assertEqual(parse_expr("5xy", split_symbols=True), 5*x*y)


    def test_rationals_floats(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("3x^2/5"), sympify("3*x**2/5"))
        self.assertEqual(
            normalize_floats(parse_expr("3x^2/5.")), 
            normalize_floats(0.6*x**2))

    def test_e_with_split_symbols(self):
        from sympy import E, exp
        x = Symbol('x')
        self.assertEqual(parse_expr("3*x*e^x", local_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3x*e^x", local_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3xe^x", split_symbols=True,
                                     local_dict={'e': E}),
                          3*x*exp(x))
        
    def test_with_tuples(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("(x,y)"), Tuple(x,y))


    def test_lambda_symbol(self):
        lambda_symbol = Symbol('lambda')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("lambda"), lambda_symbol)
        self.assertEqual(parse_expr("x-lambda+y"), -lambda_symbol+x+y)
        self.assertEqual(parse_expr("lambda(x)(y)"), lambda_symbol*x*y)

    def test_lambda_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        lambda_symbol = Symbol('lambda')
        sub_dict = {'lambda': 2*x*y}
        self.assertEqual(parse_expr("lambda^2+x+y"), lambda_symbol**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("lambda^2+x+y", local_dict=sub_dict,
                                    global_dict=sub_dict), 4*x**2*y**2+x+y)

    def test_as_symbol(self):
        as_symbol = Symbol('as')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("as"), as_symbol)
        self.assertEqual(parse_expr("x-as+y"), -as_symbol+x+y)
        self.assertEqual(parse_expr("as(x)(y)"), as_symbol*x*y)

    def test_as_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        as_symbol = Symbol('as')
        sub_dict = {'as': 2*x*y}
        self.assertEqual(parse_expr("as^2+x+y"), as_symbol**2+x+y)
        self.assertEqual(parse_expr("as^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("as^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)

    def test_if_symbol(self):
        if_symbol = Symbol('if')
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("if"), if_symbol)
        self.assertEqual(parse_expr("x-if+y"), -if_symbol+x+y)
        self.assertEqual(parse_expr("if(x)(y)"), if_symbol*x*y)

    def test_if_symbol_substitutions(self):
        x = Symbol('x')
        y = Symbol('y')
        if_symbol = Symbol('if')
        sub_dict = {'if': 2*x*y}
        self.assertEqual(parse_expr("if^2+x+y"), if_symbol**2+x+y)
        self.assertEqual(parse_expr("if^2+x+y", global_dict=sub_dict),
                         4*x**2*y**2+x+y)
        self.assertEqual(parse_expr("if^2+x+y", local_dict=sub_dict),
                         4*x**2*y**2+x+y)

    def test_if_as_iif(self):
        from mitesting.customized_commands import iif
        x = Symbol('x')
        sub_dict = {'if': iif}
        self.assertEqual(parse_expr('if(4>3,x,y)', local_dict=sub_dict),x)
        self.assertEqual(parse_expr('if(-4>3,y,x^2)', 
                                    local_dict=sub_dict),x**2)
        f = parse_expr('if(x=1,2,if(x>1,3,0))',local_dict=sub_dict)
        self.assertEqual(f.subs(x,1),2)
        self.assertEqual(f.subs(x,-1),0)
        self.assertEqual(f.subs(x,2),3)
        

    def test_no_evaluate(self):
        expr_no_evaluate = parse_expr("x - lambda + x + 2*lambda",
                                      evaluate=False)
        expr = parse_expr("x - lambda + x + 2*lambda")
        expr_with_evaluate = parse_expr("x + x - lambda + 2*lambda",
                                        evaluate=True)
        self.assertNotEqual(expr_no_evaluate, expr)
        self.assertEqual(expr, expr_with_evaluate)
        self.assertEqual(repr(expr_no_evaluate),'x - lambda + x + 2*lambda')

        expr1=parse_expr("2+y*x", evaluate=False)
        expr2=parse_expr("2+y*x")
        expr3=parse_expr("x*y+2", evaluate=False)
        expr4=parse_expr("foo", local_dict={'foo': expr1})
        self.assertNotEqual(expr1,expr2)
        self.assertEqual(expr2,expr3)
        self.assertNotEqual(expr1,expr3)
        self.assertEqual(expr2,expr4)
        self.assertNotEqual(expr1,expr4)
        self.assertEqual(repr(expr1), '2 + y*x')
        self.assertEqual(repr(expr4), 'y*x + 2')

        

    def test_factorial(self):
        from sympy import factorial
        expr = parse_expr("x!")
        self.assertEqual(expr, factorial(Symbol('x')))
        expr = parse_expr("5!")
        self.assertEqual(expr, 120)

    def test_boolean(self):
        self.assertEqual(parse_expr("True and True"), True)
        self.assertEqual(parse_expr("True and not True"), False)
        self.assertEqual(parse_expr("False or not True"), False)
        self.assertEqual(parse_expr("not False or not True"), True)

        local_dict = {'a': sympify(1), 'b': sympify(2), 'c': sympify(3),
                       'd': sympify(4)}
        expr = parse_expr("a and b and c and d", local_dict=local_dict)
        self.assertEqual(expr, True)
        local_dict['b'] = sympify(0)
        expr = parse_expr("a and b and c and d", local_dict=local_dict)
        self.assertEqual(expr, False)


    def test_parse_and_process(self):
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("2x")
        self.assertEqual(2*x, expr)
        expr = parse_and_process("xy", split_symbols=True)
        self.assertEqual(expr, x*y)
        expr = parse_and_process("var1*var2", 
                                 local_dict = {'var1':x, 'var2': y})
        self.assertEqual(expr, x*y)

    def test_parse_and_process_evaluate_level(self):
        from sympy import Derivative
        local_dict = {'Derivative': Derivative}
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("x+2+y*x+x*y", 
                                 evaluate_level=EVALUATE_NONE)
        self.assertNotEqual(expr, 2+x+x)
        self.assertEqual(repr(expr), 'x + 2 + y*x + x*y')
        
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict,
                                 evaluate_level = EVALUATE_PARTIAL)
        self.assertEqual(Derivative(x**2,x), expr)
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict,
                                 evaluate_level = EVALUATE_FULL)
        self.assertEqual(2*x, expr)
        expr = parse_and_process("Derivative(x^2,x)", local_dict= local_dict)
        self.assertEqual(2*x, expr)

    def test_prevent_octal(self):
        expr = parse_expr("0123")
        self.assertEqual(expr, 123)

        expr = parse_expr("0193")
        self.assertEqual(expr, 193)
 
        expr = parse_expr("0.123")
        self.assertEqual(expr, 0.123)
        
        expr = parse_expr("0.000791")
        self.assertEqual(expr, 0.000791)
        
        expr = parse_expr("4.04")
        self.assertEqual(expr, 4.04)

        expr = parse_expr("1230")
        self.assertEqual(expr, 1230)

        expr = parse_expr("0009505")
        self.assertEqual(expr, 9505)
        
        expr = parse_expr("89-088")
        self.assertEqual(expr,1)

        expr = parse_expr("72x/072 - x + 081")
        self.assertEqual(expr, 81)

    def test_prevent_hexadecimal(self):
        from sympy import Symbol
        expr = parse_expr("0x99")
        self.assertEqual(expr, 0)
        
        expr = parse_expr("10x99")
        self.assertEqual(expr, 10*Symbol("x99"))
        

    def test_split_with_function(self):
        from sympy import Symbol, Function
        x=Symbol('x')
        a=Symbol('a')
        f=Function(str('f'))
        fsym=Symbol('f')
        
        expr = parse_expr('af(x)', split_symbols=True)
        self.assertEqual(expr, a*fsym*x)

        expr = parse_expr('af(x)', split_symbols=True, 
                          local_dict={'f': f})
        self.assertEqual(expr, a*f(x))


    def test_callable_symbol(self):
        from sympy import Symbol
        from mitesting.sympy_customized import SymbolCallable
        
        x=Symbol('x')
        a=Symbol('a')
        f=SymbolCallable(str('f'))
        fsym=Symbol(str('f'))
        
        expr = parse_expr('af(x)', split_symbols=True)
        self.assertEqual(expr, a*fsym*x)

        expr = parse_expr('af(x)', split_symbols=True, 
                          local_dict={'f': f})
        self.assertEqual(expr, a*f(x))
        self.assertEqual(expr, a*fsym(x))
        

    def test_relational(self):
        from sympy import Symbol, Eq, Ne, Lt, Ge, Or, And
        
        x=Symbol('x')
        y=Symbol('y')
        
        expr = parse_expr("x=y")
        self.assertEqual(expr, Eq(x,y))

        expr = parse_expr("x==y")
        self.assertEqual(expr, False)

        expr = parse_expr("x != y")
        self.assertEqual(expr, Ne(x,y))
 
        expr = parse_expr("x !== y")
        self.assertEqual(expr, True)
       
        expr = parse_expr("x < y")
        self.assertEqual(expr, Lt(x,y))

        expr = parse_expr("x >= y")
        self.assertEqual(expr, Ge(x,y))

        expr = parse_expr("x=y | x^2 != y")
        self.assertEqual(expr,Or(Eq(x,y),Ne(x**2,y)))
        
        expr = parse_expr("(x=1)=(y=2)")
        self.assertEqual(expr,Eq(Eq(x,1),Eq(y,2)))

        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        z=Symbol('z')
        expr = parse_expr("x-1=y+c and (y/a=x(z) or a^2 != (b+2)(c-1)/2)")
        self.assertEqual(expr, And(Eq(x-1,y+c), Or(Eq(y/a,x*z), Ne(a**2,(b+2)*(c-1)/2))))

    def test_tuple_no_parens(self):
        from mitesting.sympy_customized import TupleNoParen

        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')

        expr = parse_expr("(a,b,c)")
        self.assertEqual(expr, Tuple(a,b,c))
        self.assertNotEqual(expr, TupleNoParen(a,b,c))

        expr = parse_expr("a,b,c")
        self.assertEqual(expr, TupleNoParen(a,b,c))
        self.assertNotEqual(expr, Tuple(a,b,c))

        local_dict = {'t1': Tuple(a,b,c), 't2': TupleNoParen(a,b,c),
                      't3': (a,b,c)}

        expr=parse_expr("t1", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a,b,c))

        expr=parse_expr("t2", local_dict=local_dict)
        self.assertEqual(expr, TupleNoParen(a,b,c))

        expr=parse_expr("t3", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a,b,c))

        def f(x,y):
            return Tuple(x+y,x-y)
        local_dict = {'f': f}
        expr=parse_expr("f(a,b)", local_dict=local_dict)
        self.assertEqual(expr, Tuple(a+b,a-b))

        def f(x,y):
            return TupleNoParen(x+y,x-y)
        local_dict = {'f': f}
        expr=parse_expr("f(a,b)", local_dict=local_dict)
        self.assertEqual(expr, TupleNoParen(a+b,a-b))


    def test_derivative_prime_notation(self):
        from sympy import Symbol, Function, Derivative, latex
        from mitesting.sympy_customized import SymbolCallable, \
            DerivativePrimeNotation, DerivativePrimeSimple
        
        f=Function(str('f'))
        g=SymbolCallable(str('g'))
        x=Symbol('x')
        y=Symbol('y')
        
        fn=Function(str('fn'))
        
        local_dict={'f': f, 'g': g, 'fn': fn}
        
        expr=parse_expr("f'(x)+g'(y)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(f(x),x)
                         +DerivativePrimeSimple(g(y),y))
        self.assertEqual(latex(expr), "f'(x) + g'(y)")

        expr=parse_expr("yf'(x)", local_dict=local_dict, split_symbols=True)
        self.assertEqual(expr, y*DerivativePrimeSimple(f(x),x))

        expr=parse_expr("2f'(x)", local_dict=local_dict)
        self.assertEqual(expr, 2*DerivativePrimeSimple(f(x),x))

        expr=parse_expr("fn'(x)", local_dict=local_dict)
        self.assertEqual(expr, DerivativePrimeSimple(fn(x),x))

        expr=parse_expr("2f'(x*y)", local_dict=local_dict)
        self.assertEqual(expr, 2*DerivativePrimeNotation(f,x*y))
        from sympy import Subs
        self.assertEqual(expr.doit(), 2*Subs(Derivative(f(x),x),x,x*y))
        
        expr2=parse_expr("2f'(x*y, dummy_variable==='t')", local_dict=local_dict)
        self.assertEqual(expr,expr2)
        self.assertEqual(expr.doit(),expr2.doit())
        
        expr3=parse_expr("2f'(x*y, dummy_variable==='s')", local_dict=local_dict)
        self.assertEqual(expr3,expr2)
        self.assertEqual(expr3.doit(),expr2.doit())
        


    def test_derivative_simplified_notation(self):
        from sympy import Symbol, Function, Derivative, latex
        from mitesting.sympy_customized import SymbolCallable, \
            DerivativeSimplifiedNotation
        
        f=Function(str('f'))
        g=SymbolCallable(str('g'))
        x=Symbol('x')
        y=Symbol('y')
        fn=Function(str('fn'))
        xx=Symbol('xx')
        local_dict={'f': f, 'g': g, 'fn': fn, 'xx': xx}
        
        expr=parse_expr("df/dx+dg/dy", local_dict=local_dict)
        self.assertEqual(expr, DerivativeSimplifiedNotation(f(x),x)
                         +DerivativeSimplifiedNotation(g(y),y))
        self.assertEqual(latex(expr), "\\frac{d f}{d x} + \\frac{d g}{d y}")

        expr=parse_expr("ydf/dxy", local_dict=local_dict, split_symbols=True)
        self.assertEqual(expr, y**2*DerivativeSimplifiedNotation(f(x),x))
        
        expr=parse_expr("ydf/dxy", local_dict=local_dict)
        self.assertEqual(expr, Symbol('ydf')/Symbol('dxy'))

        expr=parse_expr("3dfn/dxx", local_dict=local_dict)
        self.assertEqual(expr, 3*DerivativeSimplifiedNotation(fn(xx),xx))

