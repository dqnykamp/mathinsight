from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import six

from django.test import SimpleTestCase
from mitesting.math_objects import *
from sympy import Symbol, diff, Tuple, sympify
from sympy.printing import latex
import random

class MathObjectTests(SimpleTestCase):
    def setUp(self):
        random.seed()
    
    def test_base_case(self):
        expression = sympify("5*x")
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertEqual(six.text_type(mobject), '5 x')
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.return_expression(), expression)

    def test_round_on_compare(self):
        expression = sympify("5*x/3")
        expression_rounded = sympify("1.667*x")
        expression_less_rounded = sympify("1.6667*x")
        expression_too_rounded = sympify("1.67*x")

        mobject = math_object(expression, round_on_compare=4)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded)
        self.assertEqual(mobject.compare_with_expression(expression)\
                         ['fraction_equal'],1)
        self.assertFalse(mobject.compare_with_expression(expression)\
                         ['round_absolute'])
        self.assertEqual(mobject.compare_with_expression(expression_rounded)\
                         ['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                            expression_less_rounded)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                            expression_too_rounded)['fraction_equal'],0)
        
        mobject = math_object(expression, round_on_compare=4, 
                              round_absolute=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded)
        self.assertEqual(mobject.compare_with_expression(expression)\
                         ['fraction_equal'],1)
        self.assertFalse(mobject.compare_with_expression(expression)\
                         ['round_absolute'])
        self.assertEqual(mobject.compare_with_expression(expression_rounded)\
                         ['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                            expression_less_rounded)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                            expression_too_rounded)['fraction_equal'],0)
        

    def test_round_on_compare_absolute(self):
        expression = sympify("115*sin(pi*x)/3")
        expression_rounded = sympify("38.333*sin(3.142*x)")
        expression_less_rounded = sympify("38.33333*sin(3.14159*x)")
        expression_too_rounded = sympify("38.33*sin(3.1412*x)")
        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded)
        self.assertEqual(mobject.compare_with_expression(expression)\
                         ['fraction_equal'] ,1)
        self.assertTrue(mobject.compare_with_expression(expression)\
                         ['round_absolute'])
        self.assertEqual(mobject.compare_with_expression(expression_rounded)\
                         ['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_less_rounded)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_too_rounded)['fraction_equal'],0)


    def test_round_on_compare_partial_credit(self):
        expression = sympify("5*x/3")
        expression_rounded = sympify("1.667*x")
        expression_too_rounded = sympify("1.67*x")
        expression_too_rounded2 = sympify("1.7*x")

        mobject = math_object(expression, round_on_compare=4)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)

        mobject = math_object(expression, round_on_compare=4, 
                              round_partial_credit_digits=1)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)

        mobject = math_object(expression, round_on_compare=4, 
                              round_partial_credit_digits=1,
                              round_partial_credit_percent=0)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)

        mobject = math_object(expression, round_on_compare=4, 
                              round_partial_credit_digits=1,
                              round_partial_credit_percent=80)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0.8)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)

        mobject = math_object(expression, round_on_compare=4, 
                              round_partial_credit_digits=2,
                              round_partial_credit_percent=80)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],4)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0.8)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],4)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0.8*0.8)
        self.assertEqual(compare['round_level_used'],2)
        self.assertEqual(compare['round_level_required'],4)


    def test_round_on_compare_absolute_partial_credit(self):
        expression = sympify("115*sin(pi*x)/3")
        expression_rounded = sympify("38.333*sin(3.142*x)")
        expression_too_rounded = sympify("38.33*sin(3.1412*x)")
        expression_too_rounded2 = sympify("38.3*sin(3.141*x)")
        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True)

        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)

        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True,
                              round_partial_credit_digits=1)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],2)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)

        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True,
                              round_partial_credit_digits=1,
                              round_partial_credit_percent=0)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],2)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)

        mobject = math_object(expression, round_on_compare=3,
                              round_absolute=True,
                              round_partial_credit_digits=1,
                              round_partial_credit_percent=80)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0.8)
        self.assertEqual(compare['round_level_used'],2)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)

        mobject = math_object(expression, round_on_compare=3, 
                              round_absolute=True,
                              round_partial_credit_digits=2,
                              round_partial_credit_percent=80)
        compare=mobject.compare_with_expression(expression_rounded)
        self.assertEqual(compare['fraction_equal'],1)
        self.assertEqual(compare['round_level_used'],3)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded)
        self.assertEqual(compare['fraction_equal'],0.8)
        self.assertEqual(compare['round_level_used'],2)
        self.assertEqual(compare['round_level_required'],3)
        compare=mobject.compare_with_expression(expression_too_rounded2)
        self.assertEqual(compare['fraction_equal'],0.8*0.8)
        self.assertEqual(compare['round_level_used'],1)
        self.assertEqual(compare['round_level_required'],3)


    def test_round_up_5(self):
        expression = sympify("123.456")
        expression_rounded = sympify("123.455")
        mobject = math_object(expression, round_on_compare=2,
                              round_absolute=True)
        self.assertEqual(mobject.compare_with_expression(expression_rounded)\
                         ['fraction_equal'],1)
        # This shold work, but doesn't as .evalf doesn't work right
        # mobject = math_object(expression, round_on_compare=5)
        # self.assertEqual(mobject.compare_with_expression(expression_rounded)\
        #                  ['fraction_equal'],1)


    def test_normalize_on_compare(self):
        from sympy.abc import x,y
        expression = 1/x + 1/y
        expression2 = (x+y)/(x*y)
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal_on_normalize'],1)

        mobject = math_object(expression, normalize_on_compare=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],1)

        mobject = math_object(expression, normalize_on_compare=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal_on_normalize'],1)

        expression = x**2-y**2
        expression2 = (x+y)*(x-y)
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal_on_normalize'],1)

        mobject = math_object(expression, normalize_on_compare=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],1)

        mobject = math_object(expression, normalize_on_compare=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal_on_normalize'],1)

    def test_split_symbols_on_compare(self):
        mobject = math_object("x")
        self.assertFalse(mobject.return_split_symbols_on_compare())
        mobject = math_object("x", split_symbols_on_compare=True)
        self.assertTrue(mobject.return_split_symbols_on_compare())
        mobject = math_object("x", split_symbols_on_compare=False)
        self.assertFalse(mobject.return_split_symbols_on_compare())

    def test_tuple_ordering(self):
        expression = sympify(sympify("(1,x**2,1-z)"))
        expression2 = sympify(sympify("(x**2,1,1-z)"))
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertFalse(mobject.return_if_unordered())

        mobject = math_object(expression, tuple_is_unordered=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],1)
        self.assertTrue(mobject.return_if_unordered())

        mobject = math_object(expression, tuple_is_unordered=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expression2)['fraction_equal'],0)
        self.assertFalse(mobject.return_if_unordered())


    def test_copy_parameters_from(self):
        mobject = math_object("3*x", n_digits=5, round_decimals=0,
                              normalize_on_compare=False,
                              split_symbols_on_compare=True,
                              tuple_is_unordered=True)
        self.assertEqual(mobject._parameters['n_digits'],5)
        self.assertEqual(mobject._parameters['round_decimals'],0)
        self.assertFalse(mobject._parameters['normalize_on_compare'])
        self.assertTrue(mobject._parameters['split_symbols_on_compare'])
        self.assertTrue(mobject._parameters['tuple_is_unordered'])
        self.assertTrue(mobject.return_if_unordered())

        mobject2 = math_object("3*x", n_digits=4, round_decimals=3,
                               normalize_on_compare=True,
                               split_symbols_on_compare=False,
                               tuple_is_unordered=False,
                               copy_parameters_from=mobject)
        self.assertEqual(mobject2._parameters['n_digits'],5)
        self.assertEqual(mobject2._parameters['round_decimals'],0)
        self.assertFalse(mobject2._parameters['normalize_on_compare'])
        self.assertTrue(mobject2._parameters['split_symbols_on_compare'])
        self.assertTrue(mobject2._parameters['tuple_is_unordered'])
        self.assertTrue(mobject2.return_if_unordered())
        self.assertTrue(mobject2.return_split_symbols_on_compare)

    def test_comparison_operators(self):
        mobject1 = math_object(1)
        mobject2 = math_object(2)
        mobject2a = math_object(2)
        self.assertFalse(mobject1 == mobject2)
        self.assertTrue(mobject2 == mobject2a)
        self.assertTrue(mobject1 != mobject2)
        self.assertFalse(mobject2 != mobject2a)
        self.assertTrue(mobject1 < mobject2)
        self.assertFalse(mobject2 < mobject2a)
        self.assertTrue(mobject1 <= mobject2)
        self.assertTrue(mobject2 <= mobject2a)
        self.assertFalse(mobject2 <= mobject1)
        self.assertTrue(mobject2 > mobject1)
        self.assertFalse(mobject2 > mobject2a)
        self.assertFalse(mobject1 >= mobject2)
        self.assertTrue(mobject2 >= mobject2a)
        self.assertTrue(mobject2 >= mobject1)
        
        mobject0 = math_object(0)
        self.assertTrue(mobject1 == True)
        self.assertTrue(mobject0 == False)
        self.assertFalse(mobject1 == False)
        self.assertFalse(mobject0 == True)


    def test_eval_to_comparison_precision(self):
        mobject = math_object(1, round_on_compare=5)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152050*log(1325.2*z)")
        expr_too_rounded = sympify("152100*log(1325.2*z)")
        self.assertEqual(mobject.eval_to_comparison_precision(expr), expr_rounded)
        self.assertNotEqual(mobject.eval_to_comparison_precision(expr), expr)
        self.assertNotEqual(mobject.eval_to_comparison_precision(expr), expr_too_rounded)

        mobject = math_object(1, round_on_compare=-1, round_absolute=True)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152050*log(1330*z)")
        expr_too_rounded = sympify("152100*log(1330*z)")
        self.assertEqual(mobject.eval_to_comparison_precision(expr), expr_rounded)
        self.assertNotEqual(mobject.eval_to_comparison_precision(expr), expr)
        self.assertNotEqual(mobject.eval_to_comparison_precision(expr), expr_too_rounded)

        mobject = math_object(1)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152100*log(1330*z)")
        self.assertNotEqual(mobject.eval_to_comparison_precision(expr), expr_rounded)
        self.assertEqual(mobject.eval_to_comparison_precision(expr), expr)

    def test_eval_to_comparison_precision_roundoff_error(self):
        # test that eval_to_comparison_precision helps to normalize
        # in presence of round-off error
        mobject = math_object(1)
        expr1 = sympify((.1/.11 - .1/.12)*(.1/.11 + .1/.12))
        expr2 = sympify((.1/.11)**2 - (.1/.12)**2)
        # not equal due to roundoff error
        self.assertNotEqual(expr1,expr2)
        # equal when eval to precision
        self.assertEqual(mobject.eval_to_comparison_precision(expr1),
                          mobject.eval_to_comparison_precision(expr2))
        # verify that keep exactly 14 digits of accuracy
        self.assertEqual(mobject.eval_to_comparison_precision(expr1),
                          0.13200183654729)

        
    def test_text_basics(self):
        mobject = math_object("7/9*x**2-3/5*x+33")
        self.assertEqual(six.text_type(mobject), 
                         '\\frac{7 x^{2}}{9} - \\frac{3 x}{5} + 33')
        mobject = math_object("Integral(f,x)")
        self.assertEqual(six.text_type(mobject), 
                         '\\int f\\, dx')
        mobject = math_object("sin(2*pi*x)*exp(5.2*x)")
        self.assertEqual(six.text_type(mobject), 
                         'e^{5.2 x} \\sin{\\left (2 \\pi x \\right )}')
        

    def test_text_lines(self):
        from sympy.geometry import Line
        from sympy import Point
        expr = Line(Point(2,3), Point(3,5))
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '- 2 x + y + 1 = 0')
        mobject = math_object(expr, xvar = 's', yvar = 't')
        self.assertEqual(six.text_type(mobject), 
                         '- 2 s + t + 1 = 0')

    def test_text_symbols(self):
        expr = sympify("blacktriangle*bigstar")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '\\bigstar \\blacktriangle')
        expr = sympify("2*x*Box - 3*y*lozenge")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '2 \\Box x - 3 \\lozenge y')

    def test_float_conversion(self):
        mobject = math_object("3*2/5")
        self.assertEqual(float(mobject), 1.2)
        self.assertEqual(mobject.float(), 1.2)
        mobject = math_object("3*x/5")
        self.assertRaises(TypeError, float, mobject)


    def test_list_equality(self):
        expr = sympify("[1, 2*x, 4*sin(3*z)]")
        expr_switch = sympify("[2*x, 1, 4*sin(3*z)]")
        expr_augment = sympify("[1, 2*x, 4*sin(3*z),0]")
        expr_reduce = sympify("[1, 2*x]")
        mobject = math_object(expr)
        self.assertEqual(mobject.compare_with_expression(expr)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr_switch)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr_augment)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr_reduce)['fraction_equal'],0)
        
    def test_relational_equality(self):
        expr1 = sympify("3*x < 5")
        expr2 = sympify("5 > 3*x")
        expr3 = sympify("3*x > 5")
        expr4 = sympify("5 < 3*x")
        expr5 = sympify("3*x <= 5")
        expr6 = sympify("5 >= 3*x")
        expr7 = sympify("3*x >= 5")
        expr8 = sympify("5 <= 3*x")
        expr9 = sympify("Eq(3*x,5)")
        expr10 = sympify("Eq(5,3*x)")
        expr11 = sympify("Ne(3*x,5)")
        expr12 = sympify("Ne(5,3*x)")
        expr13 = sympify("6*x < 10")
        expr14 = sympify("-9*x > -15")
        expr15 = sympify("3*x-5 < 0")
        expr16 = sympify("3*x+2 < 7")
        expr17 = sympify("2*(8-3*x)+(x-1)*(x+1)-x^2 > 5")

        mobject = math_object(expr1)
        self.assertEqual(mobject.compare_with_expression(expr1)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr3)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr4)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr5)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr6)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr7)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr8)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr9)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr10)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr11)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr12)['fraction_equal'],0)

        self.assertEqual(mobject.compare_with_expression(expr13)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr13)['fraction_equal_on_normalize'],1)
        self.assertEqual(mobject.compare_with_expression(expr14)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr14)['fraction_equal_on_normalize'],1)
        self.assertEqual(mobject.compare_with_expression(expr15)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr15)['fraction_equal_on_normalize'],1)
        self.assertEqual(mobject.compare_with_expression(expr16)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr16)['fraction_equal_on_normalize'],1)
        self.assertEqual(mobject.compare_with_expression(expr17)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr17)['fraction_equal_on_normalize'],1)

        mobject = math_object(expr5)
        self.assertEqual(mobject.compare_with_expression(expr1)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr3)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr4)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr5)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr6)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr7)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr8)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr9)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr10)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr11)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr12)['fraction_equal'],0)
        
        mobject = math_object(expr9)
        self.assertEqual(mobject.compare_with_expression(expr1)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr3)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr4)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr5)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr6)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr7)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr8)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr9)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr10)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr11)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr12)['fraction_equal'],0)

        mobject = math_object(expr11)
        self.assertEqual(mobject.compare_with_expression(expr1)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr3)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr4)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr5)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr6)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr7)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr8)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr9)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr10)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr11)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr12)['fraction_equal'],1)


    def test_line_equality(self):
        from sympy.geometry import Line
        from sympy import Point
        expr1 = Line(Point(2,3), Point(3,5))
        expr2 = Line(Point(3,5), Point(2,3))
        expr3 = Line(Point(2,3), Point(4,7))
        expr4 = Line(Point(4,7), Point(1,1))
        expr5 = Line(Point(2,3), Point(3,4))
        mobject = math_object(expr1)
        self.assertEqual(mobject.compare_with_expression(expr1)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr3)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr4)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr5)['fraction_equal'],0)

    def test_evaluate_false(self):
        from mitesting.sympy_customized import parse_expr, EVALUATE_NONE, \
            EVALUATE_PARTIAL, EVALUATE_FULL
        expr_string="x-x+x*x/x"
        expr_evaluated = sympify(expr_string)
        expr_unevaluated = parse_expr(expr_string, evaluate=False)
        mobject = math_object(expr_unevaluated)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated)['fraction_equal'],1)
        self.assertEqual(six.text_type(mobject), latex(expr_unevaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_FULL)

        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_NONE)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated)['fraction_equal_on_normalize'],1)
        self.assertEqual(six.text_type(mobject), latex(expr_unevaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_NONE)
        
        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_PARTIAL)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated)['fraction_equal'],1)
        self.assertEqual(six.text_type(mobject), latex(expr_unevaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_PARTIAL)

        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_FULL)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated)['fraction_equal'],1)
        self.assertEqual(six.text_type(mobject), latex(expr_unevaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_FULL)
        


    def test_evaluate_normalize_with_doit(self):
        from sympy import Derivative
        x=Symbol('x')
        expr = Derivative(x**2,x)
        expr2 = 2*x
        mobject = math_object(expr)
        self.assertEqual(mobject.compare_with_expression(expr)['fraction_equal'],1)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal'],0)
        self.assertEqual(mobject.compare_with_expression(expr2)['fraction_equal_on_normalize'],1)

    def test_compare_with_sympy_expression(self):
        x=Symbol('x')
        y=Symbol('y')
        expr= x*y-x
        mobject = math_object(expr)
        # try both directions so call __eq__ in sympy and in mobject
        self.assertEqual(mobject, expr)
        self.assertEqual(expr, mobject)
        self.assertTrue(mobject == expr)
        self.assertTrue(expr == mobject)

    def test_combine_with_sympy_expression(self):
        x=Symbol('x')
        y=Symbol('y')
        expr= x*y-x
        mobject = math_object(expr)
        self.assertEqual(mobject+x**2, expr + x**2)
        self.assertEqual(mobject*x**2, expr*x**2)
        self.assertEqual(mobject**x, expr**x)


    def test_operations_with_numbers(self):
        x=Symbol('x')
        y=Symbol('y')
        expr= x*y-x
        mobject = math_object(expr)
        self.assertEqual(mobject+1, expr+1)
        self.assertEqual(1+mobject, 1+expr)
        self.assertEqual(mobject-1, expr-1)
        self.assertEqual(1-mobject, 1-expr)
        self.assertEqual(mobject*2, expr*2)
        self.assertEqual(2*mobject, 2*expr)
        self.assertEqual(mobject/2, expr/2)
        self.assertEqual(2/mobject, 2/expr)
        self.assertEqual(mobject*2.2, expr*2.2)
        self.assertEqual(2.2*mobject, 2.2*expr)
        self.assertEqual(mobject/2.2, expr/2.2)
        self.assertEqual(2.2/mobject, 2.2/expr)
        self.assertEqual(mobject**2, expr**2)
        self.assertEqual(2**mobject, 2**expr)
        
        mobject = math_object(3)
        self.assertEqual(mobject,3)
        self.assertEqual(3,mobject)



    def test_normalize_catch_polynomial_error(self):
        from mitesting.customized_commands import iif
        x = Symbol('x')
        expr = iif(x>1,1,0)
        self.assertEqual(expr,try_normalize_expr(expr))
