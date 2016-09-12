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

        
def create_new_assessment_attempt(student_record, begin_attempt=True):

    thread_content = student_record.content
    assessment = thread_content.content_object

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

        total_number_of_attempts = student_record.attempts.count()+1

        if thread_content.individualize_by_student:
            version = "%s_%s" % \
                    (student_record.enrollment.student.user.username, version)
        
        seed = "sd%s_%s_%s" % (thread_content.id, version, 
                               total_number_of_attempts)
        version = re.sub("_", " ", version)

    # create the new attempt
    with transaction.atomic(), reversion.create_revision():
        if begin_attempt:
            new_attempt = student_record.attempts.create(
                seed=seed, valid=valid_attempt, version=version)
        else:
            new_attempt = student_record.attempts.create(
                seed=seed, valid=valid_attempt, version=version,
                attempt_began=None)

            
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
            'version': version, 'assessment_seed': seed,
            'valid_attempt': valid_attempt, 
            'assessment_availability': assessment_availability }
            

def ensure_open_assessment_attempt(student_record):
    # check if there is an open, valid, unexpired assessment attempt for student
    # if not, create and return a new attempt

    thread_content = student_record.content

    # check if the assessment is even available
    assessment = thread_content.content_object

    from micourses.models import AVAILABLE
    assessment_available = \
            thread_content.return_availability(student_record) == AVAILABLE

    # treat assessment not set up for recording as not available
    if not thread_content.record_scores:
        assessment_available = False

    result = {'closed_expired': False, 'found_valid': False, 
                   'created_new': False, 'new_attempt_info': None,
                   'assessment_available': assessment_available }

    # find latest attempt, if any
    latest_attempt = student_record.latest_attempt
    
    # if found latest attempt, discard if not open and valid
    if latest_attempt:
        
        # if expired, close attempt
        if thread_content.time_limit and latest_attempt.attempt_began:
            if latest_attempt.attempt_began + thread_content.time_limit \
               < timezone.now():
                latest_attempt.closed = True
                latest_attempt.save()
            result['closed_expired'] = True

        # if have a valid and open attempt, don't create anything
        if latest_attempt.valid and not latest_attempt.closed:
            result['found_valid'] = True
            return result

    # if assessment isn't available, don't bother trying to create attempt
    if not assessment_available:
        return result

    # create new attempt
    # with attempt_began=None so that doesn't start until student views
    new_attempt_info = create_new_assessment_attempt(
        student_record=student_record, begin_attempt=False)
    
    result['created_new'] = True
    result['new_attempt_info'] = new_attempt_info
    return result


def ensure_open_assessment_attempt_all_students(thread_content):
    # for each student, create an open, valid, unexpired attempt 
    # if none exists

    from micourses.models import STUDENT_ROLE

    n_created = 0
    n_students = 0
    result = {}
    
    
    for student_record in thread_content.contentrecord_set.filter(
            enrollment__role=STUDENT_ROLE):
        result= ensure_open_assessment_attempt(student_record)
        if result['created_new']:
            n_created += 1
        n_students +=1


    if n_students:
        assessment_available = result['assessment_available']
    else:
        assessmnet_available = None

    return {'n_created': n_created, 'n_students': n_students,
            'assessment_available': assessment_available}


def close_latest_assessment_attempt(student_record):
    
    # find latest attempt, if any
    latest_attempt = student_record.latest_attempt
    
    if latest_attempt:
        # if attempt_began is None, it means student didn't start exam,
        # so just mark as invalid
        if not latest_attempt.attempt_began:
            if latest_attempt.valid:
                latest_attempt.valid=False
                latest_attempt.save()
        else:
            if not latest_attempt.closed:
                latest_attempt.closed=True
                latest_attempt.save()


def close_latest_assessment_attempt_all_students(thread_content):
    
    from micourses.models import STUDENT_ROLE

    for student_record in thread_content.contentrecord_set.filter(
            enrollment__role=STUDENT_ROLE):
        close_latest_assessment_attempt(student_record)


def get_open_attempt_info(content_record):
    thread_content = content_record.content

    open_attempt=False
    latest_attempt_info_text = "No open attempt"
    if thread_content.access_only_open_attempts:
        latest_attempt = content_record.latest_attempt

        if latest_attempt:
            if not latest_attempt.closed and latest_attempt.valid:
                if latest_attempt.time_expired():
                    latest_attempt_info_text = "Attempt expired"
                else:
                    open_attempt=True
                    if latest_attempt.attempt_began:
                        from django.utils import dateformat
                        began_string = dateformat.format(
                            timezone.localtime(
                                latest_attempt.attempt_began),
                            'F j, Y, P')
                        latest_attempt_info_text = "Open attempt, begun at %s" % began_string
                    else:
                        latest_attempt_info_text = "Open attempt, not begun"
    return {'open_attempt': open_attempt,
            'latest_attempt_info_text': latest_attempt_info_text }


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


def http_response_simple_page_from_string(s, user=None, no_links=False):
    from django.template import Template, Context
    from django.http import HttpResponse
    from django.conf import settings
    template_string = "{% extends 'base.html' %}"
    if no_links:
        template_string += "{% block nositenav %}{% endblock %}{% block nopagenav %}{% endblock %}{% block nopagenavsl %}{% endblock %}{% block breadcrumbs %}{% endblock %}"
        template_string += "{% block login %}{% if user.is_authenticated %}logged in as {{ user}}{%else%}<a href='{% url 'mi-login'%}?next={{request.path}}'>log in</a>{%endif%}{% endblock %}"

    template_string += "{% block content %}"
    template_string += str(s)
    template_string += "{% endblock %}"
    context = Context({'STATIC_URL': settings.STATIC_URL,
                       'user': user, })
    return HttpResponse(Template(template_string).render(context))



def duration_to_string(duration):
    duration_string = ""
    if duration.days:
        duration_string = "%s day" % duration.days
        if duration.days > 1:
            duration_string += "s"
    mins = int(duration.seconds/60)
    secs = duration.seconds - mins*60
    hrs = int(mins/60)
    mins -= hrs*60
    if hrs:
        if duration_string:
            duration_string += ", " 
        duration_string += "%s hour" % hrs
        if hrs > 1:
            duration_string += "s"
    if mins:
        if duration_string:
            duration_string += ", " 
        duration_string += "%s minute" % mins
        if mins > 1:
            duration_string += "s"
    if secs:
        if duration_string:
            duration_string += ", " 
        duration_string += "%s second" % secs
        if secs > 1:
            duration_string += "s"

    return duration_string


def ip_address_matches_pattern(ip_address, pattern):
    """"
    Return true if ip_address matches one of the ip address patters in pattern.
    Else return False
    """

    valid_ip_re = re.compile(
        r'(\d{1,3}|\*).(\d{1,3}|\*).(\d{1,3}|\*).(\d{1,3}|\*)$')

    # parse allowed ip addresses
    ip_list = pattern.split(",")
    for ip_string in ip_list:
        match = re.match(valid_ip_re, ip_string.strip())

        # if is a valid ip address string
        if match:
            # convert to regular expression pattern where *
            # matches any sequence of up to 3 digits
            p=re.compile(re.sub(r'\*', r'\d{1,3}',match.group()) +'$')
            if re.match(p, ip_address):
                return True

    return False


def verify_secure_browser(thread_content, request):

    safe_exam_browser_verified = False

    request_hash = request.META.get("HTTP_X_SAFEEXAMBROWSER_REQUESTHASH")
    if not request_hash:
        error_message="Assessment is viewable only through Safe Exam Browser.  Consult your instructor for proper configuration."
        return {'verified': False, 'error_message': error_message}

    else:
        import hashlib
        sha256=hashlib.sha256()
        sha256.update(request.build_absolute_uri().encode())

        for exam_key in thread_content.browser_exam_keys.splitlines():
            s = sha256.copy()
            s.update(exam_key.encode())

            if s.hexdigest() == request_hash:
                return {'verified': True}


        error_message = "Safe Exam Browser does not appear to be properly configured for this assessment.  Consult your instructor for proper configuration."

        return {'verified': False, 'error_message': error_message}



