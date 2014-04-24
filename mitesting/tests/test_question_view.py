from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from django.contrib.auth.models import AnonymousUser, User, Permission

class TestQuestionView(TestCase):

    def setUp(self):
        self.qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="a question",
            question_type = self.qt,
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
            name="x",expression="u,v,w,x,y,z",
            expression_type =Expression.RANDOM_EXPRESSION)
        self.q.expression_set.create(name="fun_x",expression="fun(x)")

    def test_view_simple(self):
        self.q.question_text="What is your name?"
        self.q.hint_text="Ask your mother."
        self.q.save()

        response = self.client.get("/assess/question/1")
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed("mitesting/question_detail.html")
        self.assertContains(response, "What is your name?")

        response = self.client.post("/assess/question/1")
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed("mitesting/question_detail.html")
        self.assertContains(response, "What is your name?")


    def test_solution(self):
        self.q.question_text="What is your name?"
        self.q.hint_text="Ask your mother."
        self.q.save()
        self.q.solution_text="The full solution"
        self.q.save()

        response = self.client.get("/assess/question/1/solution")
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed("mitesting/question_solution_detail.html")
        self.assertContains(response, "The full solution")

        response = self.client.post("/assess/question/1/solution")
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed("mitesting/question_solution_detail.html")
        self.assertContains(response, "The full solution")


    def test_expressions(self):
        self.q.question_text="${{f}}({{x}}) = {{fun_x}}$"
        self.q.solution_text="The solution is: ${{fun_x}} = {{f}}({{x}})$"
        self.q.save()
        
        response = self.client.get("/assess/question/1")
        f = response.context["f"]
        x = response.context["x"]
        fun_x = response.context["fun_x"]
        question_text = "$%s(%s) = %s$" % (f,x,fun_x)
        solution_text = "The solution is: $%s = %s(%s)$" % (fun_x,f,x)
        self.assertContains(response, question_text)
        
        seed = response.context["question_data"]["seed"]
        response = self.client.get("/assess/question/1", {'seed': seed})
        self.assertContains(response, question_text)

        response = self.client.post("/assess/question/1", {'seed': seed})
        self.assertContains(response, question_text)

        response = self.client.get("/assess/question/1/solution", 
                                   {'seed': seed})
        self.assertContains(response, solution_text)

        response = self.client.post("/assess/question/1/solution", 
                                    {'seed': seed})
        self.assertContains(response, solution_text)


    def test_need_help(self):

        response = self.client.get("/assess/question/1")
        identifier = response.context['question_data']['identifier']
        need_help_snippet = '<a class="show_help" id="%s_help_show" onclick="showHide(\'%s_help\');">Need help?</a>' % (identifier, identifier)
        self.assertNotContains(response, need_help_snippet, html=True)

        self.q.hint_text = "help"
        self.q.save()
        response = self.client.get("/assess/question/1")
        self.assertContains(response, need_help_snippet, html=True)

        response = self.client.get("/assess/question/1/solution")
        self.assertNotContains(response, need_help_snippet, html=True)

        self.q.computer_graded=True
        self.q.save()
        response = self.client.get("/assess/question/1")
        self.assertNotContains(response, need_help_snippet, html=True)


    def test_subparts(self):
        self.q.question_text="{{x}}+{{x}}"
        self.q.solution_text="2{{x}}"
        self.q.save()
        self.q.questionsubpart_set.create(question_text="{{f}}({{x}})",
                                          solution_text="{{fun_x}}")
        self.q.questionsubpart_set.create(question_text="({{x}}+1)^2",
                                          solution_text="{{x}}^2+2{{x}}+1")

        response = self.client.get("/assess/question/1")
        f = response.context["f"]
        x = response.context["x"]
        fun_x = response.context["fun_x"]
        question_text = "%s+%s" % (x,x)
        question_texta = "%s(%s)" % (f,x)
        question_textb = "(%s+1)^2" % x
        solution_text = "2%s" % (x)
        solution_texta = "%s" % fun_x
        solution_textb = "%s^2+2%s+1" % (x,x)

        self.assertContains(response, question_text)
        self.assertContains(response, question_texta)
        self.assertContains(response, question_textb)

        seed = response.context["question_data"]["seed"]
        response = self.client.get("/assess/question/1/solution?seed=%s" % seed)
        self.assertContains(response, solution_text)
        self.assertContains(response, solution_texta)
        self.assertContains(response, solution_textb)


    def test_permissions(self):
        qpks=[[],[],[]]
        for i in range(3):
            for j in range(3):
                q=Question.objects.create(
                    name="question",
                    question_text="A profound question",
                    solution_text="The only solution",
                    question_type = self.qt,
                    question_privacy = i,
                    solution_privacy = j,
                    )
                qpks[i].append(q.pk)
                
        users = [[],[],[]]
        for i in range(3):
            for j in range(3):
                username = "u%s%s" % (i,j)
                u=User.objects.create_user(username, password="pass")
                users[i].append(username)
                if i > 0:
                    p=Permission.objects.get(
                        codename = "view_assessment_%s" % i)
                    u.user_permissions.add(p)
                if j > 0:
                    p=Permission.objects.get(
                        codename = "view_assessment_%s_solution" % j)
                    u.user_permissions.add(p)
                    
        for iu in range(3):
            for ju in range(3):
                self.client.login(username=users[iu][ju],password="pass")
                for iq in range(3):
                    for jq in range(3):
                        response = self.client.get(
                            "/assess/question/%s" % qpks[iq][jq])
                        
                        if iu < iq:
                            self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/question/%s' % qpks[iq][jq])
                        else:
                            self.assertContains(
                                response, "A profound question")
                                 
                            if ju < jq:
                                self.assertNotContains(
                                    response, "View solution")
                            else: 
                                self.assertContains(
                                    response, "View solution")
                            if ju==2:
                                self.assertTrue(response.context['show_lists'])
                            else:
                                self.assertFalse(response.context['show_lists'])

                        response = self.client.get(
                            "/assess/question/%s/solution" % qpks[iq][jq])
                        
                        if ju < jq:
                            self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/question/%s/solution' % qpks[iq][jq])
                        else:
                            self.assertContains(
                                response, "The only solution")
                                 
                            if ju==2:
                                self.assertTrue(response.context['show_lists'])
                            else:
                                self.assertFalse(response.context['show_lists'])

                self.client.logout()
