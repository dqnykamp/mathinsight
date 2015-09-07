from django.contrib.auth.decorators import permission_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist

def return_user_assessment_permission_level(user, course=None):
    """
    Returns the assessment permission level of user, based on 
    role of user in course.
 
    Values are:
    0: user is not logged in, is inactive, or is not enrolled in course
    1. STUDENT_ROLE or AUDITOR_ROLE
    2. INSTRUCTOR_ROLE
    3. DESIGNER_ROLE

    If course is not specified, 
    then the maximum is taken over all enrolled courses.
    
    """

    if not (user.is_authenticated() and user.is_active):
        return 0

    try:
        permission_level = user.courseuser.return_permission_level(course)
    except (ObjectDoesNotExist, AttributeError, TypeError):
        pass
    else:
        if permission_level in [0, 1, 2, 3]:
            return permission_level

    return 0
    

def user_has_given_assessment_permission_level(user, permission_level, 
                                               course=None):
    """
    Checks whether a user has 
    a permission level greater or equal to the given permission_level
    """

    return return_user_assessment_permission_level(user, course) >= permission_level


def user_has_given_assessment_permission_level_decorator(
    permission_level, course=None, login_url=None):
    """
    Decorator for views that checks whether a user has 
    a permission level greater or equal to the given permission_level,
    redirecting to the log-in page if necessary.
    """
    return user_passes_test(
        lambda u: user_has_given_assessment_permission_level(
            u, permission_level, course=course),
        login_url=login_url)


def user_can_administer_assessment(user, course):
    """
    Check whether or not a user can administer assessment.

    True if user is instructor or designer of course.

    """

    try:
        return user.courseuser.can_administer_assessment(course)

    except AttributeError:
        return False



def user_can_administer_assessment_decorator(course, login_url=None):
    """
    Decorator for views that checks whether a user has 
    can administer assessments
    redirecting to the log-in page if necessary.
    """
    return user_passes_test(
        lambda u: user_can_administer_assessment(u, course=course),
        login_url=login_url)
