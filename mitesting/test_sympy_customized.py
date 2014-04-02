from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import SimpleTestCase
from mitesting.sympy_customized import bottom_up, parse_expr
from mitesting.customized_commands import normalize_floats
from sympy import Symbol, diff, Tuple, sympify, Integer
import random

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

