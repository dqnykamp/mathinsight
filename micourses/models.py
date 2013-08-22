from django.db import models
from django.db.models import Sum, Max, Avg
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import datetime
import settings

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
        return enrolled_course

    def active_courses(self):
        return self.course_set.filter(active=True)
    
    def get_current_role(self):
        return self.role
    
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
            .filter(date__lte = date).filter(date__gte = date_enrolled)\
            .aggregate(Sum('present'))['present__sum']

        if course_days:
            try:
                return 100.0*days_attended/float(course_days)
            except TypeError:
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
    sort_order = models.FloatField(default=0.0)

    def __unicode__(self):
        return "%s for %s" % (self.assessment_category, self.course)
    class Meta:
        verbose_name_plural = 'Course assessment categories'


    

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


    def enrolled_students_ordered(self):
        return self.enrolled_students.order_by('user__last_name', 'user__first_name')

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
        return sum(point_list)


    def all_assessments_by_category(self):
        assessment_categories=[]
        for cac in self.courseassessmentcategory_set.all():

            cac_assessments = []
            for ctc in self.coursethreadcontent_set\
                    .filter(assessment_category=cac.assessment_category):
                ctc_points = ctc.total_points()
                if ctc_points:
                    assessment_results =  \
                    {'content': ctc,
                     'assessment': ctc.thread_content.content_object,
                     'points': ctc_points,
                     }
                    cac_assessments.append(assessment_results)

            category_points = self.points_for_assessment_category \
                               (cac.assessment_category)
            cac_results = {'category': cac.assessment_category,
                           'points': category_points,
                           'number_count': cac.number_count_for_grade,
                           'assessments': cac_assessments,
                           'number_assessments_plus_one': len(cac_assessments)+1,
                           }
            assessment_categories.append(cac_results)

        return assessment_categories
    
 
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
        return sum(score_list)
 

    def student_scores_by_assessment_category(self, student):
        scores_by_category = []
        for cac in self.courseassessmentcategory_set.all():

            cac_assessments = []
            for ctc in self.coursethreadcontent_set\
                    .filter(assessment_category=cac.assessment_category):
                ctc_points = ctc.total_points()
                if ctc_points:
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
            cac_results = {'category': cac.assessment_category,
                           'points': category_points,
                           'student_score': category_student_score,
                           'percent': category_percent,
                           'number_count': cac.number_count_for_grade,
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
        for student in self.enrolled_students.all():
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


    def upcoming_assessments(self, student, date=None, days_future=None):
        if not date:
            date = datetime.date.today()

        later_date = None
        if days_future:
            later_date = date+datetime.timedelta(days_future)

        # create list of incomplete assessments with 
        # initial due dates before later_date (if set)
        # and current final due dates
        # (this initial filter doesn't account for any 
        # manual due date adjustments)
        upcoming_assessments= self.coursethreadcontent_set\
            .filter(final_due_date__gte = date) \
            .exclude(studentcontentcompletion__student=student,\
                         studentcontentcompletion__complete=True)
        if later_date:
            upcoming_assessment=upcoming_assessments\
                .filter(initial_due_date__lt = later_date)\


        # for each of this assessments, calculate adjusted due dates
        adjusted_due_date_assessments = []
        for assessment in upcoming_assessments:
            adjusted_due_date = assessment.adjusted_due_date(student)
            adjusted_due_date_assessments.append((adjusted_due_date,assessment))

        # sort by adjusted due date
        adjusted_due_date_assessments.sort()
        
        #remove past due assessments
        last_past_due_index=-1
        for (i, assessment) in enumerate(adjusted_due_date_assessments):
            if adjusted_due_date_assessments[i][0] < date:
                last_past_due_index=i
            else:
                break
        
        adjusted_due_date_assessments=adjusted_due_date_assessments\
           [last_past_due_index+1:]

        return adjusted_due_date_assessments

    def next_items(self, student, number=5):
        return self.coursethreadcontent_set\
            .exclude(studentcontentcompletion__student=student,\
                     studentcontentcompletion__complete=True)\
            .exclude(studentcontentcompletion__student=student,\
                     studentcontentcompletion__skip=True)[:number]

class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course)
    student = models.ForeignKey(CourseUser)
    date_enrolled = models.DateField()
    withdrew = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "%s enrolled in %s" % (self.student, self.course)

    class Meta:
        unique_together = ("course","student")


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
    sort_order = models.FloatField(default=0.0)
    
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

    def total_points(self):
        try:
            return self.thread_content.content_object.total_points()
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
        for student in self.course.enrolled_students.all():
            latest_attempts.append({
                    'student': student,
                    'attempt': self.get_student_latest_attempt(student),
                    'current_score': self.student_score(student),
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

            
        # if completed, show checkmark
        if completed:
            html_string += \
                '<img src="%sadmin/img/icon-yes.gif" alt="Complete" />' \
                % settings.STATIC_URL

        else:
            # if not completed, check if skipped
            try:
                skipped = self.studentcontentcompletion_set\
                    .get(student=student).skip
            except:
                skipped = False

            # if skipped, give option to remove skip
            if skipped:
                click_command = "Dajaxice.midocs.record_course_content_completion"\
                    + "(Dajax.process,{'course_thread_content_id': '%s', 'student_id': '%s', 'complete': false, 'skip': false })" \
                    % (self.id, student.id)
            
                html_string += '[skipped] ' + \
                    '<input type="button" class="coursecontentbutton" value="Remove skip" onclick="%s;">' \
                    % (click_command)

            # if not complete or skipped, 
            # give option to mark assessment as complete or skip
            # or to mark other content as done
            else:
            
                if self.initial_due_date:
                    is_assessment = True
                else:
                    is_assessment = False

                if is_assessment:
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
    
    class Meta:
        unique_together = ("content","student")


class StudentContentAttempt(models.Model):
    student = models.ForeignKey(CourseUser)
    content = models.ForeignKey(CourseThreadContent)
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(blank=True)
    score = models.FloatField(null=True, blank=True)
    seed = models.CharField(max_length=50, blank=True, null=True)

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

class QuestionStudentAnswer(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey('mitesting.Question')
    seed = models.CharField(max_length=50, blank=True, null=True)
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
    assessment_seed = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return  "%s" % self.answer

    class Meta:
        get_latest_by = "datetime"
