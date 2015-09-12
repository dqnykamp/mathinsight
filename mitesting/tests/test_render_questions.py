from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, ExpressionFromAnswer
from midocs.models import Page, PageType
from mitesting.render_questions import setup_expression_context, return_valid_answer_codes, render_question_text, render_question, process_expressions_from_answers
from mitesting.utils import get_new_seed
from micourses.models import Course, Assessment, AssessmentType, \
    STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from mitesting.sympy_customized import SymbolCallable, Symbol, Dummy
from django.contrib.auth.models import AnonymousUser, User, Permission


from sympy import sympify
import random
import json

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
        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=0)
        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        self.assertEqual(expression_context['the_x'], Symbol('x', real=True))
        self.assertEqual(expression_context['_sympy_local_dict_']['the_x'], Symbol('x', real=True))

    def test_with_composed_expressions(self):
        self.new_expr(name="expr",expression="x*x")
        self.new_expr(name="expr2",expression="expr/y")
        self.new_expr(name="expr3",expression="5*expr2 + expr*z")

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1)
        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)
        self.assertEqual(expression_context['expr'], x**2)
        self.assertEqual(expression_context['expr2'], x**2/y)
        self.assertEqual(expression_context['expr3'], 5*x**2/y + x**2*z)
        self.assertEqual(expression_context['_sympy_local_dict_']['expr'], x**2)
        self.assertEqual(expression_context['_sympy_local_dict_']['expr2'], x**2/y)
        self.assertEqual(expression_context['_sympy_local_dict_']['expr3'],
                         5*x**2/y + x**2*z)

 
    def test_overwriting_expressions(self):
        self.new_expr(name="a",expression="z/y")
        self.new_expr(name="b",expression="3*a")
        self.new_expr(name="a",expression="x+y")

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=2)
        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        z=Symbol('z', real=True)
        self.assertEqual(expression_context['a'], x+y)
        self.assertEqual(expression_context['b'], 3*z/y)
        self.assertEqual(expression_context['_sympy_local_dict_']['a'], x+y)
        self.assertEqual(expression_context['_sympy_local_dict_']['b'], 3*z/y)


    def test_with_function_names(self):
        self.new_expr(name="f",expression="f,g,h,k", 
                      expression_type = Expression.RANDOM_FUNCTION_NAME)
        self.new_expr(name="a",expression="3*f(x)+2")

        rng = random.Random()

        for i in range(10):
            results=setup_expression_context(self.q, rng=rng, seed=i)
            self.assertTrue(results['expression_context']['_user_dict_'] in  \
                                [{item: SymbolCallable(str(item),real=True)} for item in \
                                     ['f','g','h','k']])
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=Symbol('x', real=True)
            f = expression_context['f'].return_expression()
            self.assertTrue(f in [SymbolCallable(str(item), real=True) for item in \
                                      ['f','g','h','k']])
            self.assertEqual(expression_context['a'], 3*f(x)+2)
            self.assertEqual(expression_context['_sympy_local_dict_']['f'], f)
            self.assertEqual(expression_context['_sympy_local_dict_']['a'], 3*f(x)+2)

    
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
        
        rng = random.Random()

        for i in range(10):
            results=setup_expression_context(self.q, rng=rng, seed=i)
            self.assertEqual(results['expression_context']['_user_dict_'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=Symbol('x', real=True)
            m = expression_context['m'].return_expression()
            n = expression_context['n'].return_expression()
            self.assertTrue(m > n)
            self.assertTrue(m != 0)
            self.assertTrue(n != 0)
            self.assertTrue(m in range(-4, 5))
            self.assertTrue(n in range(-4, 5))
            self.assertEqual(expression_context['_sympy_local_dict_']['m'], m)
            self.assertEqual(expression_context['_sympy_local_dict_']['n'], n)

    def test_fail_conditions(self):
        self.new_expr(name="n", expression="(-4,4)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="n_greater_than_4", expression="n > 4", 
                      expression_type = Expression.CONDITION)

        rng = random.Random()
        rng.seed()
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)
        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertTrue(results['failed_conditions'])
        self.assertEqual("Condition n_greater_than_4 was not met",
                         results['failed_condition_message'])
        self.assertFalse(results['error_in_expressions'])
        expression_context = results['expression_context']
        n = expression_context['n'].return_expression()
        self.assertTrue(n in range(-4, 5))
        self.assertEqual(expression_context['_sympy_local_dict_']['n'], n)


    def test_repeatable_results(self):
        self.new_expr(name="x", expression="x,y,z,u,v,w", 
                      expression_type = Expression.RANDOM_EXPRESSION)
        self.new_expr(name="y", expression="x,y,z,u,v,w", 
                      expression_type = Expression.RANDOM_EXPRESSION)
        self.new_expr(name="m", expression="(-10,10)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="n", expression="(-10,10)", 
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="x_not_equal_y", expression="x !== y", 
                      expression_type = Expression.CONDITION)
        self.new_expr(name="n_greater_than_m", expression="n > m", 
                      expression_type = Expression.CONDITION)

        for i in range(10):

            rng = random.Random()
            rng.seed()
            seed=get_new_seed(rng=rng)

            results=setup_expression_context(self.q, rng=rng, seed=seed)
            self.assertEqual(results['expression_context']['_user_dict_'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            x=expression_context["x"]
            y=expression_context["y"]
            m=expression_context["m"]
            n=expression_context["n"]
            self.assertTrue(x != y)
            self.assertTrue(n > m)
            self.assertTrue(x in [Symbol(item, real=True) for item in 
                                  ["x","y","z","u","v","w"]])
            self.assertTrue(y in [Symbol(item, real=True) for item in 
                                  ["x","y","z","u","v","w"]])
            self.assertTrue(m in range(-10,11))
            self.assertTrue(n in range(-10,11))
        
            #try again with same seed
            results=setup_expression_context(self.q, rng=rng, seed=seed)
            self.assertEqual(results['expression_context']['_user_dict_'], {})
            self.assertFalse(results['failed_conditions'])
            self.assertFalse(results['error_in_expressions'])
            expression_context = results['expression_context']
            self.assertEqual(x,expression_context["x"])
            self.assertEqual(y,expression_context["y"])
            self.assertEqual(m,expression_context["m"])
            self.assertEqual(n,expression_context["n"])


    def test_with_error(self):
        rng = random.Random()
        rng.seed()

        self.new_expr(name="x", expression="(")
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)

        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertTrue(results['error_in_expressions'])
        expression_error = results['expression_error']
        self.assertTrue("Error in expression: x" in expression_error['x'])
        self.assertEqual("??", results['expression_context']['x'])
        self.assertEqual(Symbol("??"), results['expression_context']['_sympy_local_dict_']['x'])

    def test_with_error_post_user(self):
        rng = random.Random()
        rng.seed()

        self.new_expr(name="x", expression="(", post_user_response=True)
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)

        self.assertFalse(results['failed_conditions'])
        self.assertFalse(results['error_in_expressions'])
        self.assertTrue(results['error_in_expressions_post_user'])
        self.assertEqual(results['expression_error'],{})
        expression_error = results['expression_error_post_user']
        self.assertTrue("Error in expression: x" in expression_error['x'])
        self.assertEqual("??", results['expression_context']['x'])
        self.assertEqual(Symbol("??"), results['expression_context']['_sympy_local_dict_']['x'])



    def test_with_multiple_errors(self):
        self.new_expr(name="e1", expression="3*x^2/z")
        self.new_expr(name="e2", expression="e1[0]+y")
        self.new_expr(name="e3", expression="e2*e1+z")
        self.new_expr(name="e4", expression="e3/")
        self.new_expr(name="e5", expression="e2/e1 + e3/e4")

        rng = random.Random()
        rng.seed()
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)
        self.assertEqual(results['expression_context']['_user_dict_'], {})
        self.assertFalse(results['failed_conditions'])
        self.assertTrue(results['error_in_expressions'])
        expression_error = results['expression_error']
        self.assertTrue("Error in expression: e2" in expression_error['e2'])
        self.assertTrue("Error in expression: e4" in expression_error['e4'])
        self.assertEqual(expression_error.get('e1'), None)
        self.assertEqual(expression_error.get('e3'), None)
        self.assertEqual(expression_error.get('e5'), None)
        x=Symbol("x", real=True)
        z=Symbol("z", real=True)
        q=Symbol("??")
        expr_context=results['expression_context']
        self.assertEqual(expr_context['e1'], 3*x**2/z)
        self.assertEqual(expr_context['e2'], "??")
        self.assertEqual(expr_context['e3'], q*3*x**2/z+z)
        self.assertEqual(expr_context['e4'], "??")
        self.assertEqual(expr_context['e5'],q/(3*x**2/z)+(q*3*x**2/z+z)/q)
        self.assertEqual(Symbol("??"), expr_context['_sympy_local_dict_']['e2'])
        self.assertEqual(Symbol("??"), expr_context['_sympy_local_dict_']['e2'])
        self.assertEqual(Symbol("??"), expr_context['_sympy_local_dict_']['e2'])


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
        if 'i' in command_sets:
            scs_i = SympyCommandSet.objects.create(
                name = 'i', commands='i')
            if user_response:
                self.q.allowed_user_sympy_commands.add(scs_i)
            else:
                self.q.allowed_sympy_commands.add(scs_i)

    def test_initial_sympy_local_dict(self):
        from mitesting.user_commands import sin, cos, log, exp
        self.assertEqual(self.q.return_sympy_local_dict(), {})
        self.assertEqual(self.q.return_sympy_local_dict(user_response=True), 
                         {})
        self.assertEqual(self.q.return_sympy_local_dict(user_response=False),
                         {})

        self.add_allowed_sympy_commands_sets(['trig'])
        self.assertEqual(self.q.return_sympy_local_dict()['cos'],cos)
        self.assertEqual(
            self.q.return_sympy_local_dict(user_response=True)['cos'], cos)
        self.assertEqual(
            self.q.return_sympy_local_dict(user_response=False)['cos'], cos)

        self.q.customize_user_sympy_commands=True
        self.q.save()
        self.assertEqual(self.q.return_sympy_local_dict()['cos'],cos)
        with self.assertRaises(KeyError):
            self.q.return_sympy_local_dict(user_response=True)['cos']
        self.assertEqual(
            self.q.return_sympy_local_dict(user_response=False)['cos'], cos)

    def test_command_set_inclusion(self):
        x=Symbol('x')
        from mitesting.user_commands import sin, cos, log, exp, ln
        from sympy import I
        self.new_expr(name="sincos", expression="sin(x)*cos(x)", real_variables=False)
        self.new_expr(name="explog1", expression="exp(x)*log(x)", real_variables=False)
        self.new_expr(name="explog2", expression="e^x*log(x)", real_variables=False)
        self.new_expr(name="expln1", expression="exp(x)*ln(x)", real_variables=False)
        self.new_expr(name="expln2", expression="e^x*ln(x)", real_variables=False)
        self.new_expr(name="complex", expression="5*i+1-2i*i", real_variables=False)

        rng = random.Random()
        rng.seed()
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)
        expression_context = results['expression_context']

        self.assertEqual(Symbol('sin')*Symbol('cos')*x**2,
                         expression_context["sincos"])
        self.assertEqual(Symbol('sin')*Symbol('cos')*x**2,
                         expression_context['_sympy_local_dict_']["sincos"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         expression_context["explog1"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         expression_context['_sympy_local_dict_']["explog1"])
        self.assertEqual(Symbol('e')**x*Symbol('log')*x,
                         expression_context["explog2"])
        self.assertEqual(Symbol('e')**x*Symbol('log')*x,
                         expression_context['_sympy_local_dict_']["explog2"])
        self.assertEqual(Symbol('exp')*Symbol('ln')*x**2,
                         expression_context["expln1"])
        self.assertEqual(Symbol('exp')*Symbol('ln')*x**2,
                         expression_context['_sympy_local_dict_']["expln1"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         expression_context["expln2"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         expression_context['_sympy_local_dict_']["expln2"])
        self.assertEqual(5*Symbol('i')+1-2*Symbol('i')**2,
                         expression_context["complex"])
        self.assertEqual(5*Symbol('i')+1-2*Symbol('i')**2,
                         expression_context['_sympy_local_dict_']["complex"])

        self.add_allowed_sympy_commands_sets(['trig'])
        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)
        expression_context = results['expression_context']
        self.assertEqual(sin(x)*cos(x),
                         expression_context["sincos"])
        self.assertEqual(sin(x)*cos(x),
                         expression_context['_sympy_local_dict_']["sincos"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         expression_context["explog1"])
        self.assertEqual(Symbol('exp')*Symbol('log')*x**2,
                         expression_context['_sympy_local_dict_']["explog1"])
        self.assertEqual(Symbol('e')**x*Symbol('log')*x,
                         expression_context["explog2"])
        self.assertEqual(Symbol('e')**x*Symbol('log')*x,
                         expression_context['_sympy_local_dict_']["explog2"])
        self.assertEqual(Symbol('exp')*Symbol('ln')*x**2,
                         expression_context["expln1"])
        self.assertEqual(Symbol('exp')*Symbol('ln')*x**2,
                         expression_context['_sympy_local_dict_']["expln1"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         expression_context["expln2"])
        self.assertEqual(Symbol('e')**x*Symbol('ln')*x,
                         expression_context['_sympy_local_dict_']["expln2"])
        self.assertEqual(5*Symbol('i')+1-2*Symbol('i')**2,
                         expression_context["complex"])
        self.assertEqual(5*Symbol('i')+1-2*Symbol('i')**2,
                         expression_context['_sympy_local_dict_']["complex"])
       
        self.add_allowed_sympy_commands_sets(['explog'])
        self.add_allowed_sympy_commands_sets(['i'])

        seed = get_new_seed(rng)
        results=setup_expression_context(self.q, rng=rng, seed=seed)
        expression_context = results['expression_context']
        self.assertEqual(sin(x)*cos(x),
                         expression_context["sincos"])
        self.assertEqual(sin(x)*cos(x),
                         expression_context['_sympy_local_dict_']["sincos"])
        self.assertEqual(exp(x)*log(x),
                         expression_context["explog1"])
        self.assertEqual(exp(x)*log(x),
                         expression_context['_sympy_local_dict_']["explog1"])
        self.assertEqual(exp(x)*log(x),
                         expression_context["explog2"])
        self.assertEqual(exp(x)*log(x),
                         expression_context['_sympy_local_dict_']["explog2"])
        self.assertEqual(exp(x)*ln(x),
                         expression_context["expln1"])
        self.assertEqual(exp(x)*ln(x),
                         expression_context['_sympy_local_dict_']["expln1"])
        self.assertEqual(exp(x)*ln(x),
                         expression_context["expln2"])
        self.assertEqual(exp(x)*ln(x),
                         expression_context['_sympy_local_dict_']["expln2"])
        self.assertEqual(5*I+3,
                         expression_context["complex"])
        self.assertEqual(5*I+3,
                         expression_context['_sympy_local_dict_']["complex"])

        
    
    def test_customized_command_inclusion(self):
        self.new_expr(name="n", expression="(-10,10)",
                      expression_type = Expression.RANDOM_NUMBER)
        self.new_expr(name="abs_n", expression="abs(n)")
        self.new_expr(name="large_n", expression="abs_n > 3",
                      expression_type = Expression.CONDITION)
        self.new_expr(name="fun_n", expression = \
                          "if(abs_n > 5, min(0, n), max(0,n))")

        self.add_allowed_sympy_commands_sets(['absminmax', 'other'])

        rng = random.Random()
        rng.seed()

        for i in range(10):
            seed = get_new_seed(rng)
            results=setup_expression_context(self.q, rng=rng, seed=seed)

            expr_context = results['expression_context']
            n = expr_context['n'].return_expression()
            self.assertTrue(n in list(range(-10,-3)) + list(range(4,11)))
            if abs(n) > 5:
                self.assertEqual(min(0,n), expr_context['fun_n'])
            else:
                self.assertEqual(max(0,n), expr_context['fun_n'])


    def test_parsed_functions(self):
        self.new_expr(name="f",expression="x^2",
                      expression_type=Expression.FUNCTION,
                      function_inputs="x")
        
        self.new_expr(name="f_y_1",expression="f(y)+1")

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1)
        expression_context = results['expression_context']
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        self.assertEqual(expression_context['f'], x**2)
        self.assertEqual(expression_context['f_y_1'], y**2+1)


    def test_expression_with_alternates(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        self.new_expr(name="a",expression="a,b,c",
                      expression_type=Expression.EXPRESSION_WITH_ALTERNATES)
        self.new_expr(name="x_a",expression="x+a")
        self.new_expr(name="f",expression="x^2+a", 
                      expression_type=Expression.FUNCTION,
                      function_inputs="x")
        self.new_expr(name="f_y",expression="f(y)")
        

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1)
        expression_context = results['expression_context']

        self.assertEqual(expression_context['a'], a)
        self.assertEqual(expression_context['x_a'], x+a)
        self.assertEqual(expression_context['f'], x**2+a)
        self.assertEqual(expression_context['f_y'], y**2+a)
        
        alternate_exprs=expression_context['_alternate_exprs_']
        self.assertEqual(alternate_exprs['a'], [b,c])
        self.assertEqual(alternate_exprs['x_a'], [x+b, x+c])
        self.assertEqual(alternate_exprs['f'], [x**2+b, x**2+c])
        self.assertEqual(alternate_exprs['f_y'], [y**2+b, y**2+c])


    def test_parse_subscripts(self):
        a=Symbol('a', real=True)
        b=Symbol('b', real=True)
        c=Symbol('c', real=True)
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        self.new_expr(name="xx",expression="u,v,w,x,y,z",
                      expression_type=Expression.RANDOM_EXPRESSION)
        self.new_expr(name="nn",expression="n,m,s,t",
                      expression_type=Expression.RANDOM_EXPRESSION)
        self.new_expr(name="xx_nn_a",expression="xx_nn", parse_subscripts=True)
        self.new_expr(name="xx_nn_b",expression="xx_nn", parse_subscripts=False)
        self.new_expr(name="xx_nnp1_a",expression="xx_(nn+1)", parse_subscripts=True)
        self.new_expr(name="xx_nnp1_b",expression="xx_(nn+1)", parse_subscripts=False)
        self.new_expr(name="xx_plus_5_xx_nn",expression="xx+5xx_nn", parse_subscripts=True)

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1)
        expression_context = results['expression_context']

        xx=expression_context['xx']
        nn=expression_context['nn']
        self.assertEqual(expression_context['xx_nn_a'], 
                         Symbol('%s_%s' % (xx,nn), real=True))
        self.assertEqual(expression_context['xx_nn_b'], 
                         Symbol('xx_nn', real=True))
        self.assertEqual(expression_context['xx_nnp1_a'], 
                         Symbol('%s_%s + 1' % (xx,nn), real=True))
        self.assertEqual(expression_context['xx_nnp1_b'], 
                         Symbol('xx_', real=True)*(nn+1))
        self.assertEqual(expression_context["xx_plus_5_xx_nn"],
                         xx+5*expression_context['xx_nn_a'])




class TestSetupExpressionContextUserResponse(TestCase):
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

    def new_expr_from_answer(self, **kwargs):
        return ExpressionFromAnswer.objects.create(question=self.q, **kwargs)
    
    def test_expressions_from_answers(self):
        self.new_expr(name="a",expression="y+x^2")
        self.new_expr_from_answer(name="b", answer_code="borig",
                                  answer_number=1)
        self.new_expr(name="c",expression="b+y", post_user_response=True)
        self.new_expr(name="d",expression="b+y")

        user_responses=[]
        user_responses.append({'identifier': 0,
                              'code': "borig",
                              'response': "x+1" })
        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        x=Symbol('x', real=True)
        y=Symbol('y', real=True)
        b=Symbol('b', real=True)
        
        from mitesting.sympy_customized import AddUnsort
        self.assertEqual(expression_context['a'], y+x**2)
        self.assertEqual(expression_context['b'], AddUnsort(x,1,evaluate=False))
        self.assertEqual(expression_context['c'], x+y+1)
        self.assertEqual(expression_context['d'], y+b)

        
    def test_use_user_dict_not_global(self):
        self.new_expr(name="a",expression="y+x^2")
        self.new_expr(name="f",expression="g", 
                      expression_type = Expression.FUNCTION_NAME)
        self.new_expr_from_answer(name="b", answer_code="borig",
                                  answer_number=1)
        self.new_expr_from_answer(name="c", answer_code="corig",
                                  answer_number=2)

        user_responses=[]
        user_responses.append({'identifier': 0,
                              'code': "borig",
                              'response': "a" })
        user_responses.append({'identifier': 0,
                              'code': "corig",
                              'response': "g" })
        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertEqual(expression_context['b'], Symbol('a', real=True))
        self.assertEqual(expression_context['c'], SymbolCallable('g', real=True))


    def test_no_response(self):
        self.new_expr(name="a",expression="y+x^2")
        self.new_expr_from_answer(name="b", answer_code="borig",
                                  answer_number=1)
        self.new_expr_from_answer(name="c", answer_code="corig",
                                  answer_number=2, default_value="_default_")

        user_responses=[]

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertTrue(expression_context['b'].return_expression().dummy_eq(Dummy('\uff3f')))
        self.assertTrue(expression_context['c'].return_expression().dummy_eq(Dummy('_default_')))


    def test_invalid_response(self):
        self.new_expr(name="a",expression="y+x^2")
        self.new_expr_from_answer(name="b", answer_code="borig",
                                  answer_number=1)
        self.new_expr_from_answer(name="c", answer_code="corig",
                                  answer_number=2, default_value="_default_")

        user_responses=[]
        user_responses.append({'identifier': 0,
                              'code': "borig",
                              'response': ")" })
        user_responses.append({'identifier': 1,
                              'code': "corig",
                              'response': ")" })

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertTrue(expression_context['b'].return_expression().dummy_eq(Dummy('\uff3f')))
        self.assertTrue(expression_context['c'].return_expression().dummy_eq(Dummy('_default_')))

  
    def test_multiple_choice(self):
        import pickle, base64
        answer_dict = {123: 'hello', 456: 'bye', 921: 'later'}
        self.new_expr_from_answer(name="b", answer_code="borig",
                        answer_number=1, answer_data=base64.b64encode(pickle.dumps(answer_dict)).decode(),
                        answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)

        user_responses=[]
        user_responses.append({'identifier': 0,
                              'code': "borig",
                              'response': "456" })

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertEqual(expression_context['b'], Symbol('bye'))

        user_responses[0]={'identifier': 0,
                           'code': "borig",
                           'response': "1" }

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertEqual(expression_context['b'], Symbol('\uff3f'))

        user_responses[0]={'identifier': 0,
                           'code': "borig",
                           'response': "x" }

        rng = random.Random()
        results=setup_expression_context(self.q, rng=rng, seed=1,
                                         user_responses=user_responses)
        expression_context = results['expression_context']
        self.assertEqual(expression_context['b'], Symbol('\uff3f'))

        

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
        FUNCTION = QuestionAnswerOption.FUNCTION

        self.assertEqual(return_valid_answer_codes(self.q, expr_context),
                         ({},[],[]))

        self.new_answer(answer_code="h", answer="hh", answer_type=EXPRESSION)
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{})
        self.assertEqual(invalid_answers, [('h','hh')])
        self.assertTrue("Invalid answer option of expression type" in invalid_answer_messages[0])

        expr_context["h"]=1
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes,{})
        self.assertEqual(invalid_answers, [('h','hh')])
        self.assertTrue("Invalid answer option of expression type" in invalid_answer_messages[0])

        expr_context["hh"]=1
        correct_valid_answer_codes= {"h": {'answer_type': EXPRESSION, 'split_symbols_on_compare': True} }
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [])
        self.assertEqual(invalid_answer_messages, [])

        self.new_answer(answer_code="h", answer="", answer_type=MULTIPLE_CHOICE)
        correct_valid_answer_codes= {"h": {'answer_type': EXPRESSION, 'split_symbols_on_compare': True} }
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [])
        self.assertEqual(invalid_answer_messages, [])

        self.new_answer(answer_code="m", answer="mm", answer_type=EXPRESSION)
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [('m','mm')])
        self.assertTrue("Invalid answer option of expression type" in invalid_answer_messages[0])

        from mitesting.math_objects import math_object
        expr_context["mm"]=math_object('x', expression_type=Expression.INTERVAL)
        self.new_answer(answer_code="h", answer="", answer_type=MULTIPLE_CHOICE)
        correct_valid_answer_codes["m"] ={'answer_type': EXPRESSION, 'split_symbols_on_compare': True, 'expression_type': Expression.INTERVAL}
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [])
        self.assertEqual(invalid_answer_messages, [])

        self.new_answer(answer_code="n", answer="", answer_type=MULTIPLE_CHOICE)
        correct_valid_answer_codes['n'] = {'answer_type': MULTIPLE_CHOICE, 'split_symbols_on_compare': True} 
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [])
        self.assertEqual(invalid_answer_messages, [])

        self.new_answer(answer_code="p", answer="pp", answer_type=FUNCTION)
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [('p','pp')])
        self.assertTrue("Invalid answer option of function type" in invalid_answer_messages[0])

        expr_context["pp"]=1
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [('p','pp')])
        self.assertTrue("Invalid answer option of function type" in invalid_answer_messages[0])

        local_dict={}
        expr_context["_sympy_local_dict_"]=local_dict
        local_dict['pp']=sympify("x")
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [('p','pp')])
        self.assertTrue("Invalid answer option of function type" in invalid_answer_messages[0])

        local_dict={}
        expr_context["_sympy_local_dict_"]=local_dict
        local_dict['pp']=1
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [('p','pp')])
        self.assertTrue("Invalid answer option of function type" in invalid_answer_messages[0])

        from mitesting.utils import return_parsed_function
        pp=return_parsed_function("x^2", function_inputs="x",
                                  name="pp", local_dict=local_dict)
        local_dict["pp"]=pp
        correct_valid_answer_codes["p"] = {'answer_type': FUNCTION, 'split_symbols_on_compare': True}
        (valid_answer_codes, invalid_answers, invalid_answer_messages) = \
            return_valid_answer_codes(self.q, expr_context)
        self.assertEqual(valid_answer_codes, correct_valid_answer_codes)
        self.assertEqual(invalid_answers, [])
        self.assertEqual(invalid_answer_messages, [])


class TestRenderQuestionText(TestCase):
    def setUp(self):
        self.rng=random.Random()
        self.rng.seed()
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
        seed = get_new_seed(self.rng)
        results=setup_expression_context(self.q, rng=self.rng, seed=seed)
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
        PageType.objects.create(code="hmm", name="hmm")
        page = Page.objects.create(code="test", title="test")
        self.q.questionreferencepage_set.create(page=page)

        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertFalse(render_results.get('help_available',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        render_data['show_help'] = True
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])
        
        render_data['user'] = AnonymousUser()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text=""
        self.q.save()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results.get('help_available',False))
        self.assertEqual(render_results.get('hint_text',""), "Hint")
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        self.q.solution_text="Solution"
        self.q.hint_text=""
        self.q.save()
        self.q.questionreferencepage_set.get(page=page).delete()
        render_results = render_question_text(render_data)
        self.assertFalse(render_results.get('help_available',False))
        self.assertEqual(render_results.get('hint_text',""), "")
        self.assertEqual(render_results.get('reference_pages',[]),[])
        
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")
        render_results = render_question_text(render_data)
        self.assertEqual(render_results.get('reference_pages',[]),[page])

        
    def test_show_help_subparts(self):
        self.q.questionsubpart_set.create(question_text="question",
                                          solution_text="solution",
                                          hint_text="hint")

        PageType.objects.create(code="hmm", name="hmm")
        page = Page.objects.create(code="test", title="test")
        self.q.questionreferencepage_set.create(page=page, question_subpart="a")

        render_data = {"question": self.q, 
                         'expression_context': self.expr_context}
        render_results = render_question_text(render_data)
        self.assertFalse(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[])

        render_data['show_help'] = True
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        render_data['user'] = AnonymousUser()
        render_results = render_question_text(render_data)
        self.assertTrue(render_results['subparts'][0]\
                             .get('help_available',False))
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
        self.assertEqual(render_results['subparts'][0]\
                             .get('hint_text',""), "hint")
        self.assertEqual(render_results['subparts'][0]\
                             .get('reference_pages',[]),[page])

        sp.solution_text="Solution"
        sp.hint_text=""
        sp.save()
        self.q.questionreferencepage_set.get(page=page).delete()
        render_results = render_question_text(render_data)
        self.assertFalse(render_results['subparts'][0]\
                             .get('help_available',False))
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
        



class TestRenderQuestion(TestCase):
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()
        self.course = Course.objects.create(name="course", code="course")
        qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="question",
            question_type = qt,
            question_privacy = 0,
            solution_privacy = 0,
            course=self.course,
            )
        self.q.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="x",expression="u,v,w,x,y,z,a,b,c,U,V,W,X,Y,Z,A,B,C",
            expression_type =Expression.RANDOM_EXPRESSION)
        self.q_dict = {'question': self.q, }

    def test_render_blank(self):
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      question_identifier="blank")
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"blank")

        question_data=render_question(self.q_dict, rng=self.rng, solution=True, 
                                      question_identifier="blank_sol")
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"blank_sol")
        
        question_data=render_question(self.q_dict, rng=self.rng, solution=False)
        self.assertEqual(question_data["question"],self.q)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"")
        self.assertEqual(question_data["identifier"],"")
        
    def test_render_simple(self):
        self.q.question_text = "What?"
        self.q.solution_text = "This."
        self.q.hint_text = "Because"
        self.q.save()
        
        question_data=render_question(self.q_dict, rng=self.rng)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"What?")
        self.assertTrue(question_data.get("help_available"))
        self.assertEqual(question_data["hint_text"], "Because")
        
        question_data=render_question(self.q_dict, rng=self.rng, solution=True)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"This.")
        self.assertFalse(question_data.get("help_available"))
        self.assertEqual(question_data.get("hint_text",""), "")

        question_data=render_question(self.q_dict, rng=self.rng, show_help=False)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["rendered_text"],"What?")
        self.assertFalse(question_data.get("help_available"))
        self.assertEqual(question_data.get("hint_text",""), "")

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser())
        self.assertTrue(question_data.get("help_available"))
        

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

        question_data=render_question(self.q_dict, rng=self.rng)
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
        question_data=render_question(self.q_dict, rng=self.rng)
        text = question_data["rendered_text"]
        seed = question_data["seed"]
        new_q_dict={'question': self.q, 'seed': seed}
        question_data=render_question(new_q_dict, rng=self.rng)
        self.assertEqual(question_data["rendered_text"],text)
        self.assertEqual(question_data["seed"],seed)
        

    def test_solution_button(self):
        self.q.question_text = "What?"
        self.q.solution_text = "This."
        self.q.save()
  
        question_data=render_question(self.q_dict, rng=self.rng)
        self.assertFalse(question_data.get("show_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url",""),"")

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      allow_solution_buttons=True)
        self.assertFalse(question_data.get("show_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url",""),"")

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser())
        self.assertFalse(question_data.get("show_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url",""),"")

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser(),
                                      allow_solution_buttons=True)
        self.assertTrue(question_data.get("show_solution_button",False))
        self.assertTrue(question_data.get("enable_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url"),
                         "/question/%s/inject_solution" % self.q.id)


        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser(),
                                      allow_solution_buttons=False)
        self.assertFalse(question_data.get("show_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url",""),"")


        self.q.computer_graded=True
        self.q.save()
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser(),
                                      allow_solution_buttons=True)
        self.assertTrue(question_data.get("show_solution_button",False))
        self.assertTrue(question_data.get("enable_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url"),
                         "/question/%s/inject_solution" % self.q.id)

        self.q.computer_graded=False
        self.q.save()

        at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=2, solution_privacy=2)
        asmt = Assessment.objects.create(
            code="a", name="a", assessment_type=at, course=self.course)
        
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser(),
                                      assessment=asmt,
                                      allow_solution_buttons=True)
        self.assertFalse(question_data.get("show_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url",""),"")

        at.question_privacy=0;
        at.solution_privacy=0;
        at.save()
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      user=AnonymousUser(),
                                      assessment=asmt,
                                      allow_solution_buttons=True)
        self.assertTrue(question_data.get("show_solution_button",False))
        self.assertTrue(question_data.get("enable_solution_button",False))
        self.assertEqual(question_data.get("inject_solution_url"),
                         "/question/%s/inject_solution" % self.q.id)


    def test_readonly(self):
        answer_code='ans'
        identifier = "abc_5"
        answer_identifier ="1_%s" % (identifier)

        self.q.questionansweroption_set.create(answer_code=answer_code, answer="x")
        self.q.question_text = "{% answer 'ans' %}"
        self.q.save()
        
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      question_identifier=identifier)
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20'>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      question_identifier=identifier,
                                      readonly=True)
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20' readonly>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

    def test_prefilled_responses(self):
        answer_code='ans'
        identifier = "abc_5"
        answer_identifier ="1_%s" % (identifier)
        previous_response = "complete guess"
        prefilled_responses = []
        prefilled_responses.append({ 
            'code': answer_code,
            'response': previous_response })


        self.q.questionansweroption_set.create(answer_code=answer_code, answer="x")
        self.q.question_text = "{% answer '" + answer_code + "' %}"
        self.q.save()
        
        new_q_dict = self.q_dict.copy()

        class ResponseObject(object):
            pass
        response=ResponseObject()
        response.response = json.dumps(prefilled_responses)
        new_q_dict['response'] = response
        
        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier)

        self.assertTrue(question_data["success"])
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20' value='%s'>" % (answer_identifier, answer_identifier, previous_response)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])

        prefilled_responses[0]= { 
            'code': answer_code+"a",
            'response': previous_response }

        new_q_dict = self.q_dict.copy()
        response.response = json.dumps(prefilled_responses)
        new_q_dict['response'] = response

        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier
)
        self.assertTrue(question_data['success'])
        answerblank_html = "<input type='text' class='mi_answer' id='id_answer_%s' name='answer_%s' maxlength='200' size='20'>" % (answer_identifier, answer_identifier)
        self.assertInHTML(answerblank_html, question_data["rendered_text"])


        prefilled_responses[0]= { 
            'code': answer_code,
            'response': previous_response }
        prefilled_responses.append({ 
            'code': answer_code,
            'response': previous_response })

        new_q_dict = self.q_dict.copy()
        response.response = json.dumps(prefilled_responses)
        new_q_dict['response'] = response

        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier)
        self.assertTrue(question_data['success'])
        
 
    def test_buttons(self):
        self.q.hint_text="hint"
        self.q.save()

        question_data=render_question(self.q_dict, rng=self.rng)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_available",False))
        
        self.q.computer_graded=True
        self.q.save()

        question_data=render_question(self.q_dict, rng=self.rng)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_available",False))

        self.q.questionansweroption_set.create(answer_code="x", answer="x")
        self.q.question_text="{% answer 'x' %}"
        self.q.save()

        question_data=render_question(self.q_dict, rng=self.rng)
        
        self.assertTrue(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertTrue(question_data.get("help_available",False))

        question_data=render_question(self.q_dict, rng=self.rng, show_help=False)
        
        self.assertTrue(question_data.get("submit_button",False))
        self.assertFalse(question_data.get("auto_submit",False))
        self.assertFalse(question_data.get("help_available",False))

        question_data=render_question(self.q_dict, rng=self.rng, auto_submit=True)
        
        self.assertFalse(question_data.get("submit_button",False))
        self.assertTrue(question_data.get("auto_submit",False))

    def test_computer_grade_data(self):
        import pickle, base64
        identifier="one"
        seed = "4c"
        answer_code='ans'
        answer_identifier = "1_%s" % (identifier)
        self.q.expression_set.create(
            name="expr1", expression="n*x", 
            expression_type = Expression.GENERIC)
        self.q.expression_set.create(
            name="expr2", expression="n^2-x", 
            expression_type = Expression.GENERIC)
        self.q.questionansweroption_set.create(answer_code=answer_code,
                                               answer="expr1")
        self.q.questionansweroption_set.create(answer_code="another",
                                               answer="expr2")
        self.q.question_text = "{% answer 'ans' %}"
        self.q.solution_text = "{{expr1}}"
        self.q.computer_graded=True
        self.q.save()

        new_q_dict = {'question': self.q, 'seed': seed}
        question_data=render_question(new_q_dict, rng=self.rng,
                                      question_identifier=identifier,
                                      user=AnonymousUser())

        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        
        self.assertEqual(cgd['identifier'],identifier)
        self.assertEqual(cgd['seed'], seed)
        self.assertFalse(cgd['show_solution_button'])
        self.assertTrue(cgd['record_response'])
        self.assertEqual(cgd.get('question_set'),None)
        self.assertEqual(cgd.get('course_code'),None)
        self.assertEqual(cgd.get('assessment_code'),None)
        self.assertEqual(cgd.get('assessment_seed'),None)
        self.assertEqual(cgd['answer_info'],
                         [{'identifier': answer_identifier,
                           'code': answer_code, 'points': 1, 
                           'type': QuestionAnswerOption.EXPRESSION,
                           'group': None, 'assign_to_expression': None,
                           'prefilled_response': None,
                           'expression_type': Expression.GENERIC}])

        question_data=render_question(self.q_dict, rng=self.rng,
                                      record_response=False,
                                      allow_solution_buttons=True,
                                      user=AnonymousUser())
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        self.assertFalse(cgd['record_response'])
        self.assertTrue(cgd['show_solution_button'])
         
        question_data=render_question(self.q_dict, rng=self.rng,
                                      record_response=True,
                                      allow_solution_buttons=False,
                                      user=AnonymousUser())
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        self.assertTrue(cgd['record_response'])
        self.assertFalse(cgd['show_solution_button'])

    def test_computer_grade_data_assessment(self):
        import pickle, base64

        identifier="one"
        seed = "4c"
        assessment_seed = "12d"
        assessment_code = "the_test"
        question_set=5

        self.q.questionansweroption_set.create(answer_code="x", answer="x")
        self.q.question_text="{% answer 'x' %}"
        self.q.save()

        at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=2, solution_privacy=2)
        asmt = Assessment.objects.create(
            code=assessment_code, name="a", assessment_type=at,
            course=self.course)


        self.q.computer_graded=True
        self.q.save()

        new_q_dict = {'question': self.q, 'question_set': question_set,
                      'seed': seed}
        question_data=render_question(new_q_dict, rng=self.rng,
                                      question_identifier=identifier,
                                      assessment=asmt,
                                      assessment_seed=assessment_seed)
        cgd = pickle.loads(
            base64.b64decode(question_data["computer_grade_data"]))
        
        self.assertEqual(cgd['identifier'],identifier)
        self.assertEqual(cgd['seed'], seed)
        self.assertEqual(cgd['course_code'], self.course.code)
        self.assertEqual(cgd['assessment_code'], assessment_code)
        self.assertEqual(cgd['assessment_seed'], assessment_seed)
        self.assertEqual(cgd['question_set'], question_set)


    def test_errors(self):
        self.q.expression_set.create(
            name="n", expression=")", 
            post_user_response=True)

        question_data=render_question(self.q_dict, rng=self.rng)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["error_message"],"")
        
        question_data=render_question(self.q_dict, rng=self.rng,
                                      show_post_user_errors=False)
        self.assertTrue(question_data["success"])
        self.assertEqual(question_data["error_message"],"")
        
        question_data=render_question(self.q_dict, rng=self.rng, 
                                      show_post_user_errors=True)
        self.assertTrue(question_data["success"])
        self.assertTrue("Error in expression" in question_data["error_message"])

        self.q.expression_set.create(name="m", expression=")")

        question_data=render_question(self.q_dict, rng=self.rng)
        self.assertFalse(question_data["success"])
        self.assertTrue("Error in expression" in question_data["error_message"])


    def test_dynamictext(self):
        from dynamictext.models import DynamicText
        self.q.question_text="{% dynamictext %}Hello{%enddynamictext %}"
        self.q.save()
        process_expressions_from_answers(self.q)

        self.assertEqual(DynamicText.return_number_for_object(self.q), 1)
        dt = DynamicText.return_dynamictext(self.q,0)
        qid = "thisqid"
        dtid = dt.return_identifier(instance_identifier=qid)

        question_data=render_question(self.q_dict, rng=self.rng,
                                      question_identifier=qid)
        self.assertHTMLEqual('<span id="id_%s">Hello</span>' % dtid,
                             question_data['rendered_text'])

        self.assertTrue(dt.return_javascript_render_function(
            mathjax=True, instance_identifier=qid)
                        in question_data['dynamictext_javascript'])
        
        self.q.question_text="Is this {% dynamictext %}dynamic{%enddynamictext %} text? {% dynamictext %}Yes.{%enddynamictext%}"
        self.q.save() 
        process_expressions_from_answers(self.q)
       
        
        self.assertEqual(DynamicText.return_number_for_object(self.q), 2)
        dt0 = DynamicText.return_dynamictext(self.q,0)
        dt1 = DynamicText.return_dynamictext(self.q,1)
        qid = "thisqid"
        dt0id = dt0.return_identifier(instance_identifier=qid)
        dt1id = dt1.return_identifier(instance_identifier=qid)

        question_data=render_question(self.q_dict, rng=self.rng,
                                      question_identifier=qid)
        self.assertHTMLEqual('Is this <span id="id_%s">dynamic</span> text? <span id="id_%s">Yes.</span>' % (dt0id, dt1id),
                             question_data['rendered_text'])

        self.assertTrue(dt0.return_javascript_render_function(
            mathjax=True, instance_identifier=qid)
                        in question_data['dynamictext_javascript'])
        self.assertTrue(dt1.return_javascript_render_function(
            mathjax=True, instance_identifier=qid)
                        in question_data['dynamictext_javascript'])
        
    def test_assign_to_expression(self):
        self.q.expression_set.create(name="n", expression="y")
        self.q.expression_set.create(name="m", expression="apple+1",
                                     post_user_response=True)

        identifier="abc"
        answer_code='z'
        response = "x+1"
        prefilled_responses = []
        prefilled_responses.append({ 
            'code': answer_code,
            'response': response })

        self.q.questionansweroption_set.create(answer_code=answer_code, 
                                               answer="n")
        self.q.question_text = "n={{n}}, {% answer '" + answer_code + "' assign_to_expression='apple' %}, apple={{apple}}, m={{m}},"
        self.q.save()
        
        process_expressions_from_answers(self.q)

        class ResponseObject(object):
            pass
        response=ResponseObject()
        response.response = json.dumps(prefilled_responses)
        new_q_dict = {'question': self.q, 'response': response}

        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier)

        self.assertTrue(question_data["success"])
        self.assertTrue('n=y,' in question_data["rendered_text"])
        self.assertTrue('apple=x + 1,' in question_data["rendered_text"])
        self.assertTrue('m=x + 2,' in question_data["rendered_text"])
        

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      question_identifier=identifier)

        self.assertTrue(question_data["success"])
        self.assertTrue('n=y,' in question_data["rendered_text"])
        self.assertTrue('apple=\uff3f,' in question_data["rendered_text"])
        self.assertTrue('m=\uff3f + 1,' in question_data["rendered_text"])
        
        self.q.question_text = "n={{n}}, {% answer '" + answer_code + "' assign_to_expression='apple' assign_to_expression_default='???' %}, apple={{apple}}, m={{m}},"
        self.q.save()
        process_expressions_from_answers(self.q)

        question_data=render_question(self.q_dict, rng=self.rng, 
                                      question_identifier=identifier)

        self.assertTrue(question_data["success"])
        self.assertTrue('n=y,' in question_data["rendered_text"])
        self.assertTrue('apple=???,' in question_data["rendered_text"])
        self.assertTrue('m=??? + 1,' in question_data["rendered_text"])


    def test_assign_to_expression_with_captured_applet_object(self):
        self.q.expression_set.create(name="one", expression="1")
        self.q.expression_set.create(name="n", expression="y")
        self.q.expression_set.create(name="m", expression="apple+1",
                                     post_user_response=True)
        
        from midocs.models import Applet, AppletType, AppletObjectType
        at = AppletType.objects.create(code="Geogebra", name="Geogebra",
                                       description="a", help_text="b",
                                       error_string="c")
        aot = AppletObjectType.objects.create(object_type="Boolean")

        applet_code="the_applet"
        applet=Applet.objects.create(title="applet", code=applet_code,
                                     applet_type=at, highlight=False,
                                     hidden=False)
        
        applet.appletobject_set.create(object_type=aot, name="d",
                                       capture_changes=True)
        

        identifier="abc"
        answer_code='z'
        response = "x+1"
        prefilled_responses = []
        prefilled_responses.append({ 
            'code': 'one',
            'response': "" })
        prefilled_responses.append({ 
            'code': answer_code,
            'response': response })

        self.q.questionansweroption_set.create(answer_code=answer_code, 
                                               answer="n")
        self.q.questionansweroption_set.create(answer_code="one", 
                                               answer="one")

        self.q.question_text = "{% applet '" + applet_code + "' answer_d=one %} n={{n}}, {% answer '" + answer_code + "' assign_to_expression='apple' %}, apple={{apple}}, m={{m}},"
        self.q.save()

        process_expressions_from_answers(self.q)

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data = return_new_auxiliary_data()

        class ResponseObject(object):
            pass
        response=ResponseObject()
        response.response = json.dumps(prefilled_responses)
        new_q_dict = {'question': self.q, 'response': response}

        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier,
                                      auxiliary_data=auxiliary_data)

        self.assertTrue(question_data["success"])
        self.assertTrue('n=y,' in question_data["rendered_text"])
        self.assertTrue('apple=x + 1,' in question_data["rendered_text"])
        self.assertTrue('m=x + 2,' in question_data["rendered_text"])
        


    def test_assign_to_expression_multiple_choice(self):

        identifier="abc"
        answer_code='z'
        option1=self.q.questionansweroption_set.create(
            answer_code=answer_code, answer="banana",
            answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)
        option2=self.q.questionansweroption_set.create(
            answer_code=answer_code, answer="carrot",
            answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)
        option3=self.q.questionansweroption_set.create(
            answer_code=answer_code, answer="steak",
            answer_type=QuestionAnswerOption.MULTIPLE_CHOICE)

        prefilled_responses = []
        prefilled_responses.append({ 
            'code': answer_code,
            'response': str(option3.id) })

        self.q.question_text = "{% answer '" + answer_code + "' assign_to_expression='apple' %}, apple={{apple}}"
        self.q.save()
        process_expressions_from_answers(self.q)

        class ResponseObject(object):
            pass
        response=ResponseObject()
        response.response = json.dumps(prefilled_responses)
        new_q_dict = {'question': self.q, 'response': response}

        question_data=render_question(new_q_dict, rng=self.rng, 
                                      question_identifier=identifier)

        self.assertTrue(question_data["success"])
        self.assertTrue('apple=steak' in question_data["rendered_text"])

        

class TestShowSolutionButton(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="course", code="course")
        self.rng = random.Random()
        self.rng.seed()
        qt = QuestionType.objects.create(name="question type")
        self.q_dicts=[[],[],[]]
        for i in range(3):
            for j in range(3):
                self.q_dicts[i].append(
                    {'question': Question.objects.create(
                        name="question",
                        question_type = qt,
                        question_privacy = i,
                        solution_privacy = j,
                        solution_text="solution",
                        course=self.course)
                })

        self.users = [AnonymousUser()]


        username = "student"
        u=User.objects.create_user(username, password="pass")
        self.course.courseenrollment_set.create(student=u.courseuser)
        self.users.append(u)

        username = "instructor"
        u=User.objects.create_user(username, password="pass")
        self.course.courseenrollment_set.create(student=u.courseuser,
                                           role=INSTRUCTOR_ROLE)
        self.users.append(u)

        username = "designer"
        u=User.objects.create_user(username, password="pass")
        self.course.courseenrollment_set.create(student=u.courseuser,
                                           role=DESIGNER_ROLE)
        self.users.append(u)

            
    def test_show_solution_button(self):
        for iq in range(3):
            for jq in range(3):
                for iu in range(4):
                    
                    question_data = render_question(
                        self.q_dicts[iq][jq], rng=self.rng, 
                        question_identifier="q",
                        user=self.users[iu], allow_solution_buttons=True)
                                                    
                    if iu >= jq:
                        self.assertTrue(question_data.get(
                                'show_solution_button',False))
                    else:
                        self.assertFalse(question_data.get(
                                'show_solution_button',False))

                    question_data = render_question(
                        self.q_dicts[iq][jq], rng=self.rng, 
                        question_identifier="q",
                        user=self.users[iu], allow_solution_buttons=False)
                    
                    self.assertFalse(question_data.get(
                            'show_solution_button',False))

                    question_data = render_question(
                        self.q_dicts[iq][jq], rng=self.rng, 
                        question_identifier="q",
                        user=self.users[iu])
                    
                    self.assertFalse(question_data.get(
                            'show_solution_button',False))


    def test_show_solution_button_assessment(self):
        
        asmts=[]
        for i in range(3):
            at = AssessmentType.objects.create(
                code="%s" % (i),
                name="%s" % (i),
                assessment_privacy=0,
                solution_privacy=i)
            asmt=Assessment.objects.create(
                code="test_%s" % (i),
                name = "Test %s" % (i),
                assessment_type = at,
                course=self.course,
                )
            asmts.append(asmt) 
        for jq in range(3):
            for iu in range(3):
                for ia in range(3):

                    question_data = render_question(
                        self.q_dicts[0][jq], rng=self.rng, 
                        question_identifier="q",
                        user=self.users[iu], 
                        assessment=asmts[ia],
                        allow_solution_buttons=True)

                    if iu >= jq and iu >= ia:
                        self.assertTrue(question_data.get(
                                'show_solution_button',False))
                    else:
                        self.assertFalse(question_data.get(
                                'show_solution_button',False))
