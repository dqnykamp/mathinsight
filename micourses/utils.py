from django.utils import formats, timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
import reversion
import pytz
import re

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


def set_n_of_objects(course, content_object):
    from django.contrib.contenttypes.models import ContentType
    from micourses.models import ThreadContent

    ct = ContentType.objects.get_for_model(content_object.__class__)
    
    # loop through all thread_contents with content object
    # and change n_objects if it doesn't match order in list
    for (i, tc) in enumerate(course.thread_contents.filter(content_type=ct,
                                            object_id = content_object.id)):
        if tc.n_of_object != i+1:
            tc.n_of_object = i+1
            super(ThreadContent,tc).save()

        
def create_new_assessment_attempt(assessment, thread_content, courseuser,
                                  student_record):

    from micourses.models import AVAILABLE, NOT_YET_AVAILABLE
    assessment_availability = thread_content.return_availability(
        student=courseuser)

    # treat assessment not set up for recording as not available
    if not thread_content.record_scores:
        assessment_availability = NOT_YET_AVAILABLE

    valid_attempt=assessment_availability==AVAILABLE

    if assessment.single_version:
       seed='1'
       version = ''
    else:
        if valid_attempt:
            attempt_number = student_record.attempts.filter(valid=True)\
                                                    .count()+1
            version = str(attempt_number)
        else:
            attempt_number = student_record.attempts.filter(valid=False)\
                                                    .count()+1
            version = "x%s" % attempt_number

        if thread_content.individualize_by_student:
            version = "%s_%s" % \
                        (courseuser.user.username, version)
        seed = "sd%s_%s" % (thread_content.id, version)
        version = re.sub("_", " ", version)

    # create the new attempt
    with transaction.atomic(), reversion.create_revision():
        new_attempt = student_record.attempts.create(
            seed=seed, valid=valid_attempt, version=version)

    from micourses.render_assessments import get_question_list
    question_list = get_question_list(assessment, seed=seed,
                                      thread_content=thread_content)

    # create the content question sets and question attempts
    with transaction.atomic(), reversion.create_revision():
        for (i,q_dict) in enumerate(question_list):
            ca_question_set = new_attempt.question_sets.create(
                question_number=i+1, question_set=q_dict['question_set'])
            qa=ca_question_set.question_attempts.create(
                question=q_dict['question'],
                seed=q_dict['seed'], valid=valid_attempt)
            q_dict["question_attempt"] = qa

    return {'new_attempt': new_attempt, 'question_list': question_list,
            'version': version, 'assessment_seed': seed,}
            

