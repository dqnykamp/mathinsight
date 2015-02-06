from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import six

from django.test import SimpleTestCase
from mitesting.math_objects import *
from django.template import TemplateSyntaxError, Context, Template
from sympy import Symbol, diff, Tuple, sympify
from mitesting.sympy_customized import latex
import random

class MathObjectTests(SimpleTestCase):
    
    def test_round(self):
        context=Context({"a": 1.2345})
        result=Template("{% load testing_tags %}{{a|round}}").render(context)
        self.assertEqual(result,"1")
        result=Template("{% load testing_tags %}{{a|round:3}}").render(context)
        self.assertEqual(result,"1.235")

        x=Symbol('x')
        context=Context({"a": 1.2345*x})
        result=Template("{% load testing_tags %}{{a|round:3}}").render(context)
        self.assertEqual(result,latex(1.235*x))

        context=Context({"a": math_object(1.2345*x)})
        result=Template("{% load testing_tags %}{{a|round:3}}").render(context)
        self.assertEqual(result,latex(1.235*x))
        
    def test_evalf(self):
        """
        #These fail due to behavior of evalf.

        context=Context({"a": 1.2345})
        result=Template("{% load testing_tags %}{{a|evalf:4}}").render(context)
        self.assertEqual(result,"1.235")

        x=Symbol('x')
        context=Context({"a": 1.2345*x})
        result=Template("{% load testing_tags %}{{a|evalf:4}}").render(context)
        self.assertEqual(result,latex(1.235*x))

        context=Context({"a": math_object(1.2345*x)})
        result=Template("{% load testing_tags %}{{a|evalf:4}}").render(context)
        self.assertEqual(result,latex(1.235*x))
        """

        context=Context({"a": 1.2345})
        result=Template("{% load testing_tags %}{{a|evalf:3}}").render(context)
        self.assertEqual(result,"1.23")

        x=Symbol('x')
        context=Context({"a": 1.2345*x})
        result=Template("{% load testing_tags %}{{a|evalf:3}}").render(context)
        self.assertEqual(result,latex(1.23*x))

        context=Context({"a": math_object(1.2345*x)})
        result=Template("{% load testing_tags %}{{a|evalf:3}}").render(context)
        self.assertEqual(result,latex(1.23*x))
        
