from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType
from mitesting.math_objects import math_object
from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL, \
    EVALUATE_FULL, SymbolCallable, TupleNoParen, Interval, \
    FiniteSet, Symbol
from sympy import sympify, Tuple
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
        x=Symbol('x', real=True)
        local_dict={}

        expr_x=self.new_expr(name="the_x",expression="x")
        expr_eval = expr_x.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr_eval, x)
        self.assertEqual(local_dict, {"the_x": x})

        expr_comb=self.new_expr(name="comb",expression="the_x^2")
        expr_eval2 = expr_comb.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr_eval2, x**2)
        self.assertEqual(local_dict, {"the_x": x,"comb": x**2})

    def test_with_no_local_dict(self):
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        expr_x=self.new_expr(name="the_x",expression="x*y")
        expr_eval = expr_x.evaluate(rng=self.rng)['expression_evaluated']
        self.assertEqual(expr_eval, x*y)
        

    def test_random_number(self):
        for i in range(10):
            local_dict={}
            test_local_dict = {}

            expr1=self.new_expr(name="a",expression="(1,10)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr1_eval = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            self.assertTrue(expr1_eval in [math_object(n) for n in range(1,11)])
            test_local_dict["a"] = expr1_eval.return_expression()
            self.assertEqual(local_dict, test_local_dict)

            expr2=self.new_expr(name="b",expression="(-2.7,0.9, 0.1)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr2_eval = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            self.assertTrue(expr2_eval in [math_object(round(b,1))
                                           for b in arange(-2.7,1.0, 0.1)])
            test_local_dict["b"] = expr2_eval.return_expression()
            self.assertEqual(local_dict, test_local_dict)

            expr3=self.new_expr(name="c",expression="(b,a, 0.5)",
                                expression_type = Expression.RANDOM_NUMBER)
            expr3_eval = expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            c_range = arange(expr2_eval.return_expression(),
                             expr1_eval.return_expression()+0.01, 0.5)
            self.assertTrue(expr3_eval in [math_object(round(c,1))
                                           for c in c_range])

            
    def test_function(self):
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        test_local_dict = {}
        
        expr1=self.new_expr(name="fun",expression="x^3- 3x",
                            function_inputs="x",
                            expression_type = Expression.FUNCTION)
        fun=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(fun, x**3-3*x)
        self.assertEqual(local_dict["fun"](y), y**3-3*y)
        self.assertEqual(str(local_dict["fun"]), "fun")

        expr2 = self.new_expr(name="fun2",expression="x-y- c*x*y+y^2",
                            function_inputs="x,y",
                            expression_type = Expression.FUNCTION)
        fun2=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(fun2, x-y-c*x*y+y**2)
        self.assertEqual(local_dict["fun2"](x,y), x-y-c*x*y+y**2)
        self.assertEqual(local_dict["fun2"](y,x), y-x-c*x*y+x**2)
        self.assertEqual(local_dict["fun2"](y,z), y-z-c*y*z+z**2)
        self.assertEqual(str(local_dict["fun2"]), "fun2")


        expr3=self.new_expr(name="fun3",expression="fun(x)- c*x*y",
                            function_inputs="x,y",
                            expression_type = Expression.FUNCTION)
        fun3=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(fun3, x**3-3*x -c*x*y)
        self.assertEqual(local_dict["fun3"](x,y), x**3-3*x-c*x*y)
        self.assertEqual(local_dict["fun3"](y,x), y**3-3*y-c*y*x)
        self.assertEqual(local_dict["fun3"](c,4), c**3-3*c-4*c**2)
        self.assertEqual(str(local_dict["fun3"]), "fun3")

        expr4=self.new_expr(name="fun_mapped", expression="map(fun, [x,y,5])")
        local_dict['map']=map
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        the_fun = local_dict['fun']
        self.assertEqual(expr4_eval, [the_fun(x), the_fun(y), the_fun(5)])
        

    def test_function_name(self):
        x = Symbol('x', real=True)
        local_dict={}
        test_dict = {}
        user_function_dict = {}

        expr1=self.new_expr(name="f", expression="f",
                            expression_type = Expression.FUNCTION_NAME)

        f = expr1.evaluate(rng=self.rng, local_dict=local_dict, 
                           user_function_dict=user_function_dict)['expression_evaluated']\
                 .return_expression()
        self.assertEqual(f, SymbolCallable(str("f"), real=True))
        test_dict["f"] = f
        self.assertEqual(local_dict, test_dict)
        self.assertEqual(user_function_dict, test_dict)
        

    def test_real_variable(self):
        x_gen = Symbol('x')
        x_real = Symbol('x', real=True)
        local_dict={}

        expr1=self.new_expr(name="xreal", expression="x")
        x1 = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                 .return_expression()

        expr2=self.new_expr(name="xgen", expression="x", real_variables=False)
        x2 = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                 .return_expression()

        expr3=self.new_expr(name="xgen", expression="x", real_variables=True)
        x3 = expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                 .return_expression()

        self.assertEqual(x_real,x1)
        self.assertEqual(x_gen,x2)
        self.assertEqual(x_real,x3)
        self.assertNotEqual(x_gen,x3)
        self.assertNotEqual(x_real,x2)
        self.assertNotEqual(x_gen,x1)
        

    def test_required_condition_ne(self):
        from sympy import Ne
        for i in range(10):
            local_dict={'Ne': Ne}
            expr1=self.new_expr(name="n",expression="(-1,1)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
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
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n2 was not met",
                                        expr2b.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n3 was not met",
                                        expr2c.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition nonzero_n4 was not met",
                                        expr2d.evaluate, rng=self.rng,
                                        local_dict=local_dict)
            else:
                expr2a_eval = expr2a.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2b_eval = expr2b.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2c_eval = expr2c.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2d_eval = expr2d.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                self.assertEqual(expr2a_eval, n)
                self.assertTrue(expr2b_eval)
                self.assertTrue(expr2c_eval)
                self.assertTrue(expr2d_eval)


    def test_required_condition_equal(self):
        from sympy import Eq, Abs
        for i in range(10):
            local_dict={'Eq': Eq, 'Abs': Abs}
            expr1=self.new_expr(name="n",expression="(-2,2)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
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
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n2 was not met",
                                        expr2b.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n3 was not met",
                                        expr2c.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition mag2_n4 was not met",
                                        expr2d.evaluate, rng=self.rng,
                                        local_dict=local_dict)
            else:
                expr2a_eval = expr2a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2b_eval = expr2b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2c_eval = expr2c.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr2d_eval = expr2d.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                self.assertTrue(expr2a_eval)
                self.assertTrue(expr2b_eval)
                self.assertTrue(expr2c_eval)
                self.assertTrue(expr2d_eval)


    def test_required_condition_symbolic_versus_numeric_equality(self):
        from sympy import Eq, Ne
        local_dict={'Ne': Ne, 'Eq': Eq}
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

            x = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            y = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
   
            if x==y:
                expr3a_eval = expr3a.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                                    .return_expression()
                self.assertTrue(expr3a_eval)

                expr3b_eval = expr3b.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                                    .return_expression()
                self.assertTrue(expr3b_eval)

                expr3c_eval = expr3c.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                                    .return_expression()
                self.assertTrue(expr3c_eval)
                

                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal1 was not met",
                                        expr3d.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal2 was not met",
                                        expr3e.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition not_equal3 was not met",
                                        expr3f.evaluate, rng=self.rng,
                                        local_dict=local_dict)


            else:

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition xx=yy",
                    expr3a.evaluate, rng=self.rng,
                    local_dict=local_dict)

                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition equal2 was not met",
                                        expr3b.evaluate, rng=self.rng,
                                        local_dict=local_dict)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition Eq\(xx,yy\)",
                    expr3c.evaluate, rng=self.rng,
                    local_dict=local_dict)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition xx!=yy",
                    expr3d.evaluate, rng=self.rng,
                    local_dict=local_dict)

                expr3e_eval = expr3e.evaluate(rng=self.rng,local_dict=local_dict)['expression_evaluated']\
                                    .return_expression()
                self.assertTrue(expr3e_eval)

                self.assertRaisesRegexp(TypeError,
                    "Could not determine truth value of required condition Ne\(xx,yy\)",
                    expr3f.evaluate, rng=self.rng,
                    local_dict=local_dict)


    def test_required_condition_complex_inequality(self):
        from sympy import Lt, Gt, Le, Ge
        from mitesting.sympy_customized import Or, And
        for i in range(10):
            local_dict={'Or': Or, 'And': And, 'Lt': Lt, 'Gt': Gt, 
                         'Le': Le, 'Ge': Ge}
            expr1=self.new_expr(name="n",expression="(-5,5)",
                                expression_type = Expression.RANDOM_NUMBER)
            n = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            expr2=self.new_expr(name="m",expression="(-5,5)",
                                expression_type = Expression.RANDOM_NUMBER)
            m = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()

            expr3a=self.new_expr(name="inequality1a",expression="Or(m<-1,n>2)",
                                 expression_type = Expression.CONDITION)
            expr3b=self.new_expr(name="inequality1b",
                                 expression="Or(Lt(m,-1),Gt(n,2))",
                                 expression_type = Expression.CONDITION)
            if not (m<-1 or n>2):
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality1a was not met",
                                        expr3a.evaluate, rng=self.rng,
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality1b was not met",
                                        expr3b.evaluate, rng=self.rng,
                                        local_dict=local_dict)
            else:
                expr3a_eval = expr3a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr3b_eval = expr3b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
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
                                        local_dict=local_dict)
                self.assertRaisesRegexp(Expression.FailedCondition,
                                        "Condition inequality2b was not met",
                                        expr4b.evaluate, rng=self.rng,
                                        local_dict=local_dict)
            else:
                expr4a_eval = expr4a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                expr4b_eval = expr4b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']\
                    .return_expression()
                self.assertTrue(expr4a_eval)
                self.assertTrue(expr4b_eval)
                
    
    def test_expression(self):
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        
        expr1=self.new_expr(name="quadratic",expression="a*z^2+b*z+c")
        quadratic=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(quadratic,a*z**2+b*z+c)
        self.assertEqual(local_dict["quadratic"], a*z**2+b*z+c)

        expr2=self.new_expr(name="linear",expression="a*y-b", \
                                expression_type=Expression.GENERIC)
        linear=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(linear,a*y-b)
        self.assertEqual(local_dict["linear"], a*y-b)
        
    def test_ordered_tuple(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        expr1=self.new_expr(name="tuple1",expression="(a,b,c)")
        tuple1 = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(tuple1.compare_with_expression((a,b,c))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,c,b))['fraction_equal'],0)
        
        expr2=self.new_expr(name="tuple2",expression="[b,c,a]")
        tuple2 = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
        self.assertEqual(tuple2,[b,c,a])

        
    def test_unordered_tuple(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        expr1=self.new_expr(name="tuple1",expression="(a,b,c)", \
                                expression_type=Expression.UNORDERED_TUPLE)
        tuple1 = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(tuple1.compare_with_expression((a,b,c))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,c,b))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((b,c,a))['fraction_equal'],1)
        self.assertEqual(tuple1.compare_with_expression((a,a,c,b))['fraction_equal'],0)

        expr2=self.new_expr(name="tuple2",expression="[3*a,b-a,c^2]", \
                                expression_type=Expression.UNORDERED_TUPLE)
        tuple2 = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(tuple2.compare_with_expression([3*a,b-a,c**2])['fraction_equal'],1)
        self.assertEqual(tuple2.compare_with_expression([3*a,c**2,b-a])['fraction_equal'],1)
        self.assertEqual(tuple2.compare_with_expression([b-a,c**2,3*a])['fraction_equal'],1)


    def test_sorted_tuple(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        expr1=self.new_expr(name="tuple1",expression="(5,-1,b^2-a,c,b)", \
                                expression_type=Expression.SORTED_TUPLE)
        tuple1 = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(tuple1.compare_with_expression((-1,5,b,c,b**2-a))['fraction_equal'],1)

        expr2=self.new_expr(name="tuple2",expression="[5,-1,b^2-a,c,b]", \
                                expression_type=Expression.SORTED_TUPLE)
        tuple2 = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(tuple2.compare_with_expression([-1,5,b,c,b**2-a])['fraction_equal'],1)


    def test_random_order_tuple(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        expr1=self.new_expr(name="tuple1",expression="(5,-1,b^2-a,c,b)", \
                                expression_type=Expression.RANDOM_ORDER_TUPLE)
        tuple_orig = (5, -1, b**2-a,c,b)
        found_different_order = False
        for i in range(100):
            tuple1 = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
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
            tuple2 = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            for j in range(5):
                self.assertTrue(tuple2[j] in tuple_orig)
            if tuple2 != tuple_orig:
                found_different_order=True
                break
        self.assertTrue(found_different_order)


    def test_tuple_no_parentheses(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        local_dict={}
        expr1=self.new_expr(name="t1",expression="a,b,c")
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1_eval, TupleNoParen(a,b,c))
        self.assertNotEqual(expr1_eval, Tuple(a,b,c))

        expr2=self.new_expr(name="t2",expression="(a,b,c)")
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, Tuple(a,b,c))
        self.assertNotEqual(expr2_eval, TupleNoParen(a,b,c))

        expr3=self.new_expr(name="t3",expression="(a+1)*b,b,a*(1-c)")
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval, TupleNoParen((a+1)*b,b,a*(1-c)))
        self.assertNotEqual(expr3_eval, Tuple((a+1)*b,b,a*(1-c)))

        expr4=self.new_expr(name="t4",expression="t1")
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval, TupleNoParen(a,b,c))
        self.assertNotEqual(expr4_eval, Tuple(a,b,c))

        expr5=self.new_expr(name="t5",expression="t2")
        expr5_eval=expr5.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr5_eval, Tuple(a,b,c))
        self.assertNotEqual(expr5_eval, TupleNoParen(a,b,c))

        

    def test_sets(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        d=Symbol('d', real=True)
        local_dict={}
        expr1=self.new_expr(name="t1",expression="b,c,a,c,d,a",
                            expression_type=Expression.SET)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertTrue(expr1_eval.return_if_unordered())
        self.assertEqual(expr1_eval.compare_with_expression(
            TupleNoParen(a,b,c,d))['fraction_equal'],1)

        expr2=self.new_expr(name="t2",expression="{b,c,a,c,d,a}",
                            expression_type=Expression.SET)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, FiniteSet(c,d,a,b))

        expr3=self.new_expr(name="t3",expression="{b,c,a,c,d,a}")
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval, FiniteSet(c,d,a,b))


    def test_single_interval(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        local_dict={'a': a, 'b': b}

        expr1=self.new_expr(name="open", expression="(a,b)",
                            expression_type=Expression.INTERVAL)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1_eval, \
            Interval(a,b,left_open=True, right_open=True))

        expr1b=self.new_expr(name="open", expression="(a,b)")
        expr1b_eval=expr1b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1b_eval, Tuple(a,b))

        expr2=self.new_expr(name="left_open", expression="(a,b]",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, \
            Interval(a,b,left_open=True, right_open=False))

        expr2b=self.new_expr(name="left_open", expression="(a,b]")
        expr2b_eval=expr2b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2b_eval, \
            Interval(a,b,left_open=True, right_open=False))

        expr3=self.new_expr(name="right_open", expression="[a,b)",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval, \
            Interval(a,b,left_open=False, right_open=True))

        expr3b=self.new_expr(name="right_open", expression="[a,b)")
        expr3b_eval=expr3b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3b_eval, \
            Interval(a,b,left_open=False, right_open=True))

        expr4=self.new_expr(name="closed", expression="[a,b]",
                            expression_type=Expression.INTERVAL)
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval, \
            Interval(a,b,left_open=False, right_open=False))

        expr4b=self.new_expr(name="closed", expression="[a,b]")
        expr4b_eval=expr4b.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4b_eval, [a,b])

    def test_interval_combinations(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        local_dict={'a': a, 'b': b}

        interval_string = "[a,b),(1,3],(a,3),[1,b]"
        interval_expression = TupleNoParen(
            Interval(a,b,left_open=False, right_open=True),\
            Interval(1,3,left_open=True, right_open=False),\
            Interval(a,3,left_open=True, right_open=True),\
            Interval(1,b,left_open=False, right_open=False))
        interval_partial_expression = TupleNoParen(
            Interval(a,b,left_open=False, right_open=True),\
            Interval(1,3,left_open=True, right_open=False),\
            Tuple(a,3),[1,b])
        
        expr1=self.new_expr(name="inttuple", expression=interval_string,
                            expression_type=Expression.INTERVAL)
        expr1_eval=expr1.evaluate(rng=self.rng)['expression_evaluated']
        self.assertEqual(expr1_eval, interval_expression)

        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)\
                    ['expression_evaluated']
        self.assertEqual(expr1_eval, interval_expression)

        expr1a=self.new_expr(name="inttuple", expression=interval_string)
        expr1a_eval=expr1a.evaluate(rng=self.rng)['expression_evaluated']
        self.assertEqual(expr1a_eval, interval_partial_expression)

        expr1b=self.new_expr(name="inttuple", expression=interval_string,
                             expression_type=Expression.INTERVAL,
                             real_variables=False)
        expr1b_eval=expr1b.evaluate(rng=self.rng, local_dict=local_dict)\
                    ['expression_evaluated']
        self.assertEqual(expr1b_eval, interval_expression)


        interval_string = "(%s)" % interval_string
        interval_expression = Tuple(*interval_expression)
        interval_partial_expression = Tuple(*interval_partial_expression)

        expr2=self.new_expr(name="inttuple2", expression=interval_string,
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng)['expression_evaluated']
        self.assertEqual(expr2_eval,interval_expression)

        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)\
                    ['expression_evaluated']
        self.assertEqual(expr2_eval, interval_expression)

        expr2a=self.new_expr(name="inttuple2", expression=interval_string)
        expr2a_eval=expr2a.evaluate(rng=self.rng, local_dict=local_dict)\
                    ['expression_evaluated']
        self.assertEqual(expr2a_eval, interval_partial_expression)


        expr3=self.new_expr(name="union", expression="[a,b)+(1,3]",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng)['expression_evaluated']
        from sympy import Union
        self.assertEqual(expr3_eval, \
                Union(Interval(a,b,left_open=False, right_open=True),\
                      Interval(1,3,left_open=True, right_open=False)))

    def test_interval_errors(self):
        a=Symbol('a')
        b=Symbol('b')
        local_dict={'a': a, 'b': b}
        expr1=self.new_expr(name="open", expression="(a,b)",
                            expression_type=Expression.INTERVAL,
                            real_variables=False)
        expr1a=self.new_expr(name="open", expression="(a,b)",
                            expression_type=Expression.INTERVAL)
        self.assertRaisesRegexp(ValueError, "Variables used in intervals must be real",
                                expr1.evaluate, rng=self.rng, 
                                local_dict=local_dict)
        self.assertRaisesRegexp(ValueError, "Variables used in intervals must be real",
                                expr1a.evaluate, rng=self.rng, 
                                local_dict=local_dict)

        local_dict={}
        self.assertRaisesRegexp(ValueError, "Variables used in intervals must be real",
                                expr1.evaluate, rng=self.rng, 
                                local_dict=local_dict)
        expr1a_eval=expr1a.evaluate(rng=self.rng, local_dict=local_dict)\
                     ['expression_evaluated']
        self.assertEqual(expr1a_eval, 
                Interval(Symbol('a',real=True),
                                       Symbol('b',real=True),
                                       left_open=True,right_open=True)),
                         

        expr2=self.new_expr(name="invalidint", expression="(1,2,3)",
                            expression_type=Expression.INTERVAL)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)\
                    ['expression_evaluated']
        self.assertEqual(expr2_eval, Tuple(1,2,3))

        expr3=self.new_expr(name="invalidint2", expression="[1,2,3],[4,5]",
                            expression_type=Expression.INTERVAL)
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval, TupleNoParen([1,2,3],Interval(4,5)))


    def test_contains(self):
        from mitesting.sympy_customized import latex, Or, And

        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        x=Symbol('x', real=True)

        local_dict={'a': a, 'b': b}
        expr1=self.new_expr(name="expr1", expression="x in (1,2)",
                            expression_type=Expression.INTERVAL, 
                            evaluate_level=EVALUATE_NONE)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1_eval, Interval(1,2,left_open=True,right_open=True).contains(x, evaluate=False))
        self.assertNotEqual(expr1_eval,  And(x < 2, x >1))
        self.assertEqual(latex(expr1_eval), r"x \in \left(1, 2\right)")

        expr1a=self.new_expr(name="expr1a", expression="x in (1,2)",
                            expression_type=Expression.INTERVAL)
        expr1a_eval=expr1a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1a_eval,
                Interval(1,2,left_open=True,right_open=True).contains(x))
        self.assertEqual(expr1a_eval,  And(x < 2, x >1))

        expr2=self.new_expr(name="expr2", expression="x in {1,2,a,b}", 
                            evaluate_level=EVALUATE_NONE)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, FiniteSet(1,2,a,b).contains(x, evaluate=False))
        self.assertEqual(expr2_eval, FiniteSet(1,2,a,b).contains(x))

        expr2a=self.new_expr(name="expr2a", expression="x in {1,2,a,b}")
        expr2a_eval=expr2a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2a_eval, FiniteSet(1,2,a,b).contains(x))
        self.assertEqual(expr2a_eval, FiniteSet(1,2,a,b).contains(x, evaluate=False))

        expr3=self.new_expr(name="expr3", 
                            expression="x in {1,2,a,b} or x in [3,4]",
                            expression_type=Expression.INTERVAL, 
                            evaluate_level=EVALUATE_NONE)
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval, 
                         Or(Interval(3,4).contains(x,evaluate=False), 
               FiniteSet(1,2,a,b).contains(x)))
                         
        expr3a=self.new_expr(name="expr3a", 
                            expression="x in {1,2,a,b} or x in [3,4]",
                            expression_type=Expression.INTERVAL)
        expr3a_eval=expr3a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
                         
        self.assertEqual(expr3a_eval, 
            Or(Interval(3,4).contains(x), FiniteSet(1,2,a,b).contains(x)))
        self.assertEqual(expr3a_eval, 
            Or(And(x<=4,x>=3), FiniteSet(1,2,a,b).contains(x)))

        expr4=self.new_expr(name="expr4", expression="x in {1,2,x}", 
                            evaluate_level=EVALUATE_NONE)
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval, FiniteSet(1,2,x).contains(x, evaluate=False))
        self.assertEqual(latex(expr4_eval), r'x \in \left\{1, 2, x\right\}')

        expr4a=self.new_expr(name="expr4a", expression="x in {1,2,x}")
        expr4a_eval=expr4a.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4a_eval, True)
        
    def test_matrix(self):
        from sympy import Matrix
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        local_dict={}

        expr1=self.new_expr(name="A", expression="\n 1 2\na b\na-b 1 \na -b\n ",
                            expression_type=Expression.MATRIX)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        A=Matrix([[1,2],[a,b],[a-b,1],[a,-b]])
        self.assertEqual(expr1_eval, A)


        expr2=self.new_expr(name="two_A", expression="2A")
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, 2*A)
        

        expr3=self.new_expr(name="v", expression="a\n5",
                            expression_type=Expression.MATRIX)
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        v = Matrix([a,5])
        self.assertEqual(expr3_eval, v)

        expr4=self.new_expr(name="Av", expression="A*v")
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval, A*v)
        
        expr5=self.new_expr(name="Av", expression="A*v",
                            expression_type=Expression.MATRIX)
        expr5_eval=expr5.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr5_eval, A*v)
        
        expr6=self.new_expr(name="err", expression="1 2 3\n1 2",
                            expression_type=Expression.MATRIX)
        self.assertRaisesRegexp(ValueError, "Invalid format for matrix\nGot rows of variable lengths",
                                expr6.evaluate, rng=self.rng, 
                                local_dict=local_dict)


    def test_vector(self):
        from sympy import Matrix
        from mitesting.sympy_customized import latex
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        local_dict={}

        expr1=self.new_expr(name="x", expression="(a,b,1,2) ",
                            expression_type=Expression.VECTOR)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        x=Matrix([a,b,1,2])
        xvec = Tuple(a,b,1,2)
        self.assertEqual(expr1_eval, x)
        self.assertEqual(str(expr1_eval), latex(xvec))
        
        expr2=self.new_expr(name="two_x", expression="2*x")
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr2_eval, 2*x)
        two_xvec = Tuple(2*a,2*b,2,4)
        self.assertEqual(str(expr2_eval), latex(two_xvec))
        
        expr3=self.new_expr(name="colv", expression="a\nb\n1\n2",
                            expression_type=Expression.MATRIX)
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        expr4=self.new_expr(name="two_colv", expression="2*colv",
                            expression_type=Expression.VECTOR)
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval, 2*x)
        self.assertEqual(str(expr4_eval), latex(two_xvec))
        
        expr5=self.new_expr(name="A", expression="2 0 3 0\n0 0 a 0",
                            expression_type=Expression.MATRIX)
        expr5_eval=expr5.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        expr6=self.new_expr(name="Ax", expression="A*x")
        expr6_eval=expr6.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        Ax=Matrix([2*a+3,a])
        self.assertEqual(expr6_eval,Ax)

        expr7=self.new_expr(name="two_A_no_vec", expression="2*A",
                           expression_type=Expression.VECTOR)
        expr7_eval=expr7.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        two_A=Matrix([[4,0,6,0],[0,0,2*a,0]])
        self.assertEqual(expr7_eval,two_A)
        self.assertEqual(str(expr7_eval),latex(two_A))


    def test_evaluate_false(self):
        local_dict={}
        expr1=self.new_expr(name="s", expression="x+x*y*x+x")
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(six.text_type(expr1_eval), "x^{2} y + 2 x")
        expr2=self.new_expr(name="s2", expression="x+x*y*x+x", 
                            evaluate_level=EVALUATE_NONE)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(six.text_type(expr2_eval), "x + x y x + x")
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr2_eval.compare_with_expression(
                expr1_eval.return_expression())['fraction_equal_on_normalize'],1)
        self.assertEqual(expr1_eval.compare_with_expression(
                expr2_eval.return_expression())['fraction_equal_on_normalize'],1)

    def test_evaluate_false_function(self):
        local_dict={}
        expr1=self.new_expr(name="f", expression="x+x*y*x+x*1+0", function_inputs="x",
                            expression_type=Expression.FUNCTION, evaluate_level=EVALUATE_NONE)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(six.text_type(expr1_eval), "x + x y x + x 1 + 0")
        expr2=self.new_expr(name="f_z", expression="f(z)", 
                            evaluate_level=EVALUATE_NONE)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(six.text_type(expr2_eval), "z + z y z + z 1 + 0")
        expr3=self.new_expr(name="f_z_eval", expression="f(z)")
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(six.text_type(expr3_eval), "y z^{2} + 2 z")

        self.assertEqual(expr2_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr2_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal_on_normalize'],1)

    def test_evaluate_partial(self):
        from sympy import Derivative, Integral
        x=Symbol('x', real=True)
        local_dict={'Derivative': Derivative, 'Integral': Integral}
        expr1=self.new_expr(name="s", expression="Derivative(x^2,x)")
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr1_eval.return_expression(), 2*x)
        expr2=self.new_expr(name="s2", expression="Derivative(x^2,x)", 
                            evaluate_level=EVALUATE_PARTIAL)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
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
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr3_eval.return_expression(), x**3/3)
        expr4=self.new_expr(name="s4", expression="Integral(x^2,x)", 
                            evaluate_level=EVALUATE_PARTIAL)
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
        self.assertEqual(expr4_eval.return_expression(), Integral(x**2,x))
        self.assertEqual(expr4_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr4_eval.compare_with_expression(
                expr3_eval.return_expression())['fraction_equal_on_normalize'],1)
        self.assertEqual(expr3_eval.compare_with_expression(
                expr4_eval.return_expression())['fraction_equal'],0)
        self.assertEqual(expr3_eval.compare_with_expression(
                expr4_eval.return_expression())['fraction_equal_on_normalize'],1)


    def test_function_local_dict(self):
        from sympy import sin
        x=Symbol('x', real=True)
        expr1=self.new_expr(name="s", expression="x*sin(x)")
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict={})['expression_evaluated']
        self.assertEqual(expr1_eval, x**2*Symbol('sin', real=True))
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict={'sin':sin})['expression_evaluated']
        self.assertEqual(expr1_eval, x*sin(x))


    def test_greek(self):
        expr = self.new_expr(name="greek", 
                             expression="lambda*gamma/delta + epsilon")
        expr_eval=expr.evaluate(rng=self.rng)['expression_evaluated']
        self.assertEqual(expr_eval, Symbol('lambda', real=True)*Symbol('gamma', real=True) \
                             / Symbol('delta', real=True) + Symbol('epsilon', real=True))
        self.assertEqual(six.text_type(expr_eval),
                         r'\epsilon + \frac{\gamma \lambda}{\delta}')


    def test_errors(self):
        symqq = Symbol('??')
        local_dict={}
        expr1=self.new_expr(name="a", expression="(")
        self.assertRaisesRegexp(ValueError, 'Error in expression: a', 
                                expr1.evaluate, rng=self.rng, 
                                local_dict=local_dict)
        self.assertEqual(local_dict['a'],symqq)
        self.assertRaisesRegexp(ValueError, 'Error in expression: a', 
                                expr1.evaluate, rng=self.rng)

        expr2=self.new_expr(name="b", expression="x-+/x", 
                            expression_type=Expression.CONDITION)
        self.assertRaisesRegexp(ValueError, 'Error in expression: b', 
                                expr2.evaluate, rng=self.rng, 
                                local_dict=local_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for condition', 
                                expr2.evaluate, rng=self.rng,
                                local_dict=local_dict)
        self.assertEqual(local_dict['b'],symqq)

        expr3=self.new_expr(name="c", expression="x[0]", 
                            expression_type=Expression.FUNCTION)
        self.assertRaisesRegexp(ValueError, 'Error in expression: c', 
                                expr3.evaluate, rng=self.rng,
                                local_dict=local_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for function', 
                                expr3.evaluate, rng=self.rng,
                                local_dict=local_dict)
        self.assertEqual(local_dict['c'],symqq)

        from sympy import sin
        local_dict['sin']=sin
        expr4=self.new_expr(name="d", expression="(x+sin, y-sin)", 
                            expression_type=Expression.UNORDERED_TUPLE)
        self.assertRaisesRegexp(ValueError, 'Error in expression: d', 
                                expr4.evaluate, rng=self.rng,
                                local_dict=local_dict)
        self.assertRaisesRegexp(ValueError, 'Invalid format for tuple', 
                                expr4.evaluate, rng=self.rng,
                                local_dict=local_dict)
        self.assertEqual(local_dict['d'],symqq)


    def test_alternate_expressions(self):
        c=Symbol('c', real=True)
        C=Symbol('C', real=True)
        d=Symbol('d', real=True)
        D=Symbol('D', real=True)
        x=Symbol('x', real=True)

        local_dict={}
        alternate_dicts=[]

        expr1=self.new_expr(name="c", expression="c,C,d,D",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr1_eval['expression_evaluated'], c)
        self.assertEqual(local_dict, {'c': c})

        self.assertEqual(expr1_eval['alternate_exprs'], [C,d,D])
        self.assertEqual(alternate_dicts[0], {'c': C})
        self.assertEqual(alternate_dicts[1], {'c': d})
        self.assertEqual(alternate_dicts[2], {'c': D})

        expr2=self.new_expr(name="v_c", expression="x+c")
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr2_eval['expression_evaluated'], x+c)
        self.assertEqual(local_dict, {'c': c, 'v_c': x+c})

        self.assertEqual(expr2_eval['alternate_exprs'], [x+C,x+d,x+D])
        self.assertEqual(alternate_dicts[0], {'c': C, 'v_c': x+C})
        self.assertEqual(alternate_dicts[1], {'c': d, 'v_c': x+d})
        self.assertEqual(alternate_dicts[2], {'c': D, 'v_c': x+D})


    def test_alternate_expressions_compounded(self):
        c=Symbol('c', real=True)
        C=Symbol('C', real=True)
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)

        local_dict={}
        alternate_dicts=[]

        expr1=self.new_expr(name="c", expression="c,C",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr1_eval['expression_evaluated'], c)
        self.assertEqual(local_dict, {'c': c})

        self.assertEqual(expr1_eval['alternate_exprs'], [C,])
        self.assertEqual(alternate_dicts[0], {'c': C})

        expr2=self.new_expr(name="v_c", expression="x+c, y+c, z+c",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr2_eval['expression_evaluated'], x+c)
        self.assertEqual(local_dict, {'c': c, 'v_c': x+c})

        self.assertEqual(expr2_eval['alternate_exprs'], [x+C, y+c, y+C,z+c,z+C])

        self.assertEqual(alternate_dicts[0], {'c': C, 'v_c': x+C})
        self.assertEqual(alternate_dicts[1], {'c': c, 'v_c': y+c})
        self.assertEqual(alternate_dicts[2], {'c': C, 'v_c': y+C})
        self.assertEqual(alternate_dicts[3], {'c': c, 'v_c': z+c})
        self.assertEqual(alternate_dicts[4], {'c': C, 'v_c': z+C})


    def test_alternate_expressions_compounded_2(self):
        c=Symbol('c', real=True)
        C=Symbol('C', real=True)
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)

        local_dict={}
        alternate_dicts=[]

        expr1=self.new_expr(name="c", expression="c,C",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr1_eval=expr1.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr1_eval['expression_evaluated'], c)
        self.assertEqual(local_dict, {'c': c})

        self.assertEqual(expr1_eval['alternate_exprs'], [C,])
        self.assertEqual(alternate_dicts[0], {'c': C})

        expr2=self.new_expr(name="v", expression="x, y, z",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr2_eval=expr2.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr2_eval['expression_evaluated'], x)
        self.assertEqual(local_dict, {'c': c, 'v': x})

        self.assertEqual(expr2_eval['alternate_exprs'], [y, z])

        self.assertEqual(alternate_dicts[0], {'c': C, 'v': x})
        self.assertEqual(alternate_dicts[1], {'c': c, 'v': y})
        self.assertEqual(alternate_dicts[2], {'c': C, 'v': y})
        self.assertEqual(alternate_dicts[3], {'c': c, 'v': z})
        self.assertEqual(alternate_dicts[4], {'c': C, 'v': z})

        expr3=self.new_expr(name="v_c", expression="v+c")
        expr3_eval=expr3.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr3_eval['expression_evaluated'], x+c)
        self.assertEqual(local_dict, {'c': c, 'v': x, 'v_c': x+c})
        
        self.assertEqual(expr3_eval['alternate_exprs'], [x+C, y+c, y+C,z+c,z+C])

        self.assertEqual(alternate_dicts[0], {'c': C, 'v': x, 'v_c': x+C})
        self.assertEqual(alternate_dicts[1], {'c': c, 'v': y, 'v_c': y+c})
        self.assertEqual(alternate_dicts[2], {'c': C, 'v': y, 'v_c': y+C})
        self.assertEqual(alternate_dicts[3], {'c': c, 'v': z, 'v_c': z+c})
        self.assertEqual(alternate_dicts[4], {'c': C, 'v': z, 'v_c': z+C})

        expr4=self.new_expr(name="v_c_a", expression="v+c+a, v+c+b",
                        expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        expr4_eval=expr4.evaluate(rng=self.rng, local_dict=local_dict,
                                  alternate_dicts=alternate_dicts)
        self.assertEqual(expr4_eval['expression_evaluated'], x+c+a)
        self.assertEqual(local_dict, {'c': c, 'v': x, 'v_c': x+c, 
                                      'v_c_a': x+c+a})

        self.assertEqual(expr4_eval['alternate_exprs'],
                         [x+C+a, y+c+a, y+C+a, z+c+a, z+C+a,
                          x+c+b, x+C+b, y+c+b, y+C+b, z+c+b, z+C+b])

        self.assertEqual(alternate_dicts[0], {'c': C, 'v': x, 'v_c': x+C, 
                                              'v_c_a': x+C+a})
        self.assertEqual(alternate_dicts[1], {'c': c, 'v': y, 'v_c': y+c, 
                                              'v_c_a': y+c+a})
        self.assertEqual(alternate_dicts[2], {'c': C, 'v': y, 'v_c': y+C, 
                                              'v_c_a': y+C+a})
        self.assertEqual(alternate_dicts[3], {'c': c, 'v': z, 'v_c': z+c, 
                                              'v_c_a': z+c+a})
        self.assertEqual(alternate_dicts[4], {'c': C, 'v': z, 'v_c': z+C, 
                                              'v_c_a': z+C+a})
        self.assertEqual(alternate_dicts[5], {'c': c, 'v': x, 'v_c': x+c, 
                                              'v_c_a': x+c+b})
        self.assertEqual(alternate_dicts[6], {'c': C, 'v': x, 'v_c': x+C, 
                                              'v_c_a': x+C+b})
        self.assertEqual(alternate_dicts[7], {'c': c, 'v': y, 'v_c': y+c, 
                                              'v_c_a': y+c+b})
        self.assertEqual(alternate_dicts[8], {'c': C, 'v': y, 'v_c': y+C, 
                                              'v_c_a': y+C+b})
        self.assertEqual(alternate_dicts[9], {'c': c, 'v': z, 'v_c': z+c, 
                                              'v_c_a': z+c+b})
        self.assertEqual(alternate_dicts[10], {'c': C, 'v': z, 'v_c': z+C, 
                                               'v_c_a': z+C+b})



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
            local_dict={}
            test_local_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = Expression.RANDOM_WORD)
            expr1_eval = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            self.assertTrue(expr1_eval in [("a","as"),("b","bs"),("c","cs"),
                                           ("d","ds"),("e","es"),("f","fs")])
            test_local_dict["a"] = Symbol(expr1_eval[0])
            self.assertEqual(local_dict, test_local_dict)

            expr2=self.new_expr(name="b",
                                expression="cat, (pony,ponies), (goose,geese)",
                                expression_type = Expression.RANDOM_WORD)
            expr2_eval = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            self.assertTrue(expr2_eval in [("cat","cats"),("pony","ponies"),
                                           ("goose","geese")])
            test_local_dict["b"] = Symbol(expr2_eval[0])
            self.assertEqual(local_dict, test_local_dict)

            expr3=self.new_expr(name="c",
                                expression="\"the pit\",(&^%$#@!,_+*&<?),"
                                + '(one, "one/two or more")',
                                expression_type = Expression.RANDOM_WORD)
            expr3_eval = expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated']
            self.assertTrue(expr3_eval in [
                    ("the pit", "the pits"),('&^%$#@!','_+*&<?'),
                    ('one', "one/two or more")])
            test_local_dict["c"] = Symbol(re.sub(' ', '_', expr3_eval[0]))
            self.assertEqual(local_dict, test_local_dict)


    def test_random_expression(self):
        x = Symbol('x', real=True)
        for i in range(10):
            local_dict={}
            test_local_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = Expression.RANDOM_EXPRESSION)
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(a in [Symbol(item, real=True) for item in
                                  ("a","b","c","d","e","f")])
            test_local_dict["a"] = a
            self.assertEqual(local_dict, test_local_dict)
    
            expr2=self.new_expr(name="b",expression="2*a*x, -3*a/x^3, a-x",
                                expression_type = Expression.RANDOM_EXPRESSION)
            b = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(b in [2*a*x, -3*a/x**3,a-x])
            test_local_dict["b"] = b
            self.assertEqual(local_dict, test_local_dict)

            expr3=self.new_expr(name="c",expression="2*b^2, (a-b)/x",
                                expression_type = Expression.RANDOM_EXPRESSION)
            c = expr3.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(c in [2*b**2, (a-b)/x]),
            test_local_dict["c"] = c
            self.assertEqual(local_dict, test_local_dict)

    def test_random_expression_evaluate_level(self):
        from sympy import Derivative, Integral
        x = Symbol('x', real=True)
        local_dict={'Derivative': Derivative }

        for i in range(10):
            expr1=self.new_expr(name="a",expression=
                                "x+x, Derivative(x^3,x), 5(x-3)",
                                expression_type = Expression.RANDOM_EXPRESSION)
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(a in [2*x, 3*x**2, 5*x-15])

            expr1.evaluate_level = EVALUATE_FULL
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(a in [2*x, 3*x**2, 5*x-15])

            expr1.evaluate_level = EVALUATE_PARTIAL
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(a in [2*x, Derivative(x**3,x), 5*x-15])
            
            expr1.evaluate_level = EVALUATE_NONE
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(six.text_type(a) in 
                            ['x + x', 'Derivative(x**3, x)', '5*(x - 3)'])

    def test_random_function_name(self):
        x = Symbol('x', real=True)
        for i in range(10):
            local_dict={}
            test_local_dict = {}

            expr1=self.new_expr(name="a",expression="a,b, c ,d,e,  f",
                                expression_type = 
                                Expression.RANDOM_FUNCTION_NAME)
            a = expr1.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertTrue(a in [SymbolCallable(str(item),real=True) for item in
                                  ("a","b","c","d","e","f")])
            test_local_dict["a"] = a
            self.assertEqual(local_dict, test_local_dict)
    
            expr2=self.new_expr(name="b",expression="2*a(x)-4")
            b = expr2.evaluate(rng=self.rng, local_dict=local_dict)['expression_evaluated'].return_expression()
            self.assertEqual(b, 2*a(x)-4)
            test_local_dict["b"] = b
            self.assertEqual(local_dict, test_local_dict)

            user_function_dict = {}
            expr3=self.new_expr(name="f",expression="this, that, the,other",
                                expression_type = 
                                Expression.RANDOM_FUNCTION_NAME)
            f = expr3.evaluate(rng=self.rng, local_dict=local_dict, \
                                   user_function_dict=user_function_dict)['expression_evaluated']\
                                   .return_expression()
            self.assertTrue(f in [SymbolCallable(str(item), real=True) for item in
                                  ("this","that","the","other")])
            self.assertEqual( user_function_dict , { str(f): f})
            test_local_dict["f"] = f
            self.assertEqual(local_dict, test_local_dict)

            

    def test_random_list_groups_match(self):
        for i in range(10):
            random_group_indices = {}
            local_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                local_dict=local_dict, 
                random_group_indices=random_group_indices)['expression_evaluated'][0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g1")
            re1 = expr2.evaluate(rng=self.rng, 
                local_dict=local_dict,
                random_group_indices=random_group_indices)['expression_evaluated'].return_expression()
            
            expr3=self.new_expr(name="rf1",expression="a,b, c ,d,e", 
                                expression_type =
                                Expression.RANDOM_FUNCTION_NAME,
                                random_list_group="g1")
            rf1 = expr3.evaluate(rng=self.rng, 
                local_dict=local_dict,
                random_group_indices=random_group_indices)['expression_evaluated'].return_expression()

            self.assertTrue((rw1,re1,rf1) in [
                    (item, Symbol(item, real=True), 
                     SymbolCallable(str(item), real=True))
                    for item in ["a","b","c","d","e"]])

            
    def test_random_list_groups_some_match(self):
        found_non_match=False
        for i in range(100):
            random_group_indices = {}
            local_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                local_dict=local_dict, 
                random_group_indices=random_group_indices)['expression_evaluated'][0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g2")
            re1 = expr2.evaluate(rng=self.rng, 
                local_dict=local_dict,
                random_group_indices=random_group_indices)['expression_evaluated'].return_expression()
            
            expr3=self.new_expr(name="rf1",expression="a,b, c ,d,e", 
                                expression_type =
                                Expression.RANDOM_FUNCTION_NAME,
                                random_list_group="g1")
            rf1 = expr3.evaluate(rng=self.rng, 
                local_dict=local_dict,
                random_group_indices=random_group_indices)['expression_evaluated'].return_expression()

            self.assertTrue((rw1,rf1) in [
                    (item, SymbolCallable(str(item), real=True))
                    for item in ["a","b","c","d","e"]])

            if str(re1) != rw1:
                found_non_match=True
                break
        
        self.assertTrue(found_non_match)    
            

    def test_random_list_groups_different_lengths(self):
        for i in range(10):
            random_group_indices = {}
            local_dict = {}
            expr1=self.new_expr(name="rw1",expression="a,b,c",
                                expression_type = Expression.RANDOM_WORD,
                                random_list_group="g1")
            rw1 = expr1.evaluate(rng=self.rng, 
                local_dict=local_dict, 
                random_group_indices=random_group_indices)['expression_evaluated'][0]
            
            expr2=self.new_expr(name="re1",expression="a,b, c ,d, e",
                                expression_type = Expression.RANDOM_EXPRESSION,
                                random_list_group="g1")
            re1 = expr2.evaluate(rng=self.rng, 
                local_dict=local_dict,
                random_group_indices=random_group_indices)['expression_evaluated'].return_expression()
            self.assertTrue((rw1,re1) in [
                    (item, Symbol(item, real=True))
                    for item in ["a","b","c"]])

        with self.assertRaisesRegexp(IndexError, 
                                     'Insufficient entries for random list group: g1'):
            for i in range(100):
                random_group_indices = {}
                local_dict = {}
                expr1=self.new_expr(name="rw1",expression="a,b,c,d,e",
                                    expression_type = Expression.RANDOM_WORD,
                                    random_list_group="g1")
                rw1 = expr1.evaluate(rng=self.rng, 
                    local_dict=local_dict, 
                    random_group_indices=random_group_indices)['expression_evaluated'][0]
                
                expr2=self.new_expr(name="re1",expression="a,b, c",
                                    expression_type =
                                    Expression.RANDOM_EXPRESSION,
                                    random_list_group="g1")
                re1 = expr2.evaluate(rng=self.rng,  \
                    local_dict=local_dict, \
                        random_group_indices=random_group_indices)['expression_evaluated'] \
                        .return_expression()
                    
                self.assertTrue((rw1,re1) in [
                        (item, Symbol(item, real=True))
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
