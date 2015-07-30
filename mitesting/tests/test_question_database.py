from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType, QuestionSubpart
from midocs.models import Page, Keyword, Subject, Author, PageType
from micourses.models import Course
from django.db import IntegrityError, transaction

class TestQuestionsAlone(TestCase):

    def setUp(self):
        self.course = Course.objects.create(name="Course", code="course")

        self.qt = QuestionType.objects.create(name="question type")
        self.q  = Question.objects.create(
            name="a question",
            question_type = self.qt,
            question_privacy = 0,
            solution_privacy = 0,
            question_text="why?"
            )
        self.q.expression_set.create(
            name="n", expression="(-10,10)", 
            expression_type = Expression.RANDOM_NUMBER)
        self.q.expression_set.create(
            name="expr",expression="x^3+ n*x")

        self.q.questionansweroption_set.create(answer_code="expr",
                                               answer="expr")
        self.q.questionansweroption_set.create(answer_code="n",
                                               answer="n")
    
        PageType.objects.create(code="type", name="type")
        self.page = Page.objects.create(code="page", title="Page")
        self.q.questionreferencepage_set.create(page=self.page)
        self.q.questionreferencepage_set.create(page=self.page, 
                                                question_subpart="a")

        self.q.keywords.add(Keyword.objects.create(code="keyword1"))
        self.q.keywords.add(Keyword.objects.create(code="keyword2"))
        self.q.subjects.add(Subject.objects.create(code="subject1"))
        self.q.subjects.add(Subject.objects.create(code="subject2"))
        self.q.subjects.add(Subject.objects.create(code="subject3"))

        self.sympycommandseta = SympyCommandSet.objects.create(
            name="Command A", commands="commanda")
        self.sympycommandsetb = SympyCommandSet.objects.create(
            name="Command B", commands="commandb")
        self.q.allowed_sympy_commands.add(self.sympycommandseta)
        self.q.allowed_user_sympy_commands.add(self.sympycommandsetb)

        self.q.questionauthor_set.create(
            author=Author.objects.create(code="authora", first_name="A",
                                         last_name="B"))
        self.q.questionauthor_set.create(
            author=Author.objects.create(code="authorb", first_name="C",
                                         last_name="D"))

        self.q.questionsubpart_set.create(question_text="subpart a")
        self.q.questionsubpart_set.create(question_text="subpart b")


    def test_save_as_new(self):
        
        new_q = self.q.save_as_new()
        new2_q = new_q.save_as_new()
        new3_q = new_q.save_as_new(course=self.course)
        new4_q = new3_q.save_as_new()

        self.assertEqual(Question.objects.count(),5)

        self.assertNotEqual(new_q, self.q)

        self.assertEqual(new_q.base_question, self.q)
        self.assertEqual(new2_q.base_question, self.q)
        self.assertEqual(new3_q.base_question, self.q)
        self.assertEqual(new4_q.base_question, self.q)

        self.assertEqual(self.q.course,None)
        self.assertEqual(new_q.course,None)
        self.assertEqual(new2_q.course,None)
        self.assertEqual(new3_q.course,self.course)
        self.assertEqual(new4_q.course,self.course)


        self.assertEqual(new_q.question_text, self.q.question_text)

        self.assertEqual(new_q.expression_set.count(),
                         self.q.expression_set.count())
        for item in new_q.expression_set.all():
            item2 = self.q.expression_set.get(name=item.name)
            self.assertEqual(item.expression, item2.expression)

        self.assertEqual(new_q.questionansweroption_set.count(),
                         self.q.questionansweroption_set.count())
        for item in new_q.questionansweroption_set.all():
            item2 = self.q.questionansweroption_set.get(
                answer_code=item.answer_code)
            self.assertEqual(item.answer, item2.answer)

        self.assertEqual(new_q.questionreferencepage_set.count(),
                         self.q.questionreferencepage_set.count())
        for (i, item) in enumerate(new_q.questionreferencepage_set.all()):
            item2 = self.q.questionreferencepage_set.all()[i]
            self.assertEqual(item.page, item2.page)
            self.assertEqual(item.question_subpart, item2.question_subpart)
        for (i, item) in enumerate(new_q.questionauthor_set.all()):
            item2 = self.q.questionauthor_set.all()[i]
            self.assertEqual(item.author, item2.author)

        self.assertEqual(set(new_q.keywords.all()), set(self.q.keywords.all()))
        self.assertEqual(set(new_q.subjects.all()), set(self.q.subjects.all()))

        self.assertEqual(set(new_q.allowed_sympy_commands.all()), 
                         set(self.q.allowed_sympy_commands.all()))
        self.assertEqual(set(new_q.allowed_user_sympy_commands.all()), 
                         set(self.q.allowed_user_sympy_commands.all()))

        
    def test_overwrite_base_question(self):
        
        no_base_q = self.q.overwrite_base_question()
        self.assertEqual(no_base_q, None)
        self.assertEqual(list(Question.objects.all()), [self.q])

        new_q = self.q.save_as_new(course=self.course)

        new_q.question_type=QuestionType.objects.create(name="new type")
        new_q.question_text = "when?"
        new_q.save()

        expr=new_q.expression_set.get(name="expr")
        expr.expression="1+x"
        expr.save()
        expr=new_q.expression_set.get(name="n")
        expr.delete()
        new_q.expression_set.create(name="new_one", expression="2z")

        
        qao = new_q.questionansweroption_set.get(answer_code="expr")
        qao.delete()
        qao=new_q.questionansweroption_set.get(answer_code="n")
        qao.answer="m"
        qao.save()
        new_q.questionansweroption_set.create(answer_code="new", answer="one")
        
        new_q.questionreferencepage_set.first().delete()
        qrp=new_q.questionreferencepage_set.last()
        qrp.question_subpart="b"
        qrp.save()
        new_q.questionreferencepage_set.create(
            page=Page.objects.create(code="page2", title="Page2"))


        new_q.keywords.remove(new_q.keywords.last())
        new_q.keywords.add(Keyword.objects.create(code="keywordnew"))

        new_q.subjects.add(Subject.objects.create(code="subjectnew"))
        new_q.subjects.remove(Subject.objects.get(code="subject2"))

        new_q.allowed_sympy_commands.remove(self.sympycommandseta)
        new_q.allowed_sympy_commands.add(self.sympycommandsetb)

        new_q.allowed_user_sympy_commands.add(self.sympycommandseta)
        new_q.allowed_user_sympy_commands.remove(self.sympycommandsetb)

        qa=new_q.questionauthor_set.first()
        qa.sort_order=10
        qa.save()
        new_q.questionauthor_set.create(
            author=Author.objects.create(code="authorc", first_name="E",
                                         last_name="F"),
            sort_order=3)

        qsp=new_q.questionsubpart_set.first()
        qsp.question_text="revised text"
        qsp.save()
        new_q.questionsubpart_set.last().delete()
        new_q.questionsubpart_set.create(question_text="new info")
        

        new_q.overwrite_base_question()

        self.q.refresh_from_db()

        self.assertEqual(self.q.base_question, None)
        self.assertEqual(self.q.course, None)
        self.assertEqual(new_q.base_question, self.q)
        self.assertEqual(new_q.course, self.course)

        self.assertEqual(new_q.question_text, self.q.question_text)

        self.assertEqual(new_q.expression_set.count(),
                         self.q.expression_set.count())
        for item in new_q.expression_set.all():
            item2 = self.q.expression_set.get(name=item.name)
            self.assertEqual(item.expression, item2.expression)

        self.assertEqual(new_q.questionansweroption_set.count(),
                         self.q.questionansweroption_set.count())
        for item in new_q.questionansweroption_set.all():
            item2 = self.q.questionansweroption_set.get(
                answer_code=item.answer_code)
            self.assertEqual(item.answer, item2.answer)

        self.assertEqual(new_q.questionreferencepage_set.count(),
                         self.q.questionreferencepage_set.count())
        for (i, item) in enumerate(new_q.questionreferencepage_set.all()):
            item2 = self.q.questionreferencepage_set.all()[i]
            self.assertEqual(item.page, item2.page)
            self.assertEqual(item.question_subpart, item2.question_subpart)
        for (i, item) in enumerate(new_q.questionauthor_set.all()):
            item2 = self.q.questionauthor_set.all()[i]
            self.assertEqual(item.author, item2.author)

        self.assertEqual(set(new_q.keywords.all()), set(self.q.keywords.all()))
        self.assertEqual(set(new_q.subjects.all()), set(self.q.subjects.all()))

        self.assertEqual(set(new_q.allowed_sympy_commands.all()), 
                         set(self.q.allowed_sympy_commands.all()))
        self.assertEqual(set(new_q.allowed_user_sympy_commands.all()), 
                         set(self.q.allowed_user_sympy_commands.all()))



class TestInAssessments(TestCase):

    def setUp(self):
        self.coursea = Course.objects.create(name="Course A", code="coursea")
        self.courseb = Course.objects.create(name="Course B", code="courseb")

        self.qt = QuestionType.objects.create(name="question type")

        self.q1  = Question.objects.create(
            name="question 1",
            question_type = self.qt,
        )
        self.q1a = self.q1.save_as_new(course=self.coursea)

        self.q2  = Question.objects.create(
            name="question 2",
            question_type = self.qt,
        )
        self.q2a = self.q2.save_as_new(course=self.coursea)

        self.q3  = Question.objects.create(
            name="question 3",
            question_type = self.qt,
        )
        self.q3a = self.q3.save_as_new(course=self.coursea)
        self.q3b = self.q3a.save_as_new(course=self.courseb)
        self.q3b.base_question = self.q3a
        self.q3b.save()

        self.q4 = Question.objects.create(
            name="question 4",
            question_type = self.qt,
        )
        self.q4a = self.q4.save_as_new(course=self.coursea)
        self.q4b = self.q4.save_as_new(course=self.courseb)

        self.q5  = Question.objects.create(
            name="question 5",
            question_type = self.qt,
        )
        self.q5b = self.q5.save_as_new(course=self.courseb)
        
        self.q6b  = Question.objects.create(
            name="question 5",
            question_type = self.qt,
            course=self.courseb
        )
        self.q6a = self.q6b.save_as_new(course=self.coursea)

        self.at = AssessmentType.objects.create(
            code="a", name="a", assessment_privacy=0, solution_privacy=0)

        self.asmt = Assessment.objects.create(
            code="the_test", name="The test", assessment_type=self.at,
            course=self.coursea)


    def test_assign_assessment(self):
        nq=Question.objects.count()

        qa=self.asmt.questionassigned_set.create(question=self.q1)
        self.assertEqual(Question.objects.count(), nq)
        self.assertEqual(qa.question, self.q1a)

        qa=self.asmt.questionassigned_set.create(question=self.q2a)
        self.assertEqual(Question.objects.count(), nq)
        self.assertEqual(qa.question, self.q2a)

        qa=self.asmt.questionassigned_set.create(question=self.q3b)
        self.assertEqual(Question.objects.count(), nq)
        self.assertEqual(qa.question, self.q3a)

        qa=self.asmt.questionassigned_set.create(question=self.q4b)
        self.assertEqual(Question.objects.count(), nq)
        self.assertEqual(qa.question, self.q4a)

        qa=self.asmt.questionassigned_set.create(question=self.q5)
        self.assertEqual(Question.objects.count(), nq+1)
        self.assertNotEqual(qa.question, self.q5)
        self.assertEqual(qa.question.name, self.q5.name)
        self.assertEqual(qa.question.course, self.asmt.course)
        self.assertEqual(qa.question.base_question, self.q5)

        
    def test_assessment_save_as_new(self):
        nq=Question.objects.count()

        qa1=self.asmt.questionassigned_set.create(question=self.q1a)
        qa2=self.asmt.questionassigned_set.create(question=self.q3a)
        qa3=self.asmt.questionassigned_set.create(question=self.q4a)
        qa4=self.asmt.questionassigned_set.create(question=self.q6a)

        self.assertEqual(Question.objects.count(), nq)
        
        with transaction.atomic():
            self.assertRaises(IntegrityError, self.asmt.save_as_new)

        asmt2 = self.asmt.save_as_new(code="test2", name="Test 2")

        self.assertEqual(Question.objects.count(), nq)

        for (i,qa) in enumerate(asmt2.questionassigned_set.all()):
            self.assertEqual(qa.question, [qa1,qa2,qa3,qa4][i].question)

        asmt3 = self.asmt.save_as_new(course=self.courseb)

        self.assertEqual(Question.objects.count(), nq+1)
        qas = asmt3.questionassigned_set.all()
        self.assertEqual(qas[1].question, self.q3b)
        self.assertEqual(qas[2].question, self.q4b)
        self.assertEqual(qas[3].question, self.q6b)

        self.assertNotEqual(qas[0].question, self.q1a)
        self.assertEqual(qas[0].question.name, self.q1a.name)
        self.assertEqual(qas[0].question.course, asmt3.course)
        self.assertEqual(qas[0].question.base_question, self.q1)
