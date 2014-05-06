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


    def test_basics_with_empty_global_dict(self):
        x = Symbol('x')
        y = Symbol('y')
        self.assertEqual(parse_expr("5x", global_dict={}), 5*x)
        global_dict = {}
        self.assertEqual(parse_expr("3y^2", global_dict=global_dict),
                          3*y**2)
        # verify global_dict is still empty
        self.assertEqual(global_dict, {})
        self.assertEqual(parse_expr("log(x)", global_dict={}),
                          Symbol('log')*x)

    def test_basics_with_no_global_dict(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("5x"), 5*x)
        self.assertEqual(parse_expr("3x^2"), 3*x**2)
        self.assertEqual(parse_expr("log(x)"), Symbol('log')*x)
        
    def test_implicit_convert_xor(self):
        x = Symbol('x')
        self.assertEqual(parse_expr("3x^2/5", global_dict={}), 
                          sympify("3*x**2/5"))
        self.assertEqual(
            normalize_floats(parse_expr("3x^2/5.", global_dict={})), 
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
        self.assertEqual(parse_expr("3*x*e^x", global_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3x*e^x", global_dict={'e': E}),
                          3*x*exp(x))
        self.assertEqual(parse_expr("3xe^x", split_symbols=True,
                                     global_dict={'e': E}),
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
        self.assertEqual(parse_expr('if(4>3,x,y)', global_dict=sub_dict),x)
        self.assertEqual(parse_expr('if(-4>3,y,x^2)', 
                                    global_dict=sub_dict),x**2)

    def test_no_evaluate(self):
        expr_no_evaluate = parse_expr("x + x - lambda + 2*lambda",
                                      evaluate=False)
        expr = parse_expr("x + x - lambda + 2*lambda")
        expr_with_evaluate = parse_expr("x + x - lambda + 2*lambda",
                                        evaluate=True)
        self.assertNotEqual(expr_no_evaluate, expr)
        self.assertEqual(expr, expr_with_evaluate)
        self.assertEqual(repr(expr_no_evaluate),'-lambda + 2*lambda + x + x')

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

        global_dict = {'a': sympify(1), 'b': sympify(2), 'c': sympify(3),
                       'd': sympify(4)}
        expr = parse_expr("a and b and c and d", global_dict=global_dict)
        self.assertEqual(expr, 4)
        global_dict['b'] = sympify(0)
        expr = parse_expr("a and b and c and d", global_dict=global_dict)
        self.assertEqual(expr, 0)
        expr = parse_expr("a and not b and c and d", global_dict=global_dict)
        self.assertEqual(expr, 4)
        expr = parse_expr("a b and c d", global_dict=global_dict)
        self.assertEqual(expr, 0)
        expr = parse_expr("a b or c d", global_dict=global_dict)
        self.assertEqual(expr, 12)
        expr = parse_expr("ab or cd", global_dict=global_dict, 
                          split_symbols=True)
        self.assertEqual(expr, 12)

    def test_parse_and_process(self):
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("2x")
        self.assertEqual(2*x, expr)
        expr = parse_and_process("xy", split_symbols=True)
        self.assertEqual(expr, x*y)
        expr = parse_and_process("var1*var2", 
                                 global_dict = {'var1':x, 'var2': y})
        self.assertEqual(expr, x*y)

    def test_parse_and_process_evaluate_level(self):
        from sympy import Derivative
        global_dict = {'Derivative': Derivative}
        x=Symbol('x')
        y=Symbol('y')
        expr = parse_and_process("2+x+x", 
                                 evaluate_level=EVALUATE_NONE)
        self.assertNotEqual(expr, 2+x+x)
        self.assertEqual(repr(expr), 'x + x + 2')
        
        expr = parse_and_process("Derivative(x^2,x)", global_dict= global_dict,
                                 evaluate_level = EVALUATE_PARTIAL)
        self.assertEqual(Derivative(x**2,x), expr)
        expr = parse_and_process("Derivative(x^2,x)", global_dict= global_dict,
                                 evaluate_level = EVALUATE_FULL)
        self.assertEqual(2*x, expr)
        expr = parse_and_process("Derivative(x^2,x)", global_dict= global_dict)
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
        
