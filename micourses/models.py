from django.db import models
from django.db.models import Sum
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

    class Meta:
        verbose_name_plural = 'Course assessment categories'

class Module(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=400,blank=True)
    course = models.ForeignKey('Course')
    assessments = models.ManyToManyField('mitesting.Assessment', through='ModuleAssessment')
    sort_order = models.FloatField(default=0.0)
    
    def __unicode__(self):
        return self.name


class ModuleAssessment(models.Model):
    module=models.ForeignKey(Module)
    assessment=models.ForeignKey('mitesting.Assessment')
    initial_due_date=models.DateField()
    final_due_date=models.DateField()
    assessment_category = models.ForeignKey(AssessmentCategory, blank=True, null=True)
    points = models.IntegerField(default=0)
    required_for_grade = models.ForeignKey(GradeLevel, blank=True, null=True)
    required_to_pass = models.BooleanField()
    max_number_attempts = models.IntegerField(default=1)
    sort_order = models.FloatField(default=0.0)
    
    def __unicode__(self):
        return "%s for %s" % (self.assessment, self.module)
    
class StudentAssessmentAttempt(models.Model):
    student = models.ForeignKey(User)
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



# should this be a group instead?
class Course(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=400,blank=True)
    assessment_categories = models.ManyToManyField(AssessmentCategory, through='CourseAssessmentCategory')

    def __unicode__(self):
        return self.name

    def points_for_assessment_category(self, assessment_category):
        return self.module_set.filter(moduleassessment__assessment_category=assessment_category).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
        
    def total_points(self):
        return self.module_set.aggregate(total_points=Sum('moduleassessment__points'))['total_points']
        
    def points_for_grade_level(self, grade_level):
        return self.module_set.filter(moduleassessment__required_for_grade=grade_level).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
      
    def points_for_assessment_category_grade_level(self, assessment_category, grade_level):
        return self.module_set.filter(moduleassessment__assessment_category=assessment_category, moduleassessment__required_for_grade=grade_level).aggregate(total_points=Sum('moduleassessment__points'))['total_points']
 
    def assessment_category_points(self):
        point_dict={}
        for gc in self.assessment_categories.all():
            
            assessment_category_list = self.module_set.values('moduleassessment__assessment_category__name').annotate(totalpoints=Sum('moduleassessment__points'))
        
        
        for gc in assessment_category_list:
            point_dict[gc['moduleassessment__assessment_category__name']] = gc['totalpoints']
        
        return point_dict

    def moduleassessments_for_assessment_category(self, assessment_category):
        return ModuleAssessment.objects.filter(module__course=self).filter(assessment_category=assessment_category)

