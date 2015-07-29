from micourses.models import STUDENT_ROLE

def check_for_student_activity(content):
    """
    Check if thread content has any student activity.

    Return True if, for a courseuser enrolled in course as STUDENT ROLE,
    there is either
    1. a content attempt, or
    2. a content completion with score_override

    Otherwise, return False
    
    """

    for attempt in content.studentcontentattempt_set.all():
        enrollment = attempt.student.courseenrollment_set.get(
                course=content.course)
        except ObjectDoesNotExist:
            continue

        if enrollment.role == STUDENT_ROLE:
            return True

    for completion in content.studentcontentcompletion_set\
        .exclude(score_override=None):

        try:
            enrollment = completion.student.courseenrollment_set.get(
                course=content.course)
        except ObjectDoesNotExist:
            continue

        if enrollment.role == STUDENT_ROLE:
            return True

    return False
