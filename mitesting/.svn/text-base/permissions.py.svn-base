from django.contrib.auth.decorators import permission_required, user_passes_test

def return_user_assessment_permission_level(user, solution=True):
    if solution:
        user_assessment_permission_level=0
        for i in range(2,0,-1):
            if user.has_perm('mitesting.view_assessment_%s_solution' % i):
                user_assessment_permission_level=i
                break
    else:
        user_assessment_permission_level=0
        for i in range(2,0,-1):
            if user.has_perm('mitesting.view_assessment_%s' % i):
                user_assessment_permission_level=i
                break

    return user_assessment_permission_level
    

def user_has_given_assessment_permission_level(user, permission_level, solution=True):
    """
    Checks whether a user has 
    a permission level greater or equal to the given permission_level
    """

    return return_user_assessment_permission_level(user,solution) >= permission_level


def user_has_given_assessment_permission_level_decorator(permission_level, solution=True, login_url=None):
    """
    Decorator for views that checks whether a user has 
    a permission level greater or equal to the given permission_level,
    redirecting to the log-in page if necessary.
    """
    return user_passes_test(lambda u: user_has_given_assessment_permission_level(u,permission_level,solution), login_url=login_url)
