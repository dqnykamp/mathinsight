from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib.auth.decorators import permission_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist

def return_user_assessment_permission_level(user):
    """
    Returns the assessment permission level of user.  Levels are:
    0: user is not logged in or is inactive
    1: user is logged in, with no special privileges
    2: user has full permissions to view assessments and solutions
       (i.e., has mitesting.administer_assessment permission)

    If user.courseuser.return_permission_level() returns 
    a valid permission level, then use that value instead

    
    """

    if not (user.is_authenticated() and user.is_active):
        return 0

    try:
        permission_level = user.courseuser.return_permission_level()
    except (ObjectDoesNotExist, AttributeError, TypeError):
        pass
    else:
        if permission_level in [0, 1, 2]:
            return permission_level

    if user.has_perm('mitesting.administer_assessment'):
        return 2
    else:
        return 1
    

def user_has_given_assessment_permission_level(user, permission_level):
    """
    Checks whether a user has 
    a permission level greater or equal to the given permission_level
    """

    return return_user_assessment_permission_level(user) >= permission_level


def user_has_given_assessment_permission_level_decorator(
    permission_level, login_url=None):
    """
    Decorator for views that checks whether a user has 
    a permission level greater or equal to the given permission_level,
    redirecting to the log-in page if necessary.
    """
    return user_passes_test(
        lambda u: user_has_given_assessment_permission_level(
            u, permission_level),
        login_url=login_url)
