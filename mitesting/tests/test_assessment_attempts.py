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
