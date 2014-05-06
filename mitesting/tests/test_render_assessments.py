from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from midocs.models import Page, Level
from mitesting.render_assessments import setup_expression_context, return_valid_answer_codes, render_question_text, render_question, get_question_list, render_question_list
from django.contrib.auth.models import AnonymousUser, User, Permission

from sympy import Symbol, sympify, Function
import random


class TestSetupExpressionContext(TestCase):
    def setUp(self):
        random.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 2,
            solution_privacy = 2,
            )
            
    def new_expr(self, **kwargs):
        return Expression.objects.create(question=self.q, **kwargs)


    def test_with_single_expression(self):
        self.new_expr(name="the_x",expression="x")

        random.seed(0)
        results=setup_expression_context(self.q)
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
        results=setup_expression_context(self.q)
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
        results=setup_expression_context(self.q)
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
            results=setup_expression_context(self.q)
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
            results=setup_expression_context(self.q)
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

        results=setup_expression_context(self.q)
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
            from mitesting.render_assessments import get_new_seed
            seed=get_new_seed()
            random.seed(seed)
            results=setup_expression_context(self.q)
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
            results=setup_expression_context(self.q)
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
        results=setup_expression_context(self.q)
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

        results=setup_expression_context(self.q)
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


    def add_allowed_sympy_commands_sets(self, command_sets, 
                                        user_response=False):

        if 'trig' in command_sets:
            scs_trig = SympyCommandSet.objects.create(
                name = 'trig', 
                commands='acosh, acos, acosh, acot, acoth, asin, asinh, atan, '
                + 'atan2, atanh, cos,  cosh, cot, coth, csc, sec, sin, sinh, '
                + 'tan, tanh')
            if user_response:
                self.q.allowed_user_sympy_commands.add(scs_trig)
            else:
                self.q.allowed_sympy_commands.add(scs_trig)
        if 'explog' in command_sets:
            scs_explog = SympyCommandSet.objects.create(
                name = 'explog', commands='exp,ln,log,e')
            if user_response:
                self.q.allowed_user_sympy_commands.add(scs_explog)
            else:
                self.q.allowed_sympy_commands.add(scs_explog)
        if 'absminmax' in command_sets:
            scs_absminmax = SympyCommandSet.objects.create(
                name = 'absminmax', commands='abs, min, max')
            if user_response:
                self.q.allowed_user_sympy_commands.add(scs_absminmax)
            else:
                self.q.allowed_sympy_commands.add(scs_absminmax)
        if 'other' in command_sets:
            scs_other = SympyCommandSet.objects.create(
                name = 'other', commands='if, index, len')
            if user_response:
                self.q.allowed_user_sympy_commands.add(scs_other)
            else:
                self.q.allowed_sympy_commands.add(scs_other)

    def test_initial_sympy_global_dict(self):
        from sympy import sin, cos, log, exp
        self.assertEqual(self.q.return_sympy_global_dict(), {})
        self.assertEqual(self.q.return_sympy_global_dict(user_response=True), 
                         {})
        self.assertEqual(self.q.return_sympy_global_dict(user_response=False),
                         {})

        self.add_allowed_sympy_commands_sets(['trig'])
        self.assertEqual(self.q.return_sympy_global_dict()['cos'],cos)
        self.assertEqual(
            self.q.return_sympy_global_dict(user_response=True)['cos'], cos)
        self.assertEqual(
            self.q.return_sympy_global_dict(user_response=False)['cos'], cos)

        self.q.customize_user_sympy_commands=True
        self.q.save()
        self.assertEqual(self.q.return_sympy_global_dict()['cos'],cos)
        with self.assertRaises(KeyError):
            self.q.return_sympy_global_dict(user_response=True)['cos']
        self.assertEqual(
            self.q.return_sympy_global_dict(user_response=False)['cos'], cos)

    def test_command_set_inclusion(self):
        x=Symbol('x')
        from sympy import sin, cos, log, exp
        self.new_expr(name="sincos", expression="sin(x)*cos(x)")
        self.new_expr(name="explog1", expression="exp(x)*log(x)")
        self.new_expr(name="explog2", expression="e^x*ln(x)")

        results=setup_expression_context(self.q)
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
        results=setup_expression_context(self.q)
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
        results=setup_expression_context(self.q)
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
                          "if(abs_n > 5, min(0, n), max(0,n))")

        self.add_allowed_sympy_commands_sets(['absminmax', 'other'])

        for i in range(10):
            results=setup_expression_context(self.q)

            expr_context = results['expression_context']
            n = expr_context['n'].return_expression()
            self.assertTrue(n in range(-10,-3) + range(4,11))
            if abs(n) > 5:
                self.assertEqual(min(0,n), expr_context['fun_n'])
            else:
                self.assertEqual(max(0,n), expr_context['fun_n'])


    

class TestAnswerCodes(TestCase):
    def setUp(self):
        random.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 2,
            solution_privacy = 2,
            )
            
    def new_answer(self, **kwargs):
        return QuestionAnswerOption.objects.create(question=self.q, **kwargs)
    
    def test_valid_answer_codes(self):
        from django.template import Context
        expr_context = Context({})

        EXPRESSION = QuestionAnswerOption.EXPRESSION
        MULTIPLE_CHOICE = QuestionAnswerOption.MULTIPLE_CHOICE

        self.assertEqual(return_valid_answer_codes(self.q, expr_context),
                         ({},[]))

        self.new_answer(answer_code="h", answer="hh", answer_type=EXPRESSION)
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{})
        self.assertTrue("Invalid answer code" in invalid_answers[0])

        expr_context["h"]=1
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{})
        self.assertTrue("Invalid answer code" in invalid_answers[0])


        expr_context["hh"]=1
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{"h": EXPRESSION })
        self.assertEqual(invalid_answers, [])

        self.new_answer(answer_code="h", answer="", answer_type=MULTIPLE_CHOICE)
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{"h": MULTIPLE_CHOICE})
        self.assertEqual(invalid_answers, [])

        self.new_answer(answer_code="m", answer="mm", answer_type=EXPRESSION)
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{"h": MULTIPLE_CHOICE})
        self.assertTrue("Invalid answer code" in invalid_answers[0])

        expr_context["mm"]=1
        self.new_answer(answer_code="h", answer="", answer_type=MULTIPLE_CHOICE)
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, 
                         {"m": EXPRESSION,"h": MULTIPLE_CHOICE})
        self.assertEqual(invalid_answers, [])

        self.new_answer(answer_code="n", answer="", answer_type=MULTIPLE_CHOICE)
        (valid_answer_codes, invalid_answers) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, 
                         {"m": EXPRESSION,"h": MULTIPLE_CHOICE,
                          'n': MULTIPLE_CHOICE })
        self.assertEqual(invalid_answers, [])



class TestRenderQuestionText(TestCase):
    def setUp(self):
        random.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0,
            )
        self.q.expression_set.create(
            name="f",expression="f,g,h,k", 
            expression_type = Expression.RANDOM_FUNCTION_NAME)
        self.q.expression_set.create(
            name="n", expression="(-10,10)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="fun",expression="x^3+ n*x",
            function_inputs="x",
            expression_type = Expression.FUNCTION)
        self.q.expression_set.create(
            name="x",expression="x,y,z",
            expression_type =Expression.RANDOM_EXPRESSION)
        self.q.expression_set.create(name="fun_x",expression="fun(x)")
        results=setup_expression_context(self.q)
        self.expr_context = results["expression_context"]


    def test_render_blank(self):
        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")
        render_results = render_question_text(render_data, solution=True)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")
        render_results = render_question_text(render_data, solution=False)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")

    def test_render_simple(self):
        self.q.question_text="${{f}}({{x}}) = {{fun_x}}$"
        self.q.solution_text="${{x}} = {{n}}$"
        self.q.save()
        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'],
                         "$%s(%s) = %s$" % (
                self.expr_context["f"], self.expr_context["x"],
                self.expr_context["fun_x"]))

        render_results = render_question_text(render_data, solution=True)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'],
                         "$%s = %s$" % (
                self.expr_context["x"], self.expr_context["n"]))

        render_results = render_question_text(render_data, solution=False)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'],
                         "$%s(%s) = %s$" % (
                self.expr_context["f"], self.expr_context["x"],
                self.expr_context["fun_x"]))

    def test_render_subparts(self):
        self.q.questionsubpart_set.create(question_text="{{f}}({{x}})",
                                          solution_text="{{fun_x}}")
        self.q.questionsubpart_set.create(question_text="1+2",
                                          solution_text="3")
        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertEqual(render_results['rendered_text'], "")
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertEqual(render_results['subparts'][0]['rendered_text'],
                         "%s(%s)" % (self.expr_context["f"],
                                     self.expr_context["x"]))
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertEqual(render_results['subparts'][1]['rendered_text'],
                         "1+2")
        render_results = render_question_text(render_data, solution=True)
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertEqual(render_results['rendered_text'], "")
        self.assertEqual(render_results['subparts'][0]['rendered_text'],
                         "%s" % self.expr_context["fun_x"])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertEqual(render_results['subparts'][1]['rendered_text'],
                         "3")

    def test_render_errors(self):
        self.q.question_text = "{% hmm %}"
        self.q.save()
        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['render_error'])
        self.assertTrue("Error in question" in render_results['rendered_text'])
        self.assertTrue("Error in question template" in
                          render_results['render_error_messages'][0])

        render_results = render_question_text(render_data, solution=True)
        self.assertFalse(render_results.get('render_error',False))
        
        self.q.solution_text = "{% %}"
        render_results = render_question_text(render_data, solution=True)
        self.assertTrue(render_results['render_error'])
        self.assertTrue("Error in solution" in render_results['rendered_text'])
        self.assertTrue("Error in solution template" in
                          render_results['render_error_messages'][0])

    def test_render_error_subpart(self):
        self.q.questionsubpart_set.create(question_text="{%%}",
                                          solution_text="{% url hg %}")
        self.q.questionsubpart_set.create(question_text="{% df %}",
                                          solution_text="{% a %}")

        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['render_error'])
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertTrue("Error in question subpart" in 
                        render_results['subparts'][0]['rendered_text'])
        self.assertTrue("Error in question subpart a template" in 
                        render_results['render_error_messages'][0])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertTrue("Error in question subpart" in 
                        render_results['subparts'][1]['rendered_text'])
        self.assertTrue("Error in question subpart b template" in 
                        render_results['render_error_messages'][1])

        render_results = render_question_text(render_data, solution=True)
        self.assertTrue(render_results['render_error'])
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertTrue("Error in solution subpart" in 
                        render_results['subparts'][0]['rendered_text'])
        self.assertTrue("Error in solution subpart a template" in 
                        render_results['render_error_messages'][0])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertTrue("Error in solution subpart" in 
                        render_results['subparts'][1]['rendered_text'])
        self.assertTrue("Error in solution subpart b template" in 
                        render_results['render_error_messages'][1])

    def test_show_help(self):
        self.q.question_text="Question"
        self.q.solution_text="Solution"
        self.q.hint_text="Hint"
        self.q.save()
        Level.objects.create(code="hmm", description="")
        page = Page.objects.create(code="test", title="test")
        self.q.questionreferencepage_set.create(page=page)

        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertFalse(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        render_data['show_help'] = True
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])
        
        render_data['user'] = AnonymousUser()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertTrue(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text=""
        self.q.save()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text="Solution"
        self.q.hint_text=""
        self.q.save()
        self.q.questionreferencepage_set.get(page=page).delete()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertTrue(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")
        render_results = render_question_text(render_data)
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        
    def test_show_help_subparts(self):
        self.q.questionsubpart_set.create(question_text="question",
                                          solution_text="solution",
                                          hint_text="hint")

        Level.objects.create(code="hmm", description="")
        page = Page.objects.create(code="test", title="test")
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")

        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertFalse(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertFalse(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        render_data['show_help'] = True
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertFalse(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        render_data['user'] = AnonymousUser()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertTrue(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        sp = self.q.questionsubpart_set.all()[0]
        sp.solution_text=""
        sp.save()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertFalse(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        sp.solution_text="Solution"
        sp.hint_text=""
        sp.save()
        self.q.questionreferencepage_set.get(page=page).delete()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertTrue(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        self.q.questionreferencepage_set.create(page=page, question_subpart="b")
        self.q.questionreferencepage_set.create(page=page)
        render_results = render_question_text(render_data)
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        self.q.questionreferencepage_set.create(page=page, question_subpart="a")
        render_results = render_question_text(render_data)
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])


    def test_hint_errors(self):
        self.q.hint_text = "{% %}"
        self.q.save()
        
        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertFalse(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        
        render_data['show_help'] = True
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        self.assertTrue('Error in hint text' in render_results['hint_text'])

        self.q.hint_text = ""
        self.q.save()

        self.q.questionsubpart_set.create(question_text="question",
                                          solution_text="solution",
                                          hint_text="{% h %}")
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        self.assertTrue('Error in hint text' in 
                        render_results['subparts'][0]['hint_text'])
        


class TestShowSolutionLink(TestCase):
    def setUp(self):
        random.seed()
        qt = QuestionType.objects.create(name="question type")
        self.qs=[[],[],[]]
        self.expr_contexts=[[],[],[]]
        for i in range(3):
            for j in range(3):
                self.qs[i].append(Question.objects.create(
                        name="question",
                        question_type = qt,
                        question_privacy = i,
                        solution_privacy = j,
                        solution_text="solution",
                        ))
                results=setup_expression_context(self.qs[i][j])
                self.expr_contexts[i].append(results["expression_context"])

        self.users = [[],[],[]]
        for i in range(3):
            for j in range(3):
                self.users[i].append(User.objects.create_user(
                        "u%s%s" % (i,j), "u%s%s@example.com" % (i,j)))
                if i > 0:
                    p=Permission.objects.get(
                        codename = "view_assessment_%s" % i)
                    self.users[i][j].user_permissions.add(p)
                if j > 0:
                    p=Permission.objects.get(
                        codename = "view_assessment_%s_solution" % j)
                    self.users[i][j].user_permissions.add(p)
            
    def test_show_solution_link(self):
        for iq in range(3):
            for jq in range(3):
                for iu in range(3):
                    for ju in range(3):
                        render_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True}
                
                        render_results = render_question_text(render_data)
                        if ju >= jq:
                            self.assertTrue(render_results.get(
                                    'include_solution_link',False))
                        else:
                            self.assertFalse(render_results.get(
                                    'include_solution_link',False))

    def test_show_solution_link_subparts(self):
        for iq in range(3):
            for jq in range(3):
                self.qs[iq][jq].questionsubpart_set.create(
                    question_text="question",
                    solution_text="solution")

                for iu in range(3):
                    for ju in range(3):
                        render_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True}
                
                        render_results = render_question_text(render_data)
                        if ju >= jq:
                            self.assertTrue(render_results['subparts'][0].get(
                                    'include_solution_link',False))
                        else:
                            self.assertFalse(render_results['subparts'][0].get(
                                    'include_solution_link',False))


    def test_show_solution_link_assessment(self):
        at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=2, solution_privacy=2)
        asmt = Assessment.objects.create(
            code="a", name="a", assessment_type=at)
        for iq in range(3):
            for jq in range(3):
                for iu in range(3):
                    for ju in range(3):
                        render_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True,
                                         'assessment': asmt}
                
                        render_results = render_question_text(render_data)
                        if ju == 2:
                            self.assertTrue(render_results.get(
                                    'include_solution_link',False))
                        else:
                            self.assertFalse(render_results.get(
                                    'include_solution_link',False))

class TestRenderQuestion(TestCase):
    def setUp(self):
        random.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0,
            )
        self.q.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="x",expression="u,v,w,x,y,z,a,b,c,U,V,W,X,Y,Z,A,B,C",
            expression_type =Expression.RANDOM_EXPRESSION)

    def test_render_blank(self):
        question_data=render_question(self.q, question_identifier="blank")
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"blank")

        question_data=render_question(self.q, solution=True, 
                                      question_identifier="blank_sol")
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"blank_sol")
        
        question_data=render_question(self.q, solution=False)
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"")
        
    def test_render_simple(self):
        self.q.question_text = "What?"
        self.q.solution_text = "This."
        self.q.hint_text = "Because"
        self.q.save()
        
        question_data=render_question(self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"What?")
        self.assertTrue(question_data.get("help_available"))
        self.assertEqual(question_data["hint_text"], "Because")
        
        question_data=render_question(self.q, solution=True)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"This.")
        self.assertFalse(question_data.get("help_available"))
        self.assertEqual(question_data.get("hint_text",""), "")

        question_data=render_question(self.q, show_help=False)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"What?")
        self.assertFalse(question_data.get("help_available"))
        self.assertEqual(question_data.get("hint_text",""), "")

        question_data=render_question(self.q, user=AnonymousUser())
        self.assertTrue(question_data.get("help_available"))
        self.assertTrue(question_data.get("include_solution_link",False))
        

    def test_render_subparts(self):
        self.q.question_text = "Main question"
        self.q.solution_text = "Main solution"
        self.q.hint_text = "Main hint"
        self.q.save()
        self.q.questionsubpart_set.create(question_text="subquestion1",
                                          solution_text="subsolution1",
                                          hint_text="subhint1")
        self.q.questionsubpart_set.create(question_text="subquestion2",
                                          solution_text="subsolution2",
                                          hint_text="subhint2")

        question_data=render_question(self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"Main question")
        self.assertTrue(question_data.get("help_available"))
        self.assertFalse(question_data.get("include_solution_link",False))
        self.assertEqual(question_data.get("hint_text",""), "Main hint")
        self.assertEqual(len(question_data["subparts"]),2)

        self.assertEqual(question_data["subparts"][0]["rendered_text"],
                         "subquestion1")
        self.assertTrue(question_data["subparts"][0].get("help_available"))
        self.assertFalse(question_data["subparts"][0]\
                            .get("include_solution_link",False))
        self.assertEqual(question_data["subparts"][0].get("hint_text",""),
                         "subhint1")
        
        self.assertEqual(question_data["subparts"][1]["rendered_text"],
                         "subquestion2")
        self.assertTrue(question_data["subparts"][1].get("help_available"))
        self.assertFalse(question_data["subparts"][1]\
                            .get("include_solution_link",False))
        self.assertEqual(question_data["subparts"][1].get("hint_text",""),
                         "subhint2")

        
    def test_seed(self):
        self.q.question_text = "${{x}} = {{n}}$"
        self.q.save()
        question_data=render_question(self.q)
        text = question_data["rendered_text"]
        seed = question_data["seed"]
        question_data=render_question(self.q, seed=seed)
        self.assertEqual(question_data["rendered_text"],text)
        self.assertEqual(question_data["seed"],seed)
        

    def test_solution_link(self):
        self.q.question_text = "What?"
        self.q.solution_text = "This."
        self.q.hint_text = "Because"
        self.q.save()
  
        question_data=render_question(self.q)
        self.assertTrue(question_data.get("help_available"))
        self.assertFalse(question_data.get("include_solution_link",False))

        question_data=render_question(self.q, user=AnonymousUser())
        self.assertTrue(question_data.get("help_available"))
        self.assertTrue(question_data.get("include_solution_link",False))

        at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=2, solution_privacy=2)
        asmt = Assessment.objects.create(
            code="a", name="a", assessment_type=at)
        
        question_data=render_question(self.q, user=AnonymousUser(),
                                      assessment=asmt)
        self.assertTrue(question_data.get("help_available"))
        self.assertFalse(question_data.get("include_solution_link",False))

        at.question_privacy=0;
        at.solution_privacy=0;
        at.save()
        question_data=render_question(self.q, user=AnonymousUser(),
                                      assessment=asmt)
        self.assertTrue(question_data.get("help_available"))
        self.assertTrue(question_data.get("include_solution_link",False))


    def test_readonly(self):
        answer_code='ans'
        identifier = "abc_5"
        answer_identifier ="0_%s" % (identifier)

        self.q.questionansweroption_set.create(answer_code=answer_code, answer="x")
        self.q.question_text = "{% answer ans %}"
        self.q.save()
        
        question_data=render_question(self.q, question_identifier=identifier)
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20'>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

        question_data=render_question(self.q, question_identifier=identifier,
                                      readonly=True)
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20' readonly>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

    def test_prefilled_answers(self):
        answer_code='ans'
        identifier = "abc_5"
        answer_identifier ="0_%s" % (identifier)
        previous_answer = "complete guess"
        prefilled_answers = []
        prefilled_answers.append({ 
            'answer_code': answer_code,
            'answer': previous_answer })

        self.q.questionansweroption_set.create(answer_code=answer_code, answer="x")
        self.q.question_text = "{% answer " + answer_code + " %}"
        self.q.save()
        
        question_data=render_question(self.q, question_identifier=identifier,
                                      prefilled_answers=prefilled_answers)

        self.assertTrue(question_data["success"])
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20' value='%s'>" % (answer_identifier, answer_identifier, previous_answer)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

        prefilled_answers[0]= { 
            'answer_code': answer_code+"a",
            'answer': previous_answer }

        question_data=render_question(self.q, question_identifier=identifier,
                                      prefilled_answers=prefilled_answers)
        self.assertFalse(question_data['success'])
        self.assertTrue("Invalid previous answer" in question_data["error_message"])
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20'>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])


        prefilled_answers[0]= { 
            'answer_code': answer_code,
            'answer': previous_answer }
        prefilled_answers.append({ 
            'answer_code': answer_code,
            'answer': previous_answer })
        question_data=render_question(self.q, question_identifier=identifier,
                                      prefilled_answers=prefilled_answers)
        self.assertFalse(question_data['success'])
        self.assertFalse("Invalid previous answer" in 
                         question_data["error_message"])
        self.assertTrue("Invalid number of previous answer" in 
                        question_data["error_message"])
        
 
    def test_buttons(self):
        self.q.hint_text="hint"
        self.q.save()

        question_data=render_question(self.q)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertFalse(question_data.get("help_as_buttons",False))
        self.assertTrue(question_data.get("help_available",False))
        
        self.q.computer_graded=True
        self.q.save()

        question_data=render_question(self.q)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_as_buttons",False))
        self.assertFalse(question_data.get("help_available",False))

        self.q.questionansweroption_set.create(answer_code="x", answer="x")
        self.q.question_text="{% answer x %}"
        self.q.save()

        question_data=render_question(self.q)
        
        self.assertTrue(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_as_buttons",False))
        self.assertFalse(question_data.get("help_available",False))

        question_data=render_question(self.q, show_help=False)
        
        self.assertTrue(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertFalse(question_data.get("help_as_buttons",False))
        self.assertFalse(question_data.get("help_available",False))

        question_data=render_question(self.q, auto_submit=True)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertTrue(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_as_buttons",False))

    def test_computer_grade_data(self):
        import pickle, base64
        identifier="one"
        seed = "4c"
        answer_code='ans'
        answer_identifier = "0_%s" % (identifier)
        self.q.expression_set.create(
            name="expr1", expression="n*x", 
            expression_type = Expression.EXPRESSION)
        self.q.expression_set.create(
            name="expr2", expression="n^2-x", 
            expression_type = Expression.EXPRESSION)
        self.q.questionansweroption_set.create(answer_code=answer_code,
                                               answer="expr1")
        self.q.questionansweroption_set.create(answer_code="another",
                                               answer="expr2")
        self.q.question_text = "{% answer ans %}"
        self.q.computer_graded=True
        self.q.save()

        question_data=render_question(self.q, question_identifier=identifier,
                                      seed=seed)

        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        
        self.assertEqual(cgd['identifier'],identifier)
        self.assertEqual(cgd['seed'], seed)
        self.assertFalse(cgd['allow_solution_buttons'])
        self.assertTrue(cgd['record_answers'])
        self.assertEqual(cgd.get('question_set'),None)
        self.assertEqual(cgd.get('assessment_code'),None)
        self.assertEqual(cgd.get('assessment_seed'),None)
        self.assertEqual(cgd['answer_data'],
                         {answer_identifier: 
                          {'code': answer_code, 'points': 1, 
                           'type': QuestionAnswerOption.EXPRESSION}})

        question_data=render_question(self.q, record_answers=False,
                                      allow_solution_buttons=True)
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        self.assertFalse(cgd['record_answers'])
        self.assertTrue(cgd['allow_solution_buttons'])
         
        question_data=render_question(self.q, record_answers=True,
                                      allow_solution_buttons=False)
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        self.assertTrue(cgd['record_answers'])
        self.assertFalse(cgd['allow_solution_buttons'])

    def test_computer_grade_data_assessment(self):
        import pickle, base64

        identifier="one"
        seed = "4c"
        assessment_seed = "12d"
        assessment_code = "the_test"
        question_set=5

        self.q.questionansweroption_set.create(answer_code="x", answer="x")
        self.q.question_text="{% answer x %}"
        self.q.save()

        at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=2, solution_privacy=2)
        asmt = Assessment.objects.create(
            code=assessment_code, name="a", assessment_type=at)


        self.q.computer_graded=True
        self.q.save()

        question_data=render_question(self.q, question_identifier=identifier,
                                      seed=seed, assessment=asmt,
                                      assessment_seed=assessment_seed,
                                      question_set = question_set)
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        
        self.assertEqual(cgd['identifier'],identifier)
        self.assertEqual(cgd['seed'], seed)
        self.assertEqual(cgd['assessment_code'], assessment_code)
        self.assertEqual(cgd['assessment_seed'], assessment_seed)
        self.assertEqual(cgd['question_set'], question_set)


class TestGetQuestionList(TestCase):

    def setUp(self):
        random.seed()
        
        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            )

        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            )
        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at)
        
        self.qsa1=self.asmt.questionassigned_set.create(question=self.q1)
        self.qsa2=self.asmt.questionassigned_set.create(question=self.q2)
        self.qsa3=self.asmt.questionassigned_set.create(question=self.q3)
        self.qsa4=self.asmt.questionassigned_set.create(question=self.q4)

    
    def test_one_question_per_question_set(self):
        
        for i in range(10):
            question_list = get_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]
            self.assertEqual(question_ids, [1,2,3,4])
            
            question_sets = [ql['question_set'] for ql in question_list]
            self.assertEqual(question_sets, [1,2,3,4])
            
            points = [ql['points'] for ql in question_list]
            self.assertEqual(points,["","","",""])

            for ql in question_list:
                seed = ql['seed']
                self.assertTrue(int(seed) >= 0)
                self.assertTrue(int(seed) <= 1000000000000)


    def test_multiple_questions_per_question_set(self):
        self.qsa1.question_set=2
        self.qsa1.save()
        self.qsa3.question_set=4
        self.qsa3.save()

        valid_options = [[1,3],[1,4],[2,3],[2,4]]

        options_used = [False, False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]
            self.assertTrue(question_ids in valid_options)

            one_used = valid_options.index(question_ids)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


        self.qsa1.question_set=4
        self.qsa1.save()

        valid_options = [[2,1],[2,3],[2,4]]

        options_used = [False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]
            self.assertTrue(question_ids in valid_options)

            one_used = valid_options.index(question_ids)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


    def test_with_points(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa4.question_set=2
        self.qsa4.save()

        self.asmt.questionsetdetail_set.create(question_set=3,
                                               points = 5)
        self.asmt.questionsetdetail_set.create(question_set=2,
                                               points = 7.3)

        
        valid_options = [[2,1],[2,3],[4,1],[4,3]]

        options_used = [False, False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt)
            
            points = [ql['points'] for ql in question_list]
            self.assertEqual(points, [7.3,5])

            question_ids = [ql['question'].id for ql in question_list]
            self.assertTrue(question_ids in valid_options)

            one_used = valid_options.index(question_ids)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


class TestRenderQuestionList(TestCase):
    
    def setUp(self):
        random.seed()
   
        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 1 text.",
            solution_text = "Question number 1 solution.",
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 2 text.",
            solution_text = "Question number 2 solution.",
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 3 text.",
            solution_text = "Question number 3 solution.",
            )

        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 4 text.",
            solution_text = "Question number 4 solution.",
            )
        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at)
        
        self.qsa1=self.asmt.questionassigned_set.create(question=self.q1)
        self.qsa2=self.asmt.questionassigned_set.create(question=self.q2)
        self.qsa3=self.asmt.questionassigned_set.create(question=self.q3)
        self.qsa4=self.asmt.questionassigned_set.create(question=self.q4)


    def test_no_question_groups_all_orders(self):
        self.qsa4.delete()

        valid_orders = []
        orders_used = []
        for i in range(3):
            for j in range(3):
                if i==j:
                    continue
                for k in range(3):
                    if k==i or k==j:
                        continue
                    valid_orders.append([i+1, j+1, k+1])
                    orders_used.append(False)

        for i in range(200):
            question_list, seed = render_question_list(self.asmt)
            for question_dict in question_list:
                self.assertEqual(question_dict['points'],"")
                self.assertFalse(question_dict['previous_same_group'])
            question_ids = [ql['question'].id for ql in question_list]
            self.assertTrue(question_ids in valid_orders)
            one_used = valid_orders.index(question_ids)
            orders_used[one_used]=True
            
            if False not in orders_used:
                break

        self.assertTrue(False not in orders_used)


    def test_no_question_groups_fixed_order(self):
        self.asmt.fixed_order=True
        self.asmt.save()
            
        for j in range(10):
            question_list, seed = render_question_list(self.asmt)
            for (i,question_dict) in enumerate(question_list):
                self.assertEqual(question_dict['question'].id, i+1)
                self.assertEqual(question_dict['question_set'], i+1)
                self.assertEqual(question_dict['points'],"")
                qseed = int(question_dict['seed'])
                self.assertTrue(qseed >= 0 and qseed < 100000000000)
                self.assertEqual(question_dict['group'],"")
                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %s text." % (i+1))
                self.assertFalse(question_dict['previous_same_group'])


    def test_groups_random_order(self):
        self.asmt.questionsetdetail_set.create(question_set=1,
                                               group="apple")
        self.asmt.questionsetdetail_set.create(question_set=4,
                                               group="apple")
        for j in range(10):
            question_list, seed = render_question_list(self.asmt)
            hit_first_group_member=False
            expected_next_group_member=None
            for (i,question_dict) in enumerate(question_list):
                if hit_first_group_member:
                    self.assertTrue(question_dict['previous_same_group'])
                    self.assertEqual(question_dict['group'],'apple')
                    self.assertEqual(question_dict['question'].id, 
                                     expected_next_group_member)
                    hit_first_group_member = False
                        
                else:
                    self.assertFalse(question_dict['previous_same_group'])
                    if question_dict['group'] == 'apple':
                        hit_first_group_member = True
                        if question_dict['question'].id == 1:
                            expected_next_group_member = 4
                        else:
                            expected_next_group_member = 1

                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %s text." % question_dict['question'].id)


        self.asmt.questionsetdetail_set.create(question_set=2,
                                               group="appl")
        self.asmt.questionsetdetail_set.create(question_set=3,
                                               group="appl")

        for j in range(10):
            question_list, seed = render_question_list(self.asmt)
            hit_first_group_member=False
            expected_next_group_member=None
            for (i,question_dict) in enumerate(question_list):
                if hit_first_group_member:
                    self.assertTrue(question_dict['previous_same_group'])
                    self.assertEqual(question_dict['group'],group_found)
                    self.assertEqual(question_dict['question'].id, 
                                     expected_next_group_member)
                    hit_first_group_member = False
                        
                else:
                    self.assertFalse(question_dict['previous_same_group'])
                    group_found = question_dict['group']
                    if group_found == 'apple':
                        hit_first_group_member = True
                        if question_dict['question'].id == 1:
                            expected_next_group_member = 4
                        else:
                            expected_next_group_member = 1
                    elif group_found == 'appl':
                        hit_first_group_member = True
                        if question_dict['question'].id == 2:
                            expected_next_group_member = 3
                        else:
                            expected_next_group_member = 2
                        
                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %s text." % question_dict['question'].id)



    def test_groups_fixed_order(self):
        self.asmt.fixed_order=True
        self.asmt.save()

        self.asmt.questionsetdetail_set.create(question_set=1,
                                               group="apple")
        self.asmt.questionsetdetail_set.create(question_set=4,
                                               group="apple")
        for i in range(3):
            question_list, seed = render_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]
            self.assertEqual(question_ids, [1,2,3,4])
            psg = [ql['previous_same_group'] for ql in question_list]
            self.assertEqual(psg, [False,False,False,False])
            groups = [ql['group'] for ql in question_list]
            self.assertEqual(groups[0], "apple")
            self.assertEqual(groups[3], "apple")


        self.asmt.questionsetdetail_set.create(question_set=2,
                                               group="appl")
        self.asmt.questionsetdetail_set.create(question_set=3,
                                               group="appl")

        for i in range(3):
            question_list, seed = render_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]
            self.assertEqual(question_ids, [1,2,3,4])
            psg = [ql['previous_same_group'] for ql in question_list]
            self.assertEqual(psg, [False,False,True,False])
            groups = [ql['group'] for ql in question_list]
            self.assertEqual(groups, ["apple", "appl", "appl", "apple"])


    def test_multiple_in_question_set(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa2.question_set=7
        self.qsa2.save()
        self.qsa3.question_set=3
        self.qsa3.save()
        self.qsa4.question_set=7
        self.qsa4.save()
        
        valid_options=[[1,2],[2,1],[1,4],[4,1],
                       [3,2],[2,3],[3,4],[4,3]]

        options_used = [False, False, False, False,
                        False, False, False, False]

        for j in range(200):
            question_list, seed = render_question_list(self.asmt)
            question_ids = [ql['question'].id for ql in question_list]

            self.assertTrue(question_ids in valid_options)
            
            one_used = valid_options.index(question_ids)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)
    


    def test_points(self):
        self.assertEqual(self.asmt.get_total_points(),0)
        question_list, seed = render_question_list(self.asmt)
        
        points = [ql['points'] for ql in question_list]
        self.assertEqual(points,["","","",""])

        self.asmt.questionsetdetail_set.create(question_set=3,
                                               points = 5)
        self.assertEqual(self.asmt.get_total_points(),5)
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa4.question_set=2
        self.qsa4.save()

        self.asmt.questionsetdetail_set.create(question_set=2,
                                               points = 7.3)

        
        valid_options = [[2,1],[2,3],[4,1],[4,3],
                         [1,2],[3,2],[1,4],[3,4]]

        options_used = [False, False, False, False,
                        False, False, False, False]

        self.assertEqual(self.asmt.get_total_points(),12.3)

        for i in range(100):
            question_list, seed = render_question_list(self.asmt)

            points = [ql['points'] for ql in question_list]
            qs1 = question_list[0]['question_set']
            if qs1 == 3:
                self.assertEqual(points, [5,7.3])
            else:
                self.assertEqual(points, [7.3,5])

            question_ids = [ql['question'].id for ql in question_list]
            self.assertTrue(question_ids in valid_options)

            one_used = valid_options.index(question_ids)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


    def test_solution(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa2.question_set=7
        self.qsa2.save()
        self.qsa3.question_set=3
        self.qsa3.save()
        self.qsa4.question_set=7
        self.qsa4.save()
        
        valid_options=[[1,2],[2,1],[1,4],[4,1],
                       [3,2],[2,3],[3,4],[4,3]]


        for j in range(3):
            question_list, seed = render_question_list(self.asmt, solution=True)
            question_ids = [ql['question'].id for ql in question_list]

            self.assertTrue(question_ids in valid_options)
            
            for question_dict in question_list:
                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %s solution."
                    % question_dict['question'].id)
            
