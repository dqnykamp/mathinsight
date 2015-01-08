from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType
from mitesting.math_objects import math_object
from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL, \
    EVALUATE_FULL, SymbolCallable, TupleNoParen
from sympy import Symbol, sympify, Tuple
from numpy import arange, linspace
import re
import six
import random

class TestExpressions(TestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0
            )
            
    def new_expr(self, **kwargs):
        return Expression.objects.create(question=self.q, **kwargs)

    def test_x(self):
        global_dict={}

        expr_x=self.new_expr(name="the_x",expression="x")
        expr_eval = expr_x.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr_eval, math_object("x"))
        self.assertEqual(global_dict, {"the_x": Symbol('x')})

        expr_comb=self.new_expr(name="comb",expression="the_x^2")
        expr_eval2 = expr_comb.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr_eval2, math_object("x^2"))
        self.assertEqual(global_dict, {"the_x": Symbol('x'), 
                                       "comb": Symbol('x')**2})

    def test_with_no_globaL_dict(self):
        expr_x=self.new_expr(name="the_x",expression="x*y")
        expr_eval = expr_x.evaluate(rng=self.rng)
        self.assertEqual(expr_eval, math_object("x*y"))
        

    def test_random_number(self):
        for i in range(10):
            global_dict={}
            test_global_dict = {}

            expr1=self.new_expr(name="a",expression="(1,10)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr1_eval = expr1.evaluate(rng=self.rng, global_dict=global_dict)
            self.assertTrue(expr1_eval in [math_object(n) for n in range(1,11)])
            test_global_dict["a"] = expr1_eval.return_expression()
            self.assertEqual(global_dict, test_global_dict)

            expr2=self.new_expr(name="b",expression="(-2.7,0.9, 0.1)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr2_eval = expr2.evaluate(rng=self.rng, global_dict=global_dict)
            self.assertTrue(expr2_eval in [math_object(round(b,1))
                                           for b in arange(-2.7,1.0, 0.1)])
            test_global_dict["b"] = expr2_eval.return_expression()
            self.assertEqual(global_dict, test_global_dict)

            expr3=self.new_expr(name="c",expression="(b,a, 0.5)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr3_eval = expr3.evaluate(rng=self.rng, global_dict=global_dict)
            c_range = arange(expr2_eval.return_expression(),
                             expr1_eval.return_expression()+0.01, 0.5)
            self.assertTrue(expr3_eval in [math_object(round(c,1))
                                           for c in c_range])

            
    def test_function(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        c=Symbol('c')
        global_dict={}
        test_global_dict = {}
        
        expr1=self.new_expr(name="fun",expression="x^3- 3x",
                            function_inputs="x",
                            expression_type = Expression.FUNCTION)
        fun=expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(fun, x**3-3*x)
        self.assertEqual(global_dict["fun"](y), y**3-3*y)
        self.assertEqual(str(global_dict["fun"]), "fun")

        expr2 = self.new_expr(name="fun2",expression="x-y- c*x*y+y^2",
                            function_inputs="x,y",
                            expression_type = Expression.FUNCTION)
        fun2=expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(fun2, x-y-c*x*y+y**2)
        self.assertEqual(global_dict["fun2"](x,y), x-y-c*x*y+y**2)
        self.assertEqual(global_dict["fun2"](y,x), y-x-c*x*y+x**2)
        self.assertEqual(global_dict["fun2"](y,z), y-z-c*y*z+z**2)
        self.assertEqual(str(global_dict["fun2"]), "fun2")


        expr3=self.new_expr(name="fun3",expression="fun(x)- c*x*y",
                            function_inputs="x,y",
                            expression_type = Expression.FUNCTION)
        fun3=expr3.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(fun3, x**3-3*x -c*x*y)
        self.assertEqual(global_dict["fun3"](x,y), x**3-3*x-c*x*y)
        self.assertEqual(global_dict["fun3"](y,x), y**3-3*y-c*y*x)
        self.assertEqual(global_dict["fun3"](c,4), c**3-3*c-4*c**2)
        self.assertEqual(str(global_dict["fun3"]), "fun3")


    def test_function_name(self):
        x = Symbol('x')
        global_dict={}
        test_dict = {}
        user_function_dict = {}

        expr1=self.new_expr(name="f", expression="f",
                            expression_type = Expression.FUNCTION_NAME)

        f = expr1.evaluate(rng=self.rng, global_dict=global_dict, 
                           user_function_dict=user_function_dict)\
                 .return_expression()
        self.assertEqual(f, SymbolCallable(str("f")))
        test_dict["f"] = f
        self.assertEqual(global_dict, test_dict)
        self.assertEqual(user_function_dict, test_dict)
        

    def test_real_variable(self):
        x_gen = Symbol('x')
        x_real = Symbol('x', real=True)
        global_dict={}

        expr1=self.new_expr(name="xreal", expression="x",
                            expression_type = Expression.REAL_VARIABLE)
        x1 = expr1.evaluate(rng=self.rng, global_dict=global_dict)\
                 .return_expression()

        expr2=self.new_expr(name="xgen", expression="x")
        x2 = expr2.evaluate(rng=self.rng, global_dict=global_dict)\
                 .return_expression()

        self.assertEqual(x_real,x1)
        self.assertEqual(x_gen,x2)
        self.assertNotEqual(x_real,x2)
        self.assertNotEqual(x_gen,x1)
        
        expr3=self.new_expr(name="xmess", expression="x*y",
                            expression_type = Expression.REAL_VARIABLE)
        self.assertRaisesRegexp(ValueError, "Invalid real variable",
                                expr3.evaluate, rng=self.rng,
                                global_dict=global_dict)


    def test_required_condition_ne(self):
        from sympy import Ne
        for i in range(10):
            global_dict={'Ne': Ne}
            expr1=self.new_expr(name="n",expression="(-1,1)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            expr2a=self.new_expr(name="nonzero_n",expression="n",
                                 expression_type = Expression.CONDITION)
            expr2b=self.new_expr(name="nonzero_n2",expression="n != 0",
                                 expression_type = Expression.CONDITION)
            expr2c=self.new_expr(name="nonzero_n3",expression="Ne(n,0)",
                                 expression_type = Expression.CONDITION)
            expr2d=self.new_expr(name="nonzero_n4",expression="n !== 0",
                                 expression_type = Expression.CONDITION)
            if n == 0:
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n was not met",
                                        expr2a.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n2 was not met",
                                        expr2b.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n3 was not met",
                                        expr2c.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n4 was not met",
                                        expr2d.evaluate, rng=self.rng,
                                        global_dict=global_dict)
            else:
                expr2a_eval = expr2a.evaluate(rng=self.rng,global_dict=global_dict)\
                    .return_expression()
                expr2b_eval = expr2b.evaluate(rng=self.rng,global_dict=global_dict)\
                    .return_expression()
                expr2c_eval = expr2c.evaluate(rng=self.rng,global_dict=global_dict)\
                    .return_expression()
                expr2d_eval = expr2d.evaluate(rng=self.rng,global_dict=global_dict)\
                    .return_expression()
                self.assertEqual(expr2a_eval, n)
                self.assertTrue(expr2b_eval)
                self.assertTrue(expr2c_eval)
                self.assertTrue(expr2d_eval)


    def test_required_condition_equal(self):
        from sympy import Eq, Abs
        for i in range(10):
            global_dict={'Eq': Eq, 'Abs': Abs}
            expr1=self.new_expr(name="n",expression="(-2,2)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            expr2a=self.new_expr(name="mag2_n",expression="Abs(n)==2",
                                 expression_type = Expression.CONDITION)
            expr2b=self.new_expr(name="mag2_n2",expression="Eq(Abs(n),2)",
                                 expression_type = Expression.CONDITION)
            expr2c=self.new_expr(name="mag2_n3",expression="n^2==4",
                                 expression_type = Expression.CONDITION)
            expr2d=self.new_expr(name="mag2_n4",expression="n^2=4",
                                 expression_type = Expression.CONDITION)
            if Abs(n) != 2:
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n was not met",
                                        expr2a.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n2 was not met",
                                        expr2b.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n3 was not met",
                                        expr2c.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n4 was not met",
                                        expr2d.evaluate, rng=self.rng,
                                        global_dict=global_dict)
            else:
                expr2a_eval = expr2a.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                expr2b_eval = expr2b.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                expr2c_eval = expr2c.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                expr2d_eval = expr2d.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                self.assertTrue(expr2a_eval)
                self.assertTrue(expr2b_eval)
                self.assertTrue(expr2c_eval)
                self.assertTrue(expr2d_eval)


    def test_required_condition_symbolic_versus_numeric_equality(self):
        from sympy import Eq, Ne
        global_dict={'Ne': Ne, 'Eq': Eq}
        for i in range(10):
            expr1=self.new_expr(name="xx",expression="x,y",
                                expression_type = Expression.RANDOM_EXPRESSION)
            expr2=self.new_expr(name="yy",expression="x,y",
                                expression_type = Expression.RANDOM_EXPRESSION)
            
            expr3a=self.new_expr(name="equal1",expression="xx=yy",
                                 expression_type = Expression.CONDITION)
            expr3b=self.new_expr(name="equal2",expression="xx==yy",
                                 expression_type = Expression.CONDITION)
            expr3c=self.new_expr(name="equal3",expression="Eq(xx,yy)",
                                 expression_type = Expression.CONDITION)
            expr3d=self.new_expr(name="not_equal1",expression="xx!=yy",
                                 expression_type = Expression.CONDITION)
            expr3e=self.new_expr(name="not_equal2",expression="xx!==yy",
                                 expression_type = Expression.CONDITION)
            expr3f=self.new_expr(name="not_equal3",expression="Ne(xx,yy)",
                                 expression_type = Expression.CONDITION)

            x = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            y = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
   
            if x==y:
                expr3a_eval = expr3a.evaluate(rng=self.rng,global_dict=global_dict)\
                                    .return_expression()
                self.assertTrue(expr3a_eval)

                expr3b_eval = expr3b.evaluate(rng=self.rng,global_dict=global_dict)\
                                    .return_expression()
                self.assertTrue(expr3b_eval)

                expr3c_eval = expr3c.evaluate(rng=self.rng,global_dict=global_dict)\
                                    .return_expression()
                self.assertTrue(expr3c_eval)
                

                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal1 was not met",
                                        expr3d.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal2 was not met",
                                        expr3e.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal3 was not met",
                                        expr3f.evaluate, rng=self.rng,
                                        global_dict=global_dict)


            else:

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition xx=yy",
                    expr3a.evaluate, rng=self.rng,
                    global_dict=global_dict)

                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition equal2 was not met",
                                        expr3b.evaluate, rng=self.rng,
                                        global_dict=global_dict)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition Eq\(xx,yy\)",
                    expr3c.evaluate, rng=self.rng,
                    global_dict=global_dict)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition xx!=yy",
                    expr3d.evaluate, rng=self.rng,
                    global_dict=global_dict)

                expr3e_eval = expr3e.evaluate(rng=self.rng,global_dict=global_dict)\
                                    .return_expression()
                self.assertTrue(expr3e_eval)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition Ne\(xx,yy\)",
                    expr3f.evaluate, rng=self.rng,
                    global_dict=global_dict)


    def test_required_condition_complex_inequality(self):
        from sympy import Or, And, Lt, Gt, Le, Ge
        for i in range(10):
            global_dict={'Or': Or, 'And': And, 'Lt': Lt, 'Gt': Gt, 
                         'Le': Le, 'Ge': Ge}
            expr1=self.new_expr(name="n",expression="(-5,5)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            expr2=self.new_expr(name="m",expression="(-5,5)",
                                expression_type = Expression.RANDOM_NUMBER)
            m = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()

            expr3a=self.new_expr(name="inequality1a",expression="Or(m<-1,n>2)",
                                 expression_type = Expression.CONDITION)
            expr3b=self.new_expr(name="inequality1b",
                                 expression="Or(Lt(m,-1),Gt(n,2))",
                                 expression_type = Expression.CONDITION)
            if not (m<-1 or n>2):
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality1a was not met",
                                        expr3a.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality1b was not met",
                                        expr3b.evaluate, rng=self.rng,
                                        global_dict=global_dict)
            else:
                expr3a_eval = expr3a.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                expr3b_eval = expr3b.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                self.assertTrue(expr3a_eval)
                self.assertTrue(expr3b_eval)

            expr4a=self.new_expr(name="inequality2a",
                                 expression="Or(And(n>=-2,n<=2),And(m>-2,m<2))",
                                 expression_type = Expression.CONDITION)
            expr4b=self.new_expr(name="inequality2b",
                                expression="Or(And(Ge(n,-2),Le(n,2))," 
                                 + "And(Gt(m,-2),Lt(m,2)))",
                                expression_type = Expression.CONDITION)
            if not ((n>=-2 and n<=2) or (m>-2 and m<2)):
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality2a was not met",
                                        expr4a.evaluate, rng=self.rng,
                                        global_dict=global_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality2b was not met",
                                        expr4b.evaluate, rng=self.rng,
                                        global_dict=global_dict)
            else:
                expr4a_eval = expr4a.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                expr4b_eval = expr4b.evaluate(rng=self.rng, global_dict=global_dict)\
                    .return_expression()
                self.assertTrue(expr4a_eval)
                self.assertTrue(expr4b_eval)
                
    
    def test_expression(self):
        y=Symbol('y')
        z=Symbol('z')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        
        expr1=self.new_expr(name="quadratic",expression="a*z^2+b*z+c")
        quadratic=expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(quadratic,a*z**2+b*z+c)
        self.assertEqual(global_dict["quadratic"], a*z**2+b*z+c)

        expr2=self.new_expr(name="linear",expression="a*y-b", \
                                expression_type=Expression.GENERIC)
        linear=expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(linear,a*y-b)
        self.assertEqual(global_dict["linear"], a*y-b)
        
    def test_ordered_tuple(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        expr1=self.new_expr(name="tuple1",expression="(a,b,c)")
        tuple1 = expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(tuple1.compare_with_expression((a,b,c))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,c,b))['fraction_equal'],0)
        
        expr2=self.new_expr(name="tuple2",expression="[b,c,a]")
        tuple2 = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
        self.assertEqual(tuple2,[b,c,a])

        
    def test_unordered_tuple(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        expr1=self.new_expr(name="tuple1",expression="(a,b,c)", \
                                expression_type=Expression.UNORDERED_TUPLE)
        tuple1 = expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(tuple1.compare_with_expression((a,b,c))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,c,b))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((b,c,a))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,a,c,b))['fraction_equal'],0)

        expr2=self.new_expr(name="tuple2",expression="[3*a,b-a,c^2]", \
                                expression_type=Expression.UNORDERED_TUPLE)
        tuple2 = expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(tuple2.compare_with_expression([3*a,b-a,c**2])['fraction_equal'],1)
        self.assertEqual(tuple2.compare_with_expression([3*a,c**2,b-a])['fraction_equal'],1)
        self.assertEqual(tuple2.compare_with_expression([b-a,c**2,3*a])['fraction_equal'],1)


    def test_sorted_tuple(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        expr1=self.new_expr(name="tuple1",expression="(5,-1,b^2-a,c,b)", \
                                expression_type=Expression.SORTED_TUPLE)
        tuple1 = expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(tuple1.compare_with_expression((-1,5,b,c,b**2-a))['fraction_equal'],1)

        expr2=self.new_expr(name="tuple2",expression="[5,-1,b^2-a,c,b]", \
                                expression_type=Expression.SORTED_TUPLE)
        tuple2 = expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(tuple2.compare_with_expression([-1,5,b,c,b**2-a])['fraction_equal'],1)


    def test_random_order_tuple(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        expr1=self.new_expr(name="tuple1",expression="(5,-1,b^2-a,c,b)", \
                                expression_type=Expression.RANDOM_ORDER_TUPLE)
        tuple_orig = (5, -1, b**2-a,c,b)
        found_different_order = False
        for i in range(100):
            tuple1 = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            for j in range(5):
                self.assertTrue(tuple1[j] in tuple_orig)
            if tuple1 != tuple_orig:
                found_different_order=True
                break
        self.assertTrue(found_different_order)

        expr2=self.new_expr(name="tuple2",expression="[5,-1,b^2-a,c,b]", \
                                expression_type=Expression.RANDOM_ORDER_TUPLE)
        tuple_orig = (5, -1, b**2-a,c,b)
        found_different_order = False
        for i in range(100):
            tuple2 = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            for j in range(5):
                self.assertTrue(tuple2[j] in tuple_orig)
            if tuple2 != tuple_orig:
                found_different_order=True
                break
        self.assertTrue(found_different_order)


    def test_tuple_no_parentheses(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        global_dict={}
        expr1=self.new_expr(name="t1",expression="a,b,c")
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr1_eval, TupleNoParen(a,b,c))
        self.assertNotEqual(expr1_eval, Tuple(a,b,c))

        expr2=self.new_expr(name="t1",expression="(a,b,c)")
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, Tuple(a,b,c))
        self.assertNotEqual(expr2_eval, TupleNoParen(a,b,c))

        expr3=self.new_expr(name="t1",expression="(a+1)*b,b,a*(1-c)")
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr3_eval, TupleNoParen((a+1)*b,b,a*(1-c)))
        self.assertNotEqual(expr3_eval, Tuple((a+1)*b,b,a*(1-c)))

    def test_sets(self):
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        d=Symbol('d')
        global_dict={}
        expr1=self.new_expr(name="t1",expression="b,c,a,c,d,a",
                            expression_type=Expression.SET)
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertTrue(expr1_eval.return_if_unordered())
        self.assertEqual(expr1_eval.compare_with_expression(
            TupleNoParen(a,b,c,d))['fraction_equal'],1)

        expr2=self.new_expr(name="t2",expression="{b,c,a,c,d,a}",
                            expression_type=Expression.SET)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, {c,d,a,b})

        expr3=self.new_expr(name="t3",expression="{b,c,a,c,d,a}")
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr3_eval, {c,d,a,b})

    def test_single_interval(self):
        from sympy import Interval
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        global_dict={'a': a, 'b': b}

        expr1=self.new_expr(name="open", expression="(a,b)",
                            expression_type=Expression.INTERVAL)
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr1_eval, \
                         Interval(a,b,left_open=True, right_open=True))

        expr2=self.new_expr(name="left_open", expression="(a,b]",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, \
                         Interval(a,b,left_open=True, right_open=False))

        expr3=self.new_expr(name="right_open", expression="[a,b)",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr3_eval, \
                         Interval(a,b,left_open=False, right_open=True))

        expr4=self.new_expr(name="closed", expression="[a,b]",
                            expression_type=Expression.INTERVAL)
        expr4_eval=expr4.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr4_eval, \
                         Interval(a,b,left_open=False, right_open=False))

    def test_interval_combinations(self):
        from sympy import Interval
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        global_dict={'a': a, 'b': b}

        expr1=self.new_expr(name="inttuple", expression="[a,b),(1,3]",
                            expression_type=Expression.INTERVAL)
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr1_eval, \
            TupleNoParen(Interval(a,b,left_open=False, right_open=True),\
                          Interval(1,3,left_open=True, right_open=False)))

        expr2=self.new_expr(name="inttuple2", expression="([a,b),(1,3])",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, \
            Tuple(Interval(a,b,left_open=False, right_open=True),\
                  Interval(1,3,left_open=True, right_open=False)))

        expr2=self.new_expr(name="inttuple2", expression="([a,b),(1,3])",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, \
            Tuple(Interval(a,b,left_open=False, right_open=True),\
                  Interval(1,3,left_open=True, right_open=False)))

        expr3=self.new_expr(name="union", expression="[a,b)+(1,3]",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        from sympy import Union
        self.assertEqual(expr3_eval, \
                Union(Interval(a,b,left_open=False, right_open=True),\
                      Interval(1,3,left_open=True, right_open=False)))

    def test_interval_errors(self):
        from sympy import Interval
        a=Symbol('a')
        b=Symbol('b')
        global_dict={'a': a, 'b': b}
        expr1=self.new_expr(name="open", expression="(a,b)",
                            expression_type=Expression.INTERVAL)
        self.assertRaisesRegexp(ValueError, "Variables used in intervals must be real",
                                expr1.evaluate, rng=self.rng, 
                                global_dict=global_dict)

        global_dict={}
        self.assertRaisesRegexp(ValueError, "Variables used in intervals must be real",
                                expr1.evaluate, rng=self.rng, 
                                global_dict=global_dict)

        expr2=self.new_expr(name="invalidint", expression="(1,2,3)",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval, Tuple(1,2,3))

        expr3=self.new_expr(name="invalidint2", expression="(1,2,3),[4,5]",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr3_eval, TupleNoParen(Tuple(1,2,3),Interval(4,5)))

        
    def test_evaluate_false(self):
        global_dict={}
        expr1=self.new_expr(name="s", expression="x+x*y*x+x")
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(six.text_type(expr1_eval), "x^{2} y + 2 x")
        expr2=self.new_expr(name="s2", expression="x+x*y*x+x", 
                            evaluate_level=EVALUATE_NONE)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(six.text_type(expr2_eval), "x x y + x + x")
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal_on_normalize'],1)
        self.assertEqual(expr1_eval.compare_with_expression(
                expr2_eval.return_expression())['fraction_equal'],1)

    def test_evaluate_partial(self):
        from sympy import Derivative, Integral
        x=Symbol('x')
        global_dict={'Derivative': Derivative, 'Integral': Integral}
        expr1=self.new_expr(name="s", expression="Derivative(x^2,x)")
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr1_eval.return_expression(), 2*x)
        expr2=self.new_expr(name="s2", expression="Derivative(x^2,x)", 
                            evaluate_level=EVALUATE_PARTIAL)
        expr2_eval=expr2.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr2_eval.return_expression(), Derivative(x**2,x))
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal_on_normalize'],1)
        self.assertEqual(expr1_eval.compare_with_expression(
                expr2_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr1_eval.compare_with_expression(
                expr2_eval.return_expression())['fraction_equal_on_normalize'],1)

        expr3=self.new_expr(name="s3", expression="Integral(x^2,x)")
        expr3_eval=expr3.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr3_eval.return_expression(), x**3/3)
        expr4=self.new_expr(name="s4", expression="Integral(x^2,x)", 
                            evaluate_level=EVALUATE_PARTIAL)
        expr4_eval=expr4.evaluate(rng=self.rng, global_dict=global_dict)
        self.assertEqual(expr4_eval.return_expression(), Integral(x**2,x))
        self.assertEqual(expr4_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr4_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal_on_normalize'],1)
        self.assertEqual(expr3_eval.compare_with_expression(
                expr4_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr3_eval.compare_with_expression(
                expr4_eval.return_expression())['fraction_equal_on_normalize'],1)


    def test_function_global_dict(self):
        from sympy import sin
        x=Symbol('x')
        expr1=self.new_expr(name="s", expression="x*sin(x)")
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict={})
        self.assertEqual(expr1_eval, x**2*Symbol('sin'))
        expr1_eval=expr1.evaluate(rng=self.rng, global_dict={'sin':sin})
        self.assertEqual(expr1_eval, x*sin(x))


    def test_greek(self):
        expr = self.new_expr(name="greek", 
                             expression="lambda*gamma/delta + epsilon")
        expr_eval=expr.evaluate(rng=self.rng)
        self.assertEqual(expr_eval, Symbol('lambda')*Symbol('gamma') \
                             / Symbol('delta') + Symbol('epsilon'))
        self.assertEqual(six.text_type(expr_eval),
                         r'\epsilon + \frac{\gamma \lambda}{\delta}')


    def test_errors(self):
        symqq = Symbol('??')
        global_dict={}
        expr1=self.new_expr(name="a", expression="(")
        self.assertRaisesRegexp(ValueError, 'Error in expression: a', 
                                expr1.evaluate, rng=self.rng, 
                                global_dict=global_dict)
        self.assertEqual(global_dict['a'],symqq)
        self.assertRaisesRegexp(ValueError, 'Error in expression: a', 
                                expr1.evaluate, rng=self.rng)

        expr2=self.new_expr(name="b", expression="x-+/x", 
                            expression_type=Expression.CONDITION)
        self.assertRaisesRegexp(ValueError, 'Error in expression: b', 
                                expr2.evaluate, rng=self.rng, 
                                global_dict=global_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for condition', 
                                expr2.evaluate, rng=self.rng,
                                global_dict=global_dict)
        self.assertEqual(global_dict['b'],symqq)

        expr3=self.new_expr(name="c", expression="x[0]", 
                            expression_type=Expression.FUNCTION)
        self.assertRaisesRegexp(ValueError, 'Error in expression: c', 
                                expr3.evaluate, rng=self.rng,
                                global_dict=global_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for function', 
                                expr3.evaluate, rng=self.rng,
                                global_dict=global_dict)
        self.assertEqual(global_dict['c'],symqq)

        from sympy import sin
        global_dict['sin']=sin
        expr4=self.new_expr(name="d", expression="(x+sin, y-sin)", 
                            expression_type=Expression.UNORDERED_TUPLE)
        self.assertRaisesRegexp(ValueError, 'Error in expression: d', 
                                expr4.evaluate, rng=self.rng,
                                global_dict=global_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for tuple', 
                                expr4.evaluate, rng=self.rng,
                                global_dict=global_dict)
        self.assertEqual(global_dict['d'],symqq)


class TestRandomFromList(TestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0
            )
            
    def new_expr(self, **kwargs):
        return Expression.objects.create(question=self.q, **kwargs)

    def test_random_word(self):
        for i in range(10):
            global_dict={}
            test_global_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = Expression.RANDOM_WORD)
            expr1_eval = expr1.evaluate(rng=self.rng, global_dict=global_dict)
            self.assertTrue(expr1_eval in [("a","as"),("b","bs"),("c","cs"),
                                           ("d","ds"),("e","es"),("f","fs")])
            test_global_dict["a"] = Symbol(expr1_eval[0])
            self.assertEqual(global_dict, test_global_dict)

            expr2=self.new_expr(name="b",
                                expression="cat, (pony,ponies), (goose,geese)",
                                expression_type = Expression.RANDOM_WORD)
            expr2_eval = expr2.evaluate(rng=self.rng, global_dict=global_dict)
            self.assertTrue(expr2_eval in [("cat","cats"),("pony","ponies"),
                                           ("goose","geese")])
            test_global_dict["b"] = Symbol(expr2_eval[0])
            self.assertEqual(global_dict, test_global_dict)

            expr3=self.new_expr(name="c",
                                expression="\"the pit\",(&^%$#@!,_+*&<?),"
                                + '(one, "one/two or more")',
                                expression_type = Expression.RANDOM_WORD)
            expr3_eval = expr3.evaluate(rng=self.rng, global_dict=global_dict)
            self.assertTrue(expr3_eval in [
                    ("the pit", "the pits"),('&^%$#@!','_+*&<?'),
                    ('one', "one/two or more")])
            test_global_dict["c"] = Symbol(re.sub(' ', '_', expr3_eval[0]))
            self.assertEqual(global_dict, test_global_dict)


    def test_random_expression(self):
        x = Symbol('x')
        for i in range(10):
            global_dict={}
            test_global_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = Expression.RANDOM_EXPRESSION)
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [sympify(item) for item in
                                  ("a","b","c","d","e","f")])
            test_global_dict["a"] = a
            self.assertEqual(global_dict, test_global_dict)
    
            expr2=self.new_expr(name="b",expression="2*a*x, -3*a/x^3, a-x",
                                expression_type = Expression.RANDOM_EXPRESSION)
            b = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(b in [2*a*x, -3*a/x**3,a-x])
            test_global_dict["b"] = b
            self.assertEqual(global_dict, test_global_dict)

            expr3=self.new_expr(name="c",expression="2*b^2, (a-b)/x",
                                expression_type = Expression.RANDOM_EXPRESSION)
            c = expr3.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(c in [2*b**2, (a-b)/x]),
            test_global_dict["c"] = c
            self.assertEqual(global_dict, test_global_dict)

    def test_random_expression_evaluate_level(self):
        from sympy import Derivative, Integral
        x = Symbol('x')
        global_dict={'Derivative': Derivative }

        for i in range(10):
            expr1=self.new_expr(name="a",expression=
                                "x+x, Derivative(x^3,x), 5(x-3)",
                                expression_type = Expression.RANDOM_EXPRESSION)
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [2*x, 3*x**2, 5*x-15])

            expr1.evaluate_level = EVALUATE_FULL
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [2*x, 3*x**2, 5*x-15])

            expr1.evaluate_level = EVALUATE_PARTIAL
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [2*x, Derivative(x**3,x), 5*x-15])
            
            expr1.evaluate_level = EVALUATE_NONE
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(six.text_type(a) in 
                            ['x + x', 'Derivative(x**3, x)', '5*(x - 3)'])

    def test_random_function_name(self):
        x = Symbol('x')
        for i in range(10):
            global_dict={}
            test_global_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = 
                                Expression.RANDOM_FUNCTION_NAME)
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [SymbolCallable(str(item)) for item in
                                  ("a","b","c","d","e","f")])
            test_global_dict["a"] = a
            self.assertEqual(global_dict, test_global_dict)
    
            expr2=self.new_expr(name="b",expression="2*a(x)-4")
            b = expr2.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertEqual(b, 2*a(x)-4)
            test_global_dict["b"] = b
            self.assertEqual(global_dict, test_global_dict)

            user_function_dict = {}
            expr3=self.new_expr(name="f",expression="this, that, the,other",
                                expression_type = 
                                Expression.RANDOM_FUNCTION_NAME)
            f = expr3.evaluate(rng=self.rng, global_dict=global_dict, \
                                   user_function_dict=user_function_dict)\
                                   .return_expression()
            self.assertTrue(f in [SymbolCallable(str(item)) for item in
                                  ("this","that","the","other")])
            self.assertEqual( user_function_dict , { str(f): f})
            test_global_dict["f"] = f
            self.assertEqual(global_dict, test_global_dict)

            
    def test_random_real_variable(self):
        x = Symbol('x')
        for i in range(10):
            global_dict={}
            test_global_dict={}
            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = 
                                Expression.RANDOM_REAL_VARIABLE)
            a = expr1.evaluate(rng=self.rng, global_dict=global_dict).return_expression()
            self.assertTrue(a in [Symbol(str(item),real=True) for item in
                                  ("a","b","c","d","e","f")])
            test_global_dict["a"] = a
            self.assertEqual(global_dict, test_global_dict)
            
            expr2=self.new_expr(name="amess", expression="a*b, c+d, e/f, g-h",
                            expression_type = Expression.RANDOM_REAL_VARIABLE)
            self.assertRaisesRegexp(ValueError, "Invalid real variable",
                                    expr2.evaluate, rng=self.rng,
                                    global_dict=global_dict)


    def test_random_list_groups_match(self):
        for i in range(10):
            random_group_indices = {}
            global_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                global_dict=global_dict, 
                random_group_indices=random_group_indices)[0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g1")
            re1 = expr2.evaluate(rng=self.rng, 
                global_dict=global_dict,
                random_group_indices=random_group_indices).return_expression()
            
            expr3=self.new_expr(name="rf1",expression="a,b, c ,d,e", 
                                expression_type =
                                Expression.RANDOM_FUNCTION_NAME,
                                random_list_group="g1")
            rf1 = expr3.evaluate(rng=self.rng, 
                global_dict=global_dict,
                random_group_indices=random_group_indices).return_expression()

            self.assertTrue((rw1,re1,rf1) in [
                    (item, Symbol(item), SymbolCallable(str(item)))
                    for item in ["a","b","c","d","e"]])

            
    def test_random_list_groups_some_match(self):
        found_non_match=False
        for i in range(100):
            random_group_indices = {}
            global_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                global_dict=global_dict, 
                random_group_indices=random_group_indices)[0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g2")
            re1 = expr2.evaluate(rng=self.rng, 
                global_dict=global_dict,
                random_group_indices=random_group_indices).return_expression()
            
            expr3=self.new_expr(name="rf1",expression="a,b, c ,d,e", 
                                expression_type =
                                Expression.RANDOM_FUNCTION_NAME,
                                random_list_group="g1")
            rf1 = expr3.evaluate(rng=self.rng, 
                global_dict=global_dict,
                random_group_indices=random_group_indices).return_expression()

            self.assertTrue((rw1,rf1) in [
                    (item, SymbolCallable(str(item)))
                    for item in ["a","b","c","d","e"]])

            if str(re1) != rw1:
                found_non_match=True
                break
        
        self.assertTrue(found_non_match)    
            

    def test_random_list_groups_different_lengths(self):
        for i in range(10):
            random_group_indices = {}
            global_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                global_dict=global_dict, 
                random_group_indices=random_group_indices)[0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g1")
            re1 = expr2.evaluate(rng=self.rng, 
                global_dict=global_dict,
                random_group_indices=random_group_indices).return_expression()
            
            self.assertTrue((rw1,re1) in [
                    (item, Symbol(item))
                    for item in ["a","b","c"]])


        with self.assertRaisesRegexp(IndexError, 
                                     'Insufficient entries for random list group: g1'):
            for i in range(100):
                random_group_indices = {}
                global_dict = {}
                expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                    expression_type = Expression.RANDOM_WORD,
                                    random_list_group="g1")
                rw1 = expr1.evaluate(rng=self.rng, 
                    global_dict=global_dict, 
                    random_group_indices=random_group_indices)[0]
                
                expr2=self.new_expr(name="re1",expression="a,b, c",
                                    expression_type =
                                    Expression.RANDOM_EXPRESSION,
                                    random_list_group="g1")
                re1 = expr2.evaluate(rng=self.rng,  \
                    global_dict=global_dict, \
                        random_group_indices=random_group_indices) \
                        .return_expression()
                    
                self.assertTrue((rw1,re1) in [
                        (item, Symbol(item))
                        for item in ["a","b","c"]])
            


class TestExpressionSortOrder(TestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()

    def test_sort_order(self):
        qt = QuestionType.objects.create(name="question type")
        q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0,
            )
            
        e1 = q.expression_set.create(name="a", expression="a")
        self.assertEqual(e1.sort_order, 1)

        e2 = q.expression_set.create(name="b", expression="b")
        self.assertEqual(e2.sort_order, 2)
        
        e3 = q.expression_set.create(name="c", expression="c", sort_order=10)
        self.assertEqual(e3.sort_order, 10)
        
        e4 = q.expression_set.create(name="d", expression="d")
        self.assertEqual(e4.sort_order, 11)
        
        e1.sort_order=21.2
        e1.save()

        e5 = q.expression_set.create(name="e", expression="e")
        self.assertEqual(e5.sort_order, 23)

        e3.sort_order=-100
        e3.save()

        e6 = q.expression_set.create(name="f", expression="f")
        self.assertEqual(e6.sort_order, 24)

        e6.delete()
        e5.delete()
        e1.sort_order=9
        e1.save()

        e7 = q.expression_set.create(name="g", expression="g")
        self.assertEqual(e7.sort_order, 12)

# add test with post user response


"""
post user response tests

Test required condition is invalid

Test that user response comes after others (maybe above instead?)


"""
