
from django.test import SimpleTestCase
from mitesting.customized_commands import *
from sympy import diff, Tuple, sympify
from mitesting.sympy_customized import Symbol, TupleNoParen
import random

class RoundingTests(SimpleTestCase):
    def test_round_expression_with_numbers(self):
        x = 1.2346
        self.assertEqual(round_expression(x,3), 1.235)
        self.assertEqual(round_expression(-52.2343,2), -52.23)
        # check that actually removes decimal point by using strings
        self.assertEqual(str(round_expression(1.0)), "1")
        self.assertEqual(str(round_expression(-5.0,0)), "-5")
        self.assertEqual(str(round_expression(3.7)), "4")
        self.assertEqual(str(round_expression(96.23,-2)), "100")
    
    def test_round_expression_with_symbolic_expressions(self):
        x = Symbol('x')
        self.assertEqual(round_expression(x),x)
        expr = 2.1*x**2.9-3.3*x+4.7
        expr_round = 2*x**3-3*x+5
        self.assertEqual(round_expression(expr),expr_round)
        from sympy import sin, exp
        from sympy import Symbol as sympy_Symbol
        z = sympy_Symbol('z')

        # round expressions can take strings, as it calls sympify first
        self.assertEqual(round_expression("3.93*sin(3.1*z)"), 4*sin(3*z))
        
        # round rationals inside function
        self.assertEqual(round_expression("cos(3*y/7)",3),
                          sympify("cos(0.429*y)"))
        
        # number will be taken out of exponential before rounding
        # in this case, the exponential should be multiplied by
        # zero after the rounding
        self.assertEqual(round_expression("43/11+exp(z/3-47/5)", 3),
                          3.909)

        # some bug or something that gives different result is -exp
        # self.assertEqual(round_expression("7/5-3*exp(5*z/6-7/3)/13", 5),
        #                   1.4-0.02238*exp(0.83333*z))

        self.assertEqual(round_expression("sqrt(x-3.512114)/3",2),
                          round_expression("(x-3.512114)**0.5/3",2))


    def test_round_expression_with_symbolic_tuples(self):
        # For tuples, need to call sympify first so sympify is 
        # called a second time in roun_expression
        # That way, tuples are converted to Tuples in second pass.
        expr= sympify("(-3/11, sin(2*pi*x)-sin(3*pi/7), sqrt(9/11), sqrt(4*x/2.913-3/2.132))")
        expr_rounded = sympify("(-0.2727, sin(6.2832*x)-0.9749, 0.9045, sqrt(1.3732*x-1.4071))")
        self.assertEqual(round_expression(expr,4),expr_rounded)

    def test_round_expression_gives_equivalent_results(self):
        expr1 = sympify("3.231502*x**2    - 2208.2352350*x + 152.325235")
        expr2 = sympify("3.231519*x**2.00004 - 2208.2352*x + 152.325219")
        expr3 = sympify("3.231519*x**2.00006 - 2208.235*x  + 152.325219")
        self.assertEqual(round_expression(expr1,4),
                          round_expression(expr2,4))
        self.assertNotEqual(round_expression(expr1,4),
                             round_expression(expr3,4))

        expr1 = sympify("5/3*sin(2*pi*x)")
        expr2 = sympify("1.6666*sin(6.2831*x)")
        self.assertEqual(round_expression(expr1,3),
                          round_expression(expr2,3))
        self.assertNotEqual(round_expression(expr1,4),
                             round_expression(expr2,4))
        
        expr1 = sympify("7/9*x**(3/2)")
        expr2 = sympify("0.778*x**1.5")
        self.assertEqual(round_expression(expr1,3),
                          round_expression(expr2,3))
        self.assertNotEqual(round_expression(expr1,4),
                             round_expression(expr2,4))

        expr1 = sympify("sqrt(x/3)")
        expr2 = sympify("0.57735*x**0.5")
        self.assertEqual(round_expression(expr1,6),
                          round_expression(expr2,6))
        self.assertNotEqual(round_expression(expr1,7),
                             round_expression(expr2,7))

        expr1 = sympify("tan(2*pi/7)*sin(3*x**2/4)")
        expr2 = sympify("1.2539603*sin(0.75*x**2)")
        self.assertEqual(round_expression(expr1,7),
                          round_expression(expr2,7))
        self.assertNotEqual(round_expression(expr1,8),
                             round_expression(expr2,8))

class EvalfTests(SimpleTestCase):
    def test_evalf_expression_with_numbers(self):
        x = 5.205123
        self.assertEqual(evalf_expression(x,4), 5.205)
        self.assertEqual(evalf_expression(-52.2343e34,3), -52.2e34)
        self.assertEqual(evalf_expression(-52.2343e-27,5), -52.234e-27)
    
    def test_evalf_expression_with_symbolic_expressions(self):
        x = Symbol('x')
        self.assertEqual(evalf_expression(x),x)
        expr = 0.1213*x**2.239-332.323*x+23.72
        expr_evalf = 0.121*x**2.24-332.0*x+23.7
        self.assertEqual(evalf_expression(expr,3),expr_evalf)

        from sympy import sin, exp
        from sympy import Symbol as sympy_Symbol
        z = sympy_Symbol('z')

        # evalf expressions can take strings, as it calls sympify first
        self.assertEqual(evalf_expression("3.99*sin(3.12*z)",2), 4*sin(3.1*z))
        
        # evalf rationals inside function
        self.assertEqual(evalf_expression("cos(3*y/7)",3),
                          sympify("cos(0.429*y)"))
        
        # number will be taken out of exponential before evalf
        self.assertEqual(evalf_expression("43/11+exp(z/3-47/5)", 3),
                          8.27e-5*exp(0.333*z)+3.91)

        # some bug or something that gives different result is -exp
        # self.assertEqual(evalf_expression("7/5-3*exp(5*z/6-7/3)/13", 5),
        #                   1.4-0.23077*exp(0.83333*z-2.3333))

        self.assertEqual(evalf_expression("sqrt(x-3.512114)/3",2),
                          evalf_expression("(x-3.512114)**0.5/3",2))


    def test_evalf_expression_with_symbolic_tuples(self):
        # For tuples, need to call sympify first so sympify is 
        # called a second time in evalf_expression.
        # That way, tuples are converted to Tuples in second pass.
        expr= sympify("(-3/11, sin(2*pi*x)-sin(3*pi/7), sqrt(9/11), sqrt(4*x/2.913-3/2.132))")
        expr_evalf = sympify("(-0.2727, sin(6.283*x)-0.9749, 0.9045, sqrt(1.373*x-1.407))")
        self.assertEqual(evalf_expression(expr,4),expr_evalf)


    def test_evalf_expression_gives_equivalent_results(self):
        expr1 = sympify("3.2315024*x**2  - 2208235.2350*x + 10523252235")
        expr2 = sympify("3.2315192*x**2.00004 - 2208200*x + 10523218500")
        expr3 = sympify("3.2315192*x**2.00006 - 2208200*x + 10523218500")
        self.assertEqual(evalf_expression(expr1,5),
                          evalf_expression(expr2,5))
        self.assertNotEqual(evalf_expression(expr1,5),
                             evalf_expression(expr3,5))

        expr1 = sympify("5/3*sin(2*pi*x)")
        expr2 = sympify("1.6666*sin(6.2831*x)")
        self.assertEqual(evalf_expression(expr1,4),
                          evalf_expression(expr2,4))
        self.assertNotEqual(evalf_expression(expr1,5),
                             evalf_expression(expr2,5))
        
        expr1 = sympify("7/9*x**(3/2)")
        expr2 = sympify("0.778*x**1.5")
        self.assertEqual(evalf_expression(expr1,3),
                          evalf_expression(expr2,3))
        self.assertNotEqual(evalf_expression(expr1,4),
                             evalf_expression(expr2,4))

        expr1 = sympify("sqrt(x/3)")
        expr2 = sympify("0.57735*x**0.5")
        self.assertEqual(evalf_expression(expr1,6),
                          evalf_expression(expr2,6))
        self.assertNotEqual(evalf_expression(expr1,7),
                             evalf_expression(expr2,7))

        expr1 = sympify("tan(2*pi/7)*sin(3*x**2/4)")
        expr2 = sympify("1.2539603*sin(0.75*x**2)")
        self.assertEqual(evalf_expression(expr1,8),
                          evalf_expression(expr2,8))
        self.assertNotEqual(evalf_expression(expr1,9),
                             evalf_expression(expr2,9))


class NormalizeFloatsTests(SimpleTestCase):
    def test_normalize_floats_with_numbers(self):
        x = 2135.205123820581246
        self.assertEqual(normalize_floats(x), 2135.2051238206)
        self.assertEqual(normalize_floats(-52.2343936549283e34), 
                          -52.234393654928e34)
        self.assertEqual(normalize_floats(-52.2349430012313e-27),
                          -52.234943001231e-27)
        # shouldn't change rational numbers
        expr = sympify("3421/24025")
        self.assertEqual(normalize_floats(expr),expr)
        
        # shouldn't change symbols like pi
        expr = sympify("98/152 - 3*pi/2")
        self.assertEqual(normalize_floats(expr),expr)
        expr = sympify("1323423.630302345*pi + 3*E/2")
        expr_normalized = sympify("1323423.6303023*pi + 3*E/2")
        self.assertEqual(normalize_floats(expr), expr_normalized)

    
    def test_normalize_floats_with_symbolic_expressions(self):
        x = Symbol('x')
        self.assertEqual(normalize_floats(x),x)
        expr = 0.1213*x**2.239-332.323*x+23.72
        expr_normalize = 0.1213*x**2.239-332.323*x+23.72
        self.assertEqual(normalize_floats(expr),expr_normalize)
        expr = 0.1219372103487213*x**2.2328104785329-332.3283102574243*x+23.433712364579320
        expr_normalize = -332.32831025742*x + 0.12193721034872*x**2.2328104785329 + 23.433712364579
        self.assertEqual(normalize_floats(expr),expr_normalize)


        from sympy import sin, exp
        from sympy import Symbol as sympy_Symbol
        z = sympy_Symbol('z')

        # normalize expressions can take strings, as it calls sympify first
        self.assertEqual(normalize_floats("3.99*sin(3.12*z)"), 3.99*sin(3.12*z))
        
        # don't normalize rationals inside function
        expr = sympify("cos(3*y/7)")
        self.assertEqual(normalize_floats(expr),expr)
        
        # number won't taken out of exponential
        expr = sympify("43/11+exp(z/3-47/5)")
        self.assertEqual(normalize_floats(expr), expr)

        fivesixths = sympify("5/6")
        self.assertEqual(normalize_floats("7./5-3*exp(5*z/6-7/3.)/13"),
                          1.4-0.022378146430247*exp(fivesixths*z))

        self.assertEqual(normalize_floats("sqrt(x-3.512114)/3"),
                          normalize_floats("(x-3.512114)**0.5/3"))


    def test_normalize_floats_with_symbolic_tuples(self):
        # For tuples, need to call sympify first so sympify is 
        # called a second time in normalize_floats.
        # That way, tuples are converted to Tuples in second pass.
        expr= sympify("(-3/11, sin(2*pi*x)-sin(3*pi/7), sqrt(9/11), sqrt(4*x/2.913-3/2.132))")
        expr_normalize = sympify("(-3/11, sin(2*pi*x)-sin(3*pi/7),  sqrt(9/11), sqrt(1.3731548232063*x - 1.4071294559099))")
        self.assertEqual(normalize_floats(expr),expr_normalize)

