from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, QuestionPermission, SympyCommandSet

from sympy import Symbol, sympify, Function
import random


class TestSetupExpressionContext(TestCase):
    def setUp(self):
        qt = QuestionType.objects.create(name="question type")
        qp = QuestionPermission.objects.create(name="Public")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_permission = qp,
            )
            
    def new_expr(self, **kwargs):
        return Expression.objects.create(question=self.q, **kwargs)


    def test_with_single_expression(self):
        self.new_expr(name="the_x",expression="x")

        random.seed(0)
        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        self.assertEqual(expression_context['the_x'], Symbol('x'))
        self.assertEqual(results['sympy_global_dict']['the_x'], Symbol('x'))

    def test_with_composed_expressions(self):
        self.new_expr(name="expr",expression="x*x")
        self.new_expr(name="expr2",expression="expr/y")
        self.new_expr(name="expr3",expression="5*expr2 + expr*z")

        random.seed(1)
        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        self.assertEqual(expression_context['expr'], x**2)
        self.assertEqual(expression_context['expr2'], x**2/y)
        self.assertEqual(expression_context['expr3'], 5*x**2/y + x**2*z)
        self.assertEqual(results['sympy_global_dict']['expr'], x**2)
        self.assertEqual(results['sympy_global_dict']['expr2'], x**2/y)
        self.assertEqual(results['sympy_global_dict']['expr3'],
                         5*x**2/y + x**2*z)

 
    def test_overwriting_expressions(self):
        self.new_expr(name="a",expression="z/y")
        self.new_expr(name="b",expression="3*a")
        self.new_expr(name="a",expression="x+y")

        random.seed(2)
        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        self.assertEqual(expression_context['a'], x+y)
        self.assertEqual(expression_context['b'], 3*z/y)
        self.assertEqual(results['sympy_global_dict']['a'], x+y)
        self.assertEqual(results['sympy_global_dict']['b'], 3*z/y)


    def test_with_function_names(self):
        self.new_expr(name="f",expression="f,g,h,k", 
                      expression_type = Expression.RANDOM_FUNCTION_NAME)
        self.new_expr(name="a",expression="3*f(x)+2")

        for i in range(10):
            results=self.q.setup_expression_context()
            self.assertTrue(results['user_function_dict'] in  \
                                [{item: Function(str(item))} for item in \
                                     ['f','g','h','k']])
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=Symbol('x')
            f = expression_context['f'].return_expression()
            self.assertTrue(f in [Function(str(item)) for item in \
                                      ['f','g','h','k']])
            self.assertEqual(expression_context['a'], 3*f(x)+2)
            self.assertEqual(results['sympy_global_dict']['f'], f)
            self.assertEqual(results['sympy_global_dict']['a'], 3*f(x)+2)

    
    def test_conditions(self):
        self.new_expr(name="m", expression="(-4,4)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="n", expression="(-4,4)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="m_greater_than_n", expression="m > n", 
                      expression_type = Expression.CONDITION)
        self.new_expr(name="m_nonzero", expression="m", 
                      expression_type = Expression.CONDITION)
        self.new_expr(name="n_nonzero", expression="n != 0", 
                      expression_type = Expression.CONDITION)
        
        for i in range(10):
            results=self.q.setup_expression_context()
            self.assertEqual(results['user_function_dict'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=Symbol('x')
            m = expression_context['m'].return_expression()
            n = expression_context['n'].return_expression()
            self.assertTrue(m > n)
            self.assertTrue(m != 0)
            self.assertTrue(n != 0)
            self.assertTrue(m in range(-4, 5))
            self.assertTrue(n in range(-4, 5))
            self.assertEqual(results['sympy_global_dict']['m'], m)
            self.assertEqual(results['sympy_global_dict']['n'], n)

    def test_fail_conditions(self):
        self.new_expr(name="n", expression="(-4,4)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="n_greater_than_4", expression="n > 4", 
                      expression_type = Expression.CONDITION)

        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertTrue(results['failed_conditions'])
        self.assertEqual("Condition n_greater_than_4 was not met",
                         results['failed_condition_message'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        n = expression_context['n'].return_expression()
        self.assertTrue(n in range(-4, 5))
        self.assertEqual(results['sympy_global_dict']['n'], n)


    def test_repeatable_results(self):
        self.new_expr(name="x", expression="x,y,z,u,v,w", 
                      expression_type = Expression.RANDOM_EXPRESSION)
        self.new_expr(name="y", expression="x,y,z,u,v,w", 
                      expression_type = Expression.RANDOM_EXPRESSION)
        self.new_expr(name="m", expression="(-10,10)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="n", expression="(-10,10)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="x_not_equal_y", expression="x !=y", 
                      expression_type = Expression.CONDITION)
        self.new_expr(name="n_greater_than_m", expression="n > m", 
                      expression_type = Expression.CONDITION)

        for i in range(10):
            seed=self.q.get_new_seed()
            random.seed(seed)
            results=self.q.setup_expression_context()
            self.assertEqual(results['user_function_dict'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=expression_context["x"]
            y=expression_context["y"]
            m=expression_context["m"]
            n=expression_context["n"]
            self.assertTrue(x != y)
            self.assertTrue(n > m)
            self.assertTrue(x in [Symbol(item) for item in 
                                  ["x","y","z","u","v","w"]])
            self.assertTrue(y in [Symbol(item) for item in 
                                  ["x","y","z","u","v","w"]])
            self.assertTrue(m in range(-10,11))
            self.assertTrue(n in range(-10,11))
        
            #try again with same seed
            random.seed(seed)
            results=self.q.setup_expression_context()
            self.assertEqual(results['user_function_dict'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            self.assertEqual(x,expression_context["x"])
            self.assertEqual(y,expression_context["y"])
            self.assertEqual(m,expression_context["m"])
            self.assertEqual(n,expression_context["n"])


    def test_with_error(self):
        self.new_expr(name="x", expression="(")
        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertTrue(results['error_in_expressions'])
        expression_error = results['expression_error']
        self.assertTrue("Error in expression x" in expression_error['x'])
        self.assertEqual("??", results['expression_context']['x'])
        self.assertEqual(Symbol("??"), results['sympy_global_dict']['x'])

    def test_with_multiple_errors(self):
        self.new_expr(name="e1", expression="3*x^2/z")
        self.new_expr(name="e2", expression="e1[0]+y")
        self.new_expr(name="e3", expression="e2*e1+z")
        self.new_expr(name="e4", expression="e3/")
        self.new_expr(name="e5", expression="e2/e1 + e3/e4")

        results=self.q.setup_expression_context()
        self.assertEqual(results['user_function_dict'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertTrue(results['error_in_expressions'])
        expression_error = results['expression_error']
        self.assertTrue("Error in expression e2" in expression_error['e2'])
        self.assertTrue("Error in expression e4" in expression_error['e4'])
        self.assertEqual(expression_error.get('e1'), None)
        self.assertEqual(expression_error.get('e3'), None)
        self.assertEqual(expression_error.get('e5'), None)
        x=Symbol("x")
        z=Symbol("z")
        q=Symbol("??")
        expr_context=results['expression_context']
        self.assertEqual(expr_context['e1'], 3*x**2/z)
        self.assertEqual(expr_context['e2'], "??")
        self.assertEqual(expr_context['e3'], q*3*x**2/z+z)
        self.assertEqual(expr_context['e4'], "??")
        self.assertEqual(expr_context['e5'],q/(3*x**2/z)+(q*3*x**2/z+z)/q)
        self.assertEqual(Symbol("??"), results['sympy_global_dict']['e2'])
        self.assertEqual(Symbol("??"), results['sympy_global_dict']['e2'])
        self.assertEqual(Symbol("??"), results['sympy_global_dict']['e2'])


    def add_allowed_sympy_commands_sets(self, command_sets):

        if 'trig' in command_sets:
            scs_trig = SympyCommandSet.objects.create(
                name = 'trig', 
                commands='acosh, acos, acosh, acot, acoth, asin, asinh, atan, '
                + 'atan2, atanh, cos,  cosh, cot, coth, csc, sec, sin, sinh, '
                + 'tan, tanh')
            self.q.allowed_sympy_commands.add(scs_trig)
        if 'explog' in command_sets:
            scs_explog = SympyCommandSet.objects.create(
                name = 'explog', commands='exp,ln,log,e')
            self.q.allowed_sympy_commands.add(scs_explog)
        if 'absminmax' in command_sets:
            scs_absminmax = SympyCommandSet.objects.create(
                name = 'absminmax', commands='abs, min, max')
            self.q.allowed_sympy_commands.add(scs_absminmax)
        if 'other' in command_sets:
            scs_other = SympyCommandSet.objects.create(
                name = 'other', commands='iif, index, len')
            self.q.allowed_sympy_commands.add(scs_other)


    def test_command_set_inclusion(self):
        x=Symbol('x')
        from sympy import sin, cos, log, exp
        self.new_expr(name="sincos", expression="sin(x)*cos(x)")
        self.new_expr(name="explog1", expression="exp(x)*log(x)")
        self.new_expr(name="explog2", expression="e^x*ln(x)")

        results=self.q.setup_expression_context()
        self.assertEqual(Symbol('sin')*Symbol('cos')*x**2,
                         results['expression_context']["sincos"])
        self.assertEqual(Symbol('sin')*Symbol('cos')*x**2,
                         results['sympy_global_dict']["sincos"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         results['expression_context']["explog1"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         results['sympy_global_dict']["explog1"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         results['expression_context']["explog2"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         results['sympy_global_dict']["explog2"])

        self.add_allowed_sympy_commands_sets(['trig'])
        results=self.q.setup_expression_context()
        self.assertEqual(sin(x)*cos(x),
                         results['expression_context']["sincos"])
        self.assertEqual(sin(x)*cos(x),
                         results['sympy_global_dict']["sincos"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         results['expression_context']["explog1"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         results['sympy_global_dict']["explog1"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         results['expression_context']["explog2"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         results['sympy_global_dict']["explog2"])
       
        self.add_allowed_sympy_commands_sets(['explog'])
        results=self.q.setup_expression_context()
        self.assertEqual(sin(x)*cos(x),
                         results['expression_context']["sincos"])
        self.assertEqual(sin(x)*cos(x),
                         results['sympy_global_dict']["sincos"])
        self.assertEqual(exp(x)*log(x),
                         results['expression_context']["explog1"])
        self.assertEqual(exp(x)*log(x),
                         results['sympy_global_dict']["explog1"])
        self.assertEqual(exp(x)*log(x),
                         results['expression_context']["explog2"])
        self.assertEqual(exp(x)*log(x),
                         results['sympy_global_dict']["explog2"])

        
    
    def test_customized_command_inclusion(self):
        self.new_expr(name="n", expression="(-10,10)",
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="abs_n", expression="abs(n)")
        self.new_expr(name="large_n", expression="abs_n > 3",
                      expression_type = Expression.CONDITION)
        self.new_expr(name="fun_n", expression = \
                          "iif(abs_n > 5, min(0, n), max(0,n))")

        self.add_allowed_sympy_commands_sets(['absminmax', 'other'])

        for i in range(10):
            results=self.q.setup_expression_context()

            expr_context = results['expression_context']
            n = expr_context['n'].return_expression()
            self.assertTrue(n in range(-10,-3) + range(4,11))
            if abs(n) > 5:
                self.assertEqual(min(0,n), expr_context['fun_n'])
            else:
                self.assertEqual(max(0,n), expr_context['fun_n'])



