from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.db import models
from django.db.models import Sum, Max, Avg
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
import datetime
from django.conf import settings
from math import ceil

STUDENT_ROLE = 'S'
INSTRUCTOR_ROLE = 'I'

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
    selected_course_enrollment = models.ForeignKey(
        'CourseEnrollment', blank=True, null=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __unicode__(self):
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
        if not date:
            date = course.last_attendance_day_previous_week()
            if not date:
                return None
        
        date_enrolled = self.courseenrollment_set.get(course=course)\
            .date_enrolled
        course_days = course.to_date_attendance_days(date, 
                                                     start_date=date_enrolled)
        
        attendance_data = self.studentattendance_set.filter(course=course)\
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
    


class GradeLevel(models.Model):
    grade = models.CharField(max_length=1, unique=True)
    
    def __unicode__(self):
        return self.grade

class AssessmentCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Assessment categories'


class CourseAssessmentCategory(models.Model):
    course = models.ForeignKey('Course')
    assessment_category = models.ForeignKey(AssessmentCategory)
    number_count_for_grade = models.IntegerField(blank=True, null=True)
    rescale_factor = models.FloatField(default=1.0)
    sort_order = models.FloatField(blank=True)

    def __unicode__(self):
        return "%s for %s" % (self.assessment_category, self.course)

    class Meta:
        verbose_name_plural = 'Course assessment categories'
        ordering = ['sort_order',  'id']

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.course.courseassessmentcategory_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(CourseAssessmentCategory, self).save(*args, **kwargs)

    def save_to_new_course(self, course):
        new_courseassessmentcategory = self
        new_courseassessmentcategory.pk = None
        new_courseassessmentcategory.course = course
        new_courseassessmentcategory.save()
    

class AttendanceDate(models.Model):
    course = models.ForeignKey('Course')
    date = models.DateField()
    
    class Meta:
        ordering = ['date', ]

class CourseSkipDate(models.Model):
    course = models.ForeignKey('Course')
    date = models.DateField()

class StudentAttendance(models.Model):
    course = models.ForeignKey('Course')
    student = models.ForeignKey(CourseUser)
    date = models.DateField()
    # 0: absent, 1: present, 0.5: half-present, -1: excused absense
    present = models.FloatField(default=1.0)

# should this be a group instead?
class Course(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    short_name = models.CharField(max_length=50)
    semester = models.CharField(max_length=50)
    description = models.CharField(max_length=400,blank=True)
    assessment_categories = models.ManyToManyField(AssessmentCategory, through='CourseAssessmentCategory')
    enrolled_students = models.ManyToManyField(CourseUser, through='CourseEnrollment')
    start_date = models.DateField()
    end_date = models.DateField()
    days_of_week = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=False)
    thread = models.ForeignKey('mithreads.Thread')
    track_attendance = models.BooleanField(default=False)
    adjust_due_date_attendance = models.BooleanField(default=False)
    last_attendance_date = models.DateField(blank=True, null=True)
    attendance_end_of_week = models.CharField(max_length = 2, 
                                              default='F')
    
    attendance_threshold_percent = models.SmallIntegerField(default = 75)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['start_date','id']
        permissions = (
            ("update_attendance","Can update attendance"),
        )


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
        
        for ca_category in original_course.courseassessmentcategory_set.all():
            ca_category.save_to_new_course(new_course)


        for course_thread_content in \
            original_course.coursethreadcontent_set.all():
            
            course_thread_content.save_to_new_course(new_course, new_thread)
            
            
    def shift_dates(self, n_days):
        """ 
        Shifts class dates and due dates of assignments by n_days days
        """
        
        timeshift = datetime.timedelta(days=n_days)

        self.start_date += timeshift
        self.end_date += timeshift
        self.save()

        for ctc in self.coursethreadcontent_set.all():
            if ctc.initial_due_date:
                ctc.initial_due_date += timeshift
            if ctc.final_due_date:
                ctc.final_due_date += timeshift
            if ctc.initial_due_date or ctc.final_due_date:
                ctc.save()

    def enrolled_students_ordered(self):
        return self.enrolled_students.filter(role='S').order_by('user__last_name', 'user__first_name')

    def points_for_assessment_category(self, assessment_category):
        try:
            cac=self.courseassessmentcategory_set.get\
                (assessment_category=assessment_category)
        except ObjectDoesNotExist:
            return 0
        

        point_list = []
        for ctc in self.coursethreadcontent_set\
                .filter(assessment_category=assessment_category):
            total_points = ctc.total_points()
            if total_points:
                point_list.append(total_points)

        point_list.sort()
        
        n = cac.number_count_for_grade
        if n is not None and n < len(point_list):
            point_list = point_list[-n:]
        
        return sum(point_list)*cac.rescale_factor


    def all_assessments_by_category(self):
        assessment_categories=[]
        for cac in self.courseassessmentcategory_set.all():

            cac_assessments = []
            number_assessments = 0
            for ctc in self.coursethreadcontent_set\
                    .filter(assessment_category=cac.assessment_category):
                ctc_points = ctc.total_points()
                if ctc_points:
                    number_assessments += 1
                    assessment_results =  \
                    {'content': ctc,
                     'assessment': ctc.thread_content.content_object,
                     'points': ctc_points,
                     }
                    cac_assessments.append(assessment_results)

            category_points = self.points_for_assessment_category \
                               (cac.assessment_category)

            score_comment = ""
            if cac.number_count_for_grade and \
                    cac.number_count_for_grade < number_assessments:
                score_comment = "top %s of %s" % \
                    (cac.number_count_for_grade, number_assessments)
            if cac.rescale_factor != 1.0:
                if score_comment:
                    score_comment += ", "
                score_comment += "rescale %s%%" % \
                    (round(cac.rescale_factor*1000)/10)
            if score_comment:
                score_comment = mark_safe("<br/><small style='font-weight:normal'>(%s)</small>"\
                                              % score_comment)

            cac_results = {'category': cac.assessment_category,
                           'points': category_points,
                           'number_count': cac.number_count_for_grade,
                           'rescale_factor': cac.rescale_factor,
                           'score_comment': score_comment,
                           'number_assessments': number_assessments,
                           'assessments': cac_assessments,
                           'number_assessments_plus_one': len(cac_assessments)+1,
                           }
            assessment_categories.append(cac_results)

        return assessment_categories
    
    def all_assessments_with_points(self):
        assessments = []
        # number_assessments = 0
        for ctc in self.coursethreadcontent_set.all():
            ctc_points = ctc.total_points()
            if ctc_points:
                # number_assessments += 1
                assessment_results =  \
                    {'content': ctc, \
                         'assessment': ctc.thread_content.content_object, \
                         'points': ctc_points, \
                         }
                assessments.append(assessment_results)


        return assessments
 
    def student_score_for_assessment_category(self, assessment_category,
                                              student):
        try:
            cac=self.courseassessmentcategory_set.get\
                (assessment_category=assessment_category)
        except ObjectDoesNotExist:
            return 0
        
        score_list = []
        for ctc in self.coursethreadcontent_set\
                .filter(assessment_category=assessment_category):
            total_score = ctc.student_score(student)
            if total_score:
                score_list.append(total_score)

        score_list.sort()
        
        n = cac.number_count_for_grade
        if n is not None and n < len(score_list):
            score_list = score_list[-n:]
        return sum(score_list)*cac.rescale_factor
 

    def student_scores_by_assessment_category(self, student):
        scores_by_category = []
        for cac in self.courseassessmentcategory_set.all():

            cac_assessments = []
            number_assessments=0
            for ctc in self.coursethreadcontent_set\
                    .filter(assessment_category=cac.assessment_category):
                ctc_points = ctc.total_points()
                if ctc_points:
                    number_assessments+=1
                    student_score = ctc.student_score(student)
                    if student_score:
                        percent = student_score/ctc_points*100
                    else:
                        percent = 0
                    assessment_results =  \
                    {'content': ctc,
                     'assessment': ctc.thread_content.content_object,
                     'points': ctc_points,
                     'student_score': student_score,
                     'percent': percent,
                     }
                    cac_assessments.append(assessment_results)
            category_points = self.points_for_assessment_category \
                               (cac.assessment_category)
            category_student_score = \
                self.student_score_for_assessment_category \
                (cac.assessment_category, student)
            if category_student_score and category_points:
                category_percent = category_student_score/category_points*100
            else:
                category_percent = 0

            score_comment = ""
            if cac.number_count_for_grade and \
                    cac.number_count_for_grade < number_assessments:
                score_comment = "top %s scores out of %s" % \
                    (cac.number_count_for_grade, number_assessments)
            if cac.rescale_factor != 1.0:
                if score_comment:
                    score_comment += " and "
                score_comment += "rescaling by %s%%" % \
                    (round(cac.rescale_factor*1000)/10)
            if score_comment:
                score_comment = mark_safe("<br/><small>(based on %s)</small>"\
                                              % score_comment)

            cac_results = {'category': cac.assessment_category,
                           'points': category_points,
                           'student_score': category_student_score,
                           'percent': category_percent,
                           'number_count': cac.number_count_for_grade,
                           'rescale_factor': cac.rescale_factor,
                           'score_comment': score_comment,
                           'assessments': cac_assessments,
                           }
            scores_by_category.append(cac_results)
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
    
    def all_student_scores_by_assessment_category(self):
        student_scores = []
        for student in self.enrolled_students_ordered():
            student_categories = []
            for cac in self.courseassessmentcategory_set.all():
                category_scores = []
                for ctc in self.coursethreadcontent_set\
                    .filter(assessment_category=cac.assessment_category):
                    ctc_points = ctc.total_points()
                    if ctc_points:
                        student_score = ctc.student_score(student)
                        assessment_results =  \
                            {'content': ctc,
                             'assessment': ctc.thread_content.content_object,
                             'score': student_score,}
                        category_scores.append(assessment_results)
                category_student_score = \
                    self.student_score_for_assessment_category \
                    (cac.assessment_category, student)
                student_categories.append({'category': cac.assessment_category,
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
        for cac in self.courseassessmentcategory_set.all():
            total_points += self.points_for_assessment_category\
                (cac.assessment_category)
        return total_points

    def total_student_score(self, student):
        total_score=0
        for cac in self.courseassessmentcategory_set.all():
            total_score += self.student_score_for_assessment_category\
                (cac.assessment_category, student)
        return total_score
        
    # def points_for_grade_level(self, grade_level):
    #     return self.coursethreadcontent_set\
    #         .filter(required_for_grade=grade_level)\
    #         .aggregate(total_points=Sum('points'))['total_points']
      
    # def points_for_assessment_category_grade_level(self, assessment_category, 
    #                                                grade_level):
    #     return self.coursethreadcontent_set\
    #         .filter(assessment_category=assessment_category, \
    #                     required_for_grade=grade_level) \
    #                     .aggregate(total_points=Sum('points'))['total_points']
 

    def content_for_assessment_category(self, assessment_category):
        return self.coursethreadcontent_set\
            .filter(assessment_category=assessment_category)


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
            offsets.append(datetime.timedelta((wd - initial_weekday) % 7))
        
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
            week_start += datetime.timedelta(7)

            if reached_end:
                break
        
        return self.attendancedate_set.count()


    def find_next_attendance_date(self, last_attendance_date=None):
        if not last_attendance_date:
            if self.last_attendance_date:
                last_attendance_date = self.last_attendance_date
            elif self.start_date:
                last_attendance_date = self.start_date - datetime.timedelta(1)
            else:
                return None

        try:
            return self.attendancedate_set.filter\
                (date__gt= last_attendance_date)[0].date
        except:
            return None


    def previous_week_end(self, date=None):
        if not date:
            date = datetime.date.today()

        # find end of previous week
        week_end_day = day_of_week_to_python(self.attendance_end_of_week)
        # offset is number of days since previous week_end
        offset = (date.weekday()-1-week_end_day) % 7 +1
        previous_week_end = date - datetime.timedelta(offset)
        
        # find last attendance day at or before previous_week_end
        if self.days_of_week:
            weekday_list =[item.strip() for item in self.days_of_week.split(",")]
            min_offset = 7
            for wd in weekday_list:
                min_offset = min((week_end_day-day_of_week_to_python(wd)) % 7,
                                 min_offset)
                

            previous_week_end -= datetime.timedelta(min_offset)

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
                previous_week_end -= datetime.timedelta(1)
                previous_week_end_day = previous_week_end.weekday()
                
                min_offset = 7
                for wd in weekday_list:
                    min_offset = min((previous_week_end_day
                                      -day_of_week_to_python(wd)) % 7,
                                     min_offset)
                previous_week_end -= datetime.timedelta(min_offset)

                # if a week or more before original previous week end
                # then return result regardless of it being a skip day
                if original_previous_week_end - previous_week_end >= \
                        datetime.timedelta(7):
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

        if not date:
            date = datetime.date.today()

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

        content_list= self.coursethreadcontent_set.all()

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
                (id__in=self.coursethreadcontent_set.filter \
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
        return self.coursethreadcontent_set\
            .exclude(optional=True)\
            .exclude(id__in=self.coursethreadcontent_set.filter \
                         (studentcontentcompletion__student=student,
                          studentcontentcompletion__complete=True))\
            .exclude(id__in=self.coursethreadcontent_set.filter \
                         (studentcontentcompletion__student=student,\
                              studentcontentcompletion__skip=True))[:number]

class CourseEnrollment(models.Model):
    ROLE_CHOICES = (
        (STUDENT_ROLE, 'Student'),
        (INSTRUCTOR_ROLE, 'Instructor'),
    )
    course = models.ForeignKey(Course)
    student = models.ForeignKey(CourseUser)
    section = models.IntegerField()
    date_enrolled = models.DateField()
    withdrew = models.BooleanField(default=False)
    role = models.CharField(max_length=1,
                            choices = ROLE_CHOICES,
                            default = STUDENT_ROLE)


    def __unicode__(self):
        return "%s enrolled in %s" % (self.student, self.course)

    class Meta:
        unique_together = ("course","student")
        ordering = ['student']
        
class CourseThreadContent(models.Model):
    AGGREGATE_CHOICES = (
        ('Max', 'Maximum'),
        ('Avg', 'Average'),
        ('Las', 'Last'),
    )

    course = models.ForeignKey(Course)
    thread_content = models.ForeignKey('mithreads.ThreadContent')
    instructions = models.TextField(blank=True, null=True)
    initial_due_date=models.DateField(blank=True, null=True)
    final_due_date=models.DateField(blank=True, null=True)
    assessment_category = models.ForeignKey(AssessmentCategory, 
                                            blank=True, null=True)
    individualize_by_student = models.BooleanField(default=True)
    required_for_grade = models.ForeignKey(GradeLevel, blank=True, null=True)
    required_to_pass = models.BooleanField(default=False)
    max_number_attempts = models.IntegerField(default=1)
    attempt_aggregation = models.CharField(max_length=3,
                                           choices = AGGREGATE_CHOICES,
                                           default = 'Max')
    optional = models.BooleanField(default=False)
    record_scores = models.BooleanField(default=False)
    sort_order = models.FloatField(blank=True)
    
    class Meta:
        ordering = ['sort_order', 'id']
        unique_together = ['course', 'thread_content']

    def __unicode__(self):
        return "%s for %s" % (self.thread_content, self.course)

    def clean(self):

        # check if thread_content is for the thread associated with course
        # If not, raise exception
        if self.course.thread != self.thread_content.section.thread:
            raise ValidationError, \
                "Thread content is not from course thread: %s"\
                % self.course.thread

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.course.coursethreadcontent_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(CourseThreadContent, self).save(*args, **kwargs)

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
        new_thread_content = new_thread_section.threadcontent_set.filter(
            content_type = old_thread_content.content_type,
            object_id = old_thread_content.object_id)[0]
        new_content.thread_content = new_thread_content
        new_content.save()

    def total_points(self):
        try:
            return self.thread_content.content_object.get_total_points()
        except AttributeError:
            return None


    def student_score(self, student):
        # return maximum or score of all student's assessment attempts, 
        # depending on attempt_aggregation
        # or zero if no attempt
        if self.attempt_aggregation=='Avg':
            from numpy import mean
            score = mean([sca.get_score() for sca in self.studentcontentattempt_set.filter(student=student)])
            #score = self.studentcontentattempt_set.filter(student=student).aggregate(score = Avg('score'))['score']
        elif self.attempt_aggregation=='Las':
            score = self.studentcontentattempt_set.filter(student=student).latest('datetime').get_score()
        else:
            try:
                score = max([sca.get_score() for sca in self.studentcontentattempt_set.filter(student=student)])
            except ValueError:
                score = None
            #score = self.studentcontentattempt_set.filter(student=student).aggregate(score=Max('score'))['score']
        return score


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


    def get_initial_due_date(self, student=None):
        if not student:
            return self.initial_due_date
        try:
            return self.manualduedateadjustment_set.get(student=student)\
                .initial_due_date
        except:
            return self.initial_due_date

    def get_final_due_date(self, student=None):
        if not student:
            return self.final_due_date
        try:
            return self.manualduedateadjustment_set.get(student=student)\
                .final_due_date
        except:
            return self.final_due_date

    def adjusted_due_date(self, student):
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        due_date = self.get_initial_due_date(student)
        final_due_date = self.get_final_due_date(student)

        if not due_date or not final_due_date:
            return None
        
        today = datetime.date.today()
        
        course = self.course        
        while due_date < today + datetime.timedelta(7):
            previous_week_end = \
                course.previous_week_end(due_date)

            # only update if have attendance through previous_week_end
            if not course.last_attendance_date \
                    or course.last_attendance_date < previous_week_end:
                break

            if student.percent_attendance \
                    (course=course, date=previous_week_end) \
                    < course.attendance_threshold_percent:
                break
            
            due_date += datetime.timedelta(7)
            if due_date >= final_due_date:
                due_date = final_due_date
                break

        return due_date



    def adjusted_due_date_calculation(self, student):
        # return data for calculation of adjust due date
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        due_date = self.get_initial_due_date(student)
        final_due_date = self.get_final_due_date(student)
        
        if not due_date or not final_due_date:
            return []

        today = datetime.date.today()

        course = self.course        
        
        calculation_list = []
        while due_date < today + datetime.timedelta(7):

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
            
            due_date += datetime.timedelta(7)
            if due_date >= final_due_date:
                due_date = final_due_date
                calculation['resulting_date'] = due_date
                calculation['reached_latest'] = True
                calculation_list.append(calculation)
                break

            calculation['resulting_date'] = due_date
            calculation_list.append(calculation)

        return calculation_list


    def complete_skip_button_html(self, student, full_html=False):
        if not self.course in student.course_set.all():
            return ""
        
        html_string = ""

        # check if student already completed content
        try:
            completed = self.studentcontentcompletion_set\
                .get(student=student).complete
        except:
            completed = False

            
        # if completed, show checkmark, click to give option to remove complete
        if completed:
            html_string += \
                '<img src="%sadmin/img/icon-yes.gif" alt="Complete"  onclick="$(\'#undo_complete_%s\').toggle();"/>' \
                % (settings.STATIC_URL, self.id)
            
            # add hidden undo completion button
            click_command = "Dajaxice.midocs.record_course_content_completion"\
                + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s', 'complete': false, 'skip': false })" \
                % (self.id, student.id)

            html_string += '<span id ="undo_complete_%s" hidden> <input type="button" class="coursecontentbutton" value="Undo completion" onclick="%s;"></span>' % (self.id, click_command)



        # only show buttons if not optional
        elif not self.optional:
            # if not completed, check if skipped
            try:
                skipped = self.studentcontentcompletion_set\
                    .get(student=student).skip
            except:
                skipped = False

            # if skipped, show icon, click to give option to remove skip
            if skipped:
                html_string += \
                    '<img src="%sadmin/img/icon-no.gif" alt="Complete"  onclick="$(\'#undo_skip_%s\').toggle();"/>' \
                    % (settings.STATIC_URL, self.id)

                # add hidden undo skip button
                click_command = "Dajaxice.midocs.record_course_content_completion"\
                    + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s', 'complete': false, 'skip': false })" \
                    % (self.id, student.id)

                html_string += '<span id ="undo_skip_%s" hidden> <input type="button" class="coursecontentbutton" value="Remove skip" onclick="%s;"></span>' % (self.id, click_command)


            # if not complete or skipped, 
            # give option to mark assessment as complete or skip
            # or to mark other content as done
            else:
            
                # since haven't implement "Complete" doing anything special
                # (like notifying instructors)
                # don't use Complete/Skip buttons for now

                # if self.initial_due_date:
                #     use_complete_skip_buttons = True
                # else:
                #     use_complete_skip_buttons = False
                use_complete_skip_buttons=False

                if use_complete_skip_buttons:
                    click_command = "Dajaxice.midocs.record_course_content_completion"\
                        + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s' })" \
                        % (self.id, student.id)
            
                    html_string += \
                        '<input type="button" class="coursecontentbutton" value="Complete" onclick="%s;">' \
                        % (click_command)

                    click_command = "Dajaxice.midocs.record_course_content_completion"\
                        + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s', 'complete': false, 'skip': true })" \
                        % (self.id, student.id)
            
                    html_string += \
                        ' <input type="button" class="coursecontentbutton" value="Skip" onclick="%s;">' \
                        % (click_command)

                else:
                    click_command = "Dajaxice.midocs.record_course_content_completion"\
                        + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s' })" \
                        % (self.id, student.id)
            
                    html_string += \
                        '<input type="button" class="coursecontentbutton" value="Done" onclick="%s;">' \
                        % (click_command)

            
        # if full_html, mark section for later ajax changes
        if full_html:
            html_string = '<span id="id_course_completion_%s">%s</span>' \
                % (self.id, html_string)
        
        return html_string


class ManualDueDateAdjustment(models.Model):
    content = models.ForeignKey(CourseThreadContent)
    student = models.ForeignKey(CourseUser)
    initial_due_date=models.DateField()
    final_due_date=models.DateField()
    
    def __unicode__(self):
        return "Adjustment for %s on %s" % (self.student, self.content)

    class Meta:
        unique_together = ("content","student")


class StudentContentAttempt(models.Model):
    student = models.ForeignKey(CourseUser)
    content = models.ForeignKey(CourseThreadContent)
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(blank=True)
    score = models.FloatField(null=True, blank=True)
    seed = models.CharField(max_length=150, blank=True, null=True)

    def __unicode__(self):
        return "%s attempt on %s" % (self.student, self.content)

    class Meta:
        ordering = ['datetime']
        get_latest_by = "datetime"
        
    def save(self, *args, **kwargs):
        if self.datetime is None:
            self.datetime = datetime.datetime.now()

        super(StudentContentAttempt, self).save(*args, **kwargs)


    def get_percent_credit(self):
         score = self.get_score()
         points = self.content.total_points()
         if score is None or points is None:
             return None
         return int(score*100.0/points)

    def get_score(self, ignore_manual_score = False):
        # if a score is entered in, it overrides any question answers
        # as long as not ignoring manual score
        if self.score is not None and not ignore_manual_score:
            return self.score
        
        assessment=self.content.thread_content.content_object
        # must be an assessment 
        from mitesting.models import Assessment
        if not isinstance(assessment,Assessment):
            return None
        
        question_set_details = assessment.questionsetdetail_set.all()
        if question_set_details:
            score = 0.0
            for question_set_detail in question_set_details:
                score += self.get_score_question_set(question_set_detail)
        else: 
            score = None

        return score


    def score_overridden(self):
        # determine if a score from questions is overridden by manual score
        
        if self.get_score() != self.get_score(ignore_manual_score=True):
            return True
        else:
            return False


    def get_score_question_set(self, question_set_detail):
        question_answers = self.questionstudentanswer_set\
            .filter(question_set=question_set_detail.question_set)

        if question_answers:

            if self.content.attempt_aggregation=='Avg':
                credit = question_answers.aggregate(credit=Avg('credit'))['credit']
            elif self.content.attempt_aggregation=='Las':
                credit = question_answers.latest('datetime').credit
            else:
                credit = question_answers.aggregate(credit=Max('credit'))['credit']
                
            return question_set_detail.points*credit
        else:
            return 0

    def get_percent_credit_question_set(self, question_set):
        question_answers = self.questionstudentanswer_set\
            .filter(question_set=question_set)

        if question_answers:

            if self.content.attempt_aggregation=='Avg':
                credit = question_answers.aggregate(credit=Avg('credit'))['credit']
            elif self.content.attempt_aggregation=='Las':
                credit = question_answers.latest('datetime').credit
            else:
                credit = question_answers.aggregate(credit=Max('credit'))['credit']
                
            return int(credit*100)
        else:
            return 0


    def get_latest_datetime(self):
        assessment=self.content.thread_content.content_object
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
        # is at least a minue
        latest_datetime = self.get_latest_datetime()
        if latest_datetime and latest_datetime -self.datetime \
                >= datetime.timedelta(0,60):
            return True
        else:
            return False

class StudentContentCompletion(models.Model):
    student = models.ForeignKey(CourseUser)
    content = models.ForeignKey(CourseThreadContent)
    complete = models.BooleanField(default=False)
    skip = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s attempt on %s" % (self.student, self.content)

    class Meta:
        unique_together = ['student', 'content']


class StudentContentAttemptSolutionView(models.Model):
    content_attempt = models.ForeignKey(StudentContentAttempt)
    question_set = models.SmallIntegerField()
    datetime = models.DateTimeField(auto_now_add=True)


class QuestionStudentAnswer(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey('mitesting.Question')
    seed = models.CharField(max_length=150, blank=True, null=True)
    question_set = models.SmallIntegerField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    identifier_in_answer = models.CharField(max_length=50, blank=True,
                                            null=True)
    credit = models.FloatField()
    datetime =  models.DateTimeField(auto_now_add=True)
    course_content_attempt = models.ForeignKey(StudentContentAttempt,
                                               blank=True, null=True)

    # only if don't have a course_content_attempt:
    assessment = models.ForeignKey('mitesting.Assessment', 
                                   blank=True, null=True)
    assessment_seed = models.CharField(max_length=150, blank=True, null=True)

    def __unicode__(self):
        return  "%s" % self.answer

    class Meta:
        get_latest_by = "datetime"
