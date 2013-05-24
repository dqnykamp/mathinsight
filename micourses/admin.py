from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import CommentForCredit, QuestionStudentAnswer, Course, GradeLevel, GradeCategory, CourseGradeCategory, Module, ModuleAssessment, StudentAssessmentAttempt
import reversion

class QuestionStudentAnswerAdmin(reversion.VersionAdmin):
    pass

class CommentForCreditAdmin(reversion.VersionAdmin):
    pass

class ModuleAssessmentInline(admin.TabularInline):
    model = ModuleAssessment

class ModuleAdmin(admin.ModelAdmin):
    inlines=[ModuleAssessmentInline]
    
class CourseGradeCategoryInline(admin.TabularInline):
    model = CourseGradeCategory

class CourseAdmin(admin.ModelAdmin):
    inlines=[CourseGradeCategoryInline]
    

admin.site.register(CommentForCredit,CommentForCreditAdmin)
admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)

# not use reversion yet
admin.site.register(Course, CourseAdmin)
admin.site.register(GradeLevel)
admin.site.register(GradeCategory)
admin.site.register(Module,ModuleAdmin)
admin.site.register(StudentAssessmentAttempt)
