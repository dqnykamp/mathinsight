from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from micourses.models import Course, ThreadSection, ThreadContent, Assessment, AssessmentType, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from mitesting.models import QuestionType, Question
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import random
import re
import json

"""
Anonymous user behavior:
just set seed via GET.  If seed is not specified, use seed=1.
If single version, ignore seed from GET and use seed=1.
Generate new seed and make link at bottom.
Even if resample question sets, reloading page will reset with questions
from that given assessment seed.

Logged in user who isn't in course: 
same as anonymous user behavior

Logged in user who is student of course:
If assessment is not in course thread, same as anonymous user behavior
Otherwise
- Ignore seed from GET
- Determine availability of content (not yet available, available, or past due)
- Find latest content attempt
  If content attempt validity does not match, treat as no matching attempt
  (available = valid, not yet available or past due = invalid)
  Obtain
  - assessment seed from content attempt 
  - list of questions sets in order (from content attempt question sets)
  - the latest question attempt for each question set
  - from each question attempt, determine
    - question
    - seed 
    - whether or not solution viewed
  If missing data (e.g., assessment seed or question attempts),
  then treat as though don't have content attempt and create new one (below)
- If no matching content attempt, 
  then create new content attempt and question attempts.
  Generate assessment seed as follows:
  - If past due, check for a current valid attempt.
    If found, use seed from that assessment.
    If none found, then generate seed as though a valid attempt.
  - If valid attempt, create assessment seed from 
    - course code and attempt number
    - plus username if assessment is individualized by student
    Exception: set seed=1 if assessment marked as single version
  - If not yet released, set seed to be attempt number.
  Use assessment seed to generate
  - list of question sets in order
  - question and seed
  Save 
  - assessment seed to content attempt
  - list of question sets in order to content attempt question sets
  - questions and their seeds to question attempt
  If not yet released or past due, mark content attempt as invalid.
If not valid attempt, then remove any feedback of progress on question
to make it clear that question isn't being tracked.
Maintain feedback for individual answer responses.


Looged in user who is instructor of course:
If assessment is not in course thread, same as anonymous user behavior
Otherwise:
If seed is in GET
- use that to generate assessment.
- If GET also contains list of question ids and question seeds,
  then use those ids and question seeds rather than those from assessment.
  (If number of ids and seeds doesn't match assesment or ids are invalid,
  then ignore and generate questions from assessment seed.)
- do not record any responses (not possible anyway as no matching attempts)
If seed is not in GET, treat as student of course


"""



"""
To test:

generate when is not yet available, assessment becomes available 
while submitting responses.  Should give message that should reload assessment to start real attempt.

Appropriate feedback when not yet available and when becomes past due or solution viewed.

Past due behavior changes once regenerate content attempt or question attempt.
Before regenerate, should show scores for what obtain while valid.  When regenerate, don't show any scores.




"""


def set_up_data(tcase):
    tcase.course = Course.objects.create(
        code="the_course",
        name="The Course",
    )
    tcase.section = tcase.course.thread_sections.create(name='The section')
    
    assessment_ct = ContentType.objects.get_for_model(Assessment)
    quiz = AssessmentType.objects.create(
        code="quiz", name="Quiz", assessment_privacy=0, solution_privacy=0)

    tcase.assessment = Assessment.objects.create(
        code="assessment", name="The Assessment", assessment_type=quiz,
        course=tcase.course,
        fixed_order=True,
    )

    tcase.assessment_url = reverse('miassess:assessment', 
                            kwargs={'course_code': tcase.course.code,
                                    'assessment_code': tcase.assessment.code})

    tcase.thread_content= tcase.section.thread_contents.create(
        content_type=assessment_ct, object_id=tcase.assessment.id,
        points=10,)


    qt = QuestionType.objects.create(name="question type")
    tcase.q1  = Question.objects.create(
        name="question",
        question_type = qt,
        question_privacy = 0,
        solution_privacy = 0,
        course=tcase.course,
        computer_graded=True,
        question_text = "Enter x: {% answer 'x' %}",
        solution_text = "x",
    )
    tcase.q1.expression_set.create(name="x",expression="x")
    tcase.q1.questionansweroption_set.create(answer_code="x", answer="x")
    tcase.assessment.questionassigned_set.create(question=tcase.q1)


    tcase.q2  = Question.objects.create(
        name="question",
        question_type = qt,
        question_privacy = 0,
        solution_privacy = 0,
        course=tcase.course,
        computer_graded=True,
        question_text = "Enter x+y: {% answer 'x_plus_y' %}",
        solution_text = "x+y",
    )
    tcase.q2.expression_set.create(name="x_plus_y",expression="x+y")
    tcase.q2.questionansweroption_set.create(answer_code="x_plus_y",
                                             answer="x_plus_y")
    tcase.assessment.questionassigned_set.create(question=tcase.q2)

    u=User.objects.create_user("the_student", password="pass")
    tcase.student = u.courseuser
    u=User.objects.create_user("the_instructor", password="pass")
    tcase.instructor = u.courseuser
    u=User.objects.create_user("the_designer", password="pass")
    tcase.designer = u.courseuser

    tcase.student_enrollment = tcase.course.courseenrollment_set.create(
        student=tcase.student, date_enrolled=timezone.now())
    tcase.instructor_enrollment = tcase.course.courseenrollment_set.create(
        student=tcase.instructor, date_enrolled=timezone.now(),
        role=INSTRUCTOR_ROLE)
    tcase.designer_enrollment = tcase.course.courseenrollment_set.create(
        student=tcase.designer, date_enrolled=timezone.now(),
        role=DESIGNER_ROLE)

    # run return_selected_course() so that course will be selected by default
    tcase.student.return_selected_course()
    tcase.instructor.return_selected_course()
    tcase.designer.return_selected_course()



def set_up_attempts(tcase):
    # make assessment available
    tcase.thread_content.available_before_assigned=True
    tcase.thread_content.save()

    # get content record
    tcase.record = tcase.thread_content.contentrecord_set.get(
        enrollment=tcase.student_enrollment)

    # create two valid content attempts
    from micourses.utils import create_new_assessment_attempt
    new_attempt_info = create_new_assessment_attempt(
        student_record = tcase.record)
    tcase.content_attempt_1 = new_attempt_info['new_attempt']
    new_attempt_info = create_new_assessment_attempt(
        student_record = tcase.record)
    tcase.content_attempt_2 = new_attempt_info['new_attempt']

    # in attempt 1, add correct response to question 1
    # and incorrect response to question 2
    question_attempt1 = tcase.content_attempt_1.question_sets.get(
        question_number=1).question_attempts.first()
    response = [{'code': "x", "response": "x", "identifier": "1_qa0"}]
    question_attempt1.responses.create(response = json.dumps(response),
                                       credit=1)
    question_attempt2 = tcase.content_attempt_1.question_sets.get(
        question_number=2).question_attempts.first()
    response=[{"code": "x_plus_y", "response": "z", "identifier": "1_qa1"}]
    question_attempt2.responses.create(response = json.dumps(response),
                                       credit=0)

    # in attempt 2, add incorrect response to question 1
    # and correct response to question 2
    question_attempt1 = tcase.content_attempt_2.question_sets.get(
        question_number=1).question_attempts.first()
    response = [{'code': "x", "response": "z", "identifier": "1_qa0"}]
    question_attempt1.responses.create(response = json.dumps(response),
                                       credit=0)
    question_attempt2 = tcase.content_attempt_2.question_sets.get(
        question_number=2).question_attempts.first()
    response=[{"code": "x_plus_y", "response": "x+y", "identifier": "1_qa1"}]
    question_attempt2.responses.create(response = json.dumps(response),
                                       credit=1)

class SeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumTests, cls).setUpClass()
        cls.selenium = WebDriver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def setUp(self):
        set_up_data(self)
        self.login_url= reverse("mi-login")


    def test_submit_responses_check_scores(self):
        from selenium.webdriver.common.by import By
        timeout=10
        wait = WebDriverWait(self.selenium, timeout)

        content_record = self.thread_content.contentrecord_set.get(
            enrollment=self.student_enrollment)
        self.assertEqual(self.thread_content.student_score(self.student), None)


        # remove points from thread_content
        self.thread_content.points =None
        self.thread_content.save()

        self.selenium.get('%s%s?next=%s' %
                (self.live_server_url, self.login_url, self.assessment_url))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('the_student')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('pass')

        self.selenium.find_element_by_xpath('//input[@value="login"]').click()


        # have invalid attempts
        content_attempt_x1 = content_record.attempts.first()
        self.assertFalse(content_attempt_x1.valid)

        self.assertEqual(self.thread_content.student_score(self.student), None)


        # submit correct answer, though assessment is not yet available
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('x')
        answer1.submit()

        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("not yet available" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)

        # however, should have recorded invalid response, with 100% credit
        question_attempts = content_attempt_x1.question_sets.get(
            question_number=1).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertFalse(question_attempt1.valid)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertFalse(response1.valid)
        self.assertEqual(response1.credit,1)

        # score should still be None
        self.assertEqual(self.thread_content.student_score(self.student), None)

        # assessment points section should be empty,
        # as no points assigned
        assessment_points_section = self.selenium.find_element_by_id(
                'assessment_points')
        self.assertEqual(assessment_points_section.text, "")
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"")


        # Add points to thread_content 
        # and assessment points should should appear
        self.thread_content.points = 10
        self.thread_content.save()
        
        # Reload page
        self.selenium.get('%s%s' % (self.live_server_url, self.assessment_url))
        
        # assessment points section should now be populated
        assessment_points_section = self.selenium.find_element_by_id(
            'assessment_points')
        self.assertTrue("Total points: 10" in assessment_points_section.text)
        total_points_element = self.selenium.find_element_by_id(
            'total_points')
        self.assertEqual(total_points_element.text, "10")
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "not recorded")
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"(5 points)")

        # make assessment be available before assigned
        self.thread_content.available_before_assigned=True
        self.thread_content.save()

        # submit same correct answer again
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('x')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        # feedback should indicate that need to reload to record answers
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertFalse("not yet available" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Generate a new attempt or reload page to start recording answers" in feedback.text)
        
        # A second response should be recorded.
        # Although it is marked valid, it still invalid since attempt is invalid
        self.assertEqual(responses.count(),2)
        response1 = responses.last()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,1)
        self.assertEqual(self.thread_content.student_score(self.student), None)

        # no record of score should be shown
        self.assertEqual(overall_score_element.text, "not recorded")
        self.assertEqual(question1_point_section.text,"(5 points)")


        # Reloading page should create a new, valid attempt
        self.selenium.get('%s%s' % (self.live_server_url, self.assessment_url))

        # now score should say zero
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "0")
        self.assertEqual(self.thread_content.student_score(self.student), None)

        # question itself doesn't say zero yet, as no valid response saved yet.
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"(5 points)")
        
        # submitting the correct answer should now get recorded
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('x')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        # feedback should indicate that correct score is recorded
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer recorded for the_student" in feedback.text)

        # score shown and recorded
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertTrue("5 points" in question1_point_section.text)
        self.assertTrue("achieved: 100%" in question1_point_section.text)

        # have new content valid content attempt
        self.assertEqual(content_record.attempts.count(),2)
        content_attempt_1 = content_record.attempts.last()
        self.assertTrue(content_attempt_1.valid)

        # should have recorded valid response, with 100% credit
        question_attempts = content_attempt_1.question_sets.get(
            question_number=1).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertTrue(question_attempt1.valid)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,1)

        # Create a new attempt
        self.selenium.find_element_by_id("generate_new_attempt_form").submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        # score for attempt is zero, but overall score is still 5
        # since default is maximum score
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "5")
        current_attempt_score_element = self.selenium.find_element_by_id(
            'current_attempt_score')
        self.assertEqual(current_attempt_score_element.text, "0")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"(5 points)")
        
        # submit incorrect answer
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('y')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))
        
        # feedback should indicate that incorrect score is recorded
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is incorrect" in feedback.text)
        self.assertTrue("Answer recorded for the_student" in feedback.text)
        
        # check attempt score is still 0 and overall score is 5
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "0")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertTrue("5 points" in question1_point_section.text)
        self.assertTrue("achieved: 0%" in question1_point_section.text)

        # give the assessment a future due date
        self.thread_content.initial_due = timezone.now() + \
                                          timezone.timedelta(days=1)
        self.thread_content.save()


        # submit correct answer for second question
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        answer2.send_keys('x+y')
        answer2.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa1_submit')))
        
        # feedback should indicate that correct score is recorded
        feedback =  self.selenium.find_element_by_id('question_qa1_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer recorded for the_student" in feedback.text)
        
        # check attempt score is 5 and overall score is 5
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question2_point_section = self.selenium.find_element_by_id(
            'qa1_point_info')
        self.assertTrue("5 points" in question2_point_section.text)
        self.assertTrue("achieved: 100%" in question2_point_section.text)


        # view the solution on the first question
        solution_button = self.selenium.find_element_by_id(
            "question_qa0_show_solution")
        solution_button.click()
        wait.until(EC.staleness_of(solution_button))

        # submit correct answer to question (backspace wrong one first)
        answer1.send_keys('\bx')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))
        
        # feedback should indicate that correct score was not recorded
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Solution for question already viewed" in feedback.text)
        self.assertTrue("Generate a new attempt" in feedback.text)

        # check score
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertTrue("5 points" in question1_point_section.text)
        self.assertTrue("achieved: 0%" in question1_point_section.text)


        # check record for attempt
        content_record.refresh_from_db()
        self.assertEqual(content_record.score, 5)
        self.assertEqual(content_record.attempts.count(),3)
        content_attempt_2 = content_record.attempts.last()
        self.assertTrue(content_attempt_2.valid)
        self.assertEqual(content_attempt_2.score, 5)

        # question 1
        question_attempts = content_attempt_2.question_sets.get(
            question_number=1).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertTrue(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, 0)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),2)
        response1 = responses.first()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,0)
        response2 = responses.last()
        self.assertFalse(response2.valid)
        self.assertEqual(response2.credit,1)

        # question 2
        question_attempts = content_attempt_2.question_sets.get(
            question_number=2).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertTrue(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, 1)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,1)


        # Create a new attempt
        self.selenium.find_element_by_id("generate_new_attempt_form").submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        # score for attempt is zero, but overall score is still 5
        # since default is maximum score
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "5")
        current_attempt_score_element = self.selenium.find_element_by_id(
            'current_attempt_score')
        self.assertEqual(current_attempt_score_element.text, "0")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"(5 points)")
        question2_point_section = self.selenium.find_element_by_id(
            'qa1_point_info')
        self.assertEqual(question2_point_section.text,"(5 points)")


        # submit correct answer for question 1
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('x')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer recorded for the_student" in feedback.text)

        # check score
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        # submit incorrect answer for question 2
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        answer2.send_keys('z')
        answer2.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa1_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa1_feedback')
        self.assertTrue("Answer is incorrect" in feedback.text)
        self.assertTrue("Answer recorded for the_student" in feedback.text)

        # check score
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)


        # make the assessment be past due
        self.thread_content.initial_due = timezone.now() - \
                                          timezone.timedelta(days=1)
        self.thread_content.save()

        # submit correct answer for question 2
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        answer2.send_keys('\bx+y')
        answer2.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa1_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa1_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Due date " in feedback.text)
        self.assertTrue(" of The Assessment is past" in feedback.text)
        
        # check score
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertTrue("5 points" in question2_point_section.text)
        self.assertTrue("achieved: 0%" in question2_point_section.text)

        
        # reload page to make sure last attempt is still there
        self.selenium.get('%s%s' % (self.live_server_url, self.assessment_url))

        # score for attempt is 5 and overall score is 5
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "5")
        current_attempt_score_element = self.selenium.find_element_by_id(
            'current_attempt_score')
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        # check credit for questions
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertTrue("5 points" in question1_point_section.text)
        self.assertTrue("achieved: 100%" in question1_point_section.text)
        question2_point_section = self.selenium.find_element_by_id(
            'qa1_point_info')
        self.assertTrue("5 points" in question2_point_section.text)
        self.assertTrue("achieved: 0%" in question2_point_section.text)

        
        # question 1 should have correct answer prefilled
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        self.assertEqual(answer1.get_attribute("value"),"x")

        # question 2 be prefilled by the incorrect answer submitted
        # (not the correct answer submitted after the deadline)
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        self.assertEqual(answer2.get_attribute("value"),"z")

        
        # submit correct answer for question 2 once again
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        answer2.send_keys('\bx+y')
        answer2.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa1_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa1_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Due date " in feedback.text)
        self.assertTrue(" of The Assessment is past" in feedback.text)
        
        # check score
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "5")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertTrue("5 points" in question2_point_section.text)
        self.assertTrue("achieved: 0%" in question2_point_section.text)


        # Create a new attempt
        self.selenium.find_element_by_id("generate_new_attempt_form").submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))

        # score for attempt is not recorded, but overall score is still 5
        # since default is maximum score
        overall_score_element = self.selenium.find_element_by_id(
            'overall_score')
        self.assertEqual(overall_score_element.text, "5")
        current_attempt_score_element = self.selenium.find_element_by_id(
            'current_attempt_score')
        self.assertEqual(current_attempt_score_element.text, "not recorded")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question1_point_section = self.selenium.find_element_by_id(
            'qa0_point_info')
        self.assertEqual(question1_point_section.text,"(5 points)")
        question2_point_section = self.selenium.find_element_by_id(
            'qa1_point_info')
        self.assertEqual(question2_point_section.text,"(5 points)")


        # submit correct answer for question 1
        answer1 = self.selenium.find_element_by_id("id_answer_1_qa0")
        answer1.send_keys('x')
        answer1.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa0_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa0_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Due date " in feedback.text)
        self.assertTrue(" of The Assessment is past" in feedback.text)


        # submit correct answer for question 2
        answer2 = self.selenium.find_element_by_id("id_answer_1_qa1")
        answer2.send_keys('x+y')
        answer2.submit()
        wait.until(EC.element_to_be_clickable((By.ID,'question_qa1_submit')))
        
        # check feedback
        feedback =  self.selenium.find_element_by_id('question_qa1_feedback')
        self.assertTrue("Answer is correct" in feedback.text)
        self.assertTrue("Answer not recorded" in feedback.text)
        self.assertTrue("Due date " in feedback.text)
        self.assertTrue(" of The Assessment is past" in feedback.text)

        # check scores haven't changed
        self.assertEqual(overall_score_element.text, "5")
        self.assertEqual(current_attempt_score_element.text, "not recorded")
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.assertEqual(question1_point_section.text,"(5 points)")
        self.assertEqual(question2_point_section.text,"(5 points)")


        # check record for attempt 3
        content_record.refresh_from_db()
        self.assertEqual(content_record.score, 5)
        self.assertEqual(content_record.attempts.count(),5)
        content_attempt_3 = content_record.attempts.all()[3]
        self.assertTrue(content_attempt_3.valid)
        self.assertEqual(content_attempt_3.score, 5)

        # question 1
        question_attempts = content_attempt_3.question_sets.get(
            question_number=1).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertTrue(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, 1)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,1)

        # question 2
        question_attempts = content_attempt_3.question_sets.get(
            question_number=2).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertTrue(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, 0)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),3)
        response1 = responses.first()
        self.assertTrue(response1.valid)
        self.assertEqual(response1.credit,0)
        response2= responses.all()[1]
        self.assertFalse(response2.valid)
        self.assertEqual(response2.credit,1)
        response3 = responses.last()
        self.assertFalse(response3.valid)
        self.assertEqual(response3.credit,1)


        # check record for attempt x2
        content_attempt_x2 = content_record.attempts.all()[4]
        self.assertFalse(content_attempt_x2.valid)
        self.assertEqual(content_attempt_x2.score, None)

        # question 1
        question_attempts = content_attempt_x2.question_sets.get(
            question_number=1).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertFalse(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, None)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertFalse(response1.valid)
        self.assertEqual(response1.credit,1)

        # question 2
        question_attempts = content_attempt_x2.question_sets.get(
            question_number=2).question_attempts.all()
        self.assertEqual(question_attempts.count(),1)
        question_attempt1 = question_attempts.first()
        self.assertFalse(question_attempt1.valid)
        self.assertEqual(question_attempt1.credit, None)
        responses = question_attempt1.responses.all()
        self.assertEqual(responses.count(),1)
        response1 = responses.first()
        self.assertFalse(response1.valid)
        self.assertEqual(response1.credit,1)


        # Now check scores on record pages
        overall_score_element.click()
        
        wait.until(EC.presence_of_element_located((By.ID,'assessment_score')))
        
        assessment_score_element = self.selenium.find_element_by_id(
            'assessment_score')
        self.assertEqual(float(assessment_score_element.text), 5.0)
        
        # check scores on the 3 valid attempts
        attempt1_row = self.selenium.find_element_by_id('attempt_1')
        # content_attempt_1 will be this first valid attempt
        attempt1_score = attempt1_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_1.id )
        self.assertEqual(float(attempt1_score.text), 5.0)

        attempt2_row = self.selenium.find_element_by_id('attempt_2')
        # content_attempt_2 will be this second valid attempt
        attempt2_score = attempt2_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_2.id )
        self.assertEqual(float(attempt2_score.text), 5.0)

        attempt3_row = self.selenium.find_element_by_id('attempt_3')
        # content_attempt_3 will be this third valid attempt
        attempt3_score = attempt3_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_3.id )
        self.assertEqual(float(attempt3_score.text), 5.0)


        # score for other attempts should not show up as either attempt 4 or x1
        self.assertRaises(NoSuchElementException,
                          self.selenium.find_element_by_id, 'attempt_4')
        self.assertRaises(NoSuchElementException,
                          self.selenium.find_element_by_id, 'attempt_x1')
        

        # go to attempt 2 page
        attempt_2_link = self.selenium.find_element_by_xpath(
            '//td[@id="attempt_%s_score"]/a' % content_attempt_2.id)
        attempt_2_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'content_attempt_score')))

        content_attempt_score = self.selenium.find_element_by_id(
            'content_attempt_score')
        self.assertEqual(float(content_attempt_score.text), 5.0)
        content_attempt_credit = self.selenium.find_element_by_id(
            'content_attempt_credit')
        self.assertEqual(
            float(re.sub("%","", content_attempt_credit.text)), 50)

        
        # question scores and credit
        question1_score_td = self.selenium.find_element_by_id(
            'question_1_score')
        self.assertEqual(float(question1_score_td.text), 0.0)
        question2_score_td = self.selenium.find_element_by_id(
            'question_2_score')
        self.assertEqual(float(question2_score_td.text), 5.0)
        
        question1_credit_td = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","",question1_credit_td.text)), 0)
        question2_credit_td = self.selenium.find_element_by_id(
            'question_2_credit')
        self.assertEqual(
            float(re.sub("%","",question2_credit_td.text)), 100)
        
        # go to question 1 page
        question_1_link = self.selenium.find_element_by_xpath(
            '//td[@id="question_1_score"]/a')
        question_1_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'question_score')))

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 0.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 0)

        response_1_score = self.selenium.find_element_by_id(
            'response_1_score')
        self.assertEqual(float(response_1_score.text), 0.0)
        response_1_credit = self.selenium.find_element_by_id(
            'response_1_credit')
        self.assertEqual(
            float(re.sub("%","", response_1_credit.text)), 0)

        # make sure response 2 doesn't show up
        self.assertRaises(NoSuchElementException,
                        self.selenium.find_element_by_id, 'response_2_score')
        self.assertRaises(NoSuchElementException,
                        self.selenium.find_element_by_id, 'response_x1_score')


        # go to response page
        response_1_link = self.selenium.find_element_by_xpath(
            '//td[@id="response_1_score"]/a')
        response_1_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'response_score')))

        response_score = self.selenium.find_element_by_id(
            'response_score')
        self.assertEqual(float(response_score.text), 0.0)
        response_credit = self.selenium.find_element_by_id(
            'response_credit')
        self.assertEqual(
            float(re.sub("%","", response_credit.text)), 0)

        feedback =  self.selenium.find_element_by_id('question_qrv_feedback')
        self.assertTrue("Answer is incorrect" in feedback.text)

        answer1 = self.selenium.find_element_by_id("id_answer_1_qrv")
        self.assertEqual(answer1.get_attribute("value"),"y")


        # go back to attempt 2 page
        self.selenium.back()
        self.selenium.back()

        wait.until(EC.presence_of_element_located(
            (By.ID,'question_2_score')))

        # go to question 2 page
        question_2_link = self.selenium.find_element_by_xpath(
            '//td[@id="question_2_score"]/a')
        question_2_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'question_score')))

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 5.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 100)

        response_1_score = self.selenium.find_element_by_id(
            'response_1_score')
        self.assertEqual(float(response_1_score.text), 5.0)
        response_1_credit = self.selenium.find_element_by_id(
            'response_1_credit')
        self.assertEqual(
            float(re.sub("%","", response_1_credit.text)), 100)

        # go to response page
        response_1_link = self.selenium.find_element_by_xpath(
            '//td[@id="response_1_score"]/a')
        response_1_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'response_score')))

        response_score = self.selenium.find_element_by_id(
            'response_score')
        self.assertEqual(float(response_score.text), 5.0)
        response_credit = self.selenium.find_element_by_id(
            'response_credit')
        self.assertEqual(
            float(re.sub("%","", response_credit.text)), 100)

        feedback =  self.selenium.find_element_by_id('question_qrv_feedback')
        self.assertTrue("Answer is correct" in feedback.text)

        answer1 = self.selenium.find_element_by_id("id_answer_1_qrv")
        self.assertEqual(answer1.get_attribute("value"),"x+y")


        # log out student
        self.selenium.find_element_by_id('logout_link').click()


        # log in as instructor
        content_record_instructor_url = reverse(
            'micourses:content_record_instructor',
            kwargs = {'course_code': self.course.code,
                      'content_id': self.thread_content.id,
                      'student_id': self.student.id
                  })

        self.selenium.get('%s%s?next=%s' %
                (self.live_server_url, self.login_url,
                 content_record_instructor_url))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('the_instructor')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('pass')

        self.selenium.find_element_by_xpath('//input[@value="login"]').click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'attempt_record_score')))

        attempt_record_score = self.selenium.find_element_by_id(
            'attempt_record_score')

        self.assertEqual(float(attempt_record_score.text), 5)


        # check scores on the 3 valid attempts
        attempt1_row = self.selenium.find_element_by_id('attempt_1')
        # content_attempt_1 will be this first valid attempt
        attempt1_score = attempt1_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_1.id )
        self.assertEqual(float(attempt1_score.text), 5.0)

        attempt2_row = self.selenium.find_element_by_id('attempt_2')
        # content_attempt_2 will be this second valid attempt
        attempt2_score = attempt2_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_2.id )
        self.assertEqual(float(attempt2_score.text), 5.0)

        attempt3_row = self.selenium.find_element_by_id('attempt_3')
        # content_attempt_3 will be this third valid attempt
        attempt3_score = attempt3_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_3.id )
        self.assertEqual(float(attempt3_score.text), 5.0)

        # score for invalid attempts should be attempts x1 and x2
        attemptx1_row = self.selenium.find_element_by_id('attempt_x1')
        # content_attempt_x1 will be this first invalid attempt
        attemptx1_score = attemptx1_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_x1.id )
        self.assertEqual(attemptx1_score.text, "--")
        self.assertEqual(attemptx1_row.get_attribute("class"), "invalid")

        attemptx2_row = self.selenium.find_element_by_id('attempt_x2')
        # content_attempt_x2 will be this first invalid attempt
        attemptx2_score = attemptx2_row.find_element_by_id(
            'attempt_%s_score' % content_attempt_x2.id )
        self.assertEqual(attemptx2_score.text, "--")
        self.assertEqual(attemptx2_row.get_attribute("class"), "invalid")


        # view attempt2's version of the assessment
        self.selenium.find_element_by_id('version_2_link').click()
        wait.until(EC.presence_of_element_located((By.ID,'current_seed')))
        seed=self.selenium.find_element_by_id('current_seed')
        self.assertEqual(content_attempt_2.seed, seed.text)

        self.selenium.back()
        
        # go to attempt 2 details
        wait.until(EC.presence_of_element_located((By.ID,'attempt_2_link')))
        self.selenium.find_element_by_id('attempt_2_link').click()
        
        wait.until(EC.presence_of_element_located(
            (By.ID,'content_attempt_score')))

        content_attempt_score = self.selenium.find_element_by_id(
            'content_attempt_score')
        self.assertEqual(float(content_attempt_score.text), 5.0)
        content_attempt_credit = self.selenium.find_element_by_id(
            'content_attempt_credit')
        self.assertEqual(
            float(re.sub("%","", content_attempt_credit.text)), 50)


        # question scores and credit
        question1_score_td = self.selenium.find_element_by_id(
            'question_1_score')
        self.assertEqual(float(question1_score_td.text), 0.0)
        question2_score_td = self.selenium.find_element_by_id(
            'question_2_score')
        self.assertEqual(float(question2_score_td.text), 5.0)
        
        question1_credit_td = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","",question1_credit_td.text)), 0)
        question2_credit_td = self.selenium.find_element_by_id(
            'question_2_credit')
        self.assertEqual(
            float(re.sub("%","",question2_credit_td.text)), 100)

        # view attempt2's version of question 1
        self.selenium.find_element_by_id('question_1_link').click()
        wait.until(EC.presence_of_element_located((By.ID,'current_seed')))
        seed=self.selenium.find_element_by_id('current_seed')
        self.assertEqual(content_attempt_2.seed, seed.text)

        self.selenium.back()
        
        # go to question 1 details
        wait.until(EC.presence_of_element_located((By.ID,'attempt_1_link')))
        self.selenium.find_element_by_id('attempt_1_link').click()
        
        wait.until(EC.presence_of_element_located(
            (By.ID,'question_score')))

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 0.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 0)

        response_1_score = self.selenium.find_element_by_id(
            'response_1_score')
        self.assertEqual(float(response_1_score.text), 0.0)
        response_1_credit = self.selenium.find_element_by_id(
            'response_1_credit')
        self.assertEqual(
            float(re.sub("%","", response_1_credit.text)), 0)


        # second response should show up as invalid response number x1
        response_x1_score = self.selenium.find_element_by_id(
            'response_x1_score')
        self.assertEqual(float(response_x1_score.text), 5.0)
        response_x1_credit = self.selenium.find_element_by_id(
            'response_x1_credit')
        self.assertEqual(
            float(re.sub("%","", response_x1_credit.text)), 100)
        response_x1 = self.selenium.find_element_by_id(
            'response_x1')
        self.assertEqual(response_x1.get_attribute("class"), "invalid")


        # go to response1 page
        response_1_link = self.selenium.find_element_by_xpath(
            '//td[@id="response_1_score"]/a')
        response_1_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'response_score')))

        response_score = self.selenium.find_element_by_id(
            'response_score')
        self.assertEqual(float(response_score.text), 0.0)
        response_credit = self.selenium.find_element_by_id(
            'response_credit')
        self.assertEqual(
            float(re.sub("%","", response_credit.text)), 0)

        wait.until(EC.text_to_be_present_in_element(
            (By.ID, 'question_qrv_feedback'), "Answer is incorrect"))

        answer1 = self.selenium.find_element_by_id("id_answer_1_qrv")
        self.assertEqual(answer1.get_attribute("value"),"y")

        self.selenium.back()

        wait.until(EC.presence_of_element_located(
            (By.ID,'question_score')))


        # go to response_x1 page
        response_x1_link = self.selenium.find_element_by_xpath(
            '//td[@id="response_x1_score"]/a')
        response_x1_link.click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'response_score')))

        response_score = self.selenium.find_element_by_id(
            'response_score')
        self.assertEqual(float(response_score.text), 5.0)
        response_credit = self.selenium.find_element_by_id(
            'response_credit')
        self.assertEqual(
            float(re.sub("%","", response_credit.text)), 100)
        # parent element should have invalid class
        parent_elt = response_credit.find_element_by_xpath("../self::*")
        self.assertEqual(parent_elt.get_attribute("class"), "invalid")

        feedback =  self.selenium.find_element_by_id('question_qrv_feedback')
        self.assertTrue("Answer is correct" in feedback.text)

        answer1 = self.selenium.find_element_by_id("id_answer_1_qrv")
        self.assertEqual(answer1.get_attribute("value"),"x")



    def test_update_scores(self):
        from selenium.webdriver.common.by import By
        timeout=10
        wait = WebDriverWait(self.selenium, timeout)
        
        set_up_attempts(self)
        
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        
        # log in as instructor
        content_record_instructor_url = reverse(
            'micourses:content_record_instructor',
            kwargs = {'course_code': self.course.code,
                      'content_id': self.thread_content.id,
                      'student_id': self.student.id
                  })

        self.selenium.get('%s%s?next=%s' %
                (self.live_server_url, self.login_url,
                 content_record_instructor_url))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('the_instructor')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('pass')

        self.selenium.find_element_by_xpath('//input[@value="login"]').click()

        wait.until(EC.presence_of_element_located(
            (By.ID,'attempt_record_score')))
        
        record_score = self.selenium.find_element_by_id(
            'attempt_record_score')
        self.assertEqual(float(record_score.text), 5.0)
        

        # Check behavior of record score form
        edit_form = self.selenium.find_element_by_id(
            "edit_attempt_record_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="attempt_record_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_record_score_form_score")
        score_input.send_keys("abc")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_attempt_record_score_form_inner"),
            "Enter a number"))

        # enter a blank number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_record_score_form_score")
        score_input.send_keys("\b\b\b\b\b\b\b")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_attempt_record_score_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify score 5 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        score_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(score_input.get_attribute("value")), 5.0)
        self.assertFalse("This field is required" in edit_form.text)

        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertFalse(score_overridden.is_displayed())
        delete_override = edit_form.find_element_by_id("delete_override_record")
        self.assertFalse(delete_override.is_displayed())
        
        # change record score to 1
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_record_score_form_score")
        score_input.send_keys("\b\b\b1")
        score_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(record_score.text), 1.0)
        self.assertEqual(self.thread_content.student_score(self.student), 1)
        self.record.refresh_from_db()
        self.assertEqual(self.record.score_override, 1.0)

        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        self.assertTrue(score_overridden.is_displayed())

        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertTrue(delete_override.is_displayed())

        # reload page to make sure still has overridden message displayed
        self.selenium.refresh()
        wait.until(EC.presence_of_element_located(
            (By.ID,'score_comment')))
        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertTrue(score_overridden.is_displayed())

        # remove the override
        edit_form = self.selenium.find_element_by_id(
            "edit_attempt_record_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="attempt_record_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override = edit_form.find_element_by_id("delete_override_record")
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        record_score = self.selenium.find_element_by_id(
            'attempt_record_score')
        self.assertEqual(float(record_score.text), 5.0)
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.record.refresh_from_db()
        self.assertEqual(self.record.score_override, None)

        self.assertEqual(score_comment.get_attribute("class"), "")
        self.assertFalse(score_overridden.is_displayed())
        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        


        # Check behavior of attempt score form
        the_id = self.content_attempt_1.id

        attempt_score = self.selenium.find_element_by_id(
            'attempt_%s_score' % the_id)
        self.assertEqual(float(attempt_score.text), 5.0)

        edit_form = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form" % the_id)
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="attempt_%s_score"]/input[@value="Edit"]' % the_id)
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("abc")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_attempt_%s_score_form_inner" % the_id),
            "Enter a number"))

        # enter a blank number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("\b\b\b\b\b\b\b")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_attempt_%s_score_form_inner" % the_id),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify score 5 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        score_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(score_input.get_attribute("value")), 5.0)
        self.assertFalse("This field is required" in edit_form.text)

        delete_override = edit_form.find_element_by_id("delete_override_%s" \
                                                       % the_id)
        self.assertFalse(delete_override.is_displayed())
        
        # change attempt score to 10
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("\b\b\b10")
        score_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(attempt_score.text), 10.0)
        self.assertEqual(float(record_score.text), 10.0)
        self.assertEqual(self.thread_content.student_score(self.student), 10)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, 10)
        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        self.assertEqual(float(attempt_score.text), 5.0)
        self.assertEqual(float(record_score.text), 5.0)
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, None)
        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        

        # got to attempt 1 details
        self.selenium.find_element_by_id('attempt_1_link').click()
        wait.until(EC.presence_of_element_located(
            (By.ID,'content_attempt_score')))

        
        attempt_score = self.selenium.find_element_by_id(
            'content_attempt_score')
        self.assertEqual(float(attempt_score.text), 5.0)
        attempt_credit = self.selenium.find_element_by_id(
            'content_attempt_credit')
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 50)

        question_1_score = self.selenium.find_element_by_id(
            'question_1_score')
        self.assertEqual(float(question_1_score.text), 5.0)
        question_1_credit = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","", question_1_credit.text)), 100)


        # Check behavior of attempt score form
        edit_form = self.selenium.find_element_by_id(
            "edit_content_attempt_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="content_attempt_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("abc")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_content_attempt_score_form_inner"),
            "Enter a number"))

        # enter a blank number
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("\b\b\b\b\b\b\b")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_content_attempt_score_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify score 5 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        score_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(score_input.get_attribute("value")), 5.0)
        self.assertFalse("This field is required" in edit_form.text)

        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertFalse(score_overridden.is_displayed())
        delete_override = edit_form.find_element_by_id("delete_override_attempt_score")
        self.assertFalse(delete_override.is_displayed())
        
        # change attempt score to 1
        score_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_score_form_score" % the_id)
        score_input.send_keys("\b\b\b1")
        score_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(attempt_score.text), 1.0)
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 10)
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, 1.0)

        self.assertTrue(score_overridden.is_displayed())

        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertTrue(delete_override.is_displayed())
        

        # reload page to make sure still has overridden message displayed
        self.selenium.refresh()
        wait.until(EC.presence_of_element_located(
            (By.ID,'score_overridden')))
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertTrue(score_overridden.is_displayed())

        # remove the override
        edit_form = self.selenium.find_element_by_id(
            "edit_content_attempt_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="content_attempt_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override = edit_form.find_element_by_id("delete_override_attempt_score")
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        attempt_score = self.selenium.find_element_by_id(
            'content_attempt_score')
        self.assertEqual(float(attempt_score.text), 5.0)
        attempt_credit = self.selenium.find_element_by_id(
            'content_attempt_credit')
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 50)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, None)

        self.assertFalse(score_overridden.is_displayed())
        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        


        # Check behavior of attempt credit form
        edit_form = self.selenium.find_element_by_id(
            "edit_content_attempt_credit_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="content_attempt_credit"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        credit_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_credit_form_percent" % the_id)
        credit_input.send_keys("abc")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_content_attempt_credit_form_inner"),
            "Enter a number"))

        # enter a blank number
        credit_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_credit_form_percent" % the_id)
        credit_input.send_keys("\b\b\b\b\b\b\b")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_content_attempt_credit_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify credit 50% shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        credit_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(credit_input.get_attribute("value")), 50.0)
        self.assertFalse("This field is required" in edit_form.text)

        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertFalse(score_overridden.is_displayed())
        delete_override = edit_form.find_element_by_id("delete_override_attempt_credit")
        self.assertFalse(delete_override.is_displayed())
        
        # change attempt credit to 20
        credit_input = self.selenium.find_element_by_id(
            "edit_attempt_%s_credit_form_percent" % the_id)
        credit_input.send_keys("\b\b\b\b20")
        credit_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(attempt_score.text), 2.0)
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 20)
        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, 2.0)

        self.assertTrue(score_overridden.is_displayed())

        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertTrue(delete_override.is_displayed())
        

        # reload page to make sure still has overridden message displayed
        self.selenium.refresh()
        wait.until(EC.presence_of_element_located(
            (By.ID,'score_overridden')))
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertTrue(score_overridden.is_displayed())

        # remove the override
        edit_form = self.selenium.find_element_by_id(
            "edit_content_attempt_credit_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="content_attempt_credit"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override = edit_form.find_element_by_id("delete_override_attempt_credit")
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        attempt_score = self.selenium.find_element_by_id(
            'content_attempt_score')
        self.assertEqual(float(attempt_score.text), 5.0)
        attempt_credit = self.selenium.find_element_by_id(
            'content_attempt_credit')
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 50)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        self.content_attempt_1.refresh_from_db()
        self.assertEqual(self.content_attempt_1.score_override, None)

        self.assertFalse(score_overridden.is_displayed())
        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        



        # Check behavior of question 1 score form
        edit_form = self.selenium.find_element_by_id(
            "edit_question_1_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_1_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("abc")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_1_score_form_inner"),
            "Enter a number"))

        # enter a blank number
        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("\b\b\b\b\b\b\b")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_1_score_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify score 5 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        score_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(score_input.get_attribute("value")), 5.0)
        self.assertFalse("This field is required" in edit_form.text)

        delete_override = edit_form.find_element_by_id(
            "delete_override_1_score")
        self.assertFalse(delete_override.is_displayed())
        
        # change attempt score to 3
        question_set_1 = self.content_attempt_1.question_sets\
                        .get(question_number=1)
        self.assertEqual(question_set_1.credit_override, None)

        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("\b\b\b3")
        score_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(attempt_score.text), 3.0)
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 30)
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        question_1_score = self.selenium.find_element_by_id(
            'question_1_score')
        self.assertEqual(float(question_1_score.text), 3.0)
        question_1_credit = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","", question_1_credit.text)), 60)


        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, 0.6)


        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        self.assertEqual(float(question_1_score.text), 5.0)
        question_1_credit = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","", question_1_credit.text)), 100)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, None)

        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        



        # Check behavior of question 1 credit form
        edit_form = self.selenium.find_element_by_id(
            "edit_question_1_credit_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_1_credit"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("abc")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_1_credit_form_inner"),
            "Enter a number"))

        # enter a blank number
        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("\b\b\b\b\b\b\b\b")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_1_credit_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify credit 100 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        credit_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(credit_input.get_attribute("value")), 100.0)
        self.assertFalse("This field is required" in edit_form.text)

        delete_override = edit_form.find_element_by_id(
            "delete_override_1_credit")
        self.assertFalse(delete_override.is_displayed())
        
        # change attempt credit to 80
        question_set_1 = self.content_attempt_1.question_sets\
                        .get(question_number=1)
        self.assertEqual(question_set_1.credit_override, None)

        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("\b\b\b\b\b80")
        credit_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(float(attempt_score.text), 4.0)
        self.assertEqual(
            float(re.sub("%","", attempt_credit.text)), 40)
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        question_1_score = self.selenium.find_element_by_id(
            'question_1_score')
        self.assertEqual(float(question_1_score.text), 4.0)
        question_1_credit = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","", question_1_credit.text)), 80)


        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, 0.8)


        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))

        self.assertEqual(float(question_1_score.text), 5.0)
        question_1_credit = self.selenium.find_element_by_id(
            'question_1_credit')
        self.assertEqual(
            float(re.sub("%","", question_1_credit.text)), 100)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, None)

        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        

        # got to question set 1 details
        self.selenium.find_element_by_id('attempt_1_link').click()
        wait.until(EC.presence_of_element_located(
            (By.ID,'question_score')))

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 5.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 100)


        # Check behavior of question score form
        edit_form = self.selenium.find_element_by_id(
            "edit_question_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("abc")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_score_form_inner"),
            "Enter a number"))

        # enter a blank number
        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("\b\b\b\b\b\b\b")
        score_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_score_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify score 5 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        score_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(score_input.get_attribute("value")), 5.0)
        self.assertFalse("This field is required" in edit_form.text)
        
        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertFalse(score_overridden.is_displayed())
        delete_override = edit_form.find_element_by_id(
            "delete_override_question_score")
        self.assertFalse(delete_override.is_displayed())


        # change attempt score to 3
        question_set_1 = self.content_attempt_1.question_sets\
                        .get(question_number=1)
        self.assertEqual(question_set_1.credit_override, None)

        score_input = self.selenium.find_element_by_id(
            "edit_question_1_score_form_score")
        score_input.send_keys("\b\b\b3")
        score_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 3.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 60)

        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, 0.6)

        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        self.assertTrue(score_overridden.is_displayed())

        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertTrue(delete_override.is_displayed())

        # reload page to make sure still has overridden message displayed
        self.selenium.refresh()
        wait.until(EC.presence_of_element_located(
            (By.ID,'score_comment')))
        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertTrue(score_overridden.is_displayed())

        # remove the override
        edit_form = self.selenium.find_element_by_id(
            "edit_question_score_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_score"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override = edit_form.find_element_by_id(
            "delete_override_question_score")
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))


        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 5.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 100)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, None)

        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        


        # Check behavior of question credit form
        edit_form = self.selenium.find_element_by_id(
            "edit_question_credit_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_credit"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))

        # enter invalid number
        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("abc")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_credit_form_inner"),
            "Enter a number"))

        # enter a blank number
        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("\b\b\b\b\b\b\b\b\b")
        credit_input.submit()
        wait.until(EC.text_to_be_present_in_element(
            (By.ID, "edit_question_credit_form_inner"),
            "This field is required"))
        self.assertTrue("This field is required" in edit_form.text)

        
        # cancel and click edit again, to verify credit 100 shows up again
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        credit_input = edit_form.find_element_by_xpath("*/*/input[@type='text']")
        self.assertEqual(float(credit_input.get_attribute("value")), 100.0)
        self.assertFalse("This field is required" in edit_form.text)

        delete_override = edit_form.find_element_by_id(
            "delete_override_question_credit")
        self.assertFalse(delete_override.is_displayed())
        
        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertFalse(score_overridden.is_displayed())
        delete_override = edit_form.find_element_by_id(
            "delete_override_question_credit")
        self.assertFalse(delete_override.is_displayed())

        # change attempt credit to 20
        question_set_1 = self.content_attempt_1.question_sets\
                        .get(question_number=1)
        self.assertEqual(question_set_1.credit_override, None)

        credit_input = self.selenium.find_element_by_id(
            "edit_question_1_credit_form_percent")
        credit_input.send_keys("\b\b\b\b\b20")
        credit_input.submit()
        wait.until(EC.visibility_of(edit_button))
        
        self.assertEqual(self.thread_content.student_score(self.student), 5)

        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 1.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 20)

        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, 0.2)

        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        self.assertTrue(score_overridden.is_displayed())

        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertTrue(delete_override.is_displayed())

        # reload page to make sure still has overridden message displayed
        self.selenium.refresh()
        wait.until(EC.presence_of_element_located(
            (By.ID,'score_comment')))
        score_comment = self.selenium.find_element_by_id("score_comment")
        self.assertEqual(score_comment.get_attribute("class"), "overridden")
        score_overridden = self.selenium.find_element_by_id("score_overridden")
        self.assertTrue(score_overridden.is_displayed())

        # remove the override
        edit_form = self.selenium.find_element_by_id(
            "edit_question_credit_form")
        edit_button = self.selenium.find_element_by_xpath(
            '//div[@id="question_credit"]/input[@value="Edit"]')
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        delete_override = edit_form.find_element_by_id(
            "delete_override_question_credit")
        delete_override.click()
        wait.until(EC.visibility_of(edit_button))


        question_score = self.selenium.find_element_by_id(
            'question_score')
        self.assertEqual(float(question_score.text), 5.0)
        question_credit = self.selenium.find_element_by_id(
            'question_credit')
        self.assertEqual(
            float(re.sub("%","", question_credit.text)), 100)

        self.assertEqual(self.thread_content.student_score(self.student), 5)
        question_set_1.refresh_from_db()
        self.assertEqual(question_set_1.credit_override, None)

        
        edit_button.click()
        wait.until(EC.visibility_of(edit_form))
        self.assertFalse(delete_override.is_displayed())
        edit_form.find_element_by_xpath("input[@value='Cancel']").click()
        wait.until(EC.visibility_of(edit_button))
        
