from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import SimpleTestCase
from mitesting.utils import *
from sympy import Symbol, sympify
import six

class TestDicts(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_sympy_global_dict(self):

        global_dict = return_sympy_global_dict()
        self.assertEqual(global_dict, {})

        from mitesting.customized_commands import Abs
        global_dict = return_sympy_global_dict(["Abs"])
        global_dict2 = {}
        global_dict2['Abs']=Abs
        self.assertEqual(global_dict, global_dict2)

        global_dict = return_sympy_global_dict(["Abs", "floor, ceiling"])
        from sympy import floor, ceiling
        global_dict2['ceiling']=ceiling
        global_dict2['floor']=floor
        self.assertEqual(global_dict, global_dict2)

        global_dict = return_sympy_global_dict(["Abs", "floor, ceiling",
                                                "min, max, Min, Max",
                                                "nothingvalid", "if"])
        from mitesting.customized_commands import min_including_tuples,\
            max_including_tuples, iif
        global_dict2['min']=min_including_tuples
        global_dict2['Min']=min_including_tuples
        global_dict2['max']=max_including_tuples
        global_dict2['Max']=max_including_tuples
        global_dict2['if']=iif
        self.assertEqual(global_dict, global_dict2)


        

class TestRandomNumber(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_returns_integer_in_range(self):
        from sympy import Integer
        the_num = return_random_number_sample("(1,3,1)")
        self.assertTrue(the_num in range(1,4))
        self.assertTrue(isinstance(the_num, Integer))

    def test_with_no_increment(self):
        from sympy import Integer
        the_num = return_random_number_sample("(-1,5)")
        self.assertTrue(the_num in range(-1,6))
        self.assertTrue(isinstance(the_num, Integer))

    def test_rounding_with_tenths(self):
        valid_answers = [round(0.1*a,1) for a in range(-31,52)]
        for i in range(5):
            the_num = return_random_number_sample("(-3.1,5.1,0.1)")
            self.assertTrue(the_num in valid_answers)

    def test_can_achieve_max_value(self):
        achieved_max = False
        for i in range(1000):
            the_num = return_random_number_sample("(4.04,4.15,0.01)")
            if the_num == 4.15:
                achieved_max = True
                break
        self.assertTrue(achieved_max)
    
    def test_with_global_dict(self):
        global_dict = {"x": sympify(-2), "y": sympify(2)}
        the_num = return_random_number_sample("(x,y)", global_dict=global_dict)
        self.assertTrue(the_num in range(-2,3))
    
    def test_raises_useful_exceptions(self):
        self.assertRaisesRegexp(ValueError, 'Invalid format for random number',
                                return_random_number_sample, "(")
        
        self.assertRaisesRegexp(ValueError, 'require minval <= maxval', 
                                return_random_number_sample, "(5,3)")

        self.assertRaisesRegexp(ValueError, 'Invalid format for random number', 
                                return_random_number_sample, "4")

        self.assertRaisesRegexp(ValueError, 'Invalid format for random number', 
                                return_random_number_sample, "(1,2,3,4)")

        self.assertRaisesRegexp(TypeError, 'random number must contain numbers',
                                return_random_number_sample, "(a,b,c)")


class TestRandomWordPlural(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_with_no_plurals(self):
        word = return_random_word_and_plural("hello, bye, seeya")
        self.assertTrue(word[0] in ["hello", "bye", "seeya"])
        self.assertEqual(word[0]+"s", word[1])

    def test_with_no_plurals(self):
        for i in range(3):
            word = return_random_word_and_plural(
                "(hello, helloes), bye, (seeya, seeyee)")
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
                + '("see ya", \'see yee\')')
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
                " what,kind, of,  list,  'is this?'  ")
            self.assertTrue(word[0] in ["what","kind","of","list","is this?"])
                            
    def test_with_given_index(self):
        word = return_random_word_and_plural("a,b,(c,d),e", index=2)
        self.assertEqual(word[0], "c")
        self.assertEqual(word[1], "d")
        self.assertEqual(word[2], 2)

    def test_with_extra_characters(self):
        word = return_random_word_and_plural("hi!, bye-bye, this_one, me&you,"
                                             + "this@whatever.net")
        self.assertTrue(word[0] in ["hi!","bye-bye", "this_one", "me&you",
                                    "this@whatever.net"])


    def test_raises_useful_exception(self):
        self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(")
        self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(a a)")
        self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "((a,a), a)")
        self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "a,(a,a,a)")
        self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
                                return_random_word_and_plural, "(a,(a,a))")

        # this should raise a value error, but it doesn't yet
        # self.assertRaisesRegexp(ValueError, 'Invalid format for random word',
        #                         return_random_word_and_plural, "a a, a")
       


class TestRandomExpression(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_basic_example(self):
        expr = return_random_expression("hello, bye, seeya")
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
        expr = return_random_expression("x^3, x^2+2*x*y")
        self.assertTrue(expr[0] in [x**3, x**2+2*x*y])

    def test_with_global_dict(self):
        x=Symbol("x")
        y=Symbol("y")
        global_dict = {"v1": x, "v2": y}
        expr = return_random_expression("v1+v2, v1/v2", global_dict=global_dict)
        self.assertTrue(expr[0] in [x+y, x/y])

        from sympy import sin, cos
        u = Symbol("u")
        global_dict = {"f": sin, "g": cos, "x": u }
        expr = return_random_expression("f(x), g(x)", global_dict=global_dict)
        self.assertTrue(expr[0] in [sin(u),cos(u)])

    def test_with_given_index(self):
        x = Symbol('x')
        g = Symbol('g')
        expr = return_random_expression("f(x), g(x), h(x)", index=1)
        self.assertEqual(expr[0], x*g)
        self.assertEqual(expr[1], 1)

    def test_raises_useful_exception(self):
        self.assertRaisesRegexp(ValueError,
                                'Invalid format for random expression',
                                return_random_expression, "(")

class TestParsedFunction(SimpleTestCase):
    def setUp(self):
        random.seed()

    def test_simple_function(self):
        z=Symbol('z')
        fun = return_parsed_function("x^2","x", name="f")
        self.assertEqual(fun(z), z*z)
        self.assertEqual(six.text_type(fun), "f")
    def test_function_other_variables(self):
        w=Symbol('w')
        fun = return_parsed_function("x*y*z - a/y", "y", name="f")
        self.assertEqual(fun(w), sympify("x*w*z-a/w"))
        self.assertEqual(six.text_type(fun), "f")
    def test_function_global_dict(self):
        u=Symbol('u')
        b=Symbol('b')
        fun = return_parsed_function("x*y*z - a/y", "y", name="f1g",
                                     global_dict={"a": b})
        self.assertEqual(fun(u), sympify("x*u*z-b/u"))
        self.assertEqual(six.text_type(fun), "f1g")
        fun = return_parsed_function("x*y*z - a/y", "y", name="f1g",
                                     global_dict={"y": b})
        self.assertEqual(fun(u), sympify("x*u*z-a/u"))

    def test_function_multiple_inputs(self):
        x=Symbol('x')
        y=Symbol('y')
        z=Symbol('z')
        a=Symbol('a')
        fun = return_parsed_function("s/t - a*u", "s,t,u", name="something")
        self.assertEqual(fun(x,y,z), x/y - a*z)
        self.assertEqual(six.text_type(fun), "something")
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
        self.assertEqual(six.text_type(fun), "crazy")
        fun = return_parsed_function("3*x*(x-1)", "& 2 ^ ! &$%", "crazy2")
        self.assertEqual(fun(0), result)
        self.assertEqual(fun(x*y-y**4),result)
        self.assertEqual(six.text_type(fun), "crazy2")
    def test_compose_functions(self):
        x=Symbol('x')
        y=Symbol('y')
        fun1 = return_parsed_function("3*x*(x-1)", "x",name="f")
        fun2 = return_parsed_function("x^2","x",name="g")
        self.assertEqual(fun1(fun2(x)), 3*x**2*(x**2 - 1))
        self.assertEqual(fun2(fun1(x)),9*x**2*(x - 1)**2)
        
        # compose via global_dict
        fun2 = return_parsed_function("f(x)^2","x",name="g", 
                                      global_dict={'f': fun1})
        self.assertEqual(fun2(x),9*x**2*(x - 1)**2)
    
        
        

    def test_raises_useful_exceptions(self):
        self.assertRaisesRegexp(ValueError,
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

