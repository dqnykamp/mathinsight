from django.db import models
from django.db.models import Sum, Max, Avg
from django.contrib.auth.models import User, Group
from midocs.models import Page, Video
from mitesting.models import Question
from django.contrib.auth.models import User
import datetime

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


class CommentForCredit(models.Model):
    page = models.ForeignKey(Page)
    group = models.ForeignKey(Group)
    opendate = models.DateTimeField()
    deadline = models.DateTimeField()
    
    def __unicode__(self):
        return "%s deadline" % self.page.code

class CourseUser(models.Model):
    ROLE_CHOICES = (
        ('S', 'Student'),
        ('I', 'Instructor'),
    )
    user = models.OneToOneField(User)
    selected_course = models.ForeignKey('Course', blank=True, null=True)
    role = models.CharField(max_length=1,
                            choices = ROLE_CHOICES,
                            default = 'S')
    

    def __unicode__(self):
        return self.user.__unicode__()
    
    def get_full_name(self):
        return self.user.get_full_name()
    def get_short_name(self):
        return self.user.get_short_name()

    def return_selected_course(self):
        if self.selected_course:
            return self.selected_course

        # will raise exception if course not selected
        # and enrolled in more or less than one active course
        enrolled_course = self.course_set.filter(active=True).get()
        
        # if found just one active course, make it be the selected course
        self.selected_course = enrolled_course
        self.save()

    def active_courses(self):
        return self.course_set.filter(active=True)
    
    
    def percent_attendance(self, course=None, date=None):
        if not course:
            course = self.return_selected_course()
        if not date:
            date = course.last_attendance_day_previous_week()
            if not date:
                return None
        
        date_enrolled = self.courseenrollment_set.get(course=course)\
            .date_enrolled
        course_days = course.to_date_attendance_days(date, 
                                                     start_date=date_enrolled)
        

        days_attended = self.studentattendance_set.filter(course=course)\
            .filter(date__lte = date).filter(date__gte = date_enrolled).count()
        
        return 100.0*days_attended/float(course_days)

    

class QuestionStudentAnswer(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    answer = models.CharField(max_length=400)
    seed = models.CharField(max_length=50, blank=True, null=True)
    credit = models.FloatField()
    datetime =  models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return  "%s" % self.answer


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
    number_count_for_grade = models.IntegerField(default=9999)
    sort_order = models.FloatField(default=0.0)

    def __unicode__(self):
        return "%s for %s" % (self.assessment_category, self.course)
    class Meta:
        verbose_name_plural = 'Course assessment categories'

class Module(models.Model):
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=400,blank=True)
    course = models.ForeignKey('Course')
    assessments = models.ManyToManyField('mitesting.Assessment', through='ModuleAssessment')
    sort_order = models.FloatField(default=0.0)
    
    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ("course","code")


class ModuleAssessment(models.Model):

    AGGREGATE_CHOICES = (
        ('Max', 'Maximum'),
        ('Avg', 'Average'),
        ('Las', 'Last'),
    )

    module=models.ForeignKey(Module)
    assessment=models.ForeignKey('mitesting.Assessment')
    initial_due_date=models.DateField()
    final_due_date=models.DateField()
    assessment_category = models.ForeignKey(AssessmentCategory, blank=True, null=True)
    points = models.IntegerField(default=0)
    required_for_grade = models.ForeignKey(GradeLevel, blank=True, null=True)
    required_to_pass = models.BooleanField()
    max_number_attempts = models.IntegerField(default=1)
    attempt_aggregation = models.CharField(max_length=3,
                                           choices = AGGREGATE_CHOICES,
                                           default = 'Max')
    sort_order = models.FloatField(default=0.0)
    
    def __unicode__(self):
        return "%s for %s" % (self.assessment, self.module)

    class Meta:
        unique_together = ("module","assessment")

    def student_score(self, student):
        # return maximum or score of all student's assessment attempts, 
        # depending on attempt_aggregation
        # or zero if no attempt
        if self.attempt_aggregation=='Avg':
            score = self.studentassessmentattempt_set.filter(student=student).aggregate(score = Avg('score'))['score']
        elif self.attempt_aggregation=='Las':
            score = self.studentassessmentattempt_set.filter(student=student).latest('datetime').score
        else:
            score = self.studentassessmentattempt_set.filter(student=student).aggregate(score=Max('score'))['score']
        if score:
            return score
        else:
            return 0


    def attempt_aggregation_string(self):
        if self.attempt_aggregation=='Avg':
            return "Average"
        elif self.attempt_aggregation=='Las':
            return "Last"
        else:
            return "Maximum"


    def adjusted_due_date(self, student):
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        today = datetime.date.today()
        
        due_date = self.initial_due_date
        course = self.module.course        
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
            if due_date >= self.final_due_date:
                due_date = self.final_due_date
                break

        return due_date



    def adjusted_due_date_calculation(self, student):
        # return data for calculation of adjust due date
        # adjust due date in increments of weeks
        # based on percent attendance at end of each previous week

        today = datetime.date.today()
        
        due_date = self.initial_due_date
        course = self.module.course        
        
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
            if due_date >= self.final_due_date:
                due_date = self.final_due_date
                calculation['resulting_date'] = due_date
                calculation['reached_latest'] = True
                calculation_list.append(calculation)
                break

            calculation['resulting_date'] = due_date
            calculation_list.append(calculation)

        return calculation_list


class StudentAssessmentAttempt(models.Model):
    student = models.ForeignKey(CourseUser)
    module_assessment = models.ForeignKey(ModuleAssessment)
    datetime = models.DateTimeField()
    score = models.IntegerField()

    # find maximum score for all attempts 
    # of this student on this moduleassesment
    def maximum_score(self):
        from django.db.models import Max
        return StudentAssessmentAttempt.objects.filter \
            (student=self.student, module_assessment=self.module_assessment)\
            .aggregate(Max('score'))
        
    def __unicode__(self):
        return "%s attempt on %s" % (self.student, self.module_assessment)

    class Meta:
        ordering = ['datetime']


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

# should this be a group instead?
class Course(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=400,blank=True)
    assessment_categories = models.ManyToManyField(AssessmentCategory, through='CourseAssessmentCategory')
    enrolled_students = models.ManyToManyField(CourseUser, through='CourseEnrollment')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    days_of_week = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField()
    associated_thread = models.ForeignKey('mithreads.Thread', blank=True, null=True)
    track_attendance = models.BooleanField()
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

    def points_for_assessment_category(self, assessment_category):
        return self.module_set.filter(moduleassessment__assessment_category=assessment_category).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
        
    def total_points(self):
        return self.module_set.aggregate(total_points=Sum('moduleassessment__points'))['total_points']
        
    def points_for_grade_level(self, grade_level):
        return self.module_set.filter(moduleassessment__required_for_grade=grade_level).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
      
    def points_for_assessment_category_grade_level(self, assessment_category, grade_level):
        return self.module_set.filter(moduleassessment__assessment_category=assessment_category, moduleassessment__required_for_grade=grade_level).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
 
    # def assessment_category_points(self):
    #     point_dict={}
    #     for gc in self.assessment_categories.all():
            
    #         assessment_category_list = self.module_set.values('moduleassessment__assessment_category__name').annotate(totalpoints=Sum('moduleassessment__points'))
        
        
    #     for gc in assessment_category_list:
    #         point_dict[gc['moduleassessment__assessment_category__name']] = gc['totalpoints']
        
    #     return point_dict

    def moduleassessments_for_assessment_category(self, assessment_category):
        return ModuleAssessment.objects.filter(module__course=self).filter(assessment_category=assessment_category)

    # def current_assessments(self):
    #     return ModuleAssessments.objects.filter(module__course=self).filter(publish_date__lte=datetime.date.today(),)
    

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

    def return_attendencedate_string(self):
        string_list = []
        for attendancedate in self.attendancedate_set.all():
            string_list.append(str(attendancedate.date))
        return ", ".join(string_list)
            

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


    def upcoming_assessments(self, student, date=None):
        if not date:
            date = datetime.date.today()

        week_later = date+datetime.timedelta(7)

        # create list of module assessments with 
        # initial due dates within a week and current final due dates
        upcoming_assessments= ModuleAssessment.objects\
            .filter(module__course=self)\
            .filter(initial_due_date__lt = week_later)\
            .filter(final_due_date__gte = date)
        
        # for each of this assessments, calculate adjusted due dates
        adjusted_due_date_assessments = []
        for assessment in upcoming_assessments:
            adjusted_due_date = assessment.adjusted_due_date(student)
            adjusted_due_date_assessments.append((adjusted_due_date,assessment))

        # sort by adjusted due date
        adjusted_due_date_assessments.sort()
        
        # remove past due assessments
        while len(adjusted_due_date_assessments)>0:
            if adjusted_due_date_assessments[0][0] < date:
                adjusted_due_date_assessments=adjusted_due_date_assessments[1:]
            else:
                break

        # return up to five
        return adjusted_due_date_assessments[:5]


        
    
class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course)
    student = models.ForeignKey(CourseUser)
    date_enrolled = models.DateField()
    withdrew = models.BooleanField()
    
    def __unicode__(self):
        return "%s enrolled in %s" % (self.student, self.course)

    class Meta:
        unique_together = ("course","student")


class CourseLoggedIn(models.Model):
    student = models.ForeignKey(CourseUser, unique=True)
    course = models.ForeignKey(Course)

