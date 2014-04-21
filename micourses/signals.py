from django.db.models.signals import post_save
from django.contrib.auth.models import User
from micourses.models import CourseUser

def create_course_user(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        try:
            new_course_user = CourseUser(user = user)
            new_course_user.save()
        except:
            # if don't have CourseUser table set up yet
            # (e.g., when creating initial user before migrating), ignore error
            pass

post_save.connect(create_course_user, sender = User, dispatch_uid = 'users-course-user-creation-signal')
