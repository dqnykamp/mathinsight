
from django.test import SimpleTestCase
from mitesting.utils import *
from sympy import sympify
from mitesting.sympy_customized import Symbol
import random

class TestDicts(SimpleTestCase):
    def test_sympy_local_dict(self):

        local_dict = return_sympy_local_dict()
        self.assertEqual(local_dict, {})

        from sympy import Abs
        local_dict = return_sympy_local_dict(["Abs"])
        local_dict2 = {}
        local_dict2['Abs']=Abs
        self.assertEqual(local_dict, local_dict2)

        local_dict = return_sympy_local_dict(["Abs", "floor, ceiling"])
        from sympy import floor, ceiling
        local_dict2['ceiling']=ceiling
        local_dict2['floor']=floor
        self.assertEqual(local_dict, local_dict2)

        local_dict = return_sympy_local_dict(["Abs", "floor, ceiling",
                                                "min, max, Min, Max",
                                                "nothingvalid", "if"])
        from mitesting.user_commands import min_including_tuples,\
            max_including_tuples, iif
        local_dict2['min']=min_including_tuples
        local_dict2['Min']=min_including_tuples
        local_dict2['max']=max_including_tuples
        local_dict2['Max']=max_including_tuples
        local_dict2['if']=iif
        self.assertEqual(local_dict, local_dict2)


        

class TestRandomNumber(SimpleTestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()

    def test_returns_integer_in_range(self):
        from sympy import Integer
        the_num = return_random_number_sample("(1,3,1)", rng=self.rng)
        self.assertTrue(the_num in range(1,4))
        self.assertTrue(isinstance(the_num, Integer))

    def test_with_no_increment(self):
        from sympy import Integer
        the_num = return_random_number_sample("(-1,5)", rng=self.rng)
        self.assertTrue(the_num in range(-1,6))
        self.assertTrue(isinstance(the_num, Integer))

    def test_rounding_with_tenths(self):
        valid_answers = [round(0.1*a,1) for a in range(-31,52)]
        for i in range(5):
            the_num = return_random_number_sample("(-3.1,5.1,0.1)", 
                                                  rng=self.rng)
            self.assertTrue(the_num in valid_answers)

    def test_can_achieve_max_value(self):
        achieved_max = False
        for i in range(1000):
            the_num = return_random_number_sample("(4.04,4.15,0.01)",
                                                  rng=self.rng)
            if the_num == 4.15:
                achieved_max = True
                break
        self.assertTrue(achieved_max)
    
    def test_with_local_dict(self):
        local_dict = {"x": sympify(-2), "y": sympify(2)}
        the_num = return_random_number_sample("(x,y)", rng=self.rng,
                                              local_dict=local_dict)
        self.assertTrue(the_num in range(-2,3))
    
    def test_raises_useful_exceptions(self):
        self.assertRaisesRegex(ValueError, 'Invalid format for random number',
                                return_random_number_sample, "(", rng=self.rng)
        
        self.assertRaisesRegex(ValueError, 'require minval <= maxval', 
                                return_random_number_sample, "(5,3)",
                                rng=self.rng)

        self.assertRaisesRegex(ValueError, 'Invalid format for random number', 
                                return_random_number_sample, "4", rng=self.rng)

        self.assertRaisesRegex(ValueError, 'Invalid format for random number', 
                                return_random_number_sample, "(1,2,3,4)",
                                rng=self.rng)

        self.assertRaisesRegex(TypeError, 'random number must contain numbers',
                                return_random_number_sample, "(a,b,c)",
                                rng=self.rng)


class TestRandomWordPlural(SimpleTestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()

    def test_with_no_plurals(self):
        word = return_random_word_and_plural("hello, bye, seeya", rng=self.rng)
        self.assertTrue(word[0] in ["hello", "bye", "seeya"])
        self.assertEqual(word[0]+"s", word[1])

    def test_with_no_plurals(self):
        for i in range(3):
            word = return_random_word_and_plural(
                "(hello, helloes), bye, (seeya, seeyee)", rng=self.rng)
            self.assertTrue(word[0] in ["hello", "bye", "seeya"])
            if word[2]==0:
                self.assertEqual(word[0],'hello')
                self.assertEqual(word[1],'helloes')
            elif word[2]==1:
                self.assertEqual(word[0],'bye')
                self.assertEqual(word[1],'byes')
            else:
                self.assertEqual(word[0],'seeya')
                self.assertEqual(word[1],'seeyee')

    def test_with_quoted_string(self):
        for i in range(3):
            word = return_random_word_and_plural(
                "('hello all', \"hellos to all\"), 'bye-bye', " 
                + '("see ya", \'see yee\')', rng=self.rng)
            self.assertTrue(word[0] in ["hello all", "bye-bye", "see ya"])
            if word[2]==0:
                self.assertEqual(word[0],'hello all')
                self.assertEqual(word[1],'hellos to all')
            elif word[2]==1:
                self.assertEqual(word[0],'bye-bye')
                self.assertEqual(word[1],'bye-byes')
            else:
                self.assertEqual(word[0],'see ya')
                self.assertEqual(word[1],'see yee')
            
    def test_with_varied_spacing(self):
        for i in range(3):
            word = return_random_word_and_plural(
                " what,kind, of,  list,  'is this?'  ", rng=self.rng)
            self.assertTrue(word[0] in ["what","kind","of","list","is this?"])
                            
    def test_with_given_index(self):
        word = return_random_word_and_plural("a,b,(c,d),e", rng=self.rng,
                                             index=2)
        self.assertEqual(word[0], "c")
        self.assertEqual(word[1], "d")
        self.assertEqual(word[2], 2)

    def test_with_extra_characters(self):
        word = return_random_word_and_plural("hi!, bye-bye, this_one, me&you,"
                                             + "this@whatever.net",
                                             rng=self.rng)
        self.assertTrue(word[0] in ["hi!","bye-bye", "this_one", "me&you",
                                    "this@whatever.net"])


    def test_raises_useful_exception(self):
        self.assertRaisesRegex(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(",
                                rng=self.rng)
        self.assertRaisesRegex(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(a a)",
                                rng=self.rng)
        self.assertRaisesRegex(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "((a,a), a)",
                                rng=self.rng)
        self.assertRaisesRegex(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "a,(a,a,a)",
                                rng=self.rng)
        self.assertRaisesRegex(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(a,(a,a))",
                                rng=self.rng)

        # this should raise a value error, but it doesn't yet
        # self.assertRaisesRegex(ValueError, 'Invalid format for random word',
        #                         return_random_word_and_plural, "a a, a")
       


class TestRandomExpression(SimpleTestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()

    def test_basic_example(self):
        expr = return_random_expression("hello, bye, seeya", rng=self.rng)
        self.assertTrue(expr[0] in [Symbol("hello"), Symbol("bye"),
                                    Symbol("seeya")])
        if expr[1]==0:
            self.assertEqual(expr[0],Symbol('hello'))
        elif expr[1]==1:
            self.assertEqual(expr[0],Symbol('bye'))
        else:
            self.assertEqual(expr[0],Symbol('seeya'))
        
    def test_with_math_expression(self):
        x=Symbol("x")
        y=Symbol("y")
        expr = return_random_expression("x^3, x^2+2*x*y", rng=self.rng)
        self.assertTrue(expr[0] in [x**3, x**2+2*x*y])

        x=Symbol("x", real=True)
        y=Symbol("y", real=True)
        expr = return_random_expression("x^3, x^2+2*x*y", rng=self.rng,
                                        assume_real_variables=True)
        self.assertTrue(expr[0] in [x**3, x**2+2*x*y])

    def test_with_local_dict(self):
        x=Symbol("x")
        y=Symbol("y")
        local_dict = {"v1": x, "v2": y}
        expr = return_random_expression("v1+v2, v1/v2", rng=self.rng,
                                        local_dict=local_dict)
        self.assertTrue(expr[0] in [x+y, x/y])

        from sympy import sin, cos
        u = Symbol("u")
        local_dict = {"f": sin, "g": cos, "x": u }
        expr = return_random_expression("f(x), g(x)", rng=self.rng,
                                        local_dict=local_dict)
        self.assertTrue(expr[0] in [sin(u),cos(u)])

    def test_with_given_index(self):
        x = Symbol('x')
        g = Symbol('g')
        expr = return_random_expression("f(x), g(x), h(x)", rng=self.rng,
                                        index=1)
        self.assertEqual(expr[0], x*g)
        self.assertEqual(expr[1], 1)

    def test_raises_useful_exception(self):
        self.assertRaisesRegex(ValueError,
                                'Invalid format for random expression',
                                return_random_expression, "(", rng=self.rng)

class TestParsedFunction(SimpleTestCase):
    def test_simple_function(self):
        z=Symbol('z')
        fun = return_parsed_function("x^2","x", name="f")
        self.assertEqual(fun(z), z*z)
        self.assertEqual(str(fun), "f")
    def test_function_other_variables(self):
        w=Symbol('w')
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        a=Symbol('a')
        fun = return_parsed_function("x*y*z - a/y", "y", name="f")
        self.assertEqual(fun(w), x*w*z-a/w)
        self.assertEqual(str(fun), "f")
    def test_function_local_dict(self):
        u=Symbol('u')
        a=Symbol('a')
        b=Symbol('b')
        x=Symbol('x')
        z=Symbol('z')
        fun = return_parsed_function("x*y*z - a/y", "y", name="f1g",
                                     local_dict={"a": b})
        self.assertEqual(fun(u), x*u*z-b/u)
        self.assertEqual(str(fun), "f1g")
        fun = return_parsed_function("x*y*z - a/y", "y", name="f1g",
                                     local_dict={"y": b})
        self.assertEqual(fun(u), x*u*z-a/u)

    def test_function_multiple_inputs(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        a=Symbol('a')
        fun = return_parsed_function("s/t - a*u", "s,t,u", name="something")
        self.assertEqual(fun(x,y,z), x/y - a*z)
        self.assertEqual(str(fun), "something")
    def test_function_no_inputs(self):
        x=Symbol('x')
        y=Symbol('y')
        fun = return_parsed_function("3*x", "", "g")
        self.assertEqual(fun(),3*x)
    def test_ignore_garbage_in_inputs(self):
        x=Symbol('x')
        y=Symbol('y')
        fun = return_parsed_function("3*x*(x-1)", "(", "crazy")
        result = 3*x*(x-1)
        self.assertEqual(fun(0), result)
        self.assertEqual(fun(x*y-y**4),result)
        self.assertEqual(str(fun), "crazy")
        fun = return_parsed_function("3*x*(x-1)", "& 2 ^ ! &$%", "crazy2")
        self.assertEqual(fun(0), result)
        self.assertEqual(fun(x*y-y**4),result)
        self.assertEqual(str(fun), "crazy2")
    def test_compose_functions(self):
        x=Symbol('x')
        y=Symbol('y')
        fun1 = return_parsed_function("3*x*(x-1)", "x",name="f")
        fun2 = return_parsed_function("x^2","x",name="g")
        self.assertEqual(fun1(fun2(x)), 3*x**2*(x**2 - 1))
        self.assertEqual(fun2(fun1(x)),9*x**2*(x - 1)**2)
        
        # compose via local_dict
        fun2 = return_parsed_function("f(x)^2","x",name="g", 
                                      local_dict={'f': fun1})
        self.assertEqual(fun2(x),9*x**2*(x - 1)**2)
    
        
    def test_raises_useful_exceptions(self):
        self.assertRaisesRegex(ValueError,
                                'Invalid format for function',
                                return_parsed_function, "(", "x", "f")

        # function with zero inputs
        fun = return_parsed_function("x^2-1","", name="f")
        # give it an input
        self.assertRaises(TypeError, fun, 1)

        # function with one input
        fun = return_parsed_function("x^2-1","x", name="f")
        # give it zero inputs
        self.assertRaises(TypeError, fun)
        # give it two inputs
        self.assertRaises(TypeError, fun, 1,2)

        # function with two inputs
        fun = return_parsed_function("x^2-y","x, y", name="f")
        # give it zero inputs
        self.assertRaises(TypeError, fun)
        # give it one input
        self.assertRaises(TypeError, fun, 1)
        # give it three inputs
        self.assertRaises(TypeError, fun, 1,1,1)


    def test_no_evaluate(self):
        from mitesting.models import Expression
        from mitesting.sympy_customized import latex
        z=Symbol('z')
        fun = return_parsed_function("3*x*-1*1*x-1+0-3+x","x", name="f",
                                     evaluate_level=Expression.EVALUATE_NONE)
        self.assertEqual(repr(fun(z)), '3*z*(-1)*1*z - 1 + 0 - 3 + z')
        self.assertEqual(latex(fun(z)), '3 z \\left(-1\\right) 1 z - 1 + 0 - 3 + z')
        

    def test_is_number(self):
        from mitesting.user_commands import is_number
        from mitesting.models import Expression
        t=Symbol("t")
        fun = return_parsed_function("is_number(x-2*t)", "x", name="f",
                                     local_dict = {'is_number': is_number})
        self.assertTrue(fun(2*t+5))
        self.assertFalse(fun(3*t))


    def test_evaluate_derivative_at_point(self):
        from sympy import diff
        fun1 = return_parsed_function("x^3","x", name="f1")
        fun2 = return_parsed_function("diff(f1(x),x)", "x", name="f2",
                                      local_dict={'f1': fun1, 'diff': diff})
        y=Symbol('y')
        z=Symbol('z')
        self.assertEqual(fun2(y), 3*y**2)
        self.assertEqual(fun2(2), 3*2**2)
        self.assertEqual(fun2(y*z+3), 3*(y*z+3)**2)

    def test_evaluate_indefinite_integral_at_point(self):
        from mitesting.models import Expression
        from sympy import Integral
        x=Symbol('x')
        y=Symbol('y')
        fun = return_parsed_function("Integral(x^2,(x,t))","t", name="f1",
                                     local_dict={'Integral': Integral},
                                     evaluate_level=Expression.EVALUATE_PARTIAL)
        self.assertEqual(fun(3), Integral(x**2,(x,3)))
        self.assertEqual(fun(y), Integral(x**2,(x,y)))

        fun = return_parsed_function("Integral(x^2,(x,t))","t", name="f1",
                                     local_dict={'Integral': Integral})
        self.assertEqual(fun(3), 9)
        self.assertEqual(fun(y), y**3/3)

    def test_assume_real_variables(self):
        fun=return_parsed_function("x^2", "x", name="f",
                                   assume_real_variables=True)
        self.assertEqual(fun(3),9)
        
        y  = Symbol('y', real=True)
        z  = Symbol('z')
        fun=return_parsed_function("x^2*y", "x", name="f",
                                   assume_real_variables=True)
        self.assertEqual(fun(3),9*y)
        self.assertEqual(fun(z),z**2*y)


    def test_equality(self):
        x=Symbol('x')
        y=Symbol('y')
        from sympy import Eq, Ne

        fun = return_parsed_function("x==y", "x", name="f")
        self.assertTrue(fun(y))
        self.assertFalse(fun(x))
        
        fun = return_parsed_function("x=y", "x", name="f")
        self.assertTrue(fun(y))
        self.assertEqual(fun(x), Eq(x,y))

        fun = return_parsed_function("x!==y", "x", name="f")
        self.assertTrue(fun(x))
        self.assertFalse(fun(y))
        
        fun = return_parsed_function("x!=y", "x", name="f")
        self.assertFalse(fun(y))
        self.assertEqual(fun(x), Ne(x,y))

