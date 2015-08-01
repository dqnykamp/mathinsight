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
Otherwise:
Ignore seed from GET.
Find latest content attempt or create if none.

If latest content attempt found, get seeds of assessment 
and get questions and seeds from latest associated question attempts for each question set.
If don't find a question attempt for a question set (shouldn't happen),
then create question attempt 

 and question sets from attempt.
Otherwise, create assessment seed from course code and attempt number,
as well as username if individualize by student (or seed=1 if single version)
and generate question set seeds.

Looged in user who is instructor of course:
If assessment is not in course thread, same as anonymous user behavior
Otherwise:
If seed is in GET, use that to generate assessment.
Otherwise, same behavior as students.




"""
