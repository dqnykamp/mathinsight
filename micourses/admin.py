from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import *
from mithreads.models import ThreadContent
from django.conf import settings
import reversion
from django.contrib.auth.models import User

# add reversion to User model
from reversion.helpers import patch_admin
patch_admin(User)

class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s, %s" % (obj.last_name, obj.first_name)

class CourseUserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s, %s" % (obj.user.last_name, obj.user.first_name)


class QuestionStudentAnswerAdmin(reversion.VersionAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['form_class'] = UserChoiceField
        return super(QuestionStudentAnswerAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class CourseAssessmentCategoryInline(admin.TabularInline):
    model = CourseAssessmentCategory


class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'student':
            kwargs['form_class'] = CourseUserChoiceField
        return super(CourseEnrollmentInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class CourseSkipDate(admin.TabularInline):
    model = CourseSkipDate
# class AttendanceDateInline(admin.TabularInline):
#     model = AttendanceDate

# def course_thread_content_form_factory(thread):
#     class RuntimeCourseThreadContentForm(forms.ModelForm):
        
#         thread_content = forms.ModelChoiceField\
#             (label="Thread content", queryset=ThreadContent.objects\
#                  .filter(section__thread=thread)\
#                  .order_by('section__sort_order','sort_order'))
 
#         class Meta:
#             model = CourseThreadContent
#             fields = '__all__'
            
#     return RuntimeCourseThreadContentForm
 
# class CourseThreadContentInline(admin.StackedInline):
#     model = CourseThreadContent

# # Tweak from
# # http://blog.ionelmc.ro/2012/01/19/tweaks-for-making-django-admin-faster/
# # so that don't reload choice options for every record
#     def formfield_for_dbfield(self, db_field, **kwargs):
#         formfield = super(CourseThreadContentInline, self).formfield_for_dbfield(db_field, **kwargs)
#         if db_field.name == 'thread_content' or db_field.name == 'assessment_category' or db_field.name == 'required_for_grade':
#             # dirty trick so queryset is evaluated and cached in .choices
#             formfield.choices = formfield.choices
#         return formfield


#     def get_formset(self, request, obj=None, **kwargs):
#         if obj is not None:
#             self.form = course_thread_content_form_factory(obj.thread) # obj is a Course
#         return super(CourseThreadContentInline, self).get_formset(request, obj,
#                 **kwargs)

# def course_assessment_thread_content_form_factory(thread):
#     class RuntimeAssessmentCourseThreadContentForm(forms.ModelForm):
        
#         thread_content = forms.ModelChoiceField\
#             (label="Thread content", queryset=ThreadContent.objects\
#                  .filter(section__thread=thread)\
#                  .filter(content_type__model='assessment')\
#                  .order_by('section__sort_order','sort_order'))
 
#         class Meta:
#             model = CourseThreadContent
#             fields = '__all__'
 
#     return RuntimeAssessmentCourseThreadContentForm

# class CourseAssessmentThreadContentInline(admin.StackedInline):
#     model = CourseThreadContent
#     def get_queryset(self, request):
#         qs = super(CourseAssessmentThreadContentInline, self).get_queryset(request)
#         return qs.filter(thread_content__content_type__model='assessment')

# # Tweak from
# # http://blog.ionelmc.ro/2012/01/19/tweaks-for-making-django-admin-faster/
# # so that don't reload choice options for every record
#     def formfield_for_dbfield(self, db_field, **kwargs):
#         formfield = super(CourseAssessmentThreadContentInline, self).formfield_for_dbfield(db_field, **kwargs)
#         if db_field.name == 'thread_content' or db_field.name == 'assessment_category' or db_field.name == 'required_for_grade':
#             # dirty trick so queryset is evaluated and cached in .choices
#             formfield.choices = formfield.choices
#         return formfield

#     def get_formset(self, request, obj=None, **kwargs):
#         if obj is not None:
#             self.form = course_assessment_thread_content_form_factory(obj.thread) # obj is a Course
#         return super(CourseAssessmentThreadContentInline, self)\
#             .get_formset(request, obj, **kwargs)


class CourseAdmin(reversion.VersionAdmin):
    inlines=[CourseAssessmentCategoryInline, CourseEnrollmentInline, CourseSkipDate]
    fieldsets = (
        (None, {
                'fields': ('code', ('name',  'short_name'), 'semester',
                           'description', 'active')
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



# class CourseWithThreadContent(Course):
#     class Meta:
#         proxy = True
#         verbose_name_plural = "Courses with thread content"


# class CourseWithThreadContentAdmin(admin.ModelAdmin):
#     inlines=[CourseThreadContentInline,]
#     fieldsets = (
#         (None, {
#                 'fields': ('code', 'name',  'short_name', 'semester',
#                            'description', 'thread', 'active')
#                 }),
#         ('Dates and attendance', {
#                 'classes': ('collapse',),
#                 'fields': ('start_date', 'end_date',
#                            'days_of_week', 
#                            ('track_attendance', 'adjust_due_date_attendance'),
#                            ('last_attendance_date', 'attendance_end_of_week',
#                             'attendance_threshold_percent'),
#                            )
#                 }),
#         )
    
#     class Media:
#         js = [
#             "%sjs/jquery-latest.js" % settings.STATIC_URL,
#             "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
#         ]

#     save_on_top=True


# class CourseWithAssessmentThreadContent(Course):
#     class Meta:
#         proxy = True
#         verbose_name_plural = "Courses with assessment thread content"


# class CourseWithAssessmentThreadContentAdmin(admin.ModelAdmin):
#     inlines=[CourseAssessmentThreadContentInline,]
#     fieldsets = (
#         (None, {
#                 'fields': ('code', 'name',  'short_name', 'semester',
#                            'description', 'thread', 'active')
#                 }),
#         )
    
#     class Media:
#         js = [
#             "%sjs/jquery-latest.js" % settings.STATIC_URL,
#             "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
#         ]

#     save_on_top=True


class AssessmentCategoryAdmin(reversion.VersionAdmin):
    pass


class ManualDueDateAdjustmentAdmin(reversion.VersionAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'student':
            kwargs['form_class'] = CourseUserChoiceField
        return super(ManualDueDateAdjustmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class StudentContentAttemptAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'student':
            kwargs['form_class'] = CourseUserChoiceField
        return super(StudentContentAttemptAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class StudentContentCompletionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'student':
            kwargs['form_class'] = CourseUserChoiceField
        return super(StudentContentCompletionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)
admin.site.register(Course, CourseAdmin)
#admin.site.register(CourseWithThreadContent, CourseWithThreadContentAdmin)
#admin.site.register(CourseWithAssessmentThreadContent, CourseWithAssessmentThreadContentAdmin)
admin.site.register(AssessmentCategory,AssessmentCategoryAdmin)
admin.site.register(ManualDueDateAdjustment, ManualDueDateAdjustmentAdmin)

admin.site.register(StudentContentAttempt, StudentContentAttemptAdmin)
admin.site.register(StudentContentCompletion, StudentContentCompletionAdmin)
admin.site.register(StudentContentAttemptSolutionView)
