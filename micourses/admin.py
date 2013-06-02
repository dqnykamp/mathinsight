from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import CommentForCredit, QuestionStudentAnswer, Course, GradeLevel, AssessmentCategory, CourseAssessmentCategory, Module, ModuleAssessment, StudentAssessmentAttempt, CourseEnrollment, AttendanceDate, CourseSkipDate, CourseThreadContent
from mithreads.models import ThreadContent
import settings
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
class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
class CourseSkipDate(admin.TabularInline):
    model = CourseSkipDate
class AttendanceDateInline(admin.TabularInline):
    model = AttendanceDate

def course_thread_content_form_factory(thread):
    class RuntimeCourseThreadContentForm(forms.ModelForm):
        
        thread_content = forms.ModelChoiceField\
            (label="ThreadContent", queryset=ThreadContent.objects\
                 .filter(section__thread=thread)\
                 .order_by('section__sort_order','sort_order'))
 
        class Meta:
            model = CourseThreadContent
 
    return RuntimeCourseThreadContentForm
 
class CourseThreadContentInline(admin.StackedInline):
    model = CourseThreadContent
    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.form = course_thread_content_form_factory(obj.thread) # obj is a Course
        return super(CourseThreadContentInline, self).get_formset(request, obj,
                **kwargs)

class CourseAdmin(admin.ModelAdmin):
    inlines=[CourseAssessmentCategoryInline, CourseEnrollmentInline, CourseSkipDate, AttendanceDateInline, CourseThreadContentInline]
    
    class Media:
        js = [
            "%sjs/jquery-latest.js" % settings.STATIC_URL,
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
        ]


admin.site.register(CommentForCredit,CommentForCreditAdmin)
admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)

# not use reversion yet
admin.site.register(Course, CourseAdmin)
admin.site.register(GradeLevel)
admin.site.register(AssessmentCategory)
admin.site.register(Module,ModuleAdmin)
admin.site.register(StudentAssessmentAttempt)
