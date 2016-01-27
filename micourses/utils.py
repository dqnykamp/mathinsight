from django.utils import formats, timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
import reversion
import pytz
import re
import json

def check_for_student_activity(content):
    """
    Check if thread content has any student activity.

    Return True if, for a courseuser enrolled in course as STUDENT ROLE,
    there is a content record with a score_override or content attempt,

    Otherwise, return False
    
    """

    from micourses.models import STUDENT_ROLE

    for record in content.contentrecord_set.all():
        if not record.enrollment or record.enrollment.role != STUDENT_ROLE:
            continue

        if record.score_override is not None:
            return True

        if record.attempts.exists():
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
    assessment_availability = thread_content.return_availability(student_record)

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
            

def json_dump_fields(model_instance):
    try:
        fields_to_dump = model_instance.fields_to_dump
    except AttributeError:
        return None

    data = {}
    for f in fields_to_dump:
        data[f] = getattr(model_instance,f)

    from datetime import datetime

    def json_datetime_serial(obj):
        """JSON serializer to include datetimee"""

        if isinstance(obj, datetime):
            serial = obj.isoformat()
            return serial
        raise TypeError ("Type not serializable")


    return json.dumps(data, default=json_datetime_serial)



def return_allowed_content_types():
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    
    return ContentType.objects.filter(
        Q(app_label="midocs", model='applet') | Q(app_label="midocs", model='page') |
        Q(app_label="micourses", model='assessment') | Q(app_label="midocs", model='video'))


def create_content_records(course):
    from micourses.models import ContentRecord, STUDENT_ROLE

    content_with_points = course.thread_contents.exclude(points=0)\
                                                .exclude(points=None)
    
    enrollments = course.courseenrollment_set.filter(role=STUDENT_ROLE)
        
    new_crs=[]
    

    content_records_missing={}
    for tc in content_with_points:
        d = {}
        for ce in enrollments:
            d[ce.id]=True
        content_records_missing[tc.id] = d

    records = ContentRecord.objects.filter(content__course=course) \
        .exclude(content__points=None).exclude(content__points=0)

    # since starting with ContentRecord, could have records
    # associated with content that was deleted
    records = records.filter(content__deleted=False)
    records = records.filter(enrollment__role=STUDENT_ROLE)

    for cr in records.select_related('enrollment', 'content'):
        del content_records_missing[cr.content.id][cr.enrollment.id]
    
    # create any records left in content_records_missing
    now = timezone.now()
    cr_list = []
    for k1 in content_records_missing:
        for k2 in content_records_missing[k1]:
            cr_list.append(ContentRecord(content_id=k1, enrollment_id=k2,
                                         last_modified=now))
    
    ContentRecord.objects.bulk_create(cr_list)


def create_all_content_records(active=True):
    from micourses.models import Course

    courses = Course.objects.all()
    if active:
        courses = courses.filter(active=True)

    for course in courses:
        create_content_records(course)
