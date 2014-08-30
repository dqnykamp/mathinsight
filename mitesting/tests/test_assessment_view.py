from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from django.contrib.auth.models import AnonymousUser, User, Permission, Group
import random


class TestAssessmentView(TestCase):

    def setUp(self):
        random.seed()
        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The first question",
            solution_text = "The first solution"
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The second question",
            solution_text = "The second solution"
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The third question",
            solution_text = "The third solution"
            )
        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at)
        
        self.qsa1=self.asmt.questionassigned_set.create(question=self.q1)
        self.qsa2=self.asmt.questionassigned_set.create(question=self.q2)
        self.qsa3=self.asmt.questionassigned_set.create(question=self.q3)

    def test_simple_view(self):
        response = self.client.get("/assess/the_test")
        self.assertEqual(response.context['assessment'],self.asmt)
        self.assertEqual(response.context['seed'],'1')
        self.assertTemplateUsed(response,"mitesting/assessment.html")
        self.assertContains(response, "The first question", count=1)
        self.assertContains(response, "The second question", count=1)
        self.assertContains(response, "The third question", count=1)
        self.assertEqual(len(response.context['rendered_list']),3)
        for q in response.context['rendered_list']:
            self.assertTrue(q['question'] in [self.q1, self.q2, self.q3])
            self.assertTrue(q['question_data']['success'])
        self.assertTrue(response.context["success"])

        
    def test_fixed_order(self):
        response = self.client.get("/assess/the_test")
        question_order = [q['question'].id for q in \
                              response.context['rendered_list']]
        response = self.client.get("/assess/the_test", {'seed': '1'})
        question_order2 = [q['question'].id for q in \
                              response.context['rendered_list']]
        self.assertEqual(question_order, question_order2)
        
        found_different_order = False
        for seed in range(2,200):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            question_order2 = [q['question'].id for q in \
                                   response.context['rendered_list']]
            if question_order2 != question_order:
                found_different_order = True
                break
        self.assertTrue(found_different_order)
                
        self.asmt.fixed_order=True
        self.asmt.save()
        for seed in range(1121,1129):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            question_order = [q['question'] for q in \
                                   response.context['rendered_list']]
            self.assertEqual(question_order, [self.q1,self.q2,self.q3])


        self.qsa1.question_set=10
        self.qsa1.save()
        self.qsa2.question_set=4
        self.qsa2.save()
        self.qsa3.question_set=8
        self.qsa3.save()

        for seed in range(315,319):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            question_order = [q['question'] for q in \
                                   response.context['rendered_list']]
            self.assertEqual(question_order, [self.q2,self.q3,self.q1])




    def test_nothing_random(self):

        u=User.objects.create_user("user1", password="pass")
        self.client.login(username="user1",password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)

        self.q1.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q1.question_text="Question 1, n is {{n}}."
        self.q1.solution_text="Solution for question 1, n is {{n}}."
        self.q1.save()

        response = self.client.get("/assess/the_test")

        question1ind = [q['question'] for q in \
                        response.context['rendered_list']].index(self.q1)

        question1text =  response.context['rendered_list'][question1ind] \
            ['question_data']['rendered_text']

        found_different_question1 = False

        random.seed()
        begin_seed=random.randint(2,20000)
        for seed in range(begin_seed,begin_seed+200):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            question1ind = [q['question'] for q in \
                            response.context['rendered_list']].index(self.q1)
            question1texta =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']

            if question1texta != question1text:
                found_different_question1 = True
                break
        self.assertTrue(found_different_question1)

        
        self.asmt.nothing_random=True
        self.asmt.save()

        response = self.client.get("/assess/the_test")
        question1ind = [q['question'] for q in \
                        response.context['rendered_list']].index(self.q1)

        question1text =  response.context['rendered_list'][question1ind] \
            ['question_data']['rendered_text']


        begin_seed=random.randint(2,20000)
        for seed in range(begin_seed,begin_seed+5):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            question1texta =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']

            self.assertEqual(question1text, question1texta)
            self.assertEqual(response.context['seed'],'1')


        self.asmt.nothing_random=False
        self.asmt.save()
        response = self.client.get("/assess/the_test/solution")

        question1ind = [q['question'] for q in \
                            response.context['rendered_list']].index(self.q1)

        solution1text =  response.context['rendered_list'][question1ind] \
            ['question_data']['rendered_text']

        found_different_question1 = False

        begin_seed=random.randint(2,20000)
        for seed in range(begin_seed,begin_seed+200):
            response = self.client.get("/assess/the_test/solution", 
                                       {'seed': '%s' % seed })
            question1ind = [q['question'] for q in \
                                response.context['rendered_list']].index(self.q1)
            solution1texta =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']

            if solution1texta != solution1text:
                found_different_question1 = True
                break
        self.assertTrue(found_different_question1)

        
        self.asmt.nothing_random=True
        self.asmt.save()

        response = self.client.get("/assess/the_test/solution")
        question1ind = [q['question'] for q in \
                            response.context['rendered_list']].index(self.q1)

        solution1text =  response.context['rendered_list'][question1ind] \
            ['question_data']['rendered_text']


        begin_seed=random.randint(2,20000)
        for seed in range(begin_seed,begin_seed+5):
            response = self.client.get("/assess/the_test/solution", 
                                       {'seed': '%s' % seed })
            solution1texta =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']

            self.assertEqual(solution1text, solution1texta)
            self.assertEqual(response.context['seed'],'1')


    def test_multiple_in_question_set(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa2.question_set=7
        self.qsa2.save()
        self.qsa3.question_set=3
        self.qsa3.save()
        
        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The fourth question",
            solution_text = "The fourth solution"
            )
        
        self.asmt.questionassigned_set.create(question=self.q4, 
                                              question_set=7)

        valid_options=[[self.q1,self.q2],[self.q2,self.q1],[self.q1,self.q4],[self.q4,self.q1],
                       [self.q3,self.q2],[self.q2,self.q3],[self.q3,self.q4],[self.q4,self.q3]]

        options_used = [False, False, False, False,
                        False, False, False, False]

        for seed in range(39,200):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            
            questions = [q['question'] for q in \
                                response.context['rendered_list']]

            self.assertTrue(questions in valid_options)
            
            one_used = valid_options.index(questions)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)
    

    def test_question_set_groups(self):
        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The fourth question",
            solution_text = "The fourth solution"
            )
        
        self.asmt.questionassigned_set.create(question=self.q4)
        
        self.asmt.questionsetdetail_set.create(question_set=1,
                                               group="apple")
        self.asmt.questionsetdetail_set.create(question_set=4,
                                               group="apple")
        
        begin_seed = random.randint(1,100000)
        for seed in range(begin_seed,begin_seed+10):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            questions = [q['question'] for q in \
                                response.context['rendered_list']]
            qid1=questions.index(self.q1)
            qid4=questions.index(self.q4)

            self.assertEqual(abs(qid1-qid4),1)


        self.asmt.questionsetdetail_set.create(question_set=2,
                                               group="appl")
        self.asmt.questionsetdetail_set.create(question_set=3,
                                               group="appl")
        
        begin_seed = random.randint(1,100000)
        for seed in range(begin_seed,begin_seed+10):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed })
            questions = [q['question'] for q in \
                                response.context['rendered_list']]
            qid1=questions.index(self.q1)
            qid2=questions.index(self.q2)
            qid3=questions.index(self.q3)
            qid4=questions.index(self.q4)

            self.assertEqual(abs(qid1-qid4),1)
            self.assertEqual(abs(qid2-qid3),1)


    def test_assessment_names(self):
        self.asmt.name = "This complex assessment"
        self.asmt.save()
        response = self.client.get("/assess/the_test")
        self.assertEqual(response.context['assessment_name'], 
                         "This complex assessment")
        self.assertEqual(response.context['assessment_short_name'], 
                         "This complex assessment")

        u=User.objects.create_user("user1", password="pass")
        self.client.login(username="user1",password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        response = self.client.get("/assess/the_test/solution")
        self.assertEqual(response.context['assessment_name'], 
                         "This complex assessment solution")
        self.assertEqual(response.context['assessment_short_name'], 
                         "This complex assessment sol.")

        self.asmt.short_name = "complex"
        self.asmt.save()
        response = self.client.get("/assess/the_test")
        self.assertEqual(response.context['assessment_name'], 
                         "This complex assessment")
        self.assertEqual(response.context['assessment_short_name'], 
                         "complex")
        response = self.client.get("/assess/the_test/solution")
        self.assertEqual(response.context['assessment_name'], 
                         "This complex assessment solution")
        self.assertEqual(response.context['assessment_short_name'], 
                         "complex sol.")

    def test_question_numbers(self):
        
        begin_seed = random.randint(1,100000)
        for seed in range(begin_seed,begin_seed+3):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed,
                                        'question_numbers': ''})
            
            question_numbers = [str(q['question'].id) for q in \
                                    response.context['rendered_list']]
            question_numbers = ", ".join(question_numbers)


            self.assertEqual(response.context['question_numbers'],
                             question_numbers)

        begin_seed = random.randint(1,100000)
        for seed in range(begin_seed,begin_seed+3):
            response = self.client.get("/assess/the_test", 
                                       {'seed': '%s' % seed})

            self.assertEqual(response.context['question_numbers'],
                             None)
        

    def test_question_only(self):
        seed = random.randint(1,100000)
        response = self.client.get("/assess/the_test", 
                                   {'seed': '%s' % seed})
        
        question_ids = [q['question'].id for q in \
                            response.context['rendered_list']]
        
        for i in range(3):
            response = self.client.get("/assess/the_test/%s" % (i+1), 
                                       {'seed': '%s' % seed})
            qid = [q['question'].id for q in \
                       response.context['rendered_list']]
            self.assertEqual(len(qid),1)

            self.assertEqual(qid[0], question_ids[i])


    def test_generate_assessment_link(self):
        response = self.client.get("/assess/the_test")
        self.assertFalse(response.context['generate_assessment_link'])

        u=User.objects.create_user("user1", password="pass")
        self.client.login(username="user1",password="pass")
        response = self.client.get("/assess/the_test")
        self.assertFalse(response.context['generate_assessment_link'])

        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        response = self.client.get("/assess/the_test")
        self.assertTrue(response.context['generate_assessment_link'])
                                   
        
    def test_solution_link(self):
        response = self.client.get("/assess/the_test")
        self.assertFalse(response.context['show_solution_link'])

        u=User.objects.create_user("user1", password="pass")
        self.client.login(username="user1",password="pass")
        response = self.client.get("/assess/the_test")
        self.assertFalse(response.context['show_solution_link'])

        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        response = self.client.get("/assess/the_test")
        self.assertTrue(response.context['show_solution_link'])
        response = self.client.get("/assess/the_test/solution")
        self.assertFalse(response.context['show_solution_link'])


    def test_assessment_date(self):
        import datetime
        response = self.client.get("/assess/the_test")
        self.assertEqual(response.context['assessment_date'],
                         datetime.date.today().strftime("%B %d, %Y"))
        response = self.client.get("/assess/the_test",
                                   {'date': 'Feb 41, 3102'})
        self.assertEqual(response.context['assessment_date'], 'Feb 41, 3102')
        

    def test_seed(self):
        u=User.objects.create_user("user1", password="pass")
        self.client.login(username="user1",password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)

        self.q1.expression_set.create(
            name="n", expression="(-100,100)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q1.question_text="Question 1, n is {{n}}."
        self.q1.solution_text="Solution for: Question 1, n is {{n}}."
        self.q1.save()
        
        
        begin_seed = random.randint(1,100000)
        for seed in range(begin_seed,begin_seed+3):

            response = self.client.get("/assess/the_test",
                                       {'seed': seed })

            question1ind = [q['question'] for q in \
                            response.context['rendered_list']].index(self.q1)

            question1text =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']

            response = self.client.get("/assess/the_test",
                                       {'seed': seed })

            question1inda = [q['question'] for q in \
                                response.context['rendered_list']].index(self.q1)
            self.assertEqual(question1inda, question1ind)
            
            question1texta =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']
            self.assertEqual(question1texta, question1text)

            response = self.client.get("/assess/the_test/solution",
                                       {'seed': seed })

            question1indb = [q['question'] for q in \
                                response.context['rendered_list']].index(self.q1)
            self.assertEqual(question1indb, question1ind)
            
            solution1text =  response.context['rendered_list'][question1ind] \
                ['question_data']['rendered_text']
            self.assertTrue(question1text in solution1text)


    def test_template_selected(self):

        u=User.objects.create_user("instructor", password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        self.client.login(username="instructor", password="pass")

        response = self.client.get("/assess/the_test")
        self.assertTemplateUsed(response,"mitesting/assessment.html")

        response = self.client.get("/assess/the_test/solution")
        self.assertTemplateUsed(response,"mitesting/assessment_solution.html")

        at_exam = AssessmentType.objects.create(
            code="exam", name="exam", assessment_privacy=0, solution_privacy=0,
            template_base_name = "exam")
        asmt_exam = Assessment.objects.create(
            code="the_exam", name="The exam", assessment_type=at_exam)
        
        asmt_exam.questionassigned_set.create(question=self.q1)
        asmt_exam.questionassigned_set.create(question=self.q2)
        asmt_exam.questionassigned_set.create(question=self.q3)

        response = self.client.get("/assess/the_exam")
        self.assertTemplateUsed(response,"mitesting/exam.html")
        self.assertTemplateNotUsed(response,"mitesting/assessment.html")

        response = self.client.get("/assess/the_exam/solution")
        self.assertTemplateUsed(response,"mitesting/exam_solution.html")
        self.assertTemplateNotUsed(response,
                                   "mitesting/assessment_solution.html")

        at_wonky_one = AssessmentType.objects.create(
            code="wonky_one", name="wonky_one", assessment_privacy=0, solution_privacy=0,
            template_base_name = "wonky_one")
        asmt_wonky_one = Assessment.objects.create(
            code="the_wonky_one", name="The wonky_one", assessment_type=at_wonky_one)
        
        asmt_wonky_one.questionassigned_set.create(question=self.q1)
        asmt_wonky_one.questionassigned_set.create(question=self.q2)
        asmt_wonky_one.questionassigned_set.create(question=self.q3)

        response = self.client.get("/assess/the_wonky_one")
        self.assertTemplateUsed(response,"mitesting/assessment.html")

        response = self.client.get("/assess/the_wonky_one/solution")
        self.assertTemplateUsed(response, "mitesting/assessment_solution.html")


class TestAssessmentViewPermissions(TestCase):

    def setUp(self):
        random.seed()
        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The 1 question",
            solution_text = "The 1 solution",
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The 2 question",
            solution_text = "The 2 solution"
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "The 3 question",
            solution_text = "The 3 solution"
            )
        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

    def test_permissions(self):
        asmt_codes=[[],[],[]]
        for i in range(3):
            for j in range(3):
                at = AssessmentType.objects.create(
                    code="%s_%s" % (i,j),
                    name="%s %s" % (i,j),
                    assessment_privacy=i,
                    solution_privacy=j)
                asmt=Assessment.objects.create(
                    code="test_%s_%s" % (i,j),
                    name = "Test %s %s" % (i,j),
                    assessment_type = at,
                    )
                asmt_codes[i].append(asmt.code) 
                if i==0:
                    asmt.questionassigned_set.create(question=self.q1)
                elif i==1:
                    asmt.questionassigned_set.create(question=self.q2)
                else:
                    asmt.questionassigned_set.create(question=self.q3)
               
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
            if users[iu]:
                self.client.login(username=users[iu],password="pass")
            for ia in range(3):
                for ja in range(3):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    if iu < ia:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s" % (ia,ja))
                        self.assertContains(
                            response,"The %s question" % (ia+1))

                        if iu < ja:
                            self.assertNotContains(
                                response, "Show solution")
                        else: 
                            self.assertContains(
                                response, "Show solution")

                    response = self.client.get(
                        "/assess/%s/solution" % asmt_codes[ia][ja])

                    if iu < 2:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s/solution' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s solution" % (ia,ja))
                        self.assertContains(
                            response,"The %s solution" % (ia+1))

            self.client.logout()

            

    def test_permissions_via_question(self):
        asmt_codes=[[],[],[]]
        for i in range(3):
            for j in range(3):
                asmt=Assessment.objects.create(
                    code="test_%s_%s" % (i,j),
                    name = "Test %s %s" % (i,j),
                    assessment_type = self.at,
                    )
                asmt_codes[i].append(asmt.code) 
                q=Question.objects.create(
                    name="question",
                    question_text="A profound question",
                    solution_text="The only solution",
                    question_type = self.qt,
                    question_privacy = i,
                    solution_privacy = j,
                    )
                
                asmt.questionassigned_set.create(question=q)
               
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
            if users[iu]:
                self.client.login(username=users[iu],password="pass")
            for ia in range(3):
                for ja in range(3):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    if iu < ia:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s" % (ia,ja))
                        self.assertContains(
                            response,"A profound question")

                        if iu < ja:
                            self.assertNotContains(
                                response, "Show solution")
                        else: 
                            self.assertContains(
                                response, "Show solution")

                    response = self.client.get(
                        "/assess/%s/solution" % asmt_codes[ia][ja])

                    if iu < 2:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s/solution' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s solution" % (ia,ja))
                        self.assertContains(
                            response,"The only solution")
            self.client.logout()

            
    def test_privacy_overrides(self):
        group1=Group.objects.create(name="Normal group")
        group2=Group.objects.create(name="Can see group")
        group3=Group.objects.create(name="Can see solution group")

        asmt_codes=[[],[]]
        for i in range(2):
            for j in range(2):
                at = AssessmentType.objects.create(
                    code="%s_%s" % (i+1,j+1),
                    name="%s %s" % (i+1,j+1),
                    assessment_privacy=i+1,
                    solution_privacy=j+1)
                asmt=Assessment.objects.create(
                    code="test_%s_%s" % (i+1,j+1),
                    name = "Test %s %s" % (i+1,j+1),
                    assessment_type = at,
                    )
                asmt_codes[i].append(asmt.code) 
                if i==0:
                    asmt.questionassigned_set.create(question=self.q1)
                else:
                    asmt.questionassigned_set.create(question=self.q2)
                asmt.groups_can_view.add(group2)
                asmt.groups_can_view_solution.add(group3)
        

        users = []
        user_objects = []

        username = "user"
        users.append(username)
        u=User.objects.create_user(username, password="pass")
        user_objects.append(u)
        u.groups.add(group1)

        username = "instructor"
        users.append(username)
        u=User.objects.create_user(username, password="pass")
        p=Permission.objects.get(codename = "administer_assessment")
        u.user_permissions.add(p)
        user_objects.append(u)
        u.groups.add(group1)

        for iu in range(2):
            self.client.login(username=users[iu],password="pass")
            for ia in range(2):
                for ja in range(2):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    if iu < ia:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s" % (ia+1,ja+1))
                        self.assertContains(
                            response,"The %s question" % (ia+1))

                        if iu < ja:
                            self.assertNotContains(
                                response, "Show solution")
                        else: 
                            self.assertContains(
                                response, "Show solution")

                    response = self.client.get(
                        "/assess/%s/solution" % asmt_codes[ia][ja])

                    if iu < 1:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s/solution' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s solution" % (ia+1,ja+1))
                        self.assertContains(
                            response,"The %s solution" % (ia+1))

            self.client.logout()

        

        for iu in range(2):
            user_objects[iu].groups.remove(group1)
            user_objects[iu].groups.add(group2)
            self.client.login(username=users[iu],password="pass")
            for ia in range(2):
                for ja in range(2):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    self.assertContains(
                        response,"Test %s %s" % (ia+1,ja+1))
                    self.assertContains(
                        response,"The %s question" % (ia+1))

                    if iu < ja:
                        self.assertNotContains(
                            response, "Show solution")
                    else: 
                        self.assertContains(
                            response, "Show solution")

                    response = self.client.get(
                        "/assess/%s/solution" % asmt_codes[ia][ja])

                    if iu < 1:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s/solution' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s solution" % (ia+1,ja+1))
                        self.assertContains(
                            response,"The %s solution" % (ia+1))

            self.client.logout()

        for iu in range(2):
            user_objects[iu].groups.remove(group2)
            user_objects[iu].groups.add(group3)
            self.client.login(username=users[iu],password="pass")
            for ia in range(2):
                for ja in range(2):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    if iu < ia:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s" % (ia+1,ja+1))
                        self.assertContains(
                            response,"The %s question" % (ia+1))

                        self.assertContains(
                            response, "Show solution")

                    response = self.client.get(
                        "/assess/%s/solution" % asmt_codes[ia][ja])

                    if iu < 1:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s/solution' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s solution" % (ia+1,ja+1))
                        self.assertContains(
                            response,"The %s solution" % (ia+1))

            self.client.logout()


    def test_solution_buttons(self):
  
        self.q2.solution_privacy=1
        self.q2.save()
        
        self.q3.solution_privacy=2
        self.q3.save()
        
        solution_button_1_html_fragment = '<input type="button" class="mi_show_solution" value="Show solution" id="question_qa0_show_solution" disabled >'
        solution_button_2_html_fragment = '<input type="button" class="mi_show_solution" value="Show solution" id="question_qa1_show_solution" disabled >'
        solution_button_3_html_fragment = '<input type="button" class="mi_show_solution" value="Show solution" id="question_qa2_show_solution" disabled >'


        asmt_codes=[[],[],[]]
        for i in range(3):
            for j in range(3):
                at = AssessmentType.objects.create(
                    code="%s_%s" % (i,j),
                    name="%s %s" % (i,j),
                    assessment_privacy=i,
                    solution_privacy=j)
                asmt=Assessment.objects.create(
                    code="test_%s_%s" % (i,j),
                    name = "Test %s %s" % (i,j),
                    assessment_type = at,
                    )
                asmt_codes[i].append(asmt.code) 
                asmt.questionassigned_set.create(question=self.q1)
                asmt.questionassigned_set.create(question=self.q2)
                asmt.questionassigned_set.create(question=self.q3)
               

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
            if users[iu]:
                self.client.login(username=users[iu],password="pass")
            for ia in range(3):
                for ja in range(3):
                    response = self.client.get(
                        "/assess/%s" % asmt_codes[ia][ja])

                    if iu < ia:
                        self.assertRedirects(response, '/accounts/login?next=http%%3A//testserver/assess/%s' % asmt_codes[ia][ja])
                    else:
                        self.assertContains(
                            response,"Test %s %s" % (ia,ja))
                        if iu < ja:
                            self.assertNotContains(
                                response, solution_button_1_html_fragment)
                        else:
                            self.assertContains(
                                response, solution_button_1_html_fragment)

                        if iu < 1 or iu < ja:
                            self.assertNotContains(
                                response, solution_button_2_html_fragment)
                        else:
                            self.assertContains(
                                response, solution_button_2_html_fragment)
                        if iu < 2 or iu < ja:
                            self.assertNotContains(
                                response, solution_button_3_html_fragment)
                        else:
                            self.assertContains(
                                response, solution_button_3_html_fragment)

            self.client.logout()