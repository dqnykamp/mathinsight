from django.db import models
from django.db.models import Sum, Max, Avg
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.conf import settings
from math import ceil
import pytz

STUDENT_ROLE = 'S'
INSTRUCTOR_ROLE = 'I'
NOT_YET_AVAILABLE = 0
AVAILABLE = 1
PAST_DUE = -1


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

class CourseUser(models.Model):
    user = models.OneToOneField(User)
    userid = models.CharField(max_length=20, blank=True, null=True)
    selected_course_enrollment = models.ForeignKey(
        'CourseEnrollment', blank=True, null=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

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
    

    def get_current_role(self):
        if self.selected_course_enrollment:
            return self.selected_course_enrollment.role

    def return_permission_level(self):
        if not self.selected_course_enrollment:
            return None

        role = self.selected_course_enrollment.role

        if role == INSTRUCTOR_ROLE:
            return 2
        else:
            return 1
        

    def percent_attendance(self, course=None, date=None):
        if not course:
            try:
                course = self.return_selected_course()
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None

        if date:
            try:
                with timezone.override(self.attendance_time_zone):
                    date = date.date()
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
        
        n_excused_absenses = attendance_data.filter(present = -1).count()
        
        days_attended = attendance_data.exclude(present = -1)\
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

    def save_to_new_course(self, course):
        new_coursegradecategory = self
        new_coursegradecategory.pk = None
        new_coursegradecategory.course = course
        new_coursegradecategory.save()
    

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
    adjust_due_date_attendance = models.BooleanField(default=False)
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
    # also create new thread
    def save_as(self, new_code, new_name, new_thread_code, new_thread_name):
        original_code = self.code

        thread = self.thread
        new_thread = thread.save_as(new_thread_code, new_thread_name)
    
        new_course = self
        new_course.pk = None
        new_course.code = new_code
        new_course.name = new_name
        new_course.thread = new_thread
        new_course.last_attendance_date = None
        new_course.save()
        
        original_course = Course.objects.get(code=original_code)
        
        for ca_category in original_course.coursegradecategory_set.all():
            ca_category.save_to_new_course(new_course)


        for course_thread_content in \
            original_course.thread_contents.all():
            
            course_thread_content.save_to_new_course(new_course, new_thread)
            
            
    def shift_dates(self, n_days):
        """ 
        Shifts class dates and due dates of assignments by n_days days
        """
        
        timeshift = timezone.timedelta(days=n_days)

        self.start_date += timeshift
        self.end_date += timeshift
        self.save()

        for tc in self.thread_contents.all():
            if tc.assigned_date:
                tc.assigned_date += timeshift
            if tc.initial_due_date:
                tc.initial_due_date += timeshift
            if tc.final_due_date:
                tc.final_due_date += timeshift
            if tc.assigned_data or tc.initial_due_date or tc.final_due_date:
                tc.save()

    def enrolled_students_ordered(self, active_only=True, section=None):
        student_enrollments = self.courseenrollment_set.filter(role=STUDENT_ROLE)
        if active_only:
            student_enrollments = student_enrollments.filter(withdrew=False)
        if section:
            student_enrollments = student_enrollments.filter(section=section)
        
        return self.enrolled_students.filter(courseenrollment__in=student_enrollments).order_by('user__last_name', 'user__first_name')

    def points_for_grade_category(self, grade_category):
        try:
            cgc=self.coursegradecategory_set.get\
                (grade_category=grade_category)
        except ObjectDoesNotExist:
            return 0
        

        point_list = []
        for ctc in self.thread_contents\
                .filter(grade_category=grade_category):
            total_points = ctc.total_points()
            if total_points:
                point_list.append(total_points)

        point_list.sort()
        
        n = cgc.number_count_for_grade
        if n is not None and n < len(point_list):
            point_list = point_list[-n:]
        
        return sum(point_list)*cgc.rescale_factor


    def all_assessments_by_category(self):
        grade_categories=[]
        for cgc in self.coursegradecategory_set.all():

            cgc_assessments = []
            number_assessments = 0
            for ctc in self.thread_contents\
                    .filter(grade_category=cgc.grade_category):
                ctc_points = ctc.total_points()
                if ctc_points:
                    number_assessments += 1
                    assessment_results =  \
                    {'content': ctc,
                     'assessment': ctc.content_object,
                     'points': ctc_points,
                     }
                    cgc_assessments.append(assessment_results)

            category_points = self.points_for_grade_category \
                               (cgc.grade_category)

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
        for ctc in self.thread_contents.all():
            ctc_points = ctc.total_points()
            if ctc_points:
                # number_assessments += 1
                assessment_results =  \
                    {'content': ctc, \
                         'assessment': ctc.content_object, \
                         'points': ctc_points, \
                         }
                assessments.append(assessment_results)


        return assessments
 
    def student_score_for_grade_category(self, grade_category,
                                              student):
        try:
            cgc=self.coursegradecategory_set.get\
                (grade_category=grade_category)
        except ObjectDoesNotExist:
            return 0
        
        score_list = []
        for ctc in self.thread_contents\
                .filter(grade_category=grade_category):
            total_score = ctc.student_score(student)
            if total_score:
                score_list.append(total_score)

        score_list.sort()
        
        n = cgc.number_count_for_grade
        if n is not None and n < len(score_list):
            score_list = score_list[-n:]
        return sum(score_list)*cgc.rescale_factor
 

    def student_scores_for_grade_category(self, student, cgc):

        cgc_assessments = []
        for ctc in self.thread_contents\
                .filter(grade_category=cgc.grade_category):
            ctc_points = ctc.total_points()
            if ctc_points:
                student_score = ctc.student_score(student)
                if student_score:
                    percent = student_score/ctc_points*100
                else:
                    percent = 0
                assessment_results =  \
                {'content': ctc,
                 'assessment': ctc.content_object,
                 'points': ctc_points,
                 'student_score': student_score,
                 'percent': percent,
                 }
                cgc_assessments.append(assessment_results)
        return cgc_assessments

    def student_scores_by_grade_category(self, student):
        scores_by_category = []
        for cgc in self.coursegradecategory_set.all():

            cgc_assessments = self.student_scores_for_grade_category(\
                                                            student, cgc)
            number_assessments=len(cgc_assessments)

            category_points = self.points_for_grade_category \
                               (cgc.grade_category)
            category_student_score = \
                self.student_score_for_grade_category \
                (cgc.grade_category, student)
            if category_student_score and category_points:
                category_percent = category_student_score/category_points*100
            else:
                category_percent = 0

            score_comment = ""
            if cgc.number_count_for_grade and \
                    cgc.number_count_for_grade < number_assessments:
                score_comment = "top %s scores out of %s" % \
                    (cgc.number_count_for_grade, number_assessments)
            if cgc.rescale_factor != 1.0:
                if score_comment:
                    score_comment += " and "
                score_comment += "rescaling by %s%%" % \
                    (round(cgc.rescale_factor*1000)/10)
            if score_comment:
                score_comment = mark_safe("<br/><small>(based on %s)</small>"\
                                              % score_comment)

            cgc_results = {'category': cgc.grade_category,
                           'points': category_points,
                           'student_score': category_student_score,
                           'percent': category_percent,
                           'number_count': cgc.number_count_for_grade,
                           'rescale_factor': cgc.rescale_factor,
                           'score_comment': score_comment,
                           'assessments': cgc_assessments,
                           }
            scores_by_category.append(cgc_results)
        total_points = self.total_points()
        total_student_score = self.total_student_score(student)
        if total_points and total_student_score:
            total_percent = total_student_score/total_points*100
        else:
            total_percent = 0
        return {'scores': scores_by_category,
                'total_points': total_points,
                'total_student_score': total_student_score,
                'total_percent': total_percent,
                }
    
    def all_student_scores_by_grade_category(self):
        student_scores = []
        for student in self.enrolled_students_ordered():
            student_categories = []
            for cgc in self.coursegradecategory_set.all():
                category_scores = []
                for ctc in self.thread_contents\
                    .filter(grade_category=cgc.grade_category):
                    ctc_points = ctc.total_points()
                    if ctc_points:
                        student_score = ctc.student_score(student)
                        assessment_results =  \
                            {'content': ctc,
                             'assessment': ctc.content_object,
                             'score': student_score,}
                        category_scores.append(assessment_results)
                category_student_score = \
                    self.student_score_for_grade_category \
                    (cgc.grade_category, student)
                student_categories.append({'category': cgc.grade_category,
                                           'category_score': \
                                               category_student_score,
                                           'scores': category_scores})

            student_scores.append({'student': student,
                                   'section': self.courseenrollment_set.get(student=student).section,
                                   'total_score': \
                                       self.total_student_score(student),
                                   'categories': student_categories})
        return student_scores    
                    
    def total_points(self):
        total_points=0
        for cgc in self.coursegradecategory_set.all():
            total_points += self.points_for_grade_category\
                (cgc.grade_category)
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

        with timezone.override(self.attendance_time_zone):
            if not date:
                date = timezone.now().date()
            else:
                try:
                    date = date.date()
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

        with timezone.override(self.attendance_time_zone):
            if not date:
                date = timezone.now().date()
            else:
                try:
                    date = date.date()
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


    def course_content_by_adjusted_due_date \
            (self, student, begin_date=None, end_date=None, \
                 exclude_completed=True, \
                 assessments_only=False):
        
        # create list of course content for student sorted by adjusted due date
        # if begin_date and/or end_date, then show only those with 
        # adjusted due date from begin_date until end_date
        # if exclude_completed, then exclude those a student marked complete
        # if assessments_only, then show only those with contenttype=assessment

        content_list= self.thread_contents.all()

        if assessments_only:
            assessment_content_type = ContentType.objects.get\
                (model='assessment')
            content_list = content_list.filter \
                (thread_content__content_type=assessment_content_type)
    
        # exclude content without an initial or final due date
        # since those cannot have an adjusted due date
        content_list = content_list.exclude(final_due_date=None)\
            .exclude(initial_due_date=None)

        if exclude_completed:
            content_list = content_list.exclude \
                (id__in=self.thread_contents.filter \
                     (studentcontentcompletion__student=student,
                      studentcontentcompletion__complete=True))

        # for each of content, calculate adjusted due date
        adjusted_due_date_content = []
        for coursecontent in content_list:
            adjusted_due_date = coursecontent.adjusted_due_date(student)
            adjusted_due_date_content.append((adjusted_due_date,coursecontent, coursecontent.sort_order))

        # sort by adjusted due date, then by coursecontent
        from operator import itemgetter
        adjusted_due_date_content.sort(key=itemgetter(0,2))
        
        #remove content outside dates
        if begin_date:
            last_too_early_index=-1
            for (i, coursecontent) in enumerate(adjusted_due_date_content):
                if adjusted_due_date_content[i][0] < begin_date:
                    last_too_early_index=i
                else:
                    break
        
            adjusted_due_date_content=adjusted_due_date_content\
                [last_too_early_index+1:]
            
        if end_date:
            for (i, coursecontent) in enumerate(adjusted_due_date_content):
                if adjusted_due_date_content[i][0] > end_date:
                    adjusted_due_date_content=adjusted_due_date_content[:i]
                    break

        return adjusted_due_date_content

    def next_items(self, student, number=5):
        # use subqueries with filter rather than exclude
        # to work around django bug 
        # https://code.djangoproject.com/ticket/14645
        # as suggested in
        # http://stackoverflow.com/questions/16704560/django-queryset-exclude-with-multiple-related-field-clauses
        return self.thread_contents\
            .exclude(optional=True)\
            .exclude(id__in=self.thread_contents.filter \
                         (studentcontentcompletion__student=student,
                          studentcontentcompletion__complete=True))\
            .exclude(id__in=self.thread_contents.filter \
                         (studentcontentcompletion__student=student,\
                              studentcontentcompletion__skip=True))[:number]


class CourseURLs(models.Model):
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=100)
    url = models.URLField()


class CourseEnrollment(models.Model):
    ROLE_CHOICES = (
        (STUDENT_ROLE, 'Student'),
        (INSTRUCTOR_ROLE, 'Instructor'),
    )
    course = models.ForeignKey(Course)
    student = models.ForeignKey(CourseUser)
    section = models.IntegerField(blank=True, null=True)
    group = models.SlugField(max_length=20, blank=True, null=True)
    date_enrolled = models.DateField()
    withdrew = models.BooleanField(default=False)
    role = models.CharField(max_length=1,
                            choices = ROLE_CHOICES,
                            default = STUDENT_ROLE)


    def __str__(self):
        return "%s enrolled in %s" % (self.student, self.course)

    class Meta:
        unique_together = ("course","student")
        ordering = ['student']

        
class StudentAttendance(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment)
    date = models.DateField()
    # 0: absent, 1: present, -1: excused absense
    present = models.FloatField(default=1.0)

    class Meta:
        unique_together = ['enrollment', 'date']



class NondeletedManager(models.Manager):
    use_for_related_fields=True
    def get_queryset(self):
        return super(NondeletedManager, self).get_queryset() \
            .filter(deleted=False)

class DeletedManager(models.Manager):
    def get_queryset(self):
        return super(DeletedManager, self).get_queryset() \
            .filter(deleted=True)

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
            ancestor=ancestor.parent
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
        for thread_content in self.thread_contents.all():
            thread_content.mark_deleted()
        self.deleted=True
        self.save()


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

    instructions = models.TextField(blank=True, null=True)

    assigned=models.DateTimeField(blank=True, null=True)
    initial_due=models.DateTimeField(blank=True, null=True)
    final_due=models.DateTimeField(blank=True, null=True)

    grade_category = models.ForeignKey(GradeCategory, blank=True, null=True)
    points = models.FloatField(blank=True, null=True)
    attempt_aggregation = models.CharField(max_length=3,
                                           choices = AGGREGATE_CHOICES,
                                           default = 'Max')


    individualize_by_student = models.BooleanField(default=True)
    optional = models.BooleanField(default=False)
    available_before_assigned = models.BooleanField(default=False)
    record_scores = models.BooleanField(default=True)

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
        # set course to be course of section
        self.course=self.section.get_course()

        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.section.thread_contents\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(ThreadContent, self).save(*args, **kwargs)

    def get_title(self):
        if(self.substitute_title):
            return self.substitute_title
        else:
            try:
                return self.content_object.get_title()
            except:
                return str(self.content_object)


    def return_link(self):
        try:
            if self.substitute_title:
                return self.content_object.return_link(
                    link_text=self.substitute_title)
            else:
                return self.content_object.return_link() 
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
            if student:
                try:
                    record = self.studentcontentrecordset_get(
                        enrollment__student=student)
                except ObjectDoesNotExist:
                    pass
                else:
                     if record.assigned_adjustment:
                         assigned = record.assigned_adjustment
           
            if now < assigned:
                return NOT_YET_AVAILABLE

        due = self.adjusted_due(student)
        if now <= due:
            return AVAILABLE

        return PAST_DUE


    def save_to_new_course(self, course, thread):
        original_pk = self.pk

        new_content = self
        new_content.pk = None
        new_content.course = course

        old_thread_content = self.thread_content
        old_thread_section = old_thread_content.section
        new_thread_section = thread.thread_sections.get(
            code = old_thread_section.code)
        # use filter rather than get, as it is possible to have 
        # same content_object appear multiple times
        # in that case, just take first one
        new_thread_content = new_thread_section.thread_contents.filter(
            content_type = old_thread_content.content_type,
            object_id = old_thread_content.object_id)[0]
        new_content.thread_content = new_thread_content
        new_content.save()


    def student_score(self, student):
        try:
            return self.studentcontentrecord_set.get(student=student).score
        except ObjectDoesNotExist:
            return None

    def get_student_latest_attempt(self, student):
        try:
            return self.studentcontentattempt_set.filter(student=student)\
                .latest()
        except ObjectDoesNotExist:
            return None
    
    def latest_student_attempts(self):
        latest_attempts=[]
        for student in self.course.enrolled_students_ordered():
            latest_attempts.append({
                    'student': student,
                    'attempt': self.get_student_latest_attempt(student),
                    'current_score': self.student_score(student),
                    'adjusted_due_date': self.adjusted_due_date(student),
                    'number_attempts': self.studentcontentattempt_set.filter(student=student).count(),
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
            adjustment = self.studentcontentrecord_set.get(
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
            adjustment = self.studentcontentrecord_set.get(
                enrollment__student=student).final_due_adjustment
        except:
            pass
        if adjustment:
            return adjustment
        else:
            return self.final_due

    def adjusted_due(self, student=None):
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



    def adjusted_due_date_calculation(self, student):
        # return data for calculation of adjust due date
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        due_date = self.get_initial_due_date(student)
        final_due_date = self.get_final_due_date(student)
        
        if not due_date or not final_due_date:
            return []

        today = timezone.now().date()

        course = self.course        
        
        calculation_list = []
        while due_date < today + timezone.timedelta(7):

            previous_week_end = \
                course.previous_week_end(due_date)

            calculation = {'initial_date': due_date,
                           'previous_week_end': previous_week_end,
                           'attendance_data': False,
                           'attendance_percent': 'NA',
                           'reached_threshold': False,
                           'resulting_date': due_date,
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
            
            due_date += timezone.timedelta(7)
            if due_date >= final_due_date:
                due_date = final_due_date
                calculation['resulting_date'] = due_date
                calculation['reached_latest'] = True
                calculation_list.append(calculation)
                break

            calculation['resulting_date'] = due_date
            calculation_list.append(calculation)

        return calculation_list


class StudentContentRecord(models.Model):
    enrollment = models.ForeignKey(CourseEnrollment)
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


    def __str__(self):
        return "Record for %s on %s" % (self.enrollment.student, self.content)

    class Meta:
        unique_together = ['enrollment', 'content']

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_last_modified', False):
            self.last_modified = timezone.now()

        # if changed score override, then recalculate score
        score_override_changed=True
        if self.pk is not None:
            old_scc = StudentContentRecord.objects.get(pk=self.pk)
            if self.score_override == old_scc.score_override:
                score_override_changed = False

        super(StudentContentRecord, self).save(*args, **kwargs)

        if score_override_changed:
            self.recalculate_score()


    def recalculate_score(self, total_recalculation=False):
        """
        Recalculate score of student for content.

        Set to score_override if it exists and to None if not assessment.
        Else score is aggregate of scores from each valid attempt 
        for student on this thread_content.
        Aggregate based on attempt_aggregration of thread_content.
        
        If total_recalculation, then first recalculate
        the scores of each attempt.  Otherwise, just use the
        score field from each attempt.

        """

        # if score is overridden, then just set set score to score_override
        if self.score_override is not None:
            self.score = self.score_override
            self.save()
            return self.score

        # must be an assessment 
        assessment_ct=ContentType.objects.get(model='assessment')
        if self.content.content_type != assessment_ct:
            self.score = None
            self.save()
            return self.score

        valid_attempts = self.attempts.filter(valid=True)

        if total_recalculation:
            for attempt in valid_attempts:
                attempt.recalculate_score(propagate=False,
                                          total_recalculation=True)
                
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



class ContentAttempt(models.Model):
    record = models.ForeignKey(StudentContentRecord, related_name="attempts")
    attempt_began = models.DateTimeField(blank=True, default=timezone.now)
    score_override = models.FloatField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    seed = models.CharField(max_length=150, blank=True, null=True)
    valid = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return "%s's attempt on %s" % (self.record.enrollment.student,
                                     self.record.content)

    class Meta:
        ordering = ['attempt_began']
        get_latest_by = "attempt_began"
        
    def save(self, *args, **kwargs):
        # if changed score override, then recalculate score
        score_override_changed=True
        if self.pk is not None:
            old_sca = ContentAttempt.objects.get(pk=self.pk)
            if self.score_override == old_sca.score_override:
                score_override_changed=False

        super(ContentAttempt, self).save(*args, **kwargs)

        if score_override_changed:
            self.recalculate_score()
            

    def get_percent_credit(self):
        points = self.content.total_points()
        if self.score is None or points is None:
            return None
        return int(round(self.score*100.0/points))


    def recalculate_score(self, propagate=True, total_recalculation=False):
        """
        Recalculate score of student content attempt.
        
        Set to score_override if it exists and to None if not assessment.
        Else, score is sum of scores from each associated question set.

        If propagate and attempt is valid,
        then also calculate overall score for student content.

        If total_recalculation, then also calculate the credit 
        for each question attempt (assuming score not overridden)

        """

        # if score is overridden, then just set set score to score_override
        if self.score_override is not None:
            self.score = self.score_override

        else:
            # must be an assessment 
            assessment_ct=ContentType.objects.get(model='assessment')
            if self.record.content.content_type != assessment_ct:
                self.score = None
            else:
                assessment = self.record.content.content_object
                question_set_details = assessment.questionsetdetail_set
                if total_recalculation:
                    question_sets = self.question_sets\
                                        .prefetch_related('question_attempts')
                else:
                    question_sets = self.question_sets.all()
                if question_sets:
                    total_weight = 0.0
                    self.score = 0.0
                    for question_set in questions_sets:
                        if total_recalculation:
                            for qa in question_set.question_attempts.all():
                                qa.recalculate_credit(propagate=False)
                                
                        try:
                            weight = question_set_details.get(
                                question_set.question_set).weight
                        except ObjectDoesNotExist:
                            weight = 1
                        self.score += question_set.get_credit()*weight
                        total_weight += weight
                    self.score *= record.content.points/total_weight
                    
                else: 
                    self.score = None
        
        self.save()

        if propagate and self.valid:
            self.record.recalculate_score()

        return self.score


    def get_percent_credit_question_set(self, question_set):
        question_answers = self.questionstudentanswer_set\
            .filter(question_set=question_set)

        if question_answers:

            if self.content.attempt_aggregation=='Avg':
                credit = question_answers.aggregate(credit=Avg('credit'))\
                         ['credit']
            elif self.content.attempt_aggregation=='Las':
                credit = question_answers.latest('datetime').credit
            else:
                credit = question_answers.aggregate(credit=Max('credit'))\
                         ['credit']
                
            return int(round(credit*100))
        else:
            return 0


    def get_latest_datetime(self):
        assessment=self.content.content_object
        # must be an assessment 
        from mitesting.models import Assessment
        if not isinstance(assessment,Assessment):
            return None
        

        try:
            return self.questionstudentanswer_set.all()\
                .latest('datetime').datetime
        except ObjectDoesNotExist:
            return self.datetime

    def have_datetime_interval(self):
        # true if difference between earliest and latest datetimes
        # is at least a minute
        latest_datetime = self.get_latest_datetime()
        if latest_datetime and latest_datetime -self.datetime \
                >= timezone.timedelta(0,60):
            return True
        else:
            return False


class ContentAttemptQuestionSet(models.Model):
    content_attempt = models.ForeignKey(ContentAttempt,
                                        related_name="question_sets")
    #remove null
    question_number = models.SmallIntegerField(blank=True, null=True)
    question_set = models.SmallIntegerField()
    

    class Meta:
        ordering = ['question_number']
        unique_together = [('content_attempt', 'question_number'),
                           ('content_attempt', 'question_set')]

    def get_credit(self):
        """
        Get credit of question set for content attempt.

        The credit earned is aggregate over all question attempts,
        where aggregate function is determined from thread_content 

        """
        question_attempts = self.question_attempts.all()

        if not question_attempts:
            return 0

        content = self.content_attempt.record.content

        if content.attempt_aggregation=='Avg':
            credit = question_attempts.aggregate(credit=Avg('credit'))\
                     ['credit']
        elif content.attempt_aggregation=='Las':
            credit = question_attempts.latest('datetime').credit
        else:
            credit = question_attempts.aggregate(credit=Max('credit'))\
                     ['credit']
                
        return credit


class QuestionAttempt(models.Model):
    # to delete
    content_attempt = models.ForeignKey(ContentAttempt,
                                        related_name="question_attempts",
                                        null=True)
    question_set = models.SmallIntegerField(null=True)

    # remove null
    content_attempt_question_set = models.ForeignKey(
        ContentAttemptQuestionSet, related_name="question_attempts",
        null=True)
    question = models.ForeignKey('mitesting.Question', null=True)
    seed = models.CharField(max_length=150)
    random_outcomes = models.TextField(null=True)
    attempt_began = models.DateTimeField(blank=True, default=timezone.now)
    valid = models.BooleanField(default=True, db_index=True)

    solution_viewed = models.DateTimeField(blank=True, null=True)

    credit = models.FloatField(default=0)


    class Meta:
        ordering = ['attempt_began']
        get_latest_by = "attempt_began"

        
    def __str__(self):
        qs = self.content_attempt_question_set
        return "%s's attempt on question %s of %s" % \
            (qs.content_attempt.record.enrollment.student, \
             qs.question_number, qs.content_attempt.record.content)

    def recalculate_credit(self, propagate=True):
        """
        Recalculate credit of question attempt according to attempt
        aggregation of content
        
        If propagate, also recalculate score for content attempt

        """

        responses = self.responses.filter(post_solution_view=False)

        content_attempt = self.content_attempt_question_set.content_attempt

        if not responses:
            credit=0
        else:
        
            content = content_attempt.record.content

            if content.attempt_aggregation=='Avg':
                credit = responses.aggregate(credit=Avg('credit'))\
                         ['credit']
            elif content.attempt_aggregation=='Las':
                credit = responses.latest('datetime').credit
            else:
                credit = responses.aggregate(credit=Max('credit'))\
                         ['credit']

        self.save()

        if propagate:
            content_attempt.recalculate_score()

        return self.credit



class QuestionResponse(models.Model):
    #to delete
    question = models.ForeignKey('mitesting.Question', null=True)
    seed = models.CharField(max_length=150, null=True)
    question_set = models.SmallIntegerField(null=True)
    content_attempt = models.ForeignKey(ContentAttempt, null=True)

    # remove null
    question_attempt = models.ForeignKey(QuestionAttempt,
                                         related_name="responses", null=True)
    response = models.TextField()
    identifier_in_response = models.CharField(max_length=50)
    credit = models.FloatField()
    response_submitted =  models.DateTimeField(blank=True, default=timezone.now)
    valid = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return  "%s" % self.response

    class Meta:
        ordering = ['response_submitted']
        get_latest_by = "response_submitted"

    def save(self, *args, **kwargs):
        super(QuestionResponse, self).save(*args, **kwargs)

        self.question_attempt.recalculate_credit()
