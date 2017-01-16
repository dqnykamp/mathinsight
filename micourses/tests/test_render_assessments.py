from django.test import TestCase
from mitesting.models import Question, QuestionType
from micourses.models import Course, Assessment, AssessmentType
from midocs.models import Page, PageType
from micourses.render_assessments import get_question_list, render_question_list
from mitesting.sympy_customized import SymbolCallable, Symbol, Dummy
from django.contrib.auth.models import AnonymousUser, User, Permission
from mitesting.utils import get_new_seed

from sympy import sympify
import random


class TestGetQuestionList(TestCase):

    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()

        self.course = Course.objects.create(name="course", code="course")
        
        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            course=self.course,
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            course=self.course,
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            course=self.course,
            )

        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            course=self.course,
            )

        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at,
            course=self.course)
        
        self.qsa1=self.asmt.questionassigned_set.create(question=self.q1)
        self.qsa2=self.asmt.questionassigned_set.create(question=self.q2)
        self.qsa3=self.asmt.questionassigned_set.create(question=self.q3)
        self.qsa4=self.asmt.questionassigned_set.create(question=self.q4)

    
    def test_one_question_per_question_set(self):
        
        for i in range(10):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            questions = {ql['question'] for ql in question_list}
            self.assertEqual(questions, {self.q1, self.q2, self.q3, self.q4})
            
            question_sets = sorted([ql['question_set'] for ql in question_list])
            self.assertEqual(question_sets, [1,2,3,4])

            relative_weights = [ql['relative_weight'] for ql in question_list]
            self.assertEqual(relative_weights, [1/4,1/4,1/4,1/4])
            
            for ql in question_list:
                seed = ql['seed']
                self.assertTrue(int(seed) >= 0)
                self.assertTrue(int(seed) <= 1000000000000)


    def test_multiple_questions_per_question_set(self):
        self.qsa1.question_set=2
        self.qsa1.save()
        self.qsa3.question_set=4
        self.qsa3.save()

        valid_options = [{self.q1,self.q3},{self.q1,self.q4},{self.q2,self.q3},{self.q2,self.q4}]

        options_used = [False, False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            questions = {ql['question'] for ql in question_list}
            self.assertTrue(questions in valid_options)

            one_used = valid_options.index(questions)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


        self.qsa1.question_set=4
        self.qsa1.save()

        valid_options = [{self.q2,self.q1},{self.q2,self.q3},{self.q2,self.q4}]

        options_used = [False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            questions = {ql['question'] for ql in question_list}
            self.assertTrue(questions in valid_options)

            one_used = valid_options.index(questions)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)


    def test_with_weight(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa4.question_set=2
        self.qsa4.save()

        self.asmt.questionsetdetail_set.create(question_set=3,
                                               weight = 5)
        self.asmt.questionsetdetail_set.create(question_set=2,
                                               weight = 7.3)

        valid_options = [{self.q2,self.q1},{self.q2,self.q3},{self.q4,self.q1},{self.q4,self.q3}]

        options_used = [False, False, False, False]

        for i in range(100):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            
            relative_weights = {ql['relative_weight'] for ql in question_list}
            self.assertEqual(relative_weights, {5/12.3, 7.3/12.3})

            questions = {ql['question'] for ql in question_list}
            self.assertTrue(questions in valid_options)

            one_used = valid_options.index(questions)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)

    def test_with_zero_weight(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa4.question_set=2
        self.qsa4.save()

        self.asmt.questionsetdetail_set.create(question_set=3,
                                               weight = 0)
        self.asmt.questionsetdetail_set.create(question_set=2,
                                               weight = 0)

        question_list = get_question_list(self.asmt, rng=self.rng,
                                          seed=get_new_seed(self.rng))

        for ql in question_list:
            self.assertEqual(ql['relative_weight'], 0)


class TestRenderQuestionList(TestCase):
    
    def setUp(self):
        self.rng = random.Random()
        self.rng.seed()
   
        self.course = Course.objects.create(name="Course", code="course")

        self.qt = QuestionType.objects.create(name="question type")
        self.q1  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 1 text.",
            solution_text = "Question number 1 solution.",
            course=self.course
            )
        self.q2  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 2 text.",
            solution_text = "Question number 2 solution.",
            course=self.course,
            )
        self.q3  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 3 text.",
            solution_text = "Question number 3 solution.",
            course=self.course,
            )

        self.q4  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text = "Question number 4 text.",
            solution_text = "Question number 4 solution.",
            course=self.course,
            )


        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at,
            course=self.course)
        
        self.qsa1=self.asmt.questionassigned_set.create(question=self.q1)
        self.qsa2=self.asmt.questionassigned_set.create(question=self.q2)
        self.qsa3=self.asmt.questionassigned_set.create(question=self.q3)
        self.qsa4=self.asmt.questionassigned_set.create(question=self.q4)


    def test_no_question_groups_all_orders(self):
        self.qsa4.delete()
        
        qs = [self.q1, self.q2, self.q3, self.q4]
        valid_orders = []
        orders_used = []
        for i in range(3):
            for j in range(3):
                if i==j:
                    continue
                for k in range(3):
                    if k==i or k==j:
                        continue
                    valid_orders.append([qs[i], qs[j], qs[k]])
                    orders_used.append(False)

        for i in range(200):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            for question_dict in question_list:
                self.assertEqual(question_dict['relative_weight'],1/3)
                self.assertFalse(question_dict['previous_same_group'])
            questions = [ql['question'] for ql in question_list]
            self.assertTrue(questions in valid_orders)
            one_used = valid_orders.index(questions)
            orders_used[one_used]=True
            
            if False not in orders_used:
                break

        self.assertTrue(False not in orders_used)


    def test_no_question_groups_fixed_order(self):
        self.asmt.fixed_order=True
        self.asmt.save()

        qs = [self.q1, self.q2, self.q3, self.q4]
        for j in range(10):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            for (i,question_dict) in enumerate(question_list):
                self.assertEqual(question_dict['question'], qs[i])
                self.assertEqual(question_dict['question_set'], i+1)
                self.assertEqual(question_dict['relative_weight'],1/4)
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
        qs = [self.q1, self.q2, self.q3, self.q4]
        for j in range(10):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            hit_first_group_member=False
            expected_next_group_member=None
            for (i,question_dict) in enumerate(question_list):
                if hit_first_group_member:
                    self.assertTrue(question_dict['previous_same_group'])
                    self.assertEqual(question_dict['group'],'apple')
                    self.assertEqual(qs.index(question_dict['question'])+1, 
                                     expected_next_group_member)
                    hit_first_group_member = False
                        
                else:
                    self.assertFalse(question_dict['previous_same_group'])
                    if question_dict['group'] == 'apple':
                        hit_first_group_member = True
                        if qs.index(question_dict['question']) == 0:
                            expected_next_group_member = 4
                        else:
                            expected_next_group_member = 1

                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %i text." % (qs.index(question_dict['question'])+1))


        self.asmt.questionsetdetail_set.create(question_set=2,
                                               group="appl")
        self.asmt.questionsetdetail_set.create(question_set=3,
                                               group="appl")

        for j in range(10):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            hit_first_group_member=False
            expected_next_group_member=None
            for (i,question_dict) in enumerate(question_list):
                if hit_first_group_member:
                    self.assertTrue(question_dict['previous_same_group'])
                    self.assertEqual(question_dict['group'],group_found)
                    self.assertEqual(qs.index(question_dict['question'])+1, 
                                     expected_next_group_member)
                    hit_first_group_member = False
                        
                else:
                    self.assertFalse(question_dict['previous_same_group'])
                    group_found = question_dict['group']
                    if group_found == 'apple':
                        hit_first_group_member = True
                        if qs.index(question_dict['question']) == 0:
                            expected_next_group_member = 4
                        else:
                            expected_next_group_member = 1
                    elif group_found == 'appl':
                        hit_first_group_member = True
                        if qs.index(question_dict['question']) == 1:
                            expected_next_group_member = 3
                        else:
                            expected_next_group_member = 2
                        
                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %s text." % (qs.index(question_dict['question'])+1))



    def test_groups_fixed_order(self):
        self.asmt.fixed_order=True
        self.asmt.save()

        self.asmt.questionsetdetail_set.create(question_set=1,
                                               group="apple")
        self.asmt.questionsetdetail_set.create(question_set=4,
                                               group="apple")
        for i in range(3):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            questions = [ql['question'] for ql in question_list]
            self.assertEqual(questions, [self.q1,self.q2,self.q3,self.q4])
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
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            questions = [ql['question'] for ql in question_list]
            self.assertEqual(questions, [self.q1,self.q2,self.q3,self.q4])
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
        
        valid_options=[[self.q1,self.q2],[self.q2,self.q1],[self.q1,self.q4],[self.q4,self.q1],
                       [self.q3,self.q2],[self.q2,self.q3],[self.q3,self.q4],[self.q4,self.q3]]

        options_used = [False, False, False, False,
                        False, False, False, False]

        for j in range(200):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng))
            questions = [ql['question'] for ql in question_list]
            
            self.assertTrue(questions in valid_options)
            
            one_used = valid_options.index(questions)
            options_used[one_used]=True
            
            if False not in options_used:
                break

        self.assertTrue(False not in options_used)
    


    # def test_points(self):
    #     self.assertEqual(self.asmt.get_total_points(),0)
    #     question_list = get_question_list(self.asmt, rng=self.rng,
    #                                       seed=get_new_seed(self.rng))
    #     question_list = render_question_list(
    #         self.asmt, rng=self.rng, question_list = question_list,
    #         assessment_seed=get_new_seed(self.rng))
        
    #     points = [ql['points'] for ql in question_list]
    #     self.assertEqual(points,["","","",""])

    #     self.asmt.questionsetdetail_set.create(question_set=3,
    #                                            points = 5)
    #     self.assertEqual(self.asmt.get_total_points(),5)
        
    #     self.qsa1.question_set=3
    #     self.qsa1.save()
    #     self.qsa4.question_set=2
    #     self.qsa4.save()

    #     self.asmt.questionsetdetail_set.create(question_set=2,
    #                                            points = 7.3)

        
    #     valid_options = [[self.q2,self.q1],[self.q2,self.q3],[self.q4,self.q1],[self.q4,self.q3],
    #                      [self.q1,self.q2],[self.q3,self.q2],[self.q1,self.q4],[self.q3,self.q4]]

    #     options_used = [False, False, False, False,
    #                     False, False, False, False]

    #     self.assertEqual(self.asmt.get_total_points(),12.3)

    #     for i in range(100):
    #         question_list = get_question_list(self.asmt, rng=self.rng,
    #                                           seed=get_new_seed(self.rng))
    #         question_list = render_question_list(
    #             self.asmt, rng=self.rng, question_list = question_list,
    #             assessment_seed=get_new_seed(self.rng))

    #         points = [ql['points'] for ql in question_list]
    #         qs1 = question_list[0]['question_set']
    #         if qs1 == 3:
    #             self.assertEqual(points, [5,7.3])
    #         else:
    #             self.assertEqual(points, [7.3,5])

    #         questions = [ql['question'] for ql in question_list]
    #         self.assertTrue(questions in valid_options)

    #         one_used = valid_options.index(questions)
    #         options_used[one_used]=True
            
    #         if False not in options_used:
    #             break

    #     self.assertTrue(False not in options_used)


    def test_solution(self):
        
        self.qsa1.question_set=3
        self.qsa1.save()
        self.qsa2.question_set=7
        self.qsa2.save()
        self.qsa3.question_set=3
        self.qsa3.save()
        self.qsa4.question_set=7
        self.qsa4.save()
        
        valid_options=[[self.q1,self.q2],[self.q2,self.q1],[self.q1,self.q4],[self.q4,self.q1],
                       [self.q3,self.q2],[self.q2,self.q3],[self.q3,self.q4],[self.q4,self.q3]]


        qs = [self.q1, self.q2, self.q3, self.q4]

        for j in range(3):
            question_list = get_question_list(self.asmt, rng=self.rng,
                                              seed=get_new_seed(self.rng))
            question_list = render_question_list(
                self.asmt, rng=self.rng, question_list = question_list,
                assessment_seed=get_new_seed(self.rng), solution=True)
            questions = [ql['question'] for ql in question_list]

            self.assertTrue(questions in valid_options)
            
            for (i,question_dict) in enumerate(question_list):
                self.assertEqual(
                    question_dict['question_data']['rendered_text'],
                    "Question number %i solution."
                    % (qs.index(question_dict['question'])+1))
            
