from django.db.models.signals import post_save
from django.contrib.auth.models import User
from micourses.models import CourseUser

def create_course_user(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        new_course_user = CourseUser(user = user)
        new_course_user.save()

post_save.connect(create_course_user, sender = User, dispatch_uid = 'users-course-user-creation-signal')
