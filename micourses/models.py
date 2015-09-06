from django.db import models, transaction
from django.db.models import Sum, Max, Avg
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.template import TemplateSyntaxError, Context, Template
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.conf import settings
from math import ceil
import pytz
import reversion

STUDENT_ROLE = 'S'
INSTRUCTOR_ROLE = 'I'
DESIGNER_ROLE = 'D'
NOT_YET_AVAILABLE = 0
AVAILABLE = 1
PAST_DUE = -1
ABSENT = 0
PRESENT = 1
EXCUSED = -1


def day_of_week_to_python(day_of_week):
    if day_of_week.upper() == 'S':
        return 6
    elif day_of_week.upper() == 'M':
        return 0
    elif day_of_week.upper() == 'T':
        return 1
    elif day_of_week.upper() == 'W':
        return 2
    elif day_of_week.upper() == 'TH':
        return 3
    elif day_of_week.upper() == 'F':
        return 4
    elif day_of_week.upper() == 'SA':
        return 5

class ChangeLog(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    courseuser = models.ForeignKey('CourseUser', null=True)
    action = models.CharField(choices=(("change score", "change score"), 
                                       ("change date", "change date"), 
                                       ("change", "change"), 
                                       ("delete", "delete"),
                                       ("create", "create"),
                                   ),
                              max_length=20)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    datetime = models.DateTimeField(blank=True, default=timezone.now)
    


class CourseUser(models.Model):
    user = models.OneToOneField(User)
    userid = models.CharField(max_length=20, blank=True, null=True)
    selected_course_enrollment = models.ForeignKey(
        'CourseEnrollment', blank=True, null=True,
        on_delete=models.SET_NULL)

    class Meta:
        ordering = ['user__last_name', 'user__first_name', 'user__username']

    def __str__(self):
        return "%s, %s" % (self.user.last_name, self.user.first_name)
    
    def get_full_name(self):
        return self.user.get_full_name()
    def get_short_name(self):
        return self.user.get_short_name()

    def return_selected_course(self):
        if self.selected_course_enrollment:
            return self.selected_course_enrollment.course

        # Try to find unique enrolled, active course.
        # Will raise MultipleObjectReturned if multiple enrolled courses.
        # Will raise ObjectDoesNotExist is no enrolled courses
        course_enrollment = self.courseenrollment_set.get(
            course__active=True)
        
        # if found just one active course, make it be the selected course
        self.selected_course_enrollment = course_enrollment
        self.save()
        return course_enrollment.course

    def return_selected_course_if_exists(self):
        if self.selected_course_enrollment:
            return self.selected_course_enrollment.course
        else:
            return None

    def active_courses(self):
        return self.course_set.filter(active=True)
    
    def get_current_role(self, course=None):
        """
        Returns role of course user in course.  Values:
        - None (if not enrolled in course)
        - STUDENT_ROLE
        - INSTRUCTOR_ROLE
        - DESIGNER_ROLE

        If course is None, then returns maximum role over all courses.
        """

        if course:
            try:
                course_enrollment = course.courseenrollment_set.get(student=self)
            except ObjectDoesNotExist:
                return None
            return course_enrollment.role

        else:
            # if no course specified, then treat as instructor/designer
            # if user is an instructor/designer in any course
            role = None
            for enrollment in self.courseenrollment_set.all():
                if enrollment.role==DESIGNER_ROLE:
                    return DESIGNER_ROLE
                elif enrollment.role == INSTRUCTOR_ROLE:
                    role=INSTRUCTOR_ROLE
                elif role != INSTRUCTOR_ROLE:
                    role=STUDENT_ROLE
            return role


    def return_permission_level(self, course=None):
        """
        Returns the assessment permission level of course user, based on 
        role of user in course.

        Values are:
        0. not enrolled in course
        1. STUDENT_ROLE
        2. INSTRUCTOR_ROLE
        3. DESIGNER_ROLE

        If course is not specified, 
        then the maximum is taken over all enrolled courses.

        """

        role = self.get_current_role(course)
        if role==DESIGNER_ROLE:
            return 3
        elif role == INSTRUCTOR_ROLE:
            return 2
        elif role == STUDENT_ROLE:
            return 1
        else:
            return 0
        

    def can_administer_assessment(self, course):
        """
        Return true if course user is instructor or designer of course

        """

        # course must be specified
        if course is None:
            return False
            
        return self.return_permission_level(course) >= 2


    def percent_attendance(self, course=None, date=None):
        if not course:
            try:
                course = self.return_selected_course()
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None

        if date:
            tz = pytz.timezone(course.attendance_time_zone)
            try:
                date= tz.normalize(date.astimezone(tz)).date()
            except AttributeError:
                pass
        else:
            date = course.last_attendance_day_previous_week()
            if not date:
                return None


        course_enrollment = self.courseenrollment_set.get(course=course)
        date_enrolled = course_enrollment.date_enrolled
        course_days = course.to_date_attendance_days(date, 
                                                     start_date=date_enrolled)
        
        attendance_data = course_enrollment.studentattendance_set\
            .filter(date__lte = date).filter(date__gte = date_enrolled)
        
        n_excused_absenses = attendance_data.filter(present = EXCUSED).count()
        
        days_attended = attendance_data.exclude(present = EXCUSED)\
            .aggregate(Sum('present'))['present__sum']

        if course_days:
            try:
                return 100.0*days_attended/float(course_days-n_excused_absenses)
            except (TypeError, ZeroDivisionError):
                return 0
        else:
            return 0
    


class GradeCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Grade categories'


class CourseGradeCategory(models.Model):
    course = models.ForeignKey('Course')
    grade_category = models.ForeignKey(GradeCategory)
    number_count_for_grade = models.IntegerField(blank=True, null=True)
    rescale_factor = models.FloatField(default=1.0)
    sort_order = models.FloatField(blank=True)

    def __str__(self):
        return "%s for %s" % (self.grade_category, self.course)

    class Meta:
        verbose_name_plural = 'Course grade categories'
        ordering = ['sort_order',  'id']

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.course.coursegradecategory_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(CourseGradeCategory, self).save(*args, **kwargs)



class AttendanceDate(models.Model):
    course = models.ForeignKey('Course')
    date = models.DateField()
    
    class Meta:
        ordering = ['date', ]

class CourseSkipDate(models.Model):
    course = models.ForeignKey('Course')
    date = models.DateField()


class ActiveCourseManager(models.Manager):
    def get_queryset(self):
        return super(ActiveCourseManager, self).get_queryset() \
            .filter(active=True)

class Course(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=400, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    grade_categories = models.ManyToManyField(GradeCategory, through='CourseGradeCategory', blank=True)
    enrolled_students = models.ManyToManyField(CourseUser, through='CourseEnrollment', blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    days_of_week = models.CharField(max_length=50, blank=True, null=True)
    track_attendance = models.BooleanField(default=False)
    adjust_due_attendance = models.BooleanField(default=False)
    last_attendance_date = models.DateField(blank=True, null=True)
    attendance_end_of_week = models.CharField(max_length = 2, 
                                              default='F')
    attendance_time_zone = models.CharField(max_length=50, choices = [(x,x) for x in pytz.common_timezones], default=settings.TIME_ZONE)
    attendance_threshold_percent = models.SmallIntegerField(default = 75)

    numbered = models.BooleanField(default=True)
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.FloatField(blank=True)

    objects = models.Manager()
    active_courses = ActiveCourseManager()

    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order','id']
        unique_together = ['name', 'semester']

    def all_thread_section_generator(self):
        ts = self.thread_sections.first()
        # since could have infinite loop if data is corrupted
        # (and have circular dependence in sections) 
        # limit to 10000
        for i in range(10000):
            yield ts
            ts = ts.find_next()
            if not ts:
                break

    def reset_thread_section_sort_order(self):
        for (i,ts) in enumerate(list(self.all_thread_section_generator())):
            ts.sort_order=i
            ts.save()

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = Course.objects\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(Course, self).save(*args, **kwargs)

    # save course as a new course
    # copy course thread content
    # not users
    def save_as_new(self, code, name):

        from copy import copy

        new_course = copy(self)
        new_course.id = None
        
        new_course.code = code
        new_course.name = name
        new_course.last_attendance_date = None

        new_course.save()

        for cgc in self.coursegradecategory_set.all():
            cgc.id = None
            cgc.course = new_course
            cgc.save()


        for section in self.thread_sections.all():
            section.save_as_new(course=new_course)

        return new_course

            
            
    def shift_dates(self, n_days):
        """ 
        Shifts class dates and due dates of assignments by n_days days
        """
        
        timeshift = timezone.timedelta(days=n_days)

        with transaction.atomic(), reversion.create_revision():
            self.start_date += timeshift
            self.end_date += timeshift
            self.save()

            for tc in self.thread_contents.all():
                if tc.assigned:
                    tc.assigned += timeshift
                if tc.initial_due:
                    tc.initial_due += timeshift
                if tc.final_due:
                    tc.final_due += timeshift
                if tc.assigned or tc.initial_due or tc.final_due:
                    tc.save()

    def enrolled_students_ordered(self, active_only=True, section=None):
        student_enrollments = self.courseenrollment_set.filter(role=STUDENT_ROLE)
        if active_only:
            student_enrollments = student_enrollments.filter(withdrew=False)
        if section:
            student_enrollments = student_enrollments.filter(section=section)
        
        return self.enrolled_students.filter(courseenrollment__in=student_enrollments).order_by('user__last_name', 'user__first_name')

    def points_for_grade_category(self, grade_category):

        point_list = []
        for tc in self.thread_contents\
                .filter(grade_category=grade_category):
            total_points = tc.points
            if total_points:
                point_list.append(total_points)

        point_list.sort()
        
        n = grade_category.number_count_for_grade
        if n is not None and n < len(point_list):
            point_list = point_list[-n:]
        
        return sum(point_list)*grade_category.rescale_factor


    def all_assessments_by_category(self):
        grade_categories=[]
        for cgc in self.coursegradecategory_set.all():

            cgc_assessments = []
            number_assessments = 0
            for tc in self.thread_contents\
                    .filter(grade_category=cgc):
                tc_points = tc.points
                if tc_points:
                    number_assessments += 1
                    assessment_results =  \
                    {'content': tc,
                     'assessment': tc.content_object,
                     'points': tc_points,
                     }
                    cgc_assessments.append(assessment_results)

            category_points = self.points_for_grade_category(cgc)

            score_comment = ""
            if cgc.number_count_for_grade and \
                    cgc.number_count_for_grade < number_assessments:
                score_comment = "top %s of %s" % \
                    (cgc.number_count_for_grade, number_assessments)
            if cgc.rescale_factor != 1.0:
                if score_comment:
                    score_comment += ", "
                score_comment += "rescale %s%%" % \
                    (round(cgc.rescale_factor*1000)/10)
            if score_comment:
                score_comment = mark_safe("<br/><small style='font-weight:normal'>(%s)</small>"\
                                              % score_comment)

            cgc_results = {'category': cgc.grade_category,
                           'points': category_points,
                           'number_count': cgc.number_count_for_grade,
                           'rescale_factor': cgc.rescale_factor,
                           'score_comment': score_comment,
                           'number_assessments': number_assessments,
                           'assessments': cgc_assessments,
                           'number_assessments_plus_one': len(cgc_assessments)+1,
                           }
            grade_categories.append(cgc_results)

        return grade_categories
    
    def all_assessments_with_points(self):
        assessments = []
        # number_assessments = 0
        for tc in self.thread_contents.all():
            tc_points = tc.points
            if tc_points:
                # number_assessments += 1
                assessment_results =  \
                    {'content': tc, \
                         'assessment': tc.content_object, \
                         'points': tc_points, \
                         }
                assessments.append(assessment_results)


        return assessments
 

    def student_scores_by_grade_category(self, student=None):
        student_scores = []

        enrollment=None
        cgc = None
        student_categories = []
        total_student_score = 0
        category_score_results = []
        category_scores=[]
        
        include_details = student is not None


        def summarize_category(cgc, category_scores, category_score_results,
                               include_details=False):
            n_count = cgc.number_count_for_grade
            n_assessments = len(category_scores)
            if n_count is not None and n_count < n_assessments:
                category_student_score = sum(sorted(category_scores)[-n_count:])
            else:
                category_student_score = sum(category_scores)
            category_student_score *= cgc.rescale_factor
            category_results = {
                'category': cgc.grade_category,
                'student_score': category_student_score,
                'scores': category_score_results,
            }

            if include_details:
                category_points = self.points_for_grade_category(cgc)
                if category_student_score and category_points:
                    category_percent = category_student_score/category_points\
                                       *100
                else:
                    category_percent = 0

                score_comment = ""
                if n_count is not None and n_count < n_assessments:
                    score_comment = "top %s scores out of %s" % \
                        (n_count, n_assessments)
                if cgc.rescale_factor != 1.0:
                    if score_comment:
                        score_comment += " and "
                    score_comment += "rescaling by %s%%" % \
                        (round(cgc.rescale_factor*1000)/10)
                if score_comment:
                    score_comment = mark_safe(
                        "<br/><small>(based on %s)</small>" % score_comment)

                category_results['points'] = category_points
                category_results['percent'] = category_percent
                category_results['number_count'] = n_count
                category_results['rescale_factor'] = cgc.rescale_factor
                category_results['score_comment']= score_comment


            return category_results


        records = ContentRecord.objects.filter(content__course=self) \
            .exclude(content__points=None).exclude(content__points=0)

        # since starting with ContentRecord, could have records
        # associated with content that was deleted
        records = records.filter(content__deleted=False)
        if student:
            records = records.filter(enrollment__student=student) \
                .order_by('content__grade_category', 'content')

        else:
            records = records.filter(enrollment__role=STUDENT_ROLE) \
                .order_by('enrollment__student', 'content__grade_category',
                          'content')\
 

        for cr in records \
            .select_related('enrollment__student', 'content__grade_category'):

            if enrollment != cr.enrollment:
                # if have previous student, then record student results
                if enrollment:

                    category_results = summarize_category(
                        cgc, category_scores, category_score_results,
                        include_details=include_details)
                    student_categories.append(category_results)
                    total_student_score += category_results['student_score']

                    student_scores.append(
                        {'enrollment': enrollment,
                         'total_score': total_student_score,
                         'categories': student_categories
                     })
                category_score_results=[]
                category_scores=[]
                cgc = cr.content.grade_category
                student_categories=[]
                total_student_score=0
                enrollment=cr.enrollment
                
            elif cgc != cr.content.grade_category:
                # if have previous cgc, then compute totals
                if cgc:
                    category_results = summarize_category(
                        cgc, category_scores, category_score_results,
                        include_details=include_details)
                    student_categories.append(category_results)
                    total_student_score += category_results['student_score']

                category_score_results=[]
                category_scores=[]
                cgc = cr.content.grade_category
            
            tc=cr.content
            tc_points = tc.points
            if tc_points:
                assessment_results = {
                    'content': tc,
                    'assessment': tc.content_object,
                    'score': cr.score,}
                score_or_zero = cr.score
                if not score_or_zero:
                    score_or_zero=0
                if include_details:
                    percent = score_or_zero/tc_points*100
                    assessment_results['points'] = tc_points
                    assessment_results['percent'] = percent

                category_scores.append(score_or_zero)
                category_score_results.append(assessment_results)



        # compute totals for last student and cgc
        category_results = summarize_category(
            cgc, category_scores, category_score_results,
                        include_details=include_details)
        student_categories.append(category_results)
        total_student_score += category_results['student_score']

        # if specified student, then return results as just
        # a dictionary, with percent and points included
        if student:
            total_points = self.total_points()
            if total_points and total_student_score:
                total_percent = total_student_score/total_points*100
            else:
                total_percent = 0
            return {'categories': student_categories,
                    'total_points': total_points,
                    'total_score': total_student_score,
                    'total_percent': total_percent,
                }

        else:
            student_scores.append(
                {'enrollment': enrollment,
                 'total_score': total_student_score,
                 'categories': student_categories
             })
            return student_scores    
                    
    def total_points(self):
        total_points=0
        for cgc in self.coursegradecategory_set.all():
            total_points += self.points_for_grade_category(cgc)
        return total_points

    def total_student_score(self, student):
        total_score=0
        for cgc in self.coursegradecategory_set.all():
            total_score += self.student_score_for_grade_category\
                (cgc.grade_category, student)
        return total_score
        

    def content_for_grade_category(self, grade_category):
        return self.thread_contents\
            .filter(grade_category=grade_category)


    def generate_attendance_dates(self):
        
        days_of_week_python=[]
        if self.days_of_week:
            weekday_list =[item.strip() for item in self.days_of_week.split(",")]
            for wd in weekday_list:
                days_of_week_python.append(day_of_week_to_python(wd))
        
        if not days_of_week_python:
            return None

        initial_weekday = self.start_date.weekday()
        offsets = []
        for wd in days_of_week_python:
            offsets.append(timezone.timedelta((wd - initial_weekday) % 7))
        
        offsets.sort()
        
        max_weeks = 100
        week_start = self.start_date
        skip_dates = []
        for skipdate in self.courseskipdate_set.all():
            skip_dates.append(skipdate.date)

        # delete any old attendance dates
        self.attendancedate_set.all().delete()
        
        # add new attendance dates
        reached_end = False
        for i in range(max_weeks):
            for offset in offsets:
                new_date = week_start + offset
                if new_date > self.end_date:
                    reached_end = True
                    break
                if new_date not in skip_dates:
                    self.attendancedate_set.create(date = new_date)
            week_start += timezone.timedelta(7)

            if reached_end:
                break
        
        return self.attendancedate_set.count()


    def find_next_attendance_date(self, last_attendance_date=None):
        if not last_attendance_date:
            if self.last_attendance_date:
                last_attendance_date = self.last_attendance_date
            elif self.start_date:
                last_attendance_date = self.start_date - timezone.timedelta(1)
            else:
                return None

        try:
            return self.attendancedate_set.filter\
                (date__gt= last_attendance_date)[0].date
        except:
            return None

    def previous_week_end(self, date=None):

        tz = pytz.timezone(self.attendance_time_zone)

        if not date:
            date= tz.normalize(timezone.now().astimezone(tz)).date()
        else:
            try:
                date= tz.normalize(date.astimezone(tz)).date()
            except AttributeError:
                pass

        # find end of previous week
        week_end_day = day_of_week_to_python(self.attendance_end_of_week)
        # offset is number of days since previous week_end
        offset = (date.weekday()-1-week_end_day) % 7 +1

        previous_week_end = date - timezone.timedelta(offset)


        # find last attendance day at or before previous_week_end
        if self.days_of_week:
            weekday_list =[item.strip() for item in self.days_of_week.split(",")]
            min_offset = 7
            for wd in weekday_list:
                min_offset = min((week_end_day-day_of_week_to_python(wd)) % 7,
                                 min_offset)
                

            previous_week_end -= timezone.timedelta(min_offset)

            # if previous_week_end is a course skip day, 
            # find previous day of class, up to one week in past
            skipdate=False
            try:
                self.courseskipdate_set.get(date=previous_week_end)
                original_previous_week_end=previous_week_end
                skipdate=True
            except ObjectDoesNotExist:
                pass

            
            while skipdate:
                
                # find previous day of class before previous_week_end
                previous_week_end -= timezone.timedelta(1)
                previous_week_end_day = previous_week_end.weekday()
                
                min_offset = 7
                for wd in weekday_list:
                    min_offset = min((previous_week_end_day
                                      -day_of_week_to_python(wd)) % 7,
                                     min_offset)
                previous_week_end -= timezone.timedelta(min_offset)

                # if a week or more before original previous week end
                # then return result regardless of it being a skip day
                if original_previous_week_end - previous_week_end >= \
                        timezone.timedelta(7):
                    break
                
                # determine if is a skip date
                try:
                    self.courseskipdate_set.get(date=previous_week_end)
                except ObjectDoesNotExist:
                    skipdate=False
                
        return previous_week_end
        
    def last_attendance_day_previous_week(self, date=None):
        if not self.last_attendance_date:
            return None

        tz = pytz.timezone(self.attendance_time_zone)

        if not date:
            date= tz.normalize(timezone.now().astimezone(tz)).date()
        else:
            try:
                date= tz.normalize(date.astimezone(tz)).date()
            except AttributeError:
                pass


        previous_week_end = self.previous_week_end(date)
        
        return min(self.last_attendance_date, previous_week_end)


    def to_date_attendance_days(self, date=None, start_date=None):
        if not date:
            date = self.last_attendance_day_previous_week()
            if not date:
                return None
        if not start_date:
            start_date = self.start_date
            if not start_date:
                return None

        return self.attendancedate_set.filter(date__lte = date)\
            .filter(date__gte = start_date).count()


    def content_by_date(
            self, student, begin_date=None, end_date=None, 
            exclude_completed=True,  assessments_only=False,
            by_assigned=False):
        
        # create list of course content for student
        # sorted by adjusted due date or by assigned date
        # if begin_date and/or end_date, then show only those with 
        # date from begin_date until end_date
        # if exclude_completed, then exclude those a student marked complete
        # if assessments_only, then show only those with contenttype=assessment

        try:
            enrollment = self.courseenrollment_set.get(student=student)
        except ObjectDoesNotExist:
            return []

        content_list= self.thread_contents.all()

        if assessments_only:
            assessment_content_type = ContentType.objects.get\
                (app_label="micourses", model='assessment')
            content_list = content_list.filter \
                (thread_content__content_type=assessment_content_type)
    
        # if sorting by assigned date, then exclude those without assigned
        if by_assigned:
            content_list = content_list.exclude(assigned=None)

        # else, exclude content without an initial or final due date
        # since those cannot have an adjusted due date
        else:
            from django.db.models import Q
            content_list = content_list\
                .filter(~Q(initial_due=None)|~Q(final_due=None))

        if exclude_completed:
            content_list = content_list.exclude \
                (id__in=self.thread_contents.filter \
                     (contentrecord__enrollment=enrollment,
                      contentrecord__complete=True))

        # for each of content, calculate adjusted due date
        content_with_dates = []
        for content in content_list:
            initial_due = content.get_initial_due(student)
            adjusted_due = content.get_adjusted_due(student)
            assigned = content.assigned
            if not assigned:
                assigned = "--"
            if exclude_completed:
                completed=False
            else:
                try:
                    completed = content.contentrecord_set\
                                       .get(enrollment=enrollment).complete
                except ObjectDoesNotExist:
                    completed = False

            content_with_dates.append({
                'assigned': assigned,
                'initial_due': initial_due,
                'adjusted_due': adjusted_due,
                'thread_content': content, 
                'sort_order': content.sort_order,
                'score': content.student_score(student),
                'completed': completed,
            })

        if by_assigned:
            date_column='assigned'
        else:
            date_column='adjusted_due'

        # sort by appropriate date, then by content
        from operator import itemgetter
        content_with_dates.sort(key=itemgetter(date_column,'sort_order'))
        
        #remove content outside dates
        if begin_date:
            last_too_early_index=-1
            for (i, content) in enumerate(content_with_dates):
                if content[date_column] < begin_date:
                    last_too_early_index=i
                else:
                    break
        
            content_with_dates=content_with_dates[last_too_early_index+1:]
            
        if end_date:
            for (i, content) in enumerate(content_with_dates):
                if content[date_column] > end_date:
                    content_with_dates=content_with_dates[:i]
                    break

        return content_with_dates

    def next_items(self, student, number=5):
        # use subqueries with filter rather than exclude
        # to work around django bug 
        # https://code.djangoproject.com/ticket/14645
        # as suggested in
        # http://stackoverflow.com/questions/16704560/django-queryset-exclude-with-multiple-related-field-clauses
        return self.thread_contents\
            .exclude(optional=True)\
            .exclude(id__in=self.thread_contents.filter \
                         (contentrecord__enrollment__student=student,
                          contentrecord__complete=True))\
            .exclude(id__in=self.thread_contents.filter \
                         (contentrecord__enrollment__student=student,\
                              contentrecord__skip=True))[:number]


    def import_roster(self, filename):
        """
        Import course enrollment from csv file.
        Assume CSV file has these columns:
        ID, Last Name, First Name, Internet ID, Email, Section, Group
        (ID is for courseuser.userid, Internet ID is for username)

        All new users have unusuable passwords set

        """

        import csv

        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    u = User.objects.get(username=row[3])
                except ObjectDoesNotExist:
                    u=User.objects.create_user(username=row[3], email=row[4], 
                                        first_name=row[2], last_name=row[1])

                else:
                    u.email=row[4]
                    u.first_name=row[2]
                    u.last_name=row[1]
                    u.save()

                u.courseuser.userid=row[0]
                u.courseuser.save()

                try:
                    ce = self.courseenrollment_set.get(
                        student=u.courseuser)
                except ObjectDoesNotExist:
                    ce = self.courseenrollment_set.create(
                        student=u.courseuser,
                        section=row[5],
                        group=row[6]
                    )
                else:
                    ce.section=row[5]
                    ce.group=row[6]
                    ce.save()




class CourseURL(models.Model):
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=100)
    url = models.URLField()
    sort_order = models.FloatField(blank=True)

    class Meta:
        ordering = ['sort_order']

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.course.courseurl_set\
                    .aggregate(Max('sort_order'))['sort_order__max']

            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(CourseURL, self).save(*args, **kwargs)


class CourseEnrollment(models.Model):
    ROLE_CHOICES = (
        (STUDENT_ROLE, 'Student'),
        (INSTRUCTOR_ROLE, 'Instructor'),
        (DESIGNER_ROLE, 'Designer'),
    )
    course = models.ForeignKey(Course)
    student = models.ForeignKey(CourseUser)
    section = models.CharField(max_length=20, blank=True, null=True)
    group = models.CharField(max_length=20, blank=True, null=True)
    date_enrolled = models.DateTimeField(blank=True)
    withdrew = models.BooleanField(default=False)
    role = models.CharField(max_length=1,
                            choices = ROLE_CHOICES,
                            default = STUDENT_ROLE)


    def __str__(self):
        return "%s enrolled in %s" % (self.student, self.course)

    class Meta:
        unique_together = ("course","student")
        ordering = ['student']

    def save(self, *args, **kwargs):
        if not self.date_enrolled:
            self.date_enrolled = timezone.now()
        super(CourseEnrollment, self).save(*args, **kwargs)

        # create content records for all thread content of course
        # that has points
        for tc in self.course.thread_contents.exclude(points=None):
            tc.contentrecord_set.get_or_create(enrollment=self)


@reversion.register
class StudentAttendance(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment)
    date = models.DateField()
    present = models.SmallIntegerField(default=PRESENT)

    class Meta:
        unique_together = ['enrollment', 'date']


    def present_as_word(self):
        if self.present == PRESENT:
            return "Present"
        elif self.present == EXCUSED:
            return "Excused absence"
        else:
            return "Absent"
        


class NondeletedManager(models.Manager):
    use_for_related_fields=True
    def get_queryset(self):
        return super(NondeletedManager, self).get_queryset() \
            .filter(deleted=False)

class DeletedManager(models.Manager):
    def get_queryset(self):
        return super(DeletedManager, self).get_queryset() \
            .filter(deleted=True)

@reversion.register
class ThreadSection(models.Model):
    name =  models.CharField(max_length=200, db_index=True)
    course = models.ForeignKey(Course, related_name = "thread_sections", 
                               blank=True, null=True)
    parent = models.ForeignKey('self', related_name = "child_sections",
                               blank=True, null=True)
    sort_order = models.FloatField(blank=True)

    deleted = models.BooleanField(default=False, db_index=True)

    objects = NondeletedManager()
    deleted_objects = DeletedManager()
    all_objects = models.Manager()

    def __str__(self):
        return "Section: %s. Course: %s" % (self.name,self.get_course())

    class Meta:
        ordering = ['sort_order','id']

    def get_course(self):
        ancestor = self
        for i in range(10):
            if ancestor.course:
                return ancestor.course
            # allow ancestor to be deleted section
            # so doesn't break in this case
            ancestor = ThreadSection.all_objects.get(id=ancestor.parent_id)
            #ancestor=ancestor.parent
        return None

    def return_siblings(self):
        if self.course:
            return self.course.thread_sections.all()
        else:
            return self.parent.child_sections.all()

    def find_next_sibling(self):
        siblings = self.return_siblings()
        for (i,ts) in enumerate(siblings):
            if ts == self:
                break
        if i < siblings.count()-1:
            return siblings[i+1]
        else:
            return None

    def find_previous_sibling(self):
        siblings = self.return_siblings()
        for (i,ts) in enumerate(siblings):
            if ts == self:
                break
        if i > 0:
            return siblings[i-1]
        else:
            return None

    def find_next(self):
        first_child = self.child_sections.first()
        if first_child:
            return first_child
        
        ancestor = self
        for i in range(10):
            next_sibling = ancestor.find_next_sibling()
            if next_sibling:
                return next_sibling
            else:
                if ancestor.course is None:
                    ancestor = ancestor.parent
                else:
                    return None
        return None

    def find_previous(self):
        previous_sibling = self.find_previous_sibling()

        if not previous_sibling:
            if self.course:
                return None
            else:
                return self.parent

        # find last descendant of previous sibling
        # (or sibling if no descendants)
        descendant = previous_sibling
        for i in range(10):
            last_child = descendant.child_sections.last()
            if last_child:
                descendant = last_child
            else:
                return descendant

        return None

    def reset_thread_content_sort_order(self):
        for (i,tc) in enumerate(list(self.thread_contents.all())):
            tc.sort_order=i
            tc.save()


    def clean(self):
        # Check if course exists
        # If not, raise exception
        if self.section.get_course() is None:
            raise ValidationError( \
                "Thread section does not have course: %s" % self)

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            if self.course:
                max_sort_order = self.course.thread_sections\
                    .aggregate(Max('sort_order'))['sort_order__max']
            else:
                max_sort_order = self.parent.child_sections\
                    .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(ThreadSection, self).save(*args, **kwargs)


    def mark_deleted(self):
        with transaction.atomic(), reversion.create_revision():
            # could get in an infinite loop here
            for child_section in self.child_sections.all():
                child_section.mark_deleted()
            for thread_content in self.thread_contents.all():
                thread_content.mark_deleted()
            self.deleted=True
            self.save()

    def save_as_new(self, course=None, parent=None):
        """
        Save to a new thread section with new course or parent.

        Then save all child sections as new sections.
        Does this recursively and doesn't check for infinite loops.

        Saves all thread content as new content.

        """
        from copy import copy

        new_section = copy(self)
        new_section.id = None
        
        new_section.course = course
        new_section.parent = parent

        new_section.save()

        for section in self.child_sections.all():
            section.save_as_new(parent=new_section)

        for content in self.thread_contents.all():
            content.save_as_new(section=new_section)

        return new_section
    

@reversion.register
class ThreadContent(models.Model):
    AGGREGATE_CHOICES = (
        ('Max', 'Maximum'),
        ('Avg', 'Average'),
        ('Las', 'Last'),
    )

    section = models.ForeignKey(ThreadSection, related_name="thread_contents")

    # Redundant in that should be able to determine course from section.
    # However, the direct link allows queryset of all content of course
    course = models.ForeignKey(Course, related_name="thread_contents")

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    substitute_title = models.CharField(max_length=200, blank=True, null=True)

    comment = models.CharField(max_length=200, blank=True, default="")
    instructions = models.TextField(blank=True, null=True)

    assigned=models.DateTimeField(blank=True, null=True)
    initial_due=models.DateTimeField(blank=True, null=True)
    final_due=models.DateTimeField(blank=True, null=True)

    grade_category = models.ForeignKey(CourseGradeCategory, 
                                       blank=True, null=True)
    points = models.FloatField(blank=True, null=True)
    attempt_aggregation = models.CharField(max_length=3,
                                           choices = AGGREGATE_CHOICES,
                                           default = 'Max')


    individualize_by_student = models.BooleanField(default=True)
    optional = models.BooleanField(default=False)
    available_before_assigned = models.BooleanField(default=False)
    record_scores = models.BooleanField(default=True)
    
    n_of_object=models.SmallIntegerField(default=1)
    
    sort_order = models.FloatField(blank=True)

    deleted = models.BooleanField(default=False, db_index=True)

    objects = NondeletedManager()
    deleted_objects = DeletedManager()
    all_objects = models.Manager()

    
    
    class Meta:
        ordering = ['section', 'sort_order', 'id']

    def __str__(self):
        return "%s for %s" % (self.content_object, self.course)


    def save(self, *args, **kwargs):
        # Set course to be course of section.
        # Allow section to be a deleted section so this doesn't break
        section = ThreadSection.all_objects.get(id=self.section_id)
        self.course=section.get_course()

        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = section.thread_contents\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1

        # if points changed, should recalculate score of content records
        # and if newly has nonzero points, create content records
        points_changed = False
        newly_with_points = bool(self.points)
        if self.pk is not None:
            old_tc = ThreadContent.objects.get(pk=self.pk)
            if old_tc.points != self.points:
                points_changed=True
                if old_tc.points:
                    newly_with_points=False
            else:
                newly_with_points=False

        super(ThreadContent, self).save(*args, **kwargs)

        from micourses.utils import set_n_of_objects
        set_n_of_objects(self.course, self.content_object)

        if points_changed:
            for record in self.contentrecord_set.all():
                record.recalculate_score(total_recalculation=True)

        if newly_with_points:
            for ce in self.course.courseenrollment_set.all():
                self.contentrecord_set.get_or_create(enrollment=ce)



    def get_title(self):
        if(self.substitute_title):
            return self.substitute_title
        else:
            try:
                return self.content_object.get_title()
            except:
                return str(self.content_object)


    def return_link(self):
        if self.n_of_object > 1:
            get_string="n=%s" % self.n_of_object
        else:
            get_string=""
        try:
            if self.substitute_title:
                return self.content_object.return_link(
                    link_text=self.substitute_title,
                    get_string=get_string)
            else:
                return self.content_object.return_link(get_string=get_string)
        except:
            return self.get_title()


    def find_previous(self, in_section=False):
        if in_section:
            tcs = self.section.thread_contents.all()
        else:
            tcs = self.course.thread_contents.all()
        for (i,tc) in enumerate(tcs):
            if tc == self:
                break
        if i > 0:
            return tcs[i-1]
        else:
            return None

    def find_next(self, in_section=False):
        if in_section:
            tcs = self.section.thread_contents.all()
        else:
            tcs = self.course.thread_contents.all()
        for (i,tc) in enumerate(tcs):
            if tc == self:
                break
        if i < tcs.count()-1:
            return tcs[i+1]
        else:
            return None

    def mark_deleted(self):
        with transaction.atomic(), reversion.create_revision():
            self.deleted=True
            self.save()


    def return_availability(self, student=None):
        """
        Returns availablity of ThreadContent based on
        when assigned and initially due

        If student, then these adjustments are included:
        - adjustments from attendance
        - adjustments in student content record

        Availabilty does not take into account privacy settings.
        
        """

        now = timezone.now()

        if not self.available_before_assigned:

            assigned = self.assigned
            if not assigned:
                return NOT_YET_AVAILABLE

            if student:
                try:
                    record = self.contentrecord_set.get(
                        enrollment__student=student)
                except ObjectDoesNotExist:
                    pass
                else:
                     if record.assigned_adjustment:
                         assigned = record.assigned_adjustment

            if now < assigned:
                return NOT_YET_AVAILABLE

        due = self.get_adjusted_due(student)
        if not due or now <= due:
            return AVAILABLE

        return PAST_DUE


    def save_as_new(self, section):
        """
        Save to a new thread content with new parent section.
        Determine course from section.

        For any content objects that are assessments,
        if assessment for course exists, point to that assessment
        else save a new copy of the assessment with the course.

        """
        from copy import copy

        new_content = copy(self)
        new_content.id = None
        
        new_content.section = section
        new_content.course = section.get_course()
        
        assessment_ct = ContentType.objects.get_for_model(Assessment)
        if self.content_type == assessment_ct:
            old_assessment = self.content_object
            try:
                # check if the assessment for this course exists already
                new_assessment = Assessment.objects.get(
                    course=new_content.course,
                    code = old_assessment.code)
            except Assessment.DoesNotExist:
                # if not, create a new copy
                new_assessment = old_assessment.save_as_new(
                    course=new_content.course)
            new_content.object_id = new_assessment.id

        new_content.save()

        return new_content
        

    def student_score(self, student):
        try:
            return self.contentrecord_set.get(enrollment__student=student).score
        except ObjectDoesNotExist:
            return None

    def get_student_latest_attempt(self, student):
        try:
            return self.contentrecord_set.get(enrollment__student=student)\
                .attempts.latest()
        except ObjectDoesNotExist:
            return None
    
    def latest_student_attempts(self):
        latest_attempts=[]
        for student in self.course.enrolled_students_ordered():
            content_record=None
            attempt=None
            number_attempt=0

            try:
                content_record =  self.contentrecord_set.get(
                    enrollment__student=student)
            except ObjectDoesNotExist:
                pass
            else:
                try:
                    attempt = content_record.attempts.latest()
                except ObjectDoesNotExist:
                    pass
                else:
                    number_attempts=content_record.attempts.count()

            latest_attempts.append({
                    'student': student,
                    'attempt': attempt,
                    'current_score': self.student_score(student),
                    'adjusted_due': self.get_adjusted_due(student),
                    'number_attempts': number_attempts
                    })
        return latest_attempts
        

    def attempt_aggregation_string(self):
        if self.attempt_aggregation=='Avg':
            return "Average"
        elif self.attempt_aggregation=='Las':
            return "Last"
        else:
            return "Maximum"


    def get_initial_due(self, student=None):
        if not student:
            return self.initial_due

        adjustment = None
        try:
            adjustment = self.contentrecord_set.get(
                enrollment__student=student).initial_due_adjustment
        except ObjectDoesNotExist:
            pass

        if adjustment:
            return adjustment
        else:
            return self.initial_due

    def get_final_due(self, student=None):
        if not student:
            return self.final_due

        adjustment = None
        try:
            adjustment = self.contentrecord_set.get(
                enrollment__student=student).final_due_adjustment
        except:
            pass
        if adjustment:
            return adjustment
        else:
            return self.final_due

    def get_adjusted_due(self, student=None):
        # adjust when due in increments of weeks
        # based on percent attendance at end of each previous week

        # if only one of initial due or final due is specified,
        # use that one
        
        # if no student specified, use initial due

        due = self.get_initial_due(student)
        final_due = self.get_final_due(student)

        if not due:
            if not final_due:
                return None
            else:
                return final_due
        elif not final_due:
            return due
        
        if not student:
            return due
            
        now = timezone.now()
        
        course = self.course        
        while due < now + timezone.timedelta(days=7):
            previous_week_end = \
                course.previous_week_end(due)

            # only update if have attendance through previous_week_end
            if not course.last_attendance_date \
                    or course.last_attendance_date < previous_week_end:
                break

            if student.percent_attendance \
                    (course=course, date=previous_week_end) \
                    < course.attendance_threshold_percent:
                break
            
            due += timezone.timedelta(days=7)
            if due >= final_due:
                due = final_due
                break

        return due



    def adjusted_due_calculation(self, student):
        # return data for calculation of adjust due date
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        due = self.get_initial_due(student)
        final_due = self.get_final_due(student)
        
        if not due or not final_due:
            return []

        now = timezone.now()

        course = self.course        
        
        calculation_list = []
        while due < now + timezone.timedelta(days=7):

            previous_week_end = \
                course.previous_week_end(due)

            calculation = {'initial_date': due,
                           'previous_week_end': previous_week_end,
                           'attendance_data': False,
                           'attendance_percent': None,
                           'reached_threshold': False,
                           'resulting_date': due,
                           'reached_latest': False,
                           }

            # only update if have attendance through previous_week_end
            if not course.last_attendance_date \
                    or course.last_attendance_date < previous_week_end:
                calculation_list.append(calculation)
                break

            calculation['attendance_data']=True

            attendance_percent = student.percent_attendance \
                    (course=course, date=previous_week_end)
            calculation['attendance_percent'] = round(attendance_percent,1)

            if attendance_percent < course.attendance_threshold_percent:
                calculation_list.append(calculation)
                break

            calculation['reached_threshold'] = True
            
            due += timezone.timedelta(7)
            if due >= final_due:
                due = final_due
                calculation['resulting_date'] = due
                calculation['reached_latest'] = True
                calculation_list.append(calculation)
                break

            calculation['resulting_date'] = due
            calculation_list.append(calculation)

        return calculation_list


@reversion.register
class ContentRecord(models.Model):

    # null enrollment indicates record for coursewide attempts
    enrollment = models.ForeignKey(CourseEnrollment, null=True)
    content = models.ForeignKey(ThreadContent)

    complete = models.BooleanField(default=False)
    skip = models.BooleanField(default=False)
    created = models.DateTimeField(blank=True, default=timezone.now)
    last_modified = models.DateTimeField(blank=True)
    score = models.FloatField(blank=True, null=True)
    score_override = models.FloatField(blank=True, null=True)

    assigned_adjustment = models.DateTimeField(blank=True, null=True)
    initial_due_adjustment = models.DateTimeField(blank=True, null=True)
    final_due_adjustment = models.DateTimeField(blank=True, null=True)

    fields_to_dump = ["score_override", "assigned_adjustment",
                      "initial_due_adjustment", "final_due_adjustment"]


    def __str__(self):
        if self.enrollment:
            return "Record for %s on %s" % (self.enrollment.student, self.content)
        else:
            return "Course record on %s" % (self.content)
            

    class Meta:
        unique_together = ['enrollment', 'content']


    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_last_modified', False):
            self.last_modified = timezone.now()

        cuser = kwargs.pop("cuser", None)
    
        # if changed score override, then recalculate score
        score_override_changed=True
        date_changed=True
        new_record = False
        old_cr=None

        if self.pk is None:
            new_record=True
        else:
            old_cr = ContentRecord.objects.get(pk=self.pk)
            if self.score_override == old_cr.score_override:
                score_override_changed = False

            if old_cr.assigned_adjustment==self.assigned_adjustment and \
               old_cr.initial_due_adjustment==self.initial_due_adjustment and \
               old_cr.final_due_adjustment==self.final_due_adjustment:
                date_changed=False
                

        with transaction.atomic(), reversion.create_revision():
            super(ContentRecord, self).save(*args, **kwargs)

        if score_override_changed:
            self.recalculate_score()

            if new_record:
                action="create"
            else:
                action="change score"

            from micourses.utils import json_dump_fields
            ChangeLog.objects.create(
                courseuser=cuser,
                content_type=ContentType.objects.get(app_label="micourses",
                                                     model="contentrecord"),
                object_id=self.id,
                action=action,
                old_value= json_dump_fields(old_cr),
                new_value=json_dump_fields(self),
            )

        elif date_changed:

            from micourses.utils import json_dump_fields
            ChangeLog.objects.create(
                courseuser=cuser,
                content_type=ContentType.objects.get(app_label="micourses",
                                                     model="contentrecord"),
                object_id=self.id,
                action="change date",
                old_value=json_dump_fields(old_cr),
                new_value=json_dump_fields(self),
            )
            
            

    def recalculate_score(self, total_recalculation=False):
        """
        Recalculate score of student for content.

        Set to score_override if it exists and to None if not assessment.
        Also set to None if no valid content attempt with nonblank score

        Else score is aggregate of scores from each valid attempt 
        for student on this thread_content.
        Aggregate based on attempt_aggregration of thread_content.


        
        If total_recalculation, then first recalculate
        the scores of each attempt.  Otherwise, just use the
        score field from each attempt.

        """

        if total_recalculation:
            for attempt in self.attempts.all():
                attempt.recalculate_score(propagate=False,
                                          total_recalculation=True)

        # if score is overridden, then just set set score to score_override
        if self.score_override is not None:
            self.score = self.score_override
            self.save()
            return self.score

        # must be an assessment 
        assessment_ct=ContentType.objects.get(app_label="micourses", model='assessment')
        if self.content.content_type != assessment_ct:
            self.score = None
            self.save()
            return self.score


        valid_attempts = self.attempts.filter(valid=True)

        if not valid_attempts:
            self.score=None
            self.save()
            return None


        valid_nonblank_attempts = valid_attempts.exclude(score=None)
        if not valid_nonblank_attempts:
            self.score=None
            self.save()
            return None
                
        if self.content.attempt_aggregation=='Avg':
            # calculate average score of attempts
           self.score = valid_attempts.aggregate(score = Avg('score'))['score']
        elif self.content.attempt_aggregation=='Las':
            # calculate score of last attempt
            self.score = valid_attempts.latest('datetime').score
        else:
            # calculate maximum score over all attempts
            self.score = valid_attempts.aggregate(score=Max('score'))['score']

        self.save()

        return self.score


@reversion.register
class ContentAttempt(models.Model):
    record = models.ForeignKey(ContentRecord, related_name="attempts")
    attempt_began = models.DateTimeField(blank=True, default=timezone.now)
    score_override = models.FloatField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    seed = models.CharField(max_length=150, blank=True, null=True)
    valid = models.BooleanField(default=True, db_index=True)
    version = models.CharField(max_length=100, default="")

    # for showing that an attempt is derived off a coursewide attempt
    # (an attempt with record.enrollment=None)
    base_attempt = models.ForeignKey('self', null=True, related_name="derived_attempts")

    fields_to_dump = ["score_override", "valid", "seed", "version"]


    def __str__(self):
        if self.record.enrollment:
            return "%s's attempt on %s" % (self.record.enrollment.student,
                                           self.record.content)
        else:
            return "Course attempt on %s" % (self.record.content)

    class Meta:
        ordering = ['attempt_began']
        get_latest_by = "attempt_began"
        


    def save(self, *args, **kwargs):
        cuser = kwargs.pop("cuser", None)

        # if new attempt, or changed score override or valid, 
        # then recalculate score
        new_attempt=False
        score_override_changed=True
        valid_changed=True
        old_ca=None

        if self.pk is None:
            new_attempt=True
        else:
            old_ca = ContentAttempt.objects.get(pk=self.pk)
            if self.score_override == old_ca.score_override:
                score_override_changed=False
            if self.valid == old_ca.valid:
                valid_changed=False

        with transaction.atomic(), reversion.create_revision():
            super(ContentAttempt, self).save(*args, **kwargs)

        if score_override_changed or valid_changed:
            self.recalculate_score()
            
            if new_attempt:
                action="create"
            elif score_override_changed:
                action="change score"
            else:
                action="change"

            from micourses.utils import json_dump_fields

            ChangeLog.objects.create(
                courseuser=cuser,
                content_type=ContentType.objects.get(app_label="micourses",
                                                     model="contentattempt"),
                object_id=self.id,
                action=action,
                old_value=json_dump_fields(old_ca),
                new_value=json_dump_fields(self),
            )



    def return_url(self, question_number=None):
        get_string="content_attempt=%s" % self.id

        if self.record.content.n_of_object > 1:
            get_string+="&n=%s" % self.record.content.n_of_object

        return "%s?%s" % (self.record.content.content_object.get_absolute_url(
            question_number=question_number),
                          get_string)

    def return_link(self):
        get_string="content_attempt=%s" % self.id

        if self.record.content.n_of_object > 1:
            get_string+="&n=%s" % self.record.content.n_of_object
        try:
            if self.substitute_title:
                return self.content_object.return_link(
                    link_text=self.substitute_title,
                    get_string=get_string)
            else:
                return self.content_object.return_link(get_string=get_string)
        except:
            return self.get_title()

    def get_fraction_credit(self):
        if self.score is None or self.record.content.points is None:
            return None
        return self.score/self.record.content.points

    def get_percent_credit(self):
        if self.score is None or self.record.content.points is None:
            return None
        return self.score/self.record.content.points*100


    def recalculate_score(self, propagate=True, total_recalculation=False):
        """
        Recalculate score of student content attempt.
        
        Set to score_override if it exists and to None if not assessment.
        Also set to None if no question set have a non blank credit.

        Else, score is sum of the score from each associated question set
        Score of a question set is its credited multiplied by a fraction
        of the points of the thread content.
        The fraction of points is the relative magnitude of the question
        set weight, as determined by the question set details of assessment.

        If propagate and attempt is valid,
        then also calculate overall score for student content.

        If total_recalculation, then also calculate the credit 
        for each question attempt (assuming score not overridden)

        """

        if total_recalculation:
            question_sets = self.question_sets\
                                .prefetch_related('question_attempts')
            for question_set in question_sets:
                for qa in question_set.question_attempts.all():
                    qa.recalculate_credit(propagate=False)

        # if score is overridden, then just set set score to score_override
        if self.score_override is not None:
            self.score = self.score_override

        else:
            # must be an assessment 
            assessment_ct=ContentType.objects.get(app_label="micourses", 
                                                  model='assessment')
            if self.record.content.content_type != assessment_ct or \
               self.record.content.points is None:
                self.score = None
            else:
                assessment = self.record.content.content_object
                question_set_details = assessment.questionsetdetail_set
                question_sets = self.question_sets.all()
                
                found_non_blank_credit = False
                
                if question_sets:
                    total_weight = 0.0
                    self.score = 0.0
                    for question_set in question_sets:
                        try:
                            weight = question_set_details.get(
                                question_set=question_set.question_set).weight
                        except ObjectDoesNotExist:
                            weight = 1
                        qs_credit=question_set.get_credit()
                        if qs_credit is None:
                            qs_credit=0
                        else:
                            found_non_blank_credit = True
                        self.score += qs_credit*weight
                        total_weight += weight
                    self.score *= self.record.content.points/total_weight
                    
                if not found_non_blank_credit:
                    self.score = None
        
        self.save()

        if propagate:
            self.record.recalculate_score()

        return self.score


    def get_latest_activity_time(self):
        latest_time = self.attempt_began

        for question_set in self.question_sets.all()\
            .prefetch_related('question_attempts'):

            try:
                latest_time = max(
                    latest_time, question_set.question_attempts\
                    .filter(valid=True).latest().get_latest_activity_time())
            except ObjectDoesNotExist:
                pass

        return latest_time

    def return_activity_interval(self):
        # return time attempt began and latest time of activity
        # if difference between is less than a minute, 
        # then return None for second

        latest_activity = self.get_latest_activity_time()
        if latest_activity-self.attempt_began >= timezone.timedelta(minutes=1):
            return (self.attempt_began, latest_activity)
        else:
            return (self.attempt_began, None)


    def create_derived_attempt(self, content_record, score=None, valid=True):
        new_attempt=content_record.attempts.create(
            attempt_began=self.attempt_began,
            score_override = score,
            seed=self.seed, valid=valid, version=self.version,
            base_attempt=self)
        for qs in self.question_sets.all():
            new_qs = new_attempt.question_sets.create(
                question_number = qs.question_number,
                question_set = qs.question_set)
            qa = qs.question_attempts.latest()
            new_qa = new_qs.question_attempts.create(
                question=qa.question,
                seed=qa.seed,
                random_outcomes=qa.random_outcomes,
                attempt_began=qa.attempt_began)

        return new_attempt


@reversion.register
class ContentAttemptQuestionSet(models.Model):
    content_attempt = models.ForeignKey(ContentAttempt,
                                        related_name="question_sets")
    question_number = models.SmallIntegerField()
    question_set = models.SmallIntegerField()

    credit_override = models.FloatField(blank=True, null=True)

    fields_to_dump = ["credit_override", "question_number",
                      "question_set"]

    class Meta:
        ordering = ['question_number']
        unique_together = [('content_attempt', 'question_number'),
                           ('content_attempt', 'question_set')]



    def save(self, *args, **kwargs):
        cuser = kwargs.pop("cuser", None)
    
        # if changed credit override, then recalculate score of question attempt
        credit_override_changed=True
        old_qs=None
        new_qs = False
        
        if self.pk is None:
            new_qs=True
        else:
            old_qs = ContentAttemptQuestionSet.objects.get(pk=self.pk)
            if self.credit_override == old_qs.credit_override:
                credit_override_changed=False

        with transaction.atomic(), reversion.create_revision():
            super(ContentAttemptQuestionSet, self).save(*args, **kwargs)

        if credit_override_changed:
            self.content_attempt.recalculate_score()

            if new_qs:
                action="create"
            else:
                action="change score"
            
            from micourses.utils import json_dump_fields
            ChangeLog.objects.create(
                courseuser=cuser,
                content_type=ContentType.objects.get(app_label="micourses",
                                            model="contentattemptquestionset"),
                object_id=self.id,
                action=action,
                old_value=json_dump_fields(old_qs),
                new_value=json_dump_fields(self),
            )


    def get_credit(self):
        """
        Get credit of question set for content attempt.

        The credit earned is aggregate over all question attempts,
        where aggregate function is determined from thread_content.

        Return credit_override if set.

        Return None if no valid question_attempts
        but return 0 if have valid question attempts, but just no credit

        """
        if self.credit_override:
            return self.credit_override

        question_attempts = self.question_attempts.filter(valid=True)

        if not question_attempts:
            return None

        content = self.content_attempt.record.content

        if content.attempt_aggregation=='Avg':
            credit = question_attempts.aggregate(credit=Avg('credit'))\
                     ['credit']
        elif content.attempt_aggregation=='Las':
            credit = question_attempts.latest('datetime').credit
        else:
            credit = question_attempts.aggregate(credit=Max('credit'))\
                     ['credit']
                
        # since have valid question attempts, make credit 0 rather than None
        if credit is None:
            return 0
        else:
            return credit


    def get_points(self):
        """"
        Determines points of question set by adding up weights
        of all question sets of assessment to determine relative
        weight of this question set, then multiplying by total points.
        """
    
        total_points = self.content_attempt.record.content.points

        # must be an assessment 
        assessment_ct=ContentType.objects.get(app_label="micourses", 
                                              model='assessment')

        if self.content_attempt.record.content.content_type != assessment_ct \
           or total_points is None:
            return
        

        assessment = self.content_attempt.record.content.content_object
        question_set_details = assessment.questionsetdetail_set

        question_sets = self.content_attempt.question_sets.all()
        total_weight = 0.0
        this_weight = None
        for question_set in question_sets:
            try:
                weight = question_set_details.get(
                    question_set=question_set.question_set).weight
            except ObjectDoesNotExist:
                weight = 1
            total_weight += weight
            if question_set == self:
                this_weight = weight

        points = this_weight/total_weight*total_points

        return points


    def return_activity_interval(self):
        # return time attempt began and latest time of activity
        # if difference between is less than a minute, 
        # then return None for second

        try:
            latest_activity = self.question_attempts.filter(valid=True)\
                                        .latest().get_latest_activity_time()
            attempt_began = self.question_attempts.filter(valid=True)\
                                                  .earliest().attempt_began
        except ObjectDoesNotExist:
            return (self.content_attempt.attempt_began, None)

        if latest_activity-attempt_began >= timezone.timedelta(minutes=1):
            return (attempt_began, latest_activity)
        else:
            return (attempt_began, None)

@reversion.register
class QuestionAttempt(models.Model):
    content_attempt_question_set = models.ForeignKey(
        ContentAttemptQuestionSet, related_name="question_attempts")
    question = models.ForeignKey('mitesting.Question')
    seed = models.CharField(max_length=150)
    random_outcomes = models.TextField(null=True)
    attempt_began = models.DateTimeField(blank=True, default=timezone.now)
    valid = models.BooleanField(default=True, db_index=True)

    solution_viewed = models.DateTimeField(blank=True, null=True)

    credit = models.FloatField(blank=True, null=True)


    class Meta:
        ordering = ['attempt_began']
        get_latest_by = "attempt_began"

    def __str__(self):
        qs = self.content_attempt_question_set
        if qs.content_attempt.record.enrollment:
            return "%s's attempt on question %s of %s" % \
                (qs.content_attempt.record.enrollment.student, \
                 qs.question_number, qs.content_attempt.record.content)
        else:
            return "Course attempt on question %s of %s" % \
                (qs.question_number, qs.content_attempt.record.content)

    def recalculate_credit(self, propagate=True):
        """
        Recalculate credit of question attempt according to attempt
        aggregation of content

        Credit is calculated from valid responses.
        If have no valid responses, then credit is None

        If propagate, also recalculate score for content attempt

        """

        responses = self.responses.filter(valid=True)

        content_attempt = self.content_attempt_question_set.content_attempt

        if not responses:
            self.credit=None
        else:
        
            content = content_attempt.record.content

            if content.attempt_aggregation=='Avg':
                self.credit = responses.aggregate(credit=Avg('credit'))\
                         ['credit']
            elif content.attempt_aggregation=='Las':
                self.credit = responses.latest('datetime').credit
            else:
                self.credit = responses.aggregate(credit=Max('credit'))\
                         ['credit']

        self.save()
        
        if propagate:
            content_attempt.recalculate_score()

        return self.credit

    def get_latest_activity_time(self):
        try:
            latest_response = self.responses.filter(valid=True).latest()
        except ObjectDoesNotExist:
            return self.attempt_began
        else:
            return max(self.attempt_began, latest_response.response_submitted)

    def return_activity_interval(self):
        # return time attempt began and latest time of activity
        # if difference between is less than a minute, 
        # then return None for second

        latest_activity = self.get_latest_activity_time()
        if latest_activity-self.attempt_began >= timezone.timedelta(minutes=1):
            return (self.attempt_began, latest_activity)
        else:
            return (self.attempt_began, None)


class QuestionResponse(models.Model):
    question_attempt = models.ForeignKey(QuestionAttempt,
                                         related_name="responses")
    response = models.TextField()
    credit = models.FloatField()
    response_submitted =  models.DateTimeField(blank=True, default=timezone.now)
    valid = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return  "%s" % self.response

    class Meta:
        ordering = ['question_attempt', 'response_submitted']
        get_latest_by = "response_submitted"

    def save(self, *args, **kwargs):
        super(QuestionResponse, self).save(*args, **kwargs)

        self.question_attempt.recalculate_credit()



class AssessmentType(models.Model):
    PRIVACY_CHOICES = (
        (0, 'Public'),
        (1, 'Logged in users'),
        (2, 'Instructors only'),
        )

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    assessment_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES, 
                                             default=2)
    solution_privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,
                                                default=2)
    template_base_name = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return  self.name



class Assessment(models.Model):
    code = models.SlugField(max_length=200, db_index=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=30, blank=True, null=True)
    assessment_type = models.ForeignKey(AssessmentType)
    course = models.ForeignKey('micourses.Course')
    thread_content_set = GenericRelation('micourses.ThreadContent')
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    questions = models.ManyToManyField('mitesting.Question', through='QuestionAssigned',
                                       blank=True)
    instructions = models.TextField(blank=True, null=True)
    instructions2 = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    groups_can_view = models.ManyToManyField(Group, blank=True, 
                            related_name = "assessments_can_view")
    groups_can_view_solution = models.ManyToManyField(Group, blank=True, 
                            related_name = "assessments_can_view_solution")
    background_pages = models.ManyToManyField('midocs.Page', 
                            through='AssessmentBackgroundPage', blank=True)
    allow_solution_buttons = models.BooleanField(default=True)
    fixed_order = models.BooleanField(default=False)
    single_version = models.BooleanField(default=False)
    resample_question_sets = models.BooleanField(default=False)


    class Meta:
        ordering = ["code",]
        unique_together = (("course", "code"), ("course", "name"),)

    def __str__(self):
        return "%s (Assessment: %s)" % (self.code, self.name)


    def return_short_name(self):
        if self.short_name:
            return self.short_name
        else:
            return self.name

    def get_title(self):
        return self.name

    def annotated_title(self):
        return "%s: %s" % (self.assessment_type.name,self.name)

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "assessment")
        get_string=kwargs.get("get_string", "")

        direct = kwargs.get("direct")
        if direct:
            link_url = self.get_absolute_url()
        
            seed = kwargs.get("seed")
            if seed is not None:
                link_url += "?seed=%s" % seed
                if get_string:
                    link_url += "&" + get_string
            elif get_string:
                link_url += "?" + get_string
        else:
            link_url = self.get_overview_url()
            if get_string:
                link_url += "?" + get_string

        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))


    def return_direct_link(self, **kwargs):
        kwargs['direct']=True
        return self.return_link(**kwargs)

    @models.permalink
    def get_absolute_url(self, question_number=None):
        if question_number is None:
            return('miassess:assessment', (), {'course_code': self.course.code,
                                               'assessment_code': self.code})
        else:
            return('miassess:assessment_question', (), 
                   {'course_code': self.course.code,
                    'assessment_code': self.code,
                    'question_only': question_number})


    @models.permalink
    def get_overview_url(self):
        return('miassess:assessment_overview', (), {'course_code': self.course.code,
                                                    'assessment_code': self.code})

    @models.permalink
    def get_solution_url(self):
        return('miassess:assessment_solution', (), {'course_code': self.course.code,
                                                    'assessment_code': self.code})


    def clean(self):
        """
        Check if course has changed.
        If course has changed and already have student activity on
        assessment, then raise validation error

        """
        
        if self.pk:
            orig = Assessment.objects.get(pk=self.pk)
        else:
            orig = None

        if orig and self.course != orig.course:

            found_student_activity = False
            from micourses.utils import check_for_student_activity
            for content in self.thread_content_set.filter(course=orig.course):
                if check_for_student_activity(content):
                    found_student_activity=True
                    break

            if found_student_activity:
                raise ValidationError('Cannot change course of %s from %s to %s since it already has student activity' % (self, orig.course, self.course))






    def save(self, *args, **kwargs):
        """
        Make sure assigned questions as from assessment's course

        If question's course if different, then save question as new question
        unless course already has a question that is
        1. derived from this question or
        2. derived from this question's base question.
        In that case, instead of creating new question, switch to said question.
        """

        super(Assessment, self).save(*args, **kwargs)

        for qa in self.questionassigned_set.all():
            if qa.question.course != self.course:
                
                # find related question
                q=self.course.question_set.filter(base_question=qa.question)\
                                          .first()
                if not q and qa.question.base_question:
                    q=self.course.question_set.filter(
                        base_question = qa.question.base_question).first()
                if q:
                    qa.question = q
                else:
                    qa.question = qa.question.save_as_new(course=self.course)

                qa.save()

    def determine_thread_content(self, number_in_thread=1):
        """
        Determine the thread content of the assessment.

        Return the thread content.
        
        If assessment is not in thread and number in thread is 1,
        then return None

        Otherwise, if thread content is not found, raise ObjectDoesExist exception
        """
        
        try: 
            number_in_thread = int(number_in_thread)
        except TypeError:
            number_in_thread = 1

        try:
            return self.thread_content_set.all()[number_in_thread-1]
        except (IndexError, ValueError, AssertionError):
            if number_in_thread==1 and \
               not self.thread_content_set.all():
                return None
            else:
                raise ThreadContent.DoesNotExist


    def user_can_view(self, user, solution=True, include_questions=True):
        from micourses.permissions import return_user_assessment_permission_level
        permission_level=return_user_assessment_permission_level(
            user, self.course)
        privacy_level=self.return_privacy_level(
            solution=solution, include_questions=include_questions)
        # if permission level is high enough, user can view
        if permission_level >= privacy_level:
            return True
        
        # else check if user is in one of the groups 
        allowed_users=self.return_users_of_groups_can_view(solution)
        if user in allowed_users:
            return True
        else:
            return False

    def return_users_of_groups_can_view(self, solution=False):
        if solution:
            allowed_groups= self.groups_can_view_solution.all()
        else:
            allowed_groups= self.groups_can_view.all()
        allowed_users = []
        for group in allowed_groups:
            allowed_users += list(group.user_set.all())
        return allowed_users

    def return_privacy_level(self, solution=True, include_questions=True):
        # privacy level is max of privacy level from assessment type
        # and (if include_questions==True) all question sets
        if solution:
            privacy_level = self.assessment_type.solution_privacy
        else:
            privacy_level = self.assessment_type.assessment_privacy
        if include_questions:
            for question in self.questions.all():
                privacy_level = max(privacy_level, 
                                    question.return_privacy_level(solution))
        return privacy_level
    
    def privacy_level_description(self, solution=False):
        """
        Returns description of the privacy of the assessment or solution.
        using the words of the PRIVACY_CHOICES from AssessmentType.
        Also includes statements alerting to the following situations:
        - If the privacy level was increased from that of the assessment type
          due to a higher privacy level associated with a question
        - If a privacy override will allow some groups to view a non-public
          assessment or solution.
        """
        privacy_level = self.return_privacy_level(solution=solution)
        privacy_description= AssessmentType.PRIVACY_CHOICES[privacy_level][1]
        privacy_description_addenda = []
        if privacy_level > self.return_privacy_level(solution=solution, 
                                                     include_questions=False):
            privacy_description_addenda.append(
                "increased due to an assigned question")
        
        if (solution and self.groups_can_view_solution.exists()) or \
                (not solution and self.groups_can_view.exists()):
            if privacy_level > 0:
                privacy_description_addenda.append("overridden for some groups")

        if privacy_description_addenda:
            privacy_description += " (%s)" %\
                ", ".join(privacy_description_addenda)
        
        return privacy_description
    privacy_level_description.short_description = "Assessment privacy"


    def privacy_level_solution_description(self):
        return self.privacy_level_description(solution=True)
    privacy_level_solution_description.short_description = "Solution privacy"

    def render_instructions(self):
        if not self.instructions:
            return ""
        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base + self.instructions
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions template: %s" % e

    def render_instructions2(self):
        if not self.instructions2:
            return ""
        template_string_base = "{% load testing_tags mi_tags humanize %}"
        template_string=template_string_base + self.instructions2
        try:
            t = Template(template_string)
            return mark_safe(t.render(Context({})))
        except TemplateSyntaxError as e:
            return "Error in instructions2 template: %s" % e


    def question_sets(self):
        question_set_dicts= self.questionassigned_set.order_by('question_set').values('question_set').distinct()
        question_sets = []
        for question_set_dict in question_set_dicts:
            question_sets.append(question_set_dict['question_set'])
        return question_sets


    def avoid_question_seed(self, avoid_dict, start_seed=None):

        import random
        rng=random.Random()
        rng.seed(start_seed)

        question_sets = self.question_sets()

        min_penalty=1000000
        best_seed=None

        from .render_assessments import get_question_list
        from mitesting.utils import get_new_seed

        import time
        t0=time.process_time()

        for iter in range(1000):

            seed = get_new_seed(rng)

            # force fixed order for speed
            question_list=get_question_list(self, seed=seed, rng=rng, 
                                            questions_only=True)

            penalty = 0 

            for q_dict in question_list:
                penalty += avoid_dict.get(q_dict['question'].id,0)

            if penalty==0:
                return seed

            if penalty < min_penalty:
                min_penalty = penalty
                best_seed = seed

                
        print(time.process_time()-t0)
            
        return best_seed
                    

    def save_as_new(self, name = None, code=None, course=None):
        """
        Create a new assessment and copy all fields to new assessment.

        Must either have a new name and code or be assigned to a different course.
        (Otherwise, will violate uniqueness constraint.)
        
        If course changed, then save questions as new questions
        unless course already has a question that is
        1. derived from this question
        2. this question's base question
        3. derived from this question's base question.
        In that case, instead of creating new question, switch to said question.

        """

        from copy import copy

        new_a = copy(self)
        new_a.id = None
        
        if name:
            new_a.name = name
        if code:
            new_a.code = code

        course_changed=False
        if course:
            if course != new_a.course:
                course_changed=True
            new_a.course = course

        new_a.save()
        
        for qa in self.questionassigned_set.all():
            qa.id = None
            qa.assessment = new_a

            # find related question or create new one
            if course_changed:
                qa.question=qa.question.find_replacement_question_for_course(
                    course)

            qa.save()

        for gcv in self.groups_can_view.all():
            new_a.groups_can_view.add(gcv)
        for gcv in self.groups_can_view_solution.all():
            new_a.groups_can_view_solution.add(gcv)

        for bp in self.assessmentbackgroundpage_set.all():
            bp.id = None
            bp.assessment = new_a
            bp.save()
            
        for qsd in self.questionsetdetail_set.all():
            qsd.id = None
            qsd.assessment = new_a
            qsd.save()

        return new_a



class AssessmentBackgroundPage(models.Model):
    assessment = models.ForeignKey(Assessment)
    page = models.ForeignKey('midocs.Page')
    sort_order = models.FloatField(blank=True)

    class Meta:
        ordering = ['sort_order']
    def __str__(self):
        return "%s for %s" % (self.page, self.assessment)

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.assessment.assessmentbackgroundpage_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(AssessmentBackgroundPage, self).save(*args, **kwargs)

class QuestionSetDetail(models.Model):
    assessment = models.ForeignKey(Assessment)
    question_set = models.SmallIntegerField(db_index=True)
    weight = models.FloatField(default=1)
    group = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        unique_together = ("assessment", "question_set")
    def __str__(self):
        return "%s for %s" % (self.question_set, self.assessment)


class QuestionAssigned(models.Model):
    assessment = models.ForeignKey(Assessment)
    question = models.ForeignKey('mitesting.Question')
    question_set = models.SmallIntegerField(blank=True)

    class Meta:
        verbose_name_plural = "Questions assigned"
        ordering = ['question_set', 'id']
    def __str__(self):
        return "%s for %s" % (self.question, self.assessment)

    def save(self, *args, **kwargs):
        # if the question set is null
        # make it be a unique question set,
        # i.e., one more than any other in the assessment
        if self.question_set is None:
            max_question_set = self.assessment.questionassigned_set.aggregate(Max('question_set'))
            max_question_set = max_question_set['question_set__max']
            if max_question_set:
                self.question_set = max_question_set+1
            else:
                self.question_set = 1

        # if question isn't from assessment's course
        # then find related question from course or create new question
        if self.question.course != self.assessment.course:
            self.question = self.question.find_replacement_question_for_course(
                self.assessment.course)

        super(QuestionAssigned, self).save(*args, **kwargs)
