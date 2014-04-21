from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from midocs.models import Page, Level
from mitesting.render_assessments import setup_expression_context, answer_code_list, render_question_text
from django.contrib.auth.models import AnonymousUser, User, Permission

from sympy import Symbol, sympify, Function
import random


class TestSetupExpressionContext(TestCase):
    def setUp(self):
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
            seed=self.q.get_new_seed()
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
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="fun question",
            question_type = qt,
            question_privacy = 2,
            solution_privacy = 2,
            )
            
    def new_answer(self, **kwargs):
        return QuestionAnswerOption.objects.create(question=self.q, **kwargs)
    
    def test_answer_code_list(self):
        self.assertEqual(answer_code_list(self.q),[])

        self.new_answer(answer_code="h",
                        answer_type=QuestionAnswerOption.EXPRESSION)
        self.assertEqual(answer_code_list(self.q),['h'])
        self.new_answer(answer_code="h",
                        answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)
        self.assertEqual(answer_code_list(self.q),['h'])
        self.new_answer(answer_code="m",
                        answer_type=QuestionAnswerOption.EXPRESSION)
        self.assertEqual(set(answer_code_list(self.q)),set(['m','h']))
        self.new_answer(answer_code="n",
                        answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)
        self.assertEqual(set(answer_code_list(self.q)),set(['m','h']))

        

class TestRenderQuestionText(TestCase):
    def setUp(self):
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
        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")
        render_results = render_question_text(question_data, solution=True)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")
        
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'], "")

    def test_render_simple(self):
        self.q.question_text="${{f}}({{x}}) = {{fun_x}}$"
        self.q.solution_text="${{x}} = {{n}}$"
        self.q.save()
        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'],
                         "$%s(%s) = %s$" % (
                self.expr_context["f"], self.expr_context["x"],
                self.expr_context["fun_x"]))

        render_results = render_question_text(question_data, solution=True)
        self.assertEqual(render_results['question'], self.q)
        self.assertEqual(render_results['rendered_text'],
                         "$%s = %s$" % (
                self.expr_context["x"], self.expr_context["n"]))

        render_results = render_question_text(question_data, solution=False)
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
        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['rendered_text'], "")
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertEqual(render_results['subparts'][0]['subpart_text'],
                         "%s(%s)" % (self.expr_context["f"],
                                     self.expr_context["x"]))
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertEqual(render_results['subparts'][1]['subpart_text'],
                         "1+2")
        render_results = render_question_text(question_data, solution=True)
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertEqual(render_results['rendered_text'], "")
        self.assertEqual(render_results['subparts'][0]['subpart_text'],
                         "%s" % self.expr_context["fun_x"])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertEqual(render_results['subparts'][1]['subpart_text'],
                         "3")

    def test_render_errors(self):
        self.q.question_text = "{% hmm %}"
        self.q.save()
        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertTrue(render_results['render_error'])
        self.assertTrue("Error in question" in render_results['rendered_text'])
        self.assertTrue("Error in question template" in
                          render_results['render_error_messages'][0])

        render_results = render_question_text(question_data, solution=True)
        self.assertFalse(render_results.get('render_error',False))
        
        self.q.solution_text = "{% %}"
        render_results = render_question_text(question_data, solution=True)
        self.assertTrue(render_results['render_error'])
        self.assertTrue("Error in solution" in render_results['rendered_text'])
        self.assertTrue("Error in solution template" in
                          render_results['render_error_messages'][0])

    def test_render_error_subpart(self):
        self.q.questionsubpart_set.create(question_text="{%%}",
                                          solution_text="{% url hg %}")
        self.q.questionsubpart_set.create(question_text="{% df %}",
                                          solution_text="{% a %}")

        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertTrue(render_results['render_error'])
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertTrue("Error in question subpart" in 
                        render_results['subparts'][0]['subpart_text'])
        self.assertTrue("Error in question subpart a template" in 
                        render_results['render_error_messages'][0])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertTrue("Error in question subpart" in 
                        render_results['subparts'][1]['subpart_text'])
        self.assertTrue("Error in question subpart b template" in 
                        render_results['render_error_messages'][1])

        render_results = render_question_text(question_data, solution=True)
        self.assertTrue(render_results['render_error'])
        self.assertEqual(render_results['subparts'][0]['letter'],"a")
        self.assertTrue("Error in solution subpart" in 
                        render_results['subparts'][0]['subpart_text'])
        self.assertTrue("Error in solution subpart a template" in 
                        render_results['render_error_messages'][0])
        self.assertEqual(render_results['subparts'][1]['letter'],"b")
        self.assertTrue("Error in solution subpart" in 
                        render_results['subparts'][1]['subpart_text'])
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

        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertFalse(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        question_data['show_help'] = True
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])
        
        question_data['user'] = AnonymousUser()
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertTrue(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text=""
        self.q.save()
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertFalse(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text="Solution"
        self.q.hint_text=""
        self.q.save()
        self.q.questionreferencepage_set.get(page=page).delete()
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertTrue(render_results.get('include_solution_link',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")
        render_results = render_question_text(question_data)
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        
    def test_show_help_subparts(self):
        self.q.questionsubpart_set.create(question_text="question",
                                          solution_text="solution",
                                          hint_text="hint")

        Level.objects.create(code="hmm", description="")
        page = Page.objects.create(code="test", title="test")
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")

        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertFalse(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertFalse(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        question_data['show_help'] = True
        render_results = render_question_text(question_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertFalse(render_results['subparts'][0]\
                             .get('include_solution_link',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        question_data['user'] = AnonymousUser()
        render_results = render_question_text(question_data)
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
        render_results = render_question_text(question_data)
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
        render_results = render_question_text(question_data)
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
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        self.q.questionreferencepage_set.create(page=page, question_subpart="a")
        render_results = render_question_text(question_data)
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])


    def test_hint_errors(self):
        self.q.hint_text = "{% %}"
        self.q.save()
        
        question_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(question_data)
        self.assertFalse(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        
        question_data['show_help'] = True
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        self.assertTrue('Error in hint text' in render_results['hint_text'])

        self.q.hint_text = ""
        self.q.save()

        self.q.questionsubpart_set.create(question_text="question",
                                          solution_text="solution",
                                          hint_text="{% h %}")
        render_results = render_question_text(question_data)
        self.assertTrue(render_results.get('hint_template_error',False))
        self.assertFalse(render_results.get('render_error',False))
        self.assertTrue('Error in hint text' in 
                        render_results['subparts'][0]['hint_text'])
        


class TestShowSolutionLink(TestCase):
    def setUp(self):
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
                        question_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True}
                
                        render_results = render_question_text(question_data)
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
                        question_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True}
                
                        render_results = render_question_text(question_data)
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
                        question_data = {"question": self.qs[iq][jq], 
                                         'expression_context':
                                             self.expr_contexts[iq][jq],
                                         'user': self.users[iu][ju],
                                         'show_help': True,
                                         'assessment': asmt}
                
                        render_results = render_question_text(question_data)
                        if ju == 2:
                            self.assertTrue(render_results.get(
                                    'include_solution_link',False))
                        else:
                            self.assertFalse(render_results.get(
                                    'include_solution_link',False))
