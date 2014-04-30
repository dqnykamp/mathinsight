from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import six

from django.test import SimpleTestCase
from mitesting.math_objects import *
from sympy import Symbol, diff, Tuple, sympify
from sympy.printing import latex


class MathObjectTests(SimpleTestCase):
    
    def test_base_case(self):
        expression = sympify("5*x")
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertEqual(six.text_type(mobject), '5 x')
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.return_expression(), expression)

    def test_n_digits(self):
        expression = sympify("5*x/3")
        expression_rounded = sympify("1.667*x")
        expression_less_rounded = sympify("1.6667*x")
        expression_too_rounded = sympify("1.67*x")
        mobject = math_object(expression, n_digits=4)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded)
        self.assertEqual(six.text_type(mobject), latex(expression_rounded))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_less_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_too_rounded),0)
        
    def test_round_decimals(self):
        expression = sympify("115*sin(pi*x)/3")
        expression_rounded = sympify("38.333*sin(3.142*x)")
        expression_less_rounded = sympify("38.33333*sin(3.14159*x)")
        expression_too_rounded = sympify("38.33*sin(3.1412*x)")
        mobject = math_object(expression, round_decimals=3)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded)
        self.assertEqual(six.text_type(mobject), latex(expression_rounded))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_less_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_too_rounded),0)

    def test_n_digits_and_round_decimals(self):
        expression = sympify("4115*sin(pi*x)/3")
        expression_rounded = sympify("1371.67*sin(3.142*x)")
        expression_less_rounded = sympify("1371.6666667*sin(3.14159265*x)")
        expression_too_rounded1 = sympify("1371.7*sin(3.142*x)")
        expression_too_rounded2 = sympify("1371.67*sin(3.14*x)")
        mobject = math_object(expression, n_digits=6, round_decimals=3)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression_rounded)
        self.assertNotEqual(mobject,expression_less_rounded)
        self.assertNotEqual(mobject,expression_too_rounded1)
        self.assertNotEqual(mobject,expression_too_rounded2)
        self.assertEqual(six.text_type(mobject), latex(expression_rounded))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_less_rounded),1)
        self.assertEqual(mobject.compare_with_expression(\
                expression_too_rounded1),0)
        self.assertEqual(mobject.compare_with_expression(\
                expression_too_rounded2),0)
        # for round_decimals<=0 should end with integer
        mobject = math_object("19/7*exp(2414.2341*x)", n_digits=3, 
                              round_decimals=0)
        self.assertEqual(six.text_type(mobject),'3 e^{2410 x}')
        

    def test_use_ln(self):
        expression = sympify("log(x)")
        mobject = math_object(expression, use_ln=True)
        self.assertEqual(mobject,expression)
        self.assertEqual(six.text_type(mobject), '\\ln{\\left (x \\right )}')
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertTrue(mobject.return_if_use_ln())
        mobject = math_object(expression, use_ln=False)
        self.assertEqual(mobject,expression)
        self.assertEqual(six.text_type(mobject), '\\log{\\left (x \\right )}')
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertFalse(mobject.return_if_use_ln())
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertEqual(six.text_type(mobject), '\\log{\\left (x \\right )}')
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertFalse(mobject.return_if_use_ln())

    def test_normalize_on_compare(self):
        from sympy.abc import x,y
        expression = 1/x + 1/y
        expression2 = (x+y)/(x*y)
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),-1)

        mobject = math_object(expression, normalize_on_compare=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),1)

        mobject = math_object(expression, normalize_on_compare=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),-1)

        expression = x**2-y**2
        expression2 = (x+y)*(x-y)
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),-1)

        mobject = math_object(expression, normalize_on_compare=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),1)

        mobject = math_object(expression, normalize_on_compare=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),-1)

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
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)
        self.assertFalse(mobject.return_if_unordered())

        mobject = math_object(expression, tuple_is_unordered=True)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),1)
        self.assertTrue(mobject.return_if_unordered())

        mobject = math_object(expression, tuple_is_unordered=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)
        self.assertFalse(mobject.return_if_unordered())


    def test_collapse_equal_tuple_elements(self):
        expression = sympify(sympify("(1-z,x**2,1-z)"))
        expression2 = sympify(sympify("(1-z,x**2)"))
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)

        mobject = math_object(expression, collapse_equal_tuple_elements=True)
        self.assertNotEqual(mobject,expression)
        self.assertEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),0)
        self.assertEqual(mobject.compare_with_expression(expression2),1)
        
        mobject = math_object(expression, collapse_equal_tuple_elements=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)

        expression = sympify(sympify("(1-z,1-z,1-z)"))
        expression2 = sympify(sympify("1-z"))
        mobject = math_object(expression)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)

        mobject = math_object(expression, collapse_equal_tuple_elements=True)
        self.assertNotEqual(mobject,expression)
        self.assertEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),0)
        self.assertEqual(mobject.compare_with_expression(expression2),1)
        
        mobject = math_object(expression, collapse_equal_tuple_elements=False)
        self.assertEqual(mobject,expression)
        self.assertNotEqual(mobject,expression2)
        self.assertEqual(mobject.compare_with_expression(expression),1)
        self.assertEqual(mobject.compare_with_expression(expression2),0)

    def test_output_no_delimiters(self):
        expression = sympify(sympify("(1-z,x**2,3*x*y)"))
        mobject = math_object(expression)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertFalse(mobject.return_if_output_no_delimiters())
        
        mobject = math_object(expression, output_no_delimiters=True)
        self.assertEqual(six.text_type(mobject), '- z + 1,~ x^{2},~ 3 x y')
        self.assertTrue(mobject.return_if_output_no_delimiters())

        mobject = math_object(expression, output_no_delimiters=False)
        self.assertEqual(six.text_type(mobject), latex(expression))
        self.assertFalse(mobject.return_if_output_no_delimiters())

    def test_copy_parameters_from(self):
        mobject = math_object("3*x", n_digits=5, round_decimals=0,
                              use_ln = True, normalize_on_compare=False,
                              split_symbols_on_compare=True,
                              tuple_is_unordered=True,
                              collapse_equal_tuple_elements=True,
                              output_no_delimiters=False)
        self.assertEqual(mobject._parameters['n_digits'],5)
        self.assertEqual(mobject._parameters['round_decimals'],0)
        self.assertTrue(mobject._parameters['use_ln'])
        self.assertFalse(mobject._parameters['normalize_on_compare'])
        self.assertTrue(mobject._parameters['split_symbols_on_compare'])
        self.assertTrue(mobject._parameters['tuple_is_unordered'])
        self.assertTrue(mobject._parameters['collapse_equal_tuple_elements'])
        self.assertFalse(mobject._parameters['output_no_delimiters'])
        self.assertTrue(mobject.return_if_unordered())
        self.assertTrue(mobject.return_if_use_ln())
        self.assertFalse(mobject.return_if_output_no_delimiters())
        self.assertTrue(mobject.return_split_symbols_on_compare)

        mobject2 = math_object("3*x", n_digits=4, round_decimals=3,
                               use_ln = False, normalize_on_compare=True,
                               split_symbols_on_compare=False,
                               tuple_is_unordered=False,
                               collapse_equal_tuple_elements=False,
                               output_no_delimiters=True,
                               copy_parameters_from=mobject)
        self.assertEqual(mobject2._parameters['n_digits'],5)
        self.assertEqual(mobject2._parameters['round_decimals'],0)
        self.assertTrue(mobject2._parameters['use_ln'])
        self.assertFalse(mobject2._parameters['normalize_on_compare'])
        self.assertTrue(mobject2._parameters['split_symbols_on_compare'])
        self.assertTrue(mobject2._parameters['tuple_is_unordered'])
        self.assertTrue(mobject2._parameters['collapse_equal_tuple_elements'])
        self.assertFalse(mobject2._parameters['output_no_delimiters'])
        self.assertTrue(mobject2.return_if_unordered())
        self.assertTrue(mobject2.return_if_use_ln())
        self.assertFalse(mobject2.return_if_output_no_delimiters())
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


    def test_eval_to_precision(self):
        mobject = math_object(1, n_digits=5)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152050*log(1325.2*z)")
        expr_too_rounded = sympify("152100*log(1325.2*z)")
        self.assertEqual(mobject.eval_to_precision(expr), expr_rounded)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr_too_rounded)

        mobject = math_object(1, round_decimals=-1)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152050*log(1330*z)")
        expr_too_rounded = sympify("152100*log(1330*z)")
        self.assertEqual(mobject.eval_to_precision(expr), expr_rounded)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr_too_rounded)

        mobject = math_object(1, round_decimals=-1, n_digits=4)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152100*log(1330*z)")
        expr_too_rounded = sympify("152100*log(1300*z)")
        self.assertEqual(mobject.eval_to_precision(expr), expr_rounded)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr)
        self.assertNotEqual(mobject.eval_to_precision(expr), expr_too_rounded)

        mobject = math_object(1)
        expr = sympify("152052.3282*log(1325.234*z)")
        expr_rounded = sympify("152100*log(1330*z)")
        self.assertNotEqual(mobject.eval_to_precision(expr), expr_rounded)
        self.assertEqual(mobject.eval_to_precision(expr), expr)

    def test_eval_to_precision_roundoff_error(self):
        # test that eval_to_precision helps to normalize
        # in presence of round-off error
        mobject = math_object(1)
        expr1 = sympify((.1/.11 - .1/.12)*(.1/.11 + .1/.12))
        expr2 = sympify((.1/.11)**2 - (.1/.12)**2)
        # not equal due to roundoff error
        self.assertNotEqual(expr1,expr2)
        # equal when eval to precision
        self.assertEqual(mobject.eval_to_precision(expr1),
                          mobject.eval_to_precision(expr2))
        # verify that keep exactly 14 digits of accuracy
        self.assertEqual(mobject.eval_to_precision(expr1),
                          0.13200183654729)

    def test_convert_expression(self):
        expr = sympify("152052.3282*log(1325.234*z)")
        mobject = math_object(expr, n_digits=5)
        expr_rounded = sympify("152050*log(1325.2*z)")
        expr_too_rounded = sympify("152100*log(1325.2*z)")
        self.assertEqual(mobject.convert_expression(), expr_rounded)
        self.assertNotEqual(mobject.convert_expression(), expr)
        self.assertNotEqual(mobject.convert_expression(), expr_too_rounded)

        expr = sympify("152052.3282*log(1325.234*z)")
        mobject = math_object(expr, round_decimals=-1)
        expr_rounded = sympify("152050*log(1330*z)")
        expr_too_rounded = sympify("152100*log(1330*z)")
        self.assertEqual(mobject.convert_expression(), expr_rounded)
        self.assertNotEqual(mobject.convert_expression(), expr)
        self.assertNotEqual(mobject.convert_expression(), expr_too_rounded)

        expr = sympify("152052.3282*log(1325.234*z)")
        mobject = math_object(expr, round_decimals=-1, n_digits=4)
        expr_rounded = sympify("152100*log(1330*z)")
        expr_too_rounded = sympify("152100*log(1300*z)")
        self.assertEqual(mobject.convert_expression(), expr_rounded)
        self.assertNotEqual(mobject.convert_expression(), expr)
        self.assertNotEqual(mobject.convert_expression(), expr_too_rounded)

        expr = sympify("152052.3282*log(1325.234*z)")
        mobject = math_object(expr)
        expr_rounded = sympify("152100*log(1330*z)")
        self.assertNotEqual(mobject.convert_expression(), expr_rounded)
        self.assertEqual(mobject.convert_expression(), expr)
        
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
        
    def test_text_output_delimiters(self):
        expr = sympify("(1,2,3)")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '\\begin{pmatrix}1, & 2, & 3\\end{pmatrix}')
        mobject = math_object(expr, output_no_delimiters=True)
        self.assertEqual(six.text_type(mobject), 
                         '1,~ 2,~ 3')
        mobject = math_object(expr, output_no_delimiters=False)
        self.assertEqual(six.text_type(mobject), 
                         '\\begin{pmatrix}1, & 2, & 3\\end{pmatrix}')

        expr = sympify("[1,2,3]")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '\\begin{bmatrix}1, & 2, & 3\\end{bmatrix}')
        mobject = math_object(expr, output_no_delimiters=True)
        self.assertEqual(six.text_type(mobject), 
                         '1,~ 2,~ 3')
        mobject = math_object(expr, output_no_delimiters=False)
        self.assertEqual(six.text_type(mobject), 
                         '\\begin{bmatrix}1, & 2, & 3\\end{bmatrix}')
        

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

    def test_text_use_ln(self):
        expr = sympify("log(2*z)")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '\\log{\\left (2 z \\right )}')
        mobject = math_object(expr, use_ln=True)
        self.assertEqual(six.text_type(mobject), 
                         '\\ln{\\left (2 z \\right )}')
        mobject = math_object(expr, use_ln=False)
        self.assertEqual(six.text_type(mobject), 
                         '\\log{\\left (2 z \\right )}')

        expr = sympify("ln(-3*y)")
        mobject = math_object(expr)
        self.assertEqual(six.text_type(mobject), 
                         '\\log{\\left (- 3 y \\right )}')
        mobject = math_object(expr, use_ln=True)
        self.assertEqual(six.text_type(mobject), 
                         '\\ln{\\left (- 3 y \\right )}')
        mobject = math_object(expr, use_ln=False)
        self.assertEqual(six.text_type(mobject), 
                         '\\log{\\left (- 3 y \\right )}')

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
        self.assertEqual(mobject.compare_with_expression(expr),1)
        self.assertEqual(mobject.compare_with_expression(expr_switch),0)
        self.assertEqual(mobject.compare_with_expression(expr_augment),0)
        self.assertEqual(mobject.compare_with_expression(expr_reduce),0)
        
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
        mobject = math_object(expr1)
        self.assertEqual(mobject.compare_with_expression(expr1),1)
        self.assertEqual(mobject.compare_with_expression(expr2),1)
        self.assertEqual(mobject.compare_with_expression(expr3),0)
        self.assertEqual(mobject.compare_with_expression(expr4),0)
        self.assertEqual(mobject.compare_with_expression(expr5),0)
        self.assertEqual(mobject.compare_with_expression(expr6),0)
        self.assertEqual(mobject.compare_with_expression(expr7),0)
        self.assertEqual(mobject.compare_with_expression(expr8),0)
        self.assertEqual(mobject.compare_with_expression(expr9),0)
        self.assertEqual(mobject.compare_with_expression(expr10),0)
        self.assertEqual(mobject.compare_with_expression(expr11),0)
        self.assertEqual(mobject.compare_with_expression(expr12),0)

        mobject = math_object(expr5)
        self.assertEqual(mobject.compare_with_expression(expr1),0)
        self.assertEqual(mobject.compare_with_expression(expr2),0)
        self.assertEqual(mobject.compare_with_expression(expr3),0)
        self.assertEqual(mobject.compare_with_expression(expr4),0)
        self.assertEqual(mobject.compare_with_expression(expr5),1)
        self.assertEqual(mobject.compare_with_expression(expr6),1)
        self.assertEqual(mobject.compare_with_expression(expr7),0)
        self.assertEqual(mobject.compare_with_expression(expr8),0)
        self.assertEqual(mobject.compare_with_expression(expr9),0)
        self.assertEqual(mobject.compare_with_expression(expr10),0)
        self.assertEqual(mobject.compare_with_expression(expr11),0)
        self.assertEqual(mobject.compare_with_expression(expr12),0)
        
        mobject = math_object(expr9)
        self.assertEqual(mobject.compare_with_expression(expr1),0)
        self.assertEqual(mobject.compare_with_expression(expr2),0)
        self.assertEqual(mobject.compare_with_expression(expr3),0)
        self.assertEqual(mobject.compare_with_expression(expr4),0)
        self.assertEqual(mobject.compare_with_expression(expr5),0)
        self.assertEqual(mobject.compare_with_expression(expr6),0)
        self.assertEqual(mobject.compare_with_expression(expr7),0)
        self.assertEqual(mobject.compare_with_expression(expr8),0)
        self.assertEqual(mobject.compare_with_expression(expr9),1)
        self.assertEqual(mobject.compare_with_expression(expr10),1)
        self.assertEqual(mobject.compare_with_expression(expr11),0)
        self.assertEqual(mobject.compare_with_expression(expr12),0)

        mobject = math_object(expr11)
        self.assertEqual(mobject.compare_with_expression(expr1),0)
        self.assertEqual(mobject.compare_with_expression(expr2),0)
        self.assertEqual(mobject.compare_with_expression(expr3),0)
        self.assertEqual(mobject.compare_with_expression(expr4),0)
        self.assertEqual(mobject.compare_with_expression(expr5),0)
        self.assertEqual(mobject.compare_with_expression(expr6),0)
        self.assertEqual(mobject.compare_with_expression(expr7),0)
        self.assertEqual(mobject.compare_with_expression(expr8),0)
        self.assertEqual(mobject.compare_with_expression(expr9),0)
        self.assertEqual(mobject.compare_with_expression(expr10),0)
        self.assertEqual(mobject.compare_with_expression(expr11),1)
        self.assertEqual(mobject.compare_with_expression(expr12),1)


    def test_line_equality(self):
        from sympy.geometry import Line
        from sympy import Point
        expr1 = Line(Point(2,3), Point(3,5))
        expr2 = Line(Point(3,5), Point(2,3))
        expr3 = Line(Point(2,3), Point(4,7))
        expr4 = Line(Point(4,7), Point(1,1))
        expr5 = Line(Point(2,3), Point(3,4))
        mobject = math_object(expr1)
        self.assertEqual(mobject.compare_with_expression(expr1),1)
        self.assertEqual(mobject.compare_with_expression(expr2),1)
        self.assertEqual(mobject.compare_with_expression(expr3),1)
        self.assertEqual(mobject.compare_with_expression(expr4),1)
        self.assertEqual(mobject.compare_with_expression(expr5),0)

    def test_evaluate_false(self):
        from mitesting.sympy_customized import parse_expr, EVALUATE_NONE, \
            EVALUATE_PARTIAL, EVALUATE_FULL
        expr_string="x-x+x*x/x"
        expr_evaluated = sympify(expr_string)
        expr_unevaluated = parse_expr(expr_string, evaluate=False)
        mobject = math_object(expr_unevaluated)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated),1)
        self.assertEqual(six.text_type(mobject), latex(expr_evaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_FULL)

        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_NONE)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated),-1)
        self.assertEqual(six.text_type(mobject), latex(expr_unevaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_NONE)
        
        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_PARTIAL)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated),1)
        self.assertEqual(six.text_type(mobject), latex(expr_evaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_PARTIAL)

        mobject = math_object(expr_unevaluated, evaluate_level=EVALUATE_FULL)
        self.assertEqual(mobject.compare_with_expression(expr_evaluated),1)
        self.assertEqual(six.text_type(mobject), latex(expr_evaluated))
        self.assertEqual(mobject.return_evaluate_level(), EVALUATE_FULL)
        


    def test_evaluate_normalize_with_doit(self):
        from sympy import Derivative
        x=Symbol('x')
        expr = Derivative(x**2,x)
        expr2 = 2*x
        mobject = math_object(expr)
        self.assertEqual(mobject.compare_with_expression(expr),1)
        self.assertEqual(mobject.compare_with_expression(expr2),-1)

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
