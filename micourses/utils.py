from django.utils import formats, timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import pytz

def check_for_student_activity(content):
    """
    Check if thread content has any student activity.

    Return True if, for a courseuser enrolled in course as STUDENT ROLE,
    there is either
    1. a content attempt, or
    2. a content completion with score_override

    Otherwise, return False
    
    """

    from micourses.models import STUDENT_ROLE

    for attempt in content.studentcontentattempt_set.all():
        try:
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



def format_datetime(value):
    return "%s, %s" % (formats.date_format(value), formats.time_format(value))


def find_week_begin_end(course, datetime=None):

    tz = pytz.timezone(course.attendance_time_zone)
    if not datetime:
        datetime = timezone.now()
    datetime = tz.normalize(datetime.astimezone(tz))
    day_of_week = (datetime.weekday()+1) % 7
    to_beginning_of_week = timezone.timedelta(
        days=day_of_week, hours=datetime.hour,
        minutes=datetime.minute, seconds=datetime.second, 
        microseconds=datetime.microsecond
    )
    beginning_of_week = datetime - to_beginning_of_week
    end_of_week = beginning_of_week + timezone.timedelta(days=7) \
                  - timezone.timedelta(microseconds=1)

    return beginning_of_week, end_of_week


def validate_not_number(value):
    """
    Validate that string value is not a number.
    Use for urls to make sure won't get absorbed by url patterns 
    with a number in the same location as the code
    """

    # if code is all digits, raise validation error
    import re
    if re.match(r'(\d*)', value).group() == value:
        raise ValidationError("Cannot be a number")


def find_last_course(user, request=None):
    """"
    Find course of page that user last visited.  
    If user is authenticated, course enrolled in takes priority.
    
    """
    if user.is_authenticated():
        try:
            course=user.courseuser.return_selected_course_if_exists()
        except AttributeError:
            pass
        else:
            if course:
                return course
    
    if request:
        course_id=request.session.get('last_course_viewed')
        if course_id is not None:
            from micourses.models import Course
            try:
                return Course.objects.get(id=course_id)
            except (ObjectDoesNotExist, TypeError):
                pass

    return None

