from django.db import models
from django.contrib.auth.models import User, Group
from midocs.models import Page, Video
from mitesting.models import Question


class CommentForCredit(models.Model):
    page = models.ForeignKey(Page)
    group = models.ForeignKey(Group)
    opendate = models.DateTimeField()
    deadline = models.DateTimeField()
    
    def __unicode__(self):
        return "%s deadline" % self.page.code


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

class GradeCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Grade categories'

# should this be a group instead?
class Course(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=400,blank=True)
    grade_categories = models.ManyToManyField(GradeCategory, through='CourseGradeCategory')

    def __unicode__(self):
        return self.name

class CourseGradeCategory(models.Model):
    course = models.ForeignKey(Course)
    grade_category = models.ForeignKey(GradeCategory)
    number_count_for_grade = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Course grade categories'

class Module(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=400,blank=True)
    course = models.ForeignKey(Course)
    assessments = models.ManyToManyField('mitesting.Assessment', through='ModuleAssessment')
    sort_order = models.FloatField(default=0.0)
    
    def __unicode__(self):
        return self.name


class ModuleAssessment(models.Model):
    module=models.ForeignKey(Module)
    assessment=models.ForeignKey('mitesting.Assessment')
    initial_due_date=models.DateField()
    final_due_date=models.DateField()
    grade_category = models.ForeignKey(GradeCategory, blank=True, null=True)
    points = models.IntegerField(default=0)
    required_for_grade = models.ForeignKey(GradeLevel, blank=True, null=True)
    required_to_pass = models.BooleanField()
    max_number_attempts = models.IntegerField(default=1)
    sort_order = models.FloatField(default=0.0)
    

class StudentAssessmentAttempt(models.Model):
    user = models.ForeignKey(User)
    module_assessment = models.ForeignKey(ModuleAssessment)
    date = models.DateTimeField()
    score = models.IntegerField()
