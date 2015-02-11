from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from django.contrib.auth.models import AnonymousUser, User, Permission
import json
import pickle, base64
import random

class TestQuestionView(TestCase):

    def setUp(self):
        random.seed()
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

        u=User.objects.create_user("user", password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        self.client.login(username="user",password="pass")



    def test_view_simple(self):
        self.q.question_text="What is your name?"
        self.q.hint_text="Ask your mother."
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed(response,"mitesting/question_detail.html")
        self.assertContains(response, "What is your name?")


    def test_solution(self):
        self.q.question_text="What is your name?"
        self.q.hint_text="Ask your mother."
        self.q.save()
        self.q.solution_text="The full solution"
        self.q.save()

        response = self.client.get("/assess/question/%s/solution" % self.q.id)
        self.assertEqual(response.context['question'],self.q)
        self.assertTemplateUsed(response,
                                "mitesting/question_solution.html")
        self.assertContains(response, "The full solution")


    def test_expressions(self):
        self.q.question_text="${{f}}({{x}}) = {{fun_x}}$"
        self.q.solution_text="The solution is: ${{fun_x}} = {{f}}({{x}})$"
        self.q.save()
        
        response = self.client.get("/assess/question/%s" % self.q.id)
        f = response.context["f"]
        x = response.context["x"]
        fun_x = response.context["fun_x"]
        question_text = "$%s(%s) = %s$" % (f,x,fun_x)
        solution_text = "The solution is: $%s = %s(%s)$" % (fun_x,f,x)
        self.assertContains(response, question_text)
        
        seed = response.context["question_data"]["seed"]
        response = self.client.get("/assess/question/%s" % self.q.id,
                                   {'seed': seed})
        self.assertContains(response, question_text)

        response = self.client.get("/assess/question/%s/solution" % self.q.id, 
                                   {'seed': seed})
        self.assertContains(response, solution_text)


    def test_solution_button_help(self):

        response = self.client.get("/assess/question/%s" % self.q.id)
        identifier = response.context['question_data']['identifier']
        self.assertNotContains(response, "Show solution")

        self.q.solution_text = "Solution"
        self.q.save()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, "Show solution")
        self.assertTrue(response.context['question_data']\
                            ['enable_solution_button'])

        response = self.client.get("/assess/question/%s/solution" % self.q.id)
        self.assertNotContains(response, "Show solution")

        self.q.computer_graded=True
        self.q.show_solution_button_after_attempts=3
        self.q.save()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, "Show solution")
        self.assertFalse(response.context['question_data']\
                            ['enable_solution_button'])


    def test_need_help(self):

        response = self.client.get("/assess/question/%s" % self.q.id)
        identifier = response.context['question_data']['identifier']
        need_help_snippet = '<a class="show_help" id="%s_help_show" onclick="showHide(\'%s_help\');">Need help?</a>' % (identifier, identifier)
        self.assertNotContains(response, need_help_snippet, html=True)

        self.q.hint_text = "help"
        self.q.save()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, need_help_snippet, html=True)

        response = self.client.get("/assess/question/%s/solution" % self.q.id)
        self.assertNotContains(response, need_help_snippet, html=True)

        self.q.computer_graded=True
        self.q.save()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, need_help_snippet, html=True)


    def test_subparts(self):
        self.q.question_text="{{x}}+{{x}}"
        self.q.solution_text="2{{x}}"
        self.q.save()
        self.q.questionsubpart_set.create(question_text="{{f}}({{x}})",
                                          solution_text="{{fun_x}}")
        self.q.questionsubpart_set.create(question_text="({{x}}+1)^2",
                                          solution_text="{{x}}^2+2{{x}}+1")

        response = self.client.get("/assess/question/%s" % self.q.id)
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
        response = self.client.get("/assess/question/%s/solution?seed=%s" 
                                   % (self.q.id, seed))
        self.assertContains(response, solution_text)
        self.assertContains(response, solution_texta)
        self.assertContains(response, solution_textb)


    def test_multiple_choice(self):
        MULTIPLE_CHOICE = QuestionAnswerOption.MULTIPLE_CHOICE
        self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "The correct answer: {{fun_x}}",
            percent_correct = 100)
        self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "An incorrect answer: {{f}}({{x}})",
            percent_correct = 0)
        self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "A partially correct answer: {{n}}",
            percent_correct = 50)

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertNotContains(response, "The correct answer")
        self.assertNotContains(response, "An incorrect answer")
        self.assertNotContains(response, "A partially correct answer")

        self.q.question_text="Which is right? {% answer choice %}"
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)
        f = response.context["f"]
        x = response.context["x"]
        n = response.context["n"]
        fun_x = response.context["fun_x"]
        
        self.assertContains(response, "The correct answer: %s" % fun_x)
        self.assertContains(response, "An incorrect answer: %s(%s)" 
                            % (f, x))
        self.assertContains(response, "A partially correct answer: %s" % n)



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
                
        self.client.logout()
        User.objects.all().delete()

        users = [""]

        username = "user"
        users.append(username)
        u=User.objects.create_user(username, password="pass")

        username = "instructor"
        users.append(username)
        u=User.objects.create_user(username, password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)

        for iu in range(3):
            self.client.login(username=users[iu],password="pass")
            for iq in range(3):
                for jq in range(3):
                    response = self.client.get(
                        "/assess/question/%s" % qpks[iq][jq])

                    if iu < 2:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/question/%s' % qpks[iq][jq])
                    else:
                        self.assertContains(
                            response, "A profound question")

                        self.assertContains(
                            response, "Show solution")

                        self.assertTrue(response.context['show_lists'])

                    response = self.client.get(
                        "/assess/question/%s/solution" % qpks[iq][jq])

                    if iu < 2:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/question/%s/solution' % qpks[iq][jq])
                    else:
                        self.assertContains(
                            response, "The only solution")

                        self.assertTrue(response.context['show_lists'])

            self.client.logout()


    def test_errors(self):
        self.q.expression_set.create(name="xyz",expression="x*y*z")
        self.q.questionansweroption_set.create(answer_code="xyz", answer="xyz")
        self.q.question_text="{% answer xyz %}"
        self.q.computer_graded=True
        self.q.save()

        submit_button_html = '<input type="submit" id="question_qv_submit" class="mi_answer_submit" value="Submit" >'

        response = self.client.get("/assess/question/%s" % self.q.id)

        self.assertContains(response, submit_button_html, html=True)
        
        self.q.question_text="{% answer xyz %}{% badtag %}"
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)

        self.assertNotContains(response, submit_button_html, html=True)

        error_message="<li>Error in question template: Invalid block tag: 'badtag'</li>"
        self.assertContains(response, error_message, html=True)

        abc=self.q.expression_set.create(name="abc", expression="(")
        self.q.question_text="{% answer xyz %}abc={{abc}}"
        self.q.save()
        
        response = self.client.get("/assess/question/%s" % self.q.id)
        
        error_message = '<li>Error in expression: abc<br/>Invalid format for expression: (</li>'
        self.assertContains(response, error_message, html=True)
        self.assertNotContains(response, submit_button_html, html=True)
        self.assertContains(response, 'abc=??')

        abc.post_user_response=True
        abc.save()
        
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, error_message, html=True)
        self.assertContains(response, submit_button_html, html=True)
        self.assertContains(response, 'abc=??')


class TestGradeQuestionView(TestCase):
    def setUp(self):
        random.seed()
        self.qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            computer_graded=True
            )
        self.q.expression_set.create(
            name="f",expression="f,g,h,k", 
            expression_type = Expression.RANDOM_FUNCTION_NAME)
        self.q.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="n_nonzero", expression="n != 0", 
            expression_type = Expression.CONDITION)
        self.q.expression_set.create(
            name="fun",expression="x^3+ n*x",
            function_inputs="x",
            expression_type = Expression.FUNCTION)
        self.q.expression_set.create(
            name="x",expression="u,v,w,x,y,z",
            expression_type =Expression.RANDOM_EXPRESSION)
        self.q.expression_set.create(name="fun_x",expression="fun(x)")

        u=User.objects.create_user("user", password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        self.client.login(username="user",password="pass")

    def new_answer(self, **kwargs):
        return self.q.questionansweroption_set.create(**kwargs)

    def test_view_simple(self):
        computer_grade_data = {
            'seed': '0', 'identifier': 'a', 'record_answers': True,
            'allow_solution_buttons': True, 'answer_info': [],
            'applet_counter': 0}

        cgd = base64.b64encode(pickle.dumps(computer_grade_data))

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd})
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(results['identifier'], "a")
        self.assertEqual(results['number_attempts'],1)
        self.assertFalse(results['enable_solution_button'])
        self.assertFalse(results.get('inject_solution_url',''),'')
        self.assertFalse(results['correct'])
        self.assertEqual(results['answers'],{})
        
    def test_bad_cgd(self):
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": 123})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")
        
        
    def test_simple_grade(self):
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertTrue("computer_grade_data" in response.context["question_data"])
        
        self.q.question_text="Type the answer: {% answer fun_x %}"
        self.q.save()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")
        self.assertContains(response,"Invalid answer blank: fun_x")
        self.assertTrue("computer_grade_data" in response.context["question_data"])

        self.new_answer(answer_code="fun_x", answer="fun_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        self.assertContains(response, '<input class="mi_answer" type="text" id="id_answer_%s" name="answer_%s" maxlength="200" size="20" />' % (answer_identifier, answer_identifier), html=True)

        fun_x = response.context['fun_x']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(fun_x.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(1+fun_x.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])


    def test_multiple_correct_answers(self):
        self.q.question_text="Type the answer: {% answer ans %}$"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="n")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        n = response.context['n']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(2*n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])


        # add second possible correct answer
        self.q.expression_set.create(
            name="two_n", expression="2*n", 
            expression_type = Expression.GENERIC)

        ans2=self.new_answer(answer_code="ans", answer="two_n")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        n = response.context['n']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(2*n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(3*n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])



        # change second possible to 50% correct
        ans2.percent_correct=50
        ans2.save()

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        n = response.context['n']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(2*n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(3*n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])


    def test_multiple_correct_answers_mix_types(self):
        self.q.question_text="Type the answer: {% answer ans %}$"
        self.q.save()
        
        self.q.expression_set.create(
            name="g",expression="x == y", function_inputs="x",
            expression_type = Expression.FUNCTION)

        self.new_answer(answer_code="ans", answer="n")
        self.new_answer(answer_code="ans", answer="g",
                        answer_type=QuestionAnswerOption.FUNCTION)
        
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        n = response.context['n']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                       str(n.return_expression())})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: "y"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])



    def test_repeat_same_answer(self):
        self.q.question_text="Type the same answer twice: {% answer ans %}  {% answer ans %}"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the same answer twice: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        for ai in answer_identifiers:
            answers["answer_%s" % ai] = str(x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression()+1)

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])

            
    def test_two_different_answers(self):
        self.q.question_text="Type two different answers: {% answer ans1 %}  {% answer ans2 %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="x")
        self.new_answer(answer_code="ans2", answer="fun_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type two different answers: ")
        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])
        
        x = response.context['x']
        fun_x = response.context['fun_x']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[1]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[0]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        for ai in answer_identifiers:
            self.assertFalse(results["answers"][ai]["answer_correct"])
            self.assertTrue("is incorrect" in \
                                results["answers"][ai]["answer_feedback"])


        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])


    def test_two_unequal_answers(self):
        self.q.question_text="Type two different answers: {% answer ans1 points=3 %}  {% answer ans2 %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="x")
        self.new_answer(answer_code="ans2", answer="fun_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type two different answers: ")
        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])

        x = response.context['x']
        fun_x = response.context['fun_x']
        n = response.context['n']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(n.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 75% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])


    def test_answers_with_alternates(self):
        self.q.question_text="Type the answer: {% answer ans %}$"
        self.q.save()
        
        self.q.expression_set.create(
            name="ts",expression="t,s,u", 
            expression_type = Expression.EXPRESSION_WITH_ALTERNATES)

        self.new_answer(answer_code="ans", answer="ts")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: "t"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: "s"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: "u"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: "v"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])


    def test_answers_with_alternates_2(self):
        self.q.question_text="Type the answer: {% answer ans %}$"
        self.q.save()
        
        self.q.expression_set.create(
            name="ts",expression="t,s,u", 
            expression_type = Expression.EXPRESSION_WITH_ALTERNATES)

        self.q.expression_set.create(
            name="two_ts_plus_x",expression="2*ts+x")
        self.new_answer(answer_code="ans", answer="two_ts_plus_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        x = response.context['x']

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "2t+%s" % x})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "2s+%s" % x})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier:
                                   "2u+%s" % x})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "2v + %s" % x})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])

    def test_answers_with_alternates_random(self):
        self.q.question_text="Type the answer: {% answer ans %}$"
        self.q.save()
        
        self.q.expression_set.create(
            name="ts",expression="t,s,u", 
            expression_type = Expression.EXPRESSION_WITH_ALTERNATES)

        self.q.expression_set.create(
            name="xx",expression="w, y,z",
            expression_type = Expression.RANDOM_EXPRESSION)
        
        self.q.expression_set.create(
            name="num", expression="1,10",
            expression_type = Expression.RANDOM_NUMBER)

        self.q.expression_set.create(
            name="ans", expression="num*xx+ts")

        self.new_answer(answer_code="ans", answer="ans")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type the answer: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        xx = response.context['xx']
        num = response.context['num']
        
        from sympy import Symbol
        if xx==Symbol("w", real=True):
            xx2 = "y"
            xx3 = "z"
        elif xx==Symbol("y",real=True):
            xx2 = "x"
            xx3 = "z"
        elif xx==Symbol("z",real=True):
            xx2 = "x"
            xx3 = "y"

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+t" % (num,xx)})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+s" % (num,xx)})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+u" % (num,xx)})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+t" % (num,xx2)})


        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+t" % (num,xx3)})


        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+t" % (num+1,xx)})


        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])


        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 
                                   "%s%s+t" % (num-1,xx)})


        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])




    def test_question_group(self):
        self.q.question_text="Type in either order: {% answer ans1 group='a' %}  {% answer ans2 group='a' %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="x")
        self.new_answer(answer_code="ans2", answer="fun_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type in either order: ")
        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])
        
        x = response.context['x']
        fun_x = response.context['fun_x']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[1]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[0]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])


        answers["answer_" + answer_identifiers[0]] \
            = str(x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[0]] \
            = str(fun_x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = str(fun_x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])


    def test_split_symbols_on_compare(self):
        self.q.expression_set.create(
            name="two_a_x", expression="2*a*x", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans1 %} {% answer ans2 %} {% answer ans3 %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="two_a_x",
                        split_symbols_on_compare = True)
        self.new_answer(answer_code="ans2", answer="two_a_x",
                        split_symbols_on_compare = False)
        self.new_answer(answer_code="ans3", answer="two_a_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = "2a%s" % x.return_expression()
        answers["answer_" + answer_identifiers[1]] \
            = "2a%s" % x.return_expression()
        answers["answer_" + answer_identifiers[2]] \
            = "2a%s" % x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 67% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[2]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        

        answers["answer_" + answer_identifiers[0]] \
            = "2a*%s" % x.return_expression()
        answers["answer_" + answer_identifiers[1]] \
            = "2a*%s" % x.return_expression()
        answers["answer_" + answer_identifiers[2]] \
            = "2a*%s" % x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

    def test_split_with_function_name(self):

        self.q.expression_set.create(
            name="afx", expression="a*f(x)")
        
        self.q.question_text="Type answers: {% answer ans1 %} {% answer ans2 %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="afx",
                        split_symbols_on_compare = True)
        self.new_answer(answer_code="ans2", answer="afx",
                        split_symbols_on_compare = False)
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")
        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])

        x = response.context['x']
        f = response.context['f']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = "a%s(%s)" % (f.return_expression(), x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = "a%s(%s)" % (f.return_expression(), x.return_expression())

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])
        

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = "a*%s(%s)" % (f.return_expression(), x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = "a*%s(%s)" % (f.return_expression(), x.return_expression())

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = "a%s" % (f.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = "a%s" % (f.return_expression())

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("is incorrect" in \
                            results["answers"][ai]["answer_feedback"])
        




    def test_evaluate_level_on_compare_x_plus_x(self):
        from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL,\
            EVALUATE_FULL
        expr=self.q.expression_set.create(
            name="x_plus_x", expression="x+x", 
            expression_type = Expression.GENERIC)
        self.q.question_text="{% answer x_plus_x %}"
        self.q.save()
        self.new_answer(answer_code="x_plus_x", answer="x_plus_x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        x = response.context['x']
        answers = {"cgd": cgd,}

        answers["answer_" + answer_identifier] \
            = "%s + %s" % (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "2%s" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        expr.evaluate_level=EVALUATE_NONE
        expr.save()

        answers["answer_" + answer_identifier] \
            = "%s + %s" % (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "2%s" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])

        expr.evaluate_level=EVALUATE_PARTIAL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "%s + %s" % (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "2%s" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        expr.evaluate_level=EVALUATE_FULL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "%s + %s" % (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "2%s" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])


    def test_evaluate_level_on_compare_distribute(self):
        from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL,\
            EVALUATE_FULL
        expr=self.q.expression_set.create(
            name="ans", expression="6x+9", 
            expression_type = Expression.GENERIC)
        self.q.question_text="{% answer ans %}"
        self.q.save()
        self.new_answer(answer_code="ans", answer="ans")

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        x = response.context['x']
        answers = {"cgd": cgd,}

        answers["answer_" + answer_identifier] \
            = "6%s + 9" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "3(2%s+3)" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        expr.evaluate_level=EVALUATE_NONE
        expr.save()

        answers["answer_" + answer_identifier] \
            = "6%s + 9" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "3(2%s+3)" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])

        expr.evaluate_level=EVALUATE_PARTIAL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "6%s + 9" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "3(2%s+3)" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        expr.evaluate_level=EVALUATE_FULL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "6%s + 9" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "3(2%s+3)" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])


    def test_evaluate_level_on_compare_derivative(self):
        from mitesting.sympy_customized import EVALUATE_NONE, EVALUATE_PARTIAL,\
            EVALUATE_FULL
        expr=self.q.expression_set.create(
            name="deriv", expression="4x^3", 
            expression_type = Expression.GENERIC)
        self.q.question_text="{% answer deriv %}"
        self.q.save()
        self.new_answer(answer_code="deriv", answer="deriv")
        scs_derivative = SympyCommandSet.objects.create(
                name = 'derivative', commands='Derivative')
        self.q.allowed_sympy_commands.add(scs_derivative)

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        x = response.context['x']
        answers = {"cgd": cgd,}

        answers["answer_" + answer_identifier] \
            = "Derivative(%s^4,%s)" % \
            (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "4*%s^3" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        expr.evaluate_level=EVALUATE_NONE
        expr.save()

        answers["answer_" + answer_identifier] \
            = "Derivative(%s^4,%s)" % \
            (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])

        answers["answer_" + answer_identifier] \
            = "4*%s^3" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])


        expr.evaluate_level=EVALUATE_PARTIAL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "Derivative(%s^4,%s)" % \
            (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])

        answers["answer_" + answer_identifier] \
            = "4*%s^3" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])


        expr.evaluate_level=EVALUATE_FULL
        expr.save()

        answers["answer_" + answer_identifier] \
            = "Derivative(%s^4,%s)" % \
            (x.return_expression(),x.return_expression())
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] \
            = "4*%s^3" % x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])



    def test_normalize_on_compare(self):
        self.q.expression_set.create(
            name="product", expression="(x+a)(x-a)", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans1 %} {% answer ans2 %} {% answer ans3 %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="product",
                        normalize_on_compare = True)
        self.new_answer(answer_code="ans2", answer="product",
                        normalize_on_compare = False)
        self.new_answer(answer_code="ans3", answer="product")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifiers = sorted([a['identifier'] for a in 
                                     computer_grade_data["answer_info"]])

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifiers[0]] \
            = "(%s-a)(%s+a)" % (x.return_expression(),x.return_expression())
        answers["answer_" + answer_identifiers[1]] \
            = "(%s-a)(%s+a)" % (x.return_expression(),x.return_expression())
        answers["answer_" + answer_identifiers[2]] \
            = "(%s-a)(%s+a)" % (x.return_expression(),x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        for ai in answer_identifiers:
            self.assertTrue(results["answers"][ai]["answer_correct"])
            self.assertTrue("is correct" in \
                                results["answers"][ai]["answer_feedback"])

        answers["answer_" + answer_identifiers[0]] \
            = "%s^2-a^2" % x.return_expression()
        answers["answer_" + answer_identifiers[1]] \
            = "%s^2-a^2" % x.return_expression()
        answers["answer_" + answer_identifiers[2]] \
            = "%s^2-a^2" % x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 33% correct" in results["feedback"])
        ai = answer_identifiers[0]
        self.assertTrue(results["answers"][ai]["answer_correct"])
        self.assertTrue("is correct" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[1]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("answer in a different form" in \
                            results["answers"][ai]["answer_feedback"])
        ai = answer_identifiers[2]
        self.assertFalse(results["answers"][ai]["answer_correct"])
        self.assertTrue("answer in a different form" in \
                            results["answers"][ai]["answer_feedback"])


    def test_near_match_partial_correct(self):
        self.q.expression_set.create(
            name="product", expression="(x+a)(x-a)x", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans %}"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="product",
                        normalize_on_compare = True, percent_correct=50)
        self.new_answer(answer_code="ans", answer="product")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s^3-a^2*%s" \
            % (x.return_expression(),x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("answer in a different form" in 
                        results["answers"][answer_identifier]["answer_feedback"])


        self.q.expression_set.create(
            name="product2", expression="(x+a)(x^2-a*x)", 
            expression_type = Expression.GENERIC)
        self.new_answer(answer_code="ans", answer="product2",
                        normalize_on_compare = True, percent_correct=75)
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s^3-a^2*%s" \
            % (x.return_expression(),x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 75% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (75%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("answer in a different form" in 
                        results["answers"][answer_identifier]["answer_feedback"])


    def test_near_match_partial_correct2(self):
        self.q.expression_set.create(
            name="product", expression="(x+a)(x-a)", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans %}"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="product",
                        normalize_on_compare = True, percent_correct=50)
        self.new_answer(answer_code="ans", answer="product", percent_correct=75)
        self.new_answer(answer_code="ans", answer="n")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s^2-a^2" % x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("that is 75% correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("answer in a different form" in 
                        results["answers"][answer_identifier]["answer_feedback"])



    def test_partial_correct_tuples(self):
        expr=self.q.expression_set.create(
            name="tuple", expression="a,b,c,d", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans %}"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="tuple",
                        match_partial_on_compare=True)

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "a, b, c,d"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])


        answers["answer_" + answer_identifier] = "d, b, c"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])

        expr.expression_type=Expression.UNORDERED_TUPLE
        expr.save()

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 75% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (75%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])

    def test_sets(self):
        expr=self.q.expression_set.create(
            name="set", expression="a,b,c,d,a,c,a,a", 
            expression_type = Expression.SET)

        self.q.question_text="Type answers: {% answer ans %}"
        self.q.save()
        
        the_ans=self.new_answer(answer_code="ans", answer="set")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "d, a, c, b"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])

        
        answers["answer_" + answer_identifier] = "a,b,c,d,a,c,a,a"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in
                    results["answers"][answer_identifier]["answer_feedback"])

        

        the_ans.match_partial_on_compare=True
        the_ans.save()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])


    def test_intervals(self):
        self.q.expression_set.create(
            name="interval1", expression="(0,1)", 
            expression_type = Expression.INTERVAL)
        self.q.expression_set.create(
            name="interval1a", expression="(0,1)")
        self.q.expression_set.create(
            name="interval2", expression="(5,r]", 
            expression_type = Expression.INTERVAL)
        self.q.expression_set.create(
            name="interval2a", expression="(5,r]")
        self.q.expression_set.create(
            name="interval3", expression="[0,1]", 
            expression_type = Expression.INTERVAL)
        self.q.expression_set.create(
            name="interval3a", expression="[0,1]")
        self.q.expression_set.create(
            name="interval3b", expression="[0,1]", 
            expression_type = Expression.INTERVAL,
            real_variables=False)

        self.q.question_text="Type intervals: {% answer ans1 %} {% answer ans1a %} {% answer ans2 %} {% answer ans2a %} {% answer ans3 %} {% answer ans3a %} {% answer ans3b %}"
        self.q.save()
        
        self.new_answer(answer_code="ans1", answer="interval1")
        self.new_answer(answer_code="ans1a", answer="interval1a")
        self.new_answer(answer_code="ans2", answer="interval2")
        self.new_answer(answer_code="ans2a", answer="interval2a")
        self.new_answer(answer_code="ans3", answer="interval3")
        self.new_answer(answer_code="ans3a", answer="interval3a")
        self.new_answer(answer_code="ans3b", answer="interval3b")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type intervals: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier1=computer_grade_data["answer_info"][0]['identifier']
        answer_identifier1a=computer_grade_data["answer_info"][1]['identifier']
        answer_identifier2=computer_grade_data["answer_info"][2]['identifier']
        answer_identifier2a=computer_grade_data["answer_info"][3]['identifier']
        answer_identifier3=computer_grade_data["answer_info"][4]['identifier']
        answer_identifier3a=computer_grade_data["answer_info"][5]['identifier']
        answer_identifier3b=computer_grade_data["answer_info"][6]['identifier']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier1] = "(0,1)"
        answers["answer_" + answer_identifier1a] = "(0,1)"
        answers["answer_" + answer_identifier2] = "(5,r]"
        answers["answer_" + answer_identifier2a] = "(5,r]"
        answers["answer_" + answer_identifier3] = "[0,1]"
        answers["answer_" + answer_identifier3a] = "[0,1]"
        answers["answer_" + answer_identifier3b] = "[0,1]"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier1a]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2a]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier3]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier3a]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier3b]["answer_correct"])



        answers["answer_" + answer_identifier3] = "[0,a]"
        answers["answer_" + answer_identifier3a] = "[0,a]"
        answers["answer_" + answer_identifier3b] = "[0,a]"
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier1a]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2a]["answer_correct"])
        self.assertFalse(results["answers"][answer_identifier3]["answer_correct"])
        self.assertFalse(results["answers"][answer_identifier3a]["answer_correct"])
        self.assertFalse(results["answers"][answer_identifier3b]["answer_correct"])
        self.assertFalse("variables used in intervals must be real" in
                        results["answers"][answer_identifier3]["answer_feedback"])
        self.assertFalse("variables used in intervals must be real" in
                         results["answers"][answer_identifier3a]["answer_feedback"])
        self.assertTrue("variables used in intervals must be real" in
                        results["answers"][answer_identifier3b]["answer_feedback"])



    def test_matrix_vector(self):
        self.q.expression_set.create(name="A", expression="1 2\ny z",
                                     expression_type=Expression.MATRIX)
        self.q.expression_set.create(name="x1", expression="(y,z)",
                                     expression_type=Expression.VECTOR)
        self.q.expression_set.create(name="x2", expression="y\nz",
                                     expression_type=Expression.MATRIX)

        self.q.question_text="Type answers: {% answer ans1 rows=5 cols=5 %} {% answer ans2 %} {% answer ans3 rows=5 cols=2%}"
        
        self.q.save()

        self.new_answer(answer_code="ans1", answer="A")
        self.new_answer(answer_code="ans2", answer="x1")
        self.new_answer(answer_code="ans3", answer="x2")

        response = self.client.get("/assess/question/%s" % self.q.id)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier1 = computer_grade_data["answer_info"][0]['identifier']
        answer_identifier2 = computer_grade_data["answer_info"][1]['identifier']
        answer_identifier3 = computer_grade_data["answer_info"][2]['identifier']

        self.assertContains(response,"Type answers: ")
        matrix1_input_html='<span class="matrix"><textarea class=mi_answer" id="id_answer_%s" name="answer_%s" rows=%s cols=%s></textarea></span>' % (answer_identifier1, answer_identifier1, 5, 5)
        matrix2_input_html='<span class="matrix"><textarea class=mi_answer" id="id_answer_%s" name="answer_%s" rows=%s cols=%s></textarea></span>' % (answer_identifier3, answer_identifier3, 5, 2)
        standard_input_html ='<input class="mi_answer" type="text" id="id_answer_%s" maxlength="200" name="answer_%s" size="20" />' % (answer_identifier2, answer_identifier2)
        self.assertContains(response, matrix1_input_html, html=True)
        self.assertContains(response, matrix2_input_html, html=True)
        self.assertContains(response, standard_input_html, html=True)

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier1] = "\n 1 2 \n y  z  \n"
        answers["answer_" + answer_identifier2] = "(y,z)"
        answers["answer_" + answer_identifier3] = "y\nz"
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)

        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier3]["answer_correct"])



    def test_user_function(self):
        self.q.expression_set.create(
            name="f_x", expression="f(x)", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answers: {% answer ans %}"
        self.q.save()
        
        self.new_answer(answer_code="ans", answer="f_x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response,"Type answers: ")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        x = response.context['x']
        f = response.context['f']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s(%s)" % \
            (f.return_expression(),x.return_expression())
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in
                        results["answers"][answer_identifier]["answer_feedback"])


    def test_user_sympy_dict(self):
        scs_explog = SympyCommandSet.objects.create(
                name = 'explog', commands='exp,ln,log,e')

        self.q.expression_set.create(
            name="exp_x", expression="exp(x)", 
            expression_type = Expression.GENERIC)

        self.q.question_text="Type answer: {% answer exp_x %}"
        self.q.save()
        
        self.new_answer(answer_code="exp_x", answer="exp_x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        x = response.context['x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "exp(%s)" % \
            x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        
        self.q.allowed_sympy_commands.add(scs_explog)
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        self.q.customize_user_sympy_commands=True
        self.q.save()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        
        self.q.allowed_user_sympy_commands.add(scs_explog)
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

        answers["answer_" + answer_identifier] = "e^%s" % \
            x.return_expression()
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])

    def test_seed(self):
        self.q.question_text="Type answer: {% answer function %}"
        self.q.save()
        
        self.new_answer(answer_code="function", answer="fun_x")

        from mitesting.render_assessments import get_new_seed
        rng=random.Random()
        seed=get_new_seed(rng)
        response = self.client.get("/assess/question/%s" % self.q.id, {'seed': seed})

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        fun_x = response.context['fun_x']
        
        self.assertEqual(seed, computer_grade_data["seed"])
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s" % \
            fun_x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])


    def test_blank_answer(self):
        self.q.question_text="Type answer: {% answer function %}"
        self.q.save()
        
        self.new_answer(answer_code="function", answer="fun_x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        fun_x = response.context['fun_x']

        answers = {"cgd": cgd,}
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("No response" in
                        results["answers"][answer_identifier]["answer_feedback"])

        answers["answer_" + answer_identifier] = ""
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("No response" in
                        results["answers"][answer_identifier]["answer_feedback"])
        

    def test_unparsable_answer(self):
        self.q.question_text="Type answer: {% answer function %}"
        self.q.save()
        
        self.new_answer(answer_code="function", answer="fun_x")

        response = self.client.get("/assess/question/%s" % self.q.id)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        fun_x = response.context['fun_x']

        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "("
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("Unable to understand the answer" in
                        results["answers"][answer_identifier]["answer_feedback"])


    def test_bad_answer_option(self):
        bad_answer=self.new_answer(answer_code="function", answer="abc")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, "Invalid answer option of expression type with code <tt>function</tt>")
        self.assertContains(response, "answer <tt>abc</tt> is not the name of an expression.")
        self.assertNotContains(response, "Invalid answer blank")
        self.assertTrue("computer_grade_data" in 
                         response.context["question_data"])

        self.q.question_text="Type answer: {% answer function %}"
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, "Invalid answer option of expression type with code <tt>function</tt>")
        self.assertContains(response, "answer <tt>abc</tt> is not the name of an expression.")
        self.assertContains(response, "Invalid answer blank: function", count=2)
        self.assertTrue("computer_grade_data" in response.context["question_data"])

        self.new_answer(answer_code="function", answer="fun_x")
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, "Invalid answer option of expression type with code <tt>function</tt>")
        self.assertContains(response, "answer <tt>abc</tt> is not the name of an expression.")
        self.assertNotContains(response, "Invalid answer blank")
        self.assertTrue("computer_grade_data" in response.context["question_data"])
        
        bad_answer.delete()
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertNotContains(response, "Invalid answer code")
        self.assertNotContains(response, "Invalid answer blank")

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']
        fun_x = response.context['fun_x']
        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s" % fun_x.return_expression()
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        
                                   
    def test_show_solution_button(self):
        solution_button_html_fragment = \
            '<input type="button" class="mi_show_solution" value="Show solution"'

        self.q.question_text="Type answer: {% answer function %}"
        self.q.show_solution_button_after_attempts=3
        self.q.save()
        
        self.new_answer(answer_code="function", answer="fun_x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertNotContains(response, solution_button_html_fragment)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        question_identifier = computer_grade_data['identifier']

        answers = {"cgd": cgd,}

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results.get("enable_solution_button",False))
        
        answers['number_attempts_%s' % question_identifier ] = 3
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results.get("enable_solution_button",False))

        self.q.solution_text="The solution"
        self.q.save()
        
        response = self.client.get("/assess/question/%s" % self.q.id)
        self.assertContains(response, solution_button_html_fragment)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        question_identifier = computer_grade_data['identifier']

        answers = {"cgd": cgd,}

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results.get("enable_solution_button",False))

        answers['number_attempts_%s' % question_identifier ] = 1
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results.get("enable_solution_button",False))
        
        answers['number_attempts_%s' % question_identifier ] = 2
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results.get("enable_solution_button",False))
        

    def test_multiple_choice(self):
        MULTIPLE_CHOICE = QuestionAnswerOption.MULTIPLE_CHOICE
        a1 = self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "The correct answer: {{fun_x}}",
            percent_correct = 100)
        a2 = self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "An incorrect answer: {{f}}({{x}})",
            percent_correct = 0)
        a3 = self.q.questionansweroption_set.create(
            answer_code="choice", answer_type=MULTIPLE_CHOICE,
            answer = "A partially correct answer: {{n}}",
            percent_correct = 50)
        self.q.question_text="Which is right? {% answer choice %}"
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)
        
        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        f = response.context["f"]
        x = response.context["x"]
        n = response.context["n"]
        fun_x = response.context["fun_x"]

        
        answers = {"cgd": cgd,}
        answers["answer_" + answer_identifier] = "%s" % a1.id
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("are correct" in
                        results["answers"][answer_identifier]["answer_feedback"])

        answers["answer_" + answer_identifier] = "%s" % a2.id
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("are incorrect" in
                        results["answers"][answer_identifier]["answer_feedback"])

        answers["answer_" + answer_identifier] = "%s" % a3.id
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id, answers)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])


    def test_function_answer(self):
        self.q.expression_set.create(name="crit",
            expression="if(And(x > 0, x<10),1, if(Abs(x)<15, 0.5,0))", 
            function_inputs="x",
            expression_type = Expression.FUNCTION)
        commands = SympyCommandSet.objects.create(
                name = 'commands', commands='if, And, Abs')
        self.q.allowed_sympy_commands.add(commands)
        self.new_answer(answer_code="ans", answer="crit",
                        answer_type=QuestionAnswerOption.FUNCTION)

        self.q.question_text="Meet the criterion: {% answer ans %}"
        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier = computer_grade_data["answer_info"][0]['identifier']

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 9})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 5})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: 10})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("not completely correct" in
                        results["answers"][answer_identifier]["answer_feedback"])
        self.assertTrue("partial (50%) credit" in
                        results["answers"][answer_identifier]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier: -20})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertFalse(results["answers"][answer_identifier]["answer_correct"])
        self.assertTrue("is incorrect" in results["feedback"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier]["answer_feedback"])



    def test_post_user_response(self):
        self.q.question_text="One thing: {% answer fun_x assign_to_expression='good_try' %}, then double it: {% answer double_me %}"
        
        self.new_answer(answer_code="fun_x", answer="fun_x")

        self.q.expression_set.create(name="double_me",\
                        expression="2*good_try", post_user_response=True)

        self.new_answer(answer_code="double_me", answer="double_me")

        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier1 = computer_grade_data["answer_info"][0]['identifier']
        answer_identifier2 = computer_grade_data["answer_info"][1]['identifier']

        fun_x = response.context['fun_x']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier1:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier2:
                                   str(fun_x.return_expression()*2)})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)

        self.assertTrue(results["correct"])
        self.assertTrue(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue("is correct" in results["feedback"])
        self.assertTrue("is correct" in results["answers"][answer_identifier1]["answer_feedback"])

        self.assertTrue("is correct" in results["answers"][answer_identifier2]["answer_feedback"])

        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier1:
                                   "3*x(y-z)",
                                   "answer_%s" % answer_identifier2:
                                   "6*x*(y-z)"})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertFalse(results["correct"])
        self.assertTrue("is 50% correct" in results["feedback"])
        self.assertFalse(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue("is incorrect" in results["answers"][answer_identifier1]["answer_feedback"])

        self.assertTrue("is correct" in results["answers"][answer_identifier2]["answer_feedback"])


    def test_post_user_response_real(self):
        self.q.question_text="try1: {% answer a1 assign_to_expression='try1' %}, try2: {% answer a2 assign_to_expression='try2' real=True %}, try3: {% answer a3 assign_to_expression='try3' real=False %}, try1a: {% answer try2a %}, try1a: {% answer try2a %}, try3a: {% answer try3a %}"
        
        self.new_answer(answer_code="a1", answer="fun_x")
        self.new_answer(answer_code="a2", answer="fun_x")
        self.new_answer(answer_code="a3", answer="fun_x")


        self.q.expression_set.create(name="try1a",\
                        expression="try1", post_user_response=True)
        self.q.expression_set.create(name="try2a",\
                        expression="try2", post_user_response=True)
        self.q.expression_set.create(name="try3a",\
                        expression="try3", post_user_response=True)

        self.new_answer(answer_code="try1a", answer="try1a")
        self.new_answer(answer_code="try2a", answer="try2a")
        self.new_answer(answer_code="try3a", answer="try3a")

        self.q.save()

        response = self.client.get("/assess/question/%s" % self.q.id)

        cgd = response.context["question_data"]["computer_grade_data"]
        computer_grade_data = pickle.loads(base64.b64decode(cgd))
        answer_identifier1 = computer_grade_data["answer_info"][0]['identifier']
        answer_identifier2 = computer_grade_data["answer_info"][1]['identifier']
        answer_identifier3 = computer_grade_data["answer_info"][2]['identifier']
        answer_identifier1a= computer_grade_data["answer_info"][3]['identifier']
        answer_identifier2a= computer_grade_data["answer_info"][4]['identifier']
        answer_identifier3a= computer_grade_data["answer_info"][5]['identifier']

        fun_x = response.context['fun_x']
        
        response=self.client.post("/assess/question/%s/grade_question" % self.q.id,
                                  {"cgd": cgd,
                                   "answer_%s" % answer_identifier1:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier2:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier3:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier1a:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier2a:
                                   str(fun_x.return_expression()),
                                   "answer_%s" % answer_identifier3a:
                                   str(fun_x.return_expression()),
                               })

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)

        self.assertTrue(results["answers"][answer_identifier1]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier3]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier1a]["answer_correct"])
        self.assertTrue(results["answers"][answer_identifier2a]["answer_correct"])
        self.assertFalse(results["answers"][answer_identifier3a]["answer_correct"])

class TestInjectQuestionSolutionView(TestCase):
    def setUp(self):
        random.seed()
        self.qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            computer_graded=True,
            question_text = "Type answer: {% answer ans %}",
            )
        self.q.expression_set.create(
            name="f",expression="f,g,h,k", 
            expression_type = Expression.RANDOM_FUNCTION_NAME)
        self.q.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="n_nonzero", expression="n != 0", 
            expression_type = Expression.CONDITION)
        self.q.expression_set.create(
            name="fun",expression="x^3+ n*x",
            function_inputs="x",
            expression_type = Expression.FUNCTION)
        self.q.expression_set.create(
            name="x",expression="u,v,w,x,y,z",
            expression_type =Expression.RANDOM_EXPRESSION)
        self.q.expression_set.create(name="fun_x",expression="fun(x)")
        u=User.objects.create_user("user", password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        self.client.login(username="user",password="pass")


    def test_simple(self):
        self.q.questionansweroption_set.create(answer_code="ans", answer="x")

        response = self.client.get("/assess/question/%s" % self.q.id)
        cgd = response.context["question_data"]["computer_grade_data"]
        fun_x = response.context['fun_x']

        response=self.client.post("/assess/question/%s/inject_solution" % self.q.id,
                                  {"cgd": cgd})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue("<h4>Solution</h4>" in results["rendered_solution"])
        
        self.q.solution_text = "The solution is ${{fun_x}}$."
        self.q.save()
        response=self.client.post("/assess/question/%s/inject_solution" % self.q.id,
                                  {"cgd": cgd})

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertTrue("The solution is $%s$." % fun_x
                        in results["rendered_solution"])
        
        
    def test_bad_cgd(self):
        response=self.client.post("/assess/question/%s/inject_solution" % self.q.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")
        response=self.client.post("/assess/question/%s/inject_solution" % self.q.id,
                                  {"cgd": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")
        response=self.client.post("/assess/question/%s/inject_solution" % self.q.id,
                                  {"cgd": 123})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,"")


    def test_permissions(self):
        computer_grade_data = {
            'seed': '0', 'identifier': 'a', 'record_answers': True,
            'allow_solution_buttons': True, 'answer_codes': {},
            'answer_points': {}, 'applet_counter': 0}

        cgd = base64.b64encode(pickle.dumps(computer_grade_data))

        qpks=[[],[],[]]
        for i in range(3):
            for j in range(3):
                q=Question.objects.create(
                    name="question",
                    solution_text="The only solution",
                    question_type = self.qt,
                    question_privacy = i,
                    solution_privacy = j,
                    computer_graded = True
                    )
                qpks[i].append(q.pk)

        self.client.logout()
        User.objects.all().delete()

        users = [""]

        username = "user"
        users.append(username)
        u=User.objects.create_user(username, password="pass")

        username = "instructor"
        users.append(username)
        u=User.objects.create_user(username, password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)

        for iu in range(3):
            self.client.login(username=users[iu],password="pass")
            for iq in range(3):
                for jq in range(3):
                    response=self.client.post(
                        "/assess/question/%s/inject_solution" % 
                        qpks[iq][jq], {"cgd": cgd})

                    if iu < jq:
                        self.assertEqual(response.content, "")
                    else: 
                        results = json.loads(response.content)
                        self.assertTrue("The only solution" in
                                        results["rendered_solution"])

            self.client.logout()


    def test_permissions_in_assessment(self):
        at0 = AssessmentType.objects.create(
            code="a0", name="a0", assessment_privacy=0, solution_privacy=0)
        at1 = AssessmentType.objects.create(
            code="a1", name="a1", assessment_privacy=0, solution_privacy=1)
        at2 = AssessmentType.objects.create(
            code="a2", name="a2", assessment_privacy=0, solution_privacy=2)

        asmt0 = Assessment.objects.create(
            code="the_test0", name="The test0", assessment_type=at0)
        asmt1 = Assessment.objects.create(
            code="the_test1", name="The test1", assessment_type=at1)
        asmt2 = Assessment.objects.create(
            code="the_test2", name="The test2", assessment_type=at2)

        computer_grade_data = {
            'seed': '0', 'identifier': 'a', 'record_answers': True,
            'allow_solution_buttons': True, 'answer_codes': {},
            'answer_points': {}, 'applet_counter': 0}

        cgds=[]
        computer_grade_data['assessment_code'] = asmt0.code
        cgds.append(base64.b64encode(pickle.dumps(computer_grade_data)))
        computer_grade_data['assessment_code'] = asmt1.code
        cgds.append(base64.b64encode(pickle.dumps(computer_grade_data)))
        computer_grade_data['assessment_code'] = asmt2.code
        cgds.append(base64.b64encode(pickle.dumps(computer_grade_data)))

        qpks=[[],[],[]]
        for i in range(3):
            for j in range(3):
                q=Question.objects.create(
                    name="question",
                    solution_text="The only solution",
                    question_type = self.qt,
                    question_privacy = i,
                    solution_privacy = j,
                    computer_graded = True
                    )
                qpks[i].append(q.pk)

        self.client.logout()
        User.objects.all().delete()

        users = [""]

        username = "user"
        users.append(username)
        u=User.objects.create_user(username, password="pass")

        username = "instructor"
        users.append(username)
        u=User.objects.create_user(username, password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)

        for iu in range(3):
            self.client.login(username=users[iu],password="pass")
            for iq in range(3):
                for jq in range(3):
                    for ic in range(3):
                        response=self.client.post(
                            "/assess/question/%s/inject_solution" % 
                            qpks[iq][jq], {"cgd": cgds[ic]})
                        
                        if iu < jq or iu < ic:
                            self.assertEqual(response.content, "")
                        else: 
                            results = json.loads(response.content)
                            self.assertTrue("The only solution" in
                                            results["rendered_solution"])

            self.client.logout()
