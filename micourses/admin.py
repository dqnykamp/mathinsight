from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import CommentForCredit, QuestionStudentAnswer, Course, GradeLevel, AssessmentCategory, CourseAssessmentCategory, Module, ModuleAssessment, StudentAssessmentAttempt
import reversion

class QuestionStudentAnswerAdmin(reversion.VersionAdmin):
    pass

class CommentForCreditAdmin(reversion.VersionAdmin):
    pass

class ModuleAssessmentInline(admin.TabularInline):
    model = ModuleAssessment

class ModuleAdmin(admin.ModelAdmin):
    inlines=[ModuleAssessmentInline]
    
class CourseAssessmentCategoryInline(admin.TabularInline):
    model = CourseAssessmentCategory

class CourseAdmin(admin.ModelAdmin):
    inlines=[CourseAssessmentCategoryInline]
    

admin.site.register(CommentForCredit,CommentForCreditAdmin)
admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)

# not use reversion yet
admin.site.register(Course, CourseAdmin)
admin.site.register(GradeLevel)
admin.site.register(AssessmentCategory)
admin.site.register(Module,ModuleAdmin)
admin.site.register(StudentAssessmentAttempt)
