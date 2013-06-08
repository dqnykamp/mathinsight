from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import QuestionStudentAnswer, Course, GradeLevel, AssessmentCategory, CourseAssessmentCategory,CourseEnrollment, AttendanceDate, CourseSkipDate, CourseThreadContent
from mithreads.models import ThreadContent
import settings
import reversion

class QuestionStudentAnswerAdmin(reversion.VersionAdmin):
    pass

class CourseAssessmentCategoryInline(admin.TabularInline):
    model = CourseAssessmentCategory
class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
class CourseSkipDate(admin.TabularInline):
    model = CourseSkipDate
# class AttendanceDateInline(admin.TabularInline):
#     model = AttendanceDate

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
    inlines=[CourseAssessmentCategoryInline, CourseThreadContentInline, CourseEnrollmentInline, CourseSkipDate]
    fieldsets = (
        (None, {
                'fields': ('code', 'name',  'short_name', 'semester',
                           'description', 'thread', 'active')
                }),
        ('Dates and attendance', {
                'classes': ('collapse',),
                'fields': ('start_date', 'end_date',
                           'days_of_week', 
                           ('track_attendance', 'adjust_due_date_attendance'),
                           ('last_attendance_date', 'attendance_end_of_week',
                            'attendance_threshold_percent'),
                           )
                }),
        )
    
    class Media:
        js = [
            "%sjs/jquery-latest.js" % settings.STATIC_URL,
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
        ]

    save_on_top=True

admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)

# not use reversion yet
admin.site.register(Course, CourseAdmin)
admin.site.register(GradeLevel)
admin.site.register(AssessmentCategory)
