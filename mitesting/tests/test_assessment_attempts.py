from django.test import TestCase
from mitesting.models import Expression, Question, QuestionType, SympyCommandSet, QuestionAnswerOption, Assessment, AssessmentType
from micourses.models import Course
from django.contrib.auth.models import AnonymousUser, User, Permission, Group
import random

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
- Determine if have a valid attempt.
  Reasons for invalid: not yet released, past due, or solution viewed
- Find latest content attempt that matches condition
  (valid, not yet released, or past due/solution viewed)
  Obtain
  - assessment seed from content attempt 
  - order of questions and their seeds from related question attempts
    (take latest question attempt for each question set)
  If missing data (e.g., question attempts, which shouldn't happen),
  then treat as though don't have content attempt and create new one (below)
- If no matching content attempt, 
  then create new content attempt and question attempts.
  Generate assessment seed as follows:
  - If past due/solution viewed, check for a current valid attempt.
    If found, use that assessment.
    If none found, then generate seed as though a valid attempt.
  - If valid attempt, create assessment seed from 
    - course code and attempt number
    - plus username if assessment is individualized by student
    Exception: set seed=1 if assessment marked as single version
  - If not yet released, set seed to be attempt number.
  Use assessment seed to generate question order and seeds for each question.
  Save 
  - assessment seed to content attempt
  - order of questions and their seeds to question attempt
  If not yet released or past due/solution viewed, mark attempt as invalid.
If not valid attempt, then removed any feedback of progress on question
to make it clear that question isn't being tracked.
Maintain feedback for individual answer responses.
   

Looged in user who is instructor of course:
If assessment is not in course thread, same as anonymous user behavior
Otherwise:
If seed is in GET, use that to generate assessment.
Otherwise, same behavior as students.




"""
