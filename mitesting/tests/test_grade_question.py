from django.test import TestCase
from django.template import Context
from mitesting.grade_question import *
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption
from mitesting.math_objects import math_object
from mitesting.sympy_customized import parse_expr, Symbol

from sympy import sympify
import random

EXPRESSION = QuestionAnswerOption.EXPRESSION
MULTIPLE_CHOICE = QuestionAnswerOption.MULTIPLE_CHOICE
FUNCTION = QuestionAnswerOption.FUNCTION
        
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
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': MULTIPLE_CHOICE}
        
        answer_results=compare_response_with_answer_code\
                        (user_response=1, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])


        true_id=self.new_answer(answer_code="true", answer="true", answer_type=MULTIPLE_CHOICE, feedback="You got it!").id
        false_id=self.new_answer(answer_code="true", answer="false", answer_type=MULTIPLE_CHOICE, percent_correct=0, feedback="Guess again.").id
        maybe_id=self.new_answer(answer_code="true", answer="maybe", answer_type=MULTIPLE_CHOICE, percent_correct=50, feedback="You should be certain.").id
        

        answer_results=compare_response_with_answer_code\
                        (user_response=true_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])


        answer_info={'code': 'true', 'type': MULTIPLE_CHOICE}

        answer_results=compare_response_with_answer_code\
                        (user_response=true_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("are correct" in answer_results["answer_feedback"])
        self.assertTrue("You got it!" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response=false_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("incorrect" in answer_results["answer_feedback"])
        self.assertTrue("Guess again." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response=maybe_id, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])
        self.assertTrue("You should be certain." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response={"garbage":"garbage"}, the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("No response" in answer_results["answer_feedback"])


    def test_basic_expression(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        
        answer_results=compare_response_with_answer_code\
                        (user_response="hello", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("error" in answer_results["answer_feedback"])

        self.new_answer(answer_code="a", answer="ax")
        expr_context["ax"]=math_object(Symbol("a")*Symbol("x"))
        
        answer_results=compare_response_with_answer_code\
                        (user_response="ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="xa", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])



    def test_multiple_answers(self):
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        answer_info={'code': 'a', 'type': EXPRESSION}
        
        self.new_answer(answer_code="a", answer="ax", feedback="You got it!")
        expr_context["ax"]=math_object(Symbol('a')*x)
        self.new_answer(answer_code="a", answer="bx", feedback="Getting close.", percent_correct=50)
        expr_context["bx"]=math_object(Symbol('b')*x)
        self.new_answer(answer_code="a", answer="cx", feedback="Bad idea.", percent_correct=0)
        expr_context["cx"]=math_object(Symbol('c')*x)

        answer_results=compare_response_with_answer_code\
                        (user_response="ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
        self.assertTrue("You got it!" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="bx", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])
        self.assertTrue("Getting close." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="cx", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("Bad idea." in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="foo", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertFalse("You got it!" in answer_results["answer_feedback"])
        self.assertFalse("Getting close." in answer_results["answer_feedback"])
        self.assertFalse("Bad idea." in answer_results["answer_feedback"])


    def test_split_symbols_on_compare(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["two_a_x"]=math_object(2*Symbol('a')*Symbol('x'))
        expr_context["two_ax"]=math_object(2*Symbol('ax'))

        
        the_ans=self.new_answer(answer_code="a", answer="two_a_x")
        the_ans_unsplit=self.new_answer(answer_code="a", answer="two_ax",
                                        percent_correct=50,
                                        split_symbols_on_compare=False)
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        the_ans.split_symbols_on_compare=False
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2ax", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)
        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])

    def test_round_on_compare(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["aa"]=math_object(2.31313*Symbol("a"))

        
        the_ans=self.new_answer(answer_code="a", answer="aa",
                                round_on_compare=4)
        
        answer_results=compare_response_with_answer_code\
                        (user_response="2.31328a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.round_partial_credit="1"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.31228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

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
                         expr_context=expr_context, local_dict=local_dict)

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
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("70%" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="2.30228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("2 significant digits" not in answer_results["answer_feedback"])

        the_ans.round_partial_credit="2, 70"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="2.312315a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("70%" in answer_results["answer_feedback"])
        self.assertTrue("matched to 3 significant digits" in answer_results["answer_feedback"])
        self.assertTrue("4 significant digits are required" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.30228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

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
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="2.31338a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],70)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("matched to the nearest 0.001's place" in answer_results["answer_feedback"])
        self.assertTrue("matching to the 0.0001's place is required" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.33228a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(round(answer_results['percent_correct'],10),34.3)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("34%" in answer_results["answer_feedback"])
        self.assertTrue("matched to the nearest 0.1's place" in answer_results["answer_feedback"])
        self.assertTrue("matching to the 0.0001's place is required" in answer_results["answer_feedback"])



    def test_tuples(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a,b,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        expr_context["a"]=math_object(parse_expr("a,b,c"), 
                                      tuple_is_unordered=False)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        expr_context["a"]=math_object(parse_expr("a,b,c"), 
                                      tuple_is_unordered=True)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c,b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    

    def test_tuples_partial_match(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c,d"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=False
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=True
        the_ans.save()
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,d,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

    
        expr_context["a"]=math_object(parse_expr("a,b,c,d"), 
                                      tuple_is_unordered=True)

        answer_results=compare_response_with_answer_code\
                        (user_response="a,d,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])


    def test_different_tuple_types(self):

        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a,b,c"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


        expr_context["a"]=math_object(parse_expr("(a,b,c)"))
        
        answer_results=compare_response_with_answer_code\
                        (user_response="a,b,c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)


        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


    def test_tuples_of_relational(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a>b,b<=c,c>d"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a>b, c>=b, d < c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        answer_results=compare_response_with_answer_code\
                        (user_response="a>b,c>d,c>=b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        expr_context["a"]=math_object(parse_expr("a>b,b<=c,c>d"),
                                      tuple_is_unordered=True)

        answer_results=compare_response_with_answer_code\
                        (user_response="a>b,c>d,c>=b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

    def test_boolean_of_relational(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a>b and b<=c and c>d"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a>b and c>=b and d < c", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        answer_results=compare_response_with_answer_code\
                        (user_response="a>b and c>d and c>=b", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="a>b and c>=b and d<c and a>d", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=True
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="a>b and c>=b and d<c and a>d", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])


    def test_inequality_string(self):
        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'a', 'type': EXPRESSION}
        expr_context["a"]=math_object(parse_expr("a>b >=c >d >=x"))
        
        the_ans=self.new_answer(answer_code="a", answer="a")

        answer_results=compare_response_with_answer_code\
                        (user_response="a >b >=c > d >=x", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="a >b and b >=c and c > d and d >=x", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="x <=d <c <=b < a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="b >=c > d >=x", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        the_ans.match_partial_on_compare=True
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="b >=c > d >=x", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])

    def test_matrix(self):
        from mitesting.utils import return_matrix_expression

        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'A', 'type': EXPRESSION, 
                     'expression_type': Expression.MATRIX}
        expr_context["A"]=math_object(return_matrix_expression("a b\nc d"))
        
        the_ans=self.new_answer(answer_code="A", answer="A")

        answer_results=compare_response_with_answer_code\
                        (user_response="\na b  \n  c    d  \n  ",
                         the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        answer_results=compare_response_with_answer_code\
                        (user_response="q b\nc d", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        the_ans.match_partial_on_compare=True
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="q b\nc d", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])

    
        answer_results=compare_response_with_answer_code\
                        (user_response="a b\nc", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("Invalid matrix: Got rows of variable lengths" in answer_results["answer_feedback"])


    def test_vector(self):
        from mitesting.utils import return_matrix_expression
        from mitesting.customized_commands import \
            MatrixFromTuple, MatrixAsVector
        from sympy import Tuple, Matrix

        local_dict={}
        expr_context=Context({})

        answer_info={'code': 'v', 'type': EXPRESSION, 
                     'expression_type': Expression.VECTOR}
        tuple_expr=parse_expr("(a,b,c,d)")
        vector_expr=tuple_expr.replace(Tuple,MatrixFromTuple)
        matrix_expr=Matrix(vector_expr)
        
        expr_context["v_tuple"]=math_object(tuple_expr)
        expr_context["v_vector"]=math_object(vector_expr)
        expr_context["v_matrix"]=math_object(matrix_expr)
        
        the_ans=self.new_answer(answer_code="v", answer="v_vector")

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c,d)",
                         the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])
    
        the_ans.match_partial_on_compare=True
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c,q)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],75)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("75%" in answer_results["answer_feedback"])

    
        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
    
        the_ans.answer="v_matrix"
        the_ans.save()

        answer_results=compare_response_with_answer_code\
                        (user_response="(a,b,c,d)", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])
        self.assertTrue("Your answer is mathematically equivalent to the correct answer" in answer_results['answer_feedback'])    


    def test_function(self):
        from mitesting.utils import return_parsed_function
        from mitesting.user_commands import iif

        local_dict={'if': iif}
        expr_context=Context({'_sympy_local_dict_': local_dict })

        answer_info={'code': 'a', 'type': FUNCTION}
        f=return_parsed_function("x-1", function_inputs="x", name="f",
                                 local_dict=local_dict)
        expr_context["f"]=math_object(1)
        local_dict["f"]=f

        the_ans=self.new_answer(answer_code="a", answer="f",
                                answer_type=FUNCTION)

        answer_results=compare_response_with_answer_code\
                        (user_response="0", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="1", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="1.5", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="2.8", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        f=return_parsed_function("if(x^2<1,0, if(x^2=1,1, 0.5))", 
                                 function_inputs="x", name="f",
                                 local_dict=local_dict)
        local_dict["f"]=f

        answer_results=compare_response_with_answer_code\
                        (user_response="1-2", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="10", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],50)
        self.assertTrue("not completely correct" in answer_results["answer_feedback"])
        self.assertTrue("50%" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="0.5", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="x+a", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])

        f=return_parsed_function("x.func", 
                                 function_inputs="x", name="f",
                                 local_dict=local_dict)

        local_dict["f"]=f

        answer_results=compare_response_with_answer_code\
                        (user_response="1-2", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


        f=return_parsed_function("x in {y,}", 
                                 function_inputs="x", name="f")

        local_dict["f"]=f

        answer_results=compare_response_with_answer_code\
                        (user_response="y", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="z", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


        f=return_parsed_function("x=y", 
                                 function_inputs="x", name="f",
                                 local_dict=local_dict)

        local_dict["f"]=f

        answer_results=compare_response_with_answer_code\
                        (user_response="y", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="z", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


        f=return_parsed_function("x==y", 
                                 function_inputs="x", name="f",
                                 local_dict=local_dict)

        local_dict["f"]=f

        answer_results=compare_response_with_answer_code\
                        (user_response="y", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])


        answer_results=compare_response_with_answer_code\
                        (user_response="z", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


    def test_function_is_number(self):
        from mitesting.utils import return_parsed_function
        from mitesting.user_commands import is_number
        from mitesting.models import Expression

        local_dict={'is_number': is_number}
        expr_context=Context({'_sympy_local_dict_': local_dict })

        answer_info={'code': 'a', 'type': FUNCTION}
        f=return_parsed_function("is_number(x-3s)", function_inputs="x", name="f",
                                 local_dict=local_dict)
        expr_context["f"]=math_object(1)
        local_dict["f"]=f

        the_ans=self.new_answer(answer_code="a", answer="f",
                                answer_type=FUNCTION)

        answer_results=compare_response_with_answer_code\
                        (user_response="3s", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="3s-5", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertTrue(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],100)
        self.assertTrue("is correct" in answer_results["answer_feedback"])

        answer_results=compare_response_with_answer_code\
                        (user_response="4s", the_answer_info=answer_info,
                         question=self.q, 
                         expr_context=expr_context, local_dict=local_dict)

        self.assertFalse(answer_results['answer_correct'])
        self.assertEqual(answer_results['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results["answer_feedback"])


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
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')


        # set up three answers, two in the same group
        answer_info=[]

        id1='first_one'
        answer_info.append({'code': 'a', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id1, 'points': 1})
        self.new_answer(answer_code="a", answer="ax", feedback="The first answer")
        expr_context["ax"]=math_object(a*x)

        id2='second_one'
        answer_info.append({'code': 'b', 'type': EXPRESSION, 'group': 'foo',
                            'identifier': id2, 'points': 1})
        self.new_answer(answer_code="b", answer="bx", feedback="The second answer")
        expr_context["bx"]=math_object(b*x)

        id3='third_one'
        answer_info.append({'code': 'c', 'type': EXPRESSION, 'identifier': id3,
                            'points': 1})
        self.new_answer(answer_code="c", answer="cx", feedback="Answer not in group")
        expr_context["cx"]=math_object(c*x)

        
        user_responses=[]

        user_responses.append({'response': "ax"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "cx"})

        answer_results={'answers': {}}

        group_list=[0,1]
        
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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

        user_responses=[]

        user_responses.append({'response': "bx"})
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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

        user_responses=[]

        user_responses.append({'response': "ax"})
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id2]["answer_feedback"])


        # repeat second answer

        user_responses=[]

        user_responses.append({'response': "bx"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "cx"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id2]["answer_feedback"])


        # switch first and third answer

        user_responses=[]

        user_responses.append({'response': "cx"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "ax"})

        answer_results={'answers': {}}

        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,100)

        self.assertFalse(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],0)
        self.assertTrue("is incorrect" in answer_results['answers'][id1]["answer_feedback"])
        
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue("is correct" in answer_results['answers'][id2]["answer_feedback"])


    def test_multiple_answers_no_overlapp(self):
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        y=Symbol('y')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        
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
        expr_context["ax"]=math_object(a*x)
        self.new_answer(answer_code="a", answer="ay")
        expr_context["ay"]=math_object(a*y)

        self.new_answer(answer_code="b", answer="bx")
        expr_context["bx"]=math_object(b*x)
        self.new_answer(answer_code="b", answer="by")
        expr_context["by"]=math_object(b*y)
        
        self.new_answer(answer_code="c", answer="cx")
        expr_context["cx"]=math_object(c*x)
        self.new_answer(answer_code="c", answer="cy")
        expr_context["cy"]=math_object(c*y)
        
        user_responses=[]
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "cx"})
        user_responses.append({'response': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        user_responses=[]
        user_responses.append({'response': "by"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "ay"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],0)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        user_responses=[]
        user_responses.append({'response': "cy"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)




    def test_multiple_answers_overlap1(self):
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        y=Symbol('y')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')


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
        expr_context["ax"]=math_object(a*x)
        expr_context["bx"]=math_object(b*x)
        expr_context["cx"]=math_object(c*x)

        self.new_answer(answer_code="a", answer="ax")
        self.new_answer(answer_code="a", answer="bx")
        self.new_answer(answer_code="b", answer="bx")
        self.new_answer(answer_code="b", answer="cx")
        self.new_answer(answer_code="c", answer="cx")
        self.new_answer(answer_code="c", answer="ax")
 
         
        user_responses=[]
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "ax"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertFalse(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],0)

        user_responses=[]
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "bx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,300)
        self.assertTrue(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)

        user_responses=[]
        user_responses.append({'response': "dx"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "bx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
            answer_results=answer_results)
        
        self.assertEqual(points_times_100,200)
        self.assertFalse(answer_results['answers'][id1]['answer_correct'])
        self.assertEqual(answer_results['answers'][id1]['percent_correct'],0)
        self.assertTrue(answer_results['answers'][id2]['answer_correct'])
        self.assertEqual(answer_results['answers'][id2]['percent_correct'],100)
        self.assertTrue(answer_results['answers'][id3]['answer_correct'])
        self.assertEqual(answer_results['answers'][id3]['percent_correct'],100)


    def test_multiple_answers_overlap2(self):
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')
        d=Symbol('d')

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
        expr_context["ax"]=math_object(a*x)
        expr_context["bx"]=math_object(b*x)
        expr_context["cx"]=math_object(c*x)
        expr_context["dx"]=math_object(d*x)

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
 
         
        user_responses=[]
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "cx"})
        user_responses.append({'response': "dx"})
        answer_results={'answers': {}}
        group_list=[0,1,2,3]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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
        local_dict={}
        expr_context=Context({})
        x=Symbol('x')
        a=Symbol('a')
        b=Symbol('b')
        c=Symbol('c')


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
        expr_context["ax"]=math_object(a*x)
        expr_context["bx"]=math_object(b*x)
        expr_context["cx"]=math_object(c*x)

        ans11=self.new_answer(answer_code="a", answer="ax", percent_correct=100)
        ans12=self.new_answer(answer_code="a", answer="bx", percent_correct=50)
        ans22=self.new_answer(answer_code="b", answer="bx", percent_correct=100)
        ans23=self.new_answer(answer_code="b", answer="cx", percent_correct=50)
        ans33=self.new_answer(answer_code="c", answer="cx", percent_correct=100)
        ans31=self.new_answer(answer_code="c", answer="ax", percent_correct=50)
 
         
        user_responses=[]
        user_responses.append({'response': "ax"})
        user_responses.append({'response': "bx"})
        user_responses.append({'response': "cx"})
        answer_results={'answers': {}}
        group_list=[0,1,2]
        points_times_100 = grade_question_group(
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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
            group_list=group_list, user_responses=user_responses, 
            answer_info=answer_info, question=self.q,
            expr_context=expr_context, local_dict=local_dict, 
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
