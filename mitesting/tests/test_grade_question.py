from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.test import TestCase
from django.template import Context
from mitesting.grade_question import *
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption
from mitesting.math_objects import math_object
from mitesting.sympy_customized import parse_expr

from sympy import Symbol, sympify
import six
import random

EXPRESSION = QuestionAnswerOption.EXPRESSION
MULTIPLE_CHOICE = QuestionAnswerOption.MULTIPLE_CHOICE
        
class TestCompareResponse(TestCase):
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

    def new_answer(self, **kwargs):
        return self.q.questionansweroption_set.create(**kwargs)


    def test_compare_multiple_choice(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': MULTIPLE_CHOICE}
        
        answer_results=compare_response_with_answer_code\
                        (user_response=1, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])


        true_id=self.new_answer(answer_code="true", answer="true", answer_type=MULTIPLE_CHOICE, feedback="You got it!").id
        false_id=self.new_answer(answer_code="true", answer="false", answer_type=MULTIPLE_CHOICE, percent_correct=0, feedback="Guess again.").id
        maybe_id=self.new_answer(answer_code="true", answer="maybe", answer_type=MULTIPLE_CHOICE, percent_correct=50, feedback="You should be certain.").id
        

        answer_results=compare_response_with_answer_code\
                        (user_response=true_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])


        answer_info={'code': 'true', 'type': MULTIPLE_CHOICE}

        answer_results=compare_response_with_answer_code\
                        (user_response=true_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("are correct" in answer_results["answer_feedback"])
        self.assertTrue("You got it!" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response=false_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("incorrect" in answer_results["answer_feedback"])
        self.assertTrue("Guess again." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response=maybe_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])
        self.assertTrue("You should be certain." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response={"garbage":"garbage"}, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("No response" in answer_results["answer_feedback"])


    def test_basic_expression(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        
        answer_results=compare_response_with_answer_code\
                        (user_response="hello", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)
        
        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])

        self.new_answer(answer_code="a", answer="ax")
        expr_context["ax"]=math_object(sympify("a*x"))
        
        answer_results=compare_response_with_answer_code\
                        (user_response="ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="xa", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])



    def test_multiple_answers(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        
        self.new_answer(answer_code="a", answer="ax", feedback="You got it!")
        expr_context["ax"]=math_object(sympify("a*x"))
        self.new_answer(answer_code="a", answer="bx", feedback="Getting close.", percent_correct=50)
        expr_context["bx"]=math_object(sympify("b*x"))
        self.new_answer(answer_code="a", answer="cx", feedback="Bad idea.", percent_correct=0)
        expr_context["cx"]=math_object(sympify("c*x"))

        answer_results=compare_response_with_answer_code\
                        (user_response="ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
        self.assertTrue("You got it!" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="bx", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])
        self.assertTrue("Getting close." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="cx", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("Bad idea." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="foo", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertFalse("You got it!" in answer_results["answer_feedback"])
        self.assertFalse("Getting close." in answer_results["answer_feedback"])
        self.assertFalse("Bad idea." in answer_results["answer_feedback"])


    def test_split_symbols_on_compare(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["two_a_x"]=math_object(sympify("2*a*x"))
        expr_context["two_ax"]=math_object(sympify("2*ax"))

        
        the_ans=self.new_answer(answer_code="a", answer="two_a_x")
        the_ans_unsplit=self.new_answer(answer_code="a", answer="two_ax",
                                        percent_correct=50,
                                        split_symbols_on_compare=False)
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        the_ans.split_symbols_on_compare=False
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)
        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])

    def test_round_on_compare(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["aa"]=math_object(sympify("2.31313*a"))

        
        the_ans=self.new_answer(answer_code="a", answer="aa",
                                round_on_compare=4)
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2.31328a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.round_partial_credit="1"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])


        the_ans.round_partial_credit="1, 0"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])

        the_ans.round_partial_credit="1, 70"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("70%" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="2.30228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("2 significant digits" not in answer_results["answer_feedback"])

        the_ans.round_partial_credit="2, 70"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.312315a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("70%" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.30228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(round(answer_results['percent_correct'],10),49)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("49%" in answer_results["answer_feedback"])
        self.assertTrue("matched to 2 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])


        the_ans.round_partial_credit="3, 70"
        the_ans.round_absolute=True
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.313128a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="2.31338a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("matched to the nearest 0.001 place" in answer_results["answer_feedback"])
        self.assertTrue("matching to the 0.0001 place is required" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.33228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(round(answer_results['percent_correct'],10),34.3)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("34%" in answer_results["answer_feedback"])
        self.assertTrue("matched to the nearest 0.1 place" in answer_results["answer_feedback"])
        self.assertTrue("matching to the 0.0001 place is required" in answer_results["answer_feedback"])



    def test_tuples(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a,b,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        expr_context["a"]=math_object(parse_expr("a,b,c"), 
                                      tuple_is_unordered=False)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        expr_context["a"]=math_object(parse_expr("a,b,c"), 
                                      tuple_is_unordered=True)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    

    def test_tuples_partial_match(self):
        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c,d"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=False
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=True
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,d,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

    
        expr_context["a"]=math_object(parse_expr("a,b,c,d"), 
                                      tuple_is_unordered=True)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,d,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])

    
    def test_different_tuple_types(self):

        global_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)


        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


        expr_context["a"]=math_object(parse_expr("(a,b,c)"))
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,b,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)


        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, global_dict=global_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


class TestQuestionGroups(TestCase):
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

    def new_answer(self, **kwargs):
        return self.q.questionansweroption_set.create(**kwargs)

    
    def test_small_group(self):
        global_dict={}
        expr_context=Context({})


        # set up three answers, two in the same group
        answer_info=[]

        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        self.new_answer(answer_code="a", answer="ax", feedback="The first answer")
        expr_context["ax"]=math_object(sympify("a*x"))

        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        self.new_answer(answer_code="b", answer="bx", feedback="The second answer")
        expr_context["bx"]=math_object(sympify("b*x"))

        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'identifier': id3,
                            'points': 1})
        self.new_answer(answer_code="c", answer="cx", feedback="Answer not in group")
        expr_context["cx"]=math_object(sympify("c*x"))

        
        answer_user_responses=[]

        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "cx"})

        answer_results={'answers': {}}

        group_list=[0,1]
        
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        self.assertTrue("The first answer" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id2]["answer_feedback"])
        self.assertTrue("The second answer" in answer_results['answers'][id2]["answer_feedback"])
        
        # switch order of first two

        answer_user_responses=[]

        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        self.assertTrue("The second answer" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id2]["answer_feedback"])
        self.assertTrue("The first answer" in answer_results['answers'][id2]["answer_feedback"])

        # repeat first answer

        answer_user_responses=[]

        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id2]["answer_feedback"])


        # repeat second answer

        answer_user_responses=[]

        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id2]["answer_feedback"])


        # switch first and third answer

        answer_user_responses=[]

        answer_user_responses.append({'answer': "cx"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "ax"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertFalse(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id2]["answer_feedback"])


    def test_multiple_answers_no_overlapp(self):
        global_dict={}
        expr_context=Context({})


        # set up three answers in group with multiple acceptable answers each
        answer_info=[]
        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id3, 'points': 1})


        # no overlap between acceptable answers
        self.new_answer(answer_code="a", answer="ax")
        expr_context["ax"]=math_object(sympify("a*x"))
        self.new_answer(answer_code="a", answer="ay")
        expr_context["ay"]=math_object(sympify("a*y"))

        self.new_answer(answer_code="b", answer="bx")
        expr_context["bx"]=math_object(sympify("b*x"))
        self.new_answer(answer_code="b", answer="by")
        expr_context["by"]=math_object(sympify("b*y"))
        
        self.new_answer(answer_code="c", answer="cx")
        expr_context["cx"]=math_object(sympify("c*x"))
        self.new_answer(answer_code="c", answer="cy")
        expr_context["cy"]=math_object(sympify("c*y"))
        
        answer_user_responses=[]
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "cx"})
        answer_user_responses.append({'answer': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        answer_user_responses=[]
        answer_user_responses.append({'answer': "by"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "ay"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        answer_user_responses=[]
        answer_user_responses.append({'answer': "cy"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)




    def test_multiple_answers_overlap1(self):
        global_dict={}
        expr_context=Context({})


        # set up three answers in group with multiple acceptable answers each
        answer_info=[]
        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id3, 'points': 1})


        # each answer acceptable in two slots
        # not sure why would have this, but it's possible with system
        expr_context["ax"]=math_object(sympify("a*x"))
        expr_context["bx"]=math_object(sympify("b*x"))
        expr_context["cx"]=math_object(sympify("c*x"))

        self.new_answer(answer_code="a", answer="ax")
        self.new_answer(answer_code="a", answer="bx")
        self.new_answer(answer_code="b", answer="bx")
        self.new_answer(answer_code="b", answer="cx")
        self.new_answer(answer_code="c", answer="cx")
        self.new_answer(answer_code="c", answer="ax")
 
         
        answer_user_responses=[]
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],0)

        answer_user_responses=[]
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "bx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        answer_user_responses=[]
        answer_user_responses.append({'answer': "dx"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "bx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertFalse(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],0)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)


    def test_multiple_answers_overlap2(self):
        global_dict={}
        expr_context=Context({})


        # set up four answers in group with multiple acceptable answers each
        answer_info=[]
        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id3, 'points': 1})
        id4='fourth_one'
        answer_info.append({'code': 'd', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id4, 'points': 1})


        # each answer acceptable in multiple slots
        # not sure why would have this, but it's possible with system
        expr_context["ax"]=math_object(sympify("a*x"))
        expr_context["bx"]=math_object(sympify("b*x"))
        expr_context["cx"]=math_object(sympify("c*x"))
        expr_context["dx"]=math_object(sympify("d*x"))

        self.new_answer(answer_code="a", answer="ax")
        self.new_answer(answer_code="a", answer="bx")
        self.new_answer(answer_code="b", answer="ax")
        self.new_answer(answer_code="b", answer="bx")
        self.new_answer(answer_code="b", answer="cx")
        self.new_answer(answer_code="b", answer="dx")
        self.new_answer(answer_code="c", answer="bx")
        ans34=self.new_answer(answer_code="c", answer="dx")
        self.new_answer(answer_code="d", answer="ax")
        ans44=self.new_answer(answer_code="d", answer="dx")
 
         
        answer_user_responses=[]
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "cx"})
        answer_user_responses.append({'answer': "dx"})
        answer_results={'answers': {}}
        group_list=[0,1,2,3]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,400)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id4]['answer_correct'])
        self.assertEqual(answer_results['answers'][id4]['percent_correct'],100)


        ans34.delete()
        ans44.delete()

        answer_results={'answers': {}}
        group_list=[0,1,2,3]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id4]['answer_correct'])
        self.assertEqual(answer_results['answers'][id4]['percent_correct'],0)

        

    def test_multiple_answers_partial_credit(self):
        global_dict={}
        expr_context=Context({})


        # set up three answers in group with multiple acceptable answers each
        answer_info=[]
        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id3, 'points': 1})


        # each answer acceptable in two slots
        # not sure why would have this, but it's possible with system
        expr_context["ax"]=math_object(sympify("a*x"))
        expr_context["bx"]=math_object(sympify("b*x"))
        expr_context["cx"]=math_object(sympify("c*x"))

        ans11=self.new_answer(answer_code="a", answer="ax", percent_correct=100)
        ans12=self.new_answer(answer_code="a", answer="bx", percent_correct=50)
        ans22=self.new_answer(answer_code="b", answer="bx", percent_correct=100)
        ans23=self.new_answer(answer_code="b", answer="cx", percent_correct=50)
        ans33=self.new_answer(answer_code="c", answer="cx", percent_correct=100)
        ans31=self.new_answer(answer_code="c", answer="ax", percent_correct=50)
 
         
        answer_user_responses=[]
        answer_user_responses.append({'answer': "ax"})
        answer_user_responses.append({'answer': "bx"})
        answer_user_responses.append({'answer': "cx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)


        
        ans22.percent_correct=40
        ans22.save()
        ans33.percent_correct=30
        ans33.save()


        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, answer_user_responses=answer_user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, global_dict=global_dict, 
            answer_results=answer_results)


        # doesn't give maximum possible points in this case, as will choose the
        # 50% credit over the 40% + the 30%
        self.assertEqual(points_times_100,150)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertFalse(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],50)



# haven't tested grade_question function directly, but do via question_view
