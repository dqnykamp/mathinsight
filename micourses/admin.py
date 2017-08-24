from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import *
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

class CourseGradeCategoryInline(admin.TabularInline):
    model = CourseGradeCategory

class CourseURLInline(admin.TabularInline):
    model = CourseURL

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
#         if db_field.name == 'thread_content' or db_field.name == 'grade_category' or db_field.name == 'required_for_grade':
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
#         if db_field.name == 'thread_content' or db_field.name == 'grade_category' or db_field.name == 'required_for_grade':
#             # dirty trick so queryset is evaluated and cached in .choices
#             formfield.choices = formfield.choices
#         return formfield

#     def get_formset(self, request, obj=None, **kwargs):
#         if obj is not None:
#             self.form = course_assessment_thread_content_form_factory(obj.thread) # obj is a Course
#         return super(CourseAssessmentThreadContentInline, self)\
#             .get_formset(request, obj, **kwargs)


class CourseAdmin(reversion.VersionAdmin):
    inlines=[CourseGradeCategoryInline, CourseSkipDate, CourseURLInline]
    fieldsets = (
        (None, {
                'fields': ('code', ('name',  'short_name'), 'semester',
                           'description', 'sort_order', ('active', 'calculate_course_total', 'skip_assessment_overview'))
                }),
        ('Dates and attendance', {
                'classes': ('collapse',),
                'fields': ('start_date', 'end_date',
                           'days_of_week', 
                           ('track_attendance', 'adjust_due_attendance'),
                           ('last_attendance_date', 'attendance_end_of_week',
                            'attendance_threshold_percent'),
                           'attendance_time_zone',
                           )
                }),
        )
    
    class Media:
        js = [
            "%sjs/jquery-latest.js" % settings.STATIC_URL,
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
        ]

    save_on_top=True



class CourseWithEnrollment(Course):
    class Meta:
        proxy = True
        verbose_name_plural = "Courses with enrollment"


class CourseWithEnrollmentAdmin(admin.ModelAdmin):
    inlines=[CourseEnrollmentInline,]
    fieldsets = (
        (None, {
                'fields': ('code', ('name',  'short_name'), 'semester',
                           'description', ('active', 'calculate_course_total'))
                }),
        ('Dates and attendance', {
                'classes': ('collapse',),
                'fields': ('start_date', 'end_date',
                           'days_of_week', 
                           ('track_attendance', 'adjust_due_attendance'),
                           ('last_attendance_date', 'attendance_end_of_week',
                            'attendance_threshold_percent'),
                           'attendance_time_zone',
                           )
                }),
        )
    class Media:
        js = [
            "%sjs/jquery-latest.js" % settings.STATIC_URL,
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
        ]

    save_on_top=True


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


class GradeCategoryAdmin(reversion.VersionAdmin):
    pass

class QuestionAssignedInline(admin.TabularInline):
    model = QuestionAssigned
class QuestionSetDetailInline(admin.TabularInline):
    model = QuestionSetDetail
class AssessmentBackgroundPageInline(admin.TabularInline):
    model = AssessmentBackgroundPage
class AssessmentAdmin(reversion.VersionAdmin):
    inlines = [QuestionAssignedInline,QuestionSetDetailInline,AssessmentBackgroundPageInline]
    list_display = ("code","name", "assessment_type")
    list_filter = ("course", "assessment_type",)
    search_fields = ['code', 'name', 'short_name']
    readonly_fields = ('privacy_level_description',
                       'privacy_level_solution_description',)
    save_on_top=True
    save_as = True

    fieldsets = (
        (None, {
                'fields': (('code', 'short_name'),
                           'name', 
                           ('assessment_type', 'course'),
                           ('privacy_level_description',
                           'privacy_level_solution_description'),
                           ) 
                }),
        ('Privacy overrides', {
                'classes': ('collapse',),
                'fields': ('groups_can_view', 'groups_can_view_solution', )
                }),
        ('Description', {
                'classes': ('collapse',),
                'fields': ('description', )
                }),
        ('Front Matter', {
                'classes': ('collapse',),
                'fields': ('name_section_override', 'front_matter', 'front_matter2' )
                }),
        ('Notes', {
                'classes': ('collapse',),
                'fields': ('notes', )
                }),
        ('Other configurations', {
                'fields': (('fixed_order', 'single_version', 'handwritten'),
                           )
                }),
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(AssessmentAdmin, self).formfield_for_dbfield(db_field,
                                                                    **kwargs)
        if db_field.name == 'name':
            field.widget.attrs['size'] = 50
            del field.widget.attrs['class']
        if db_field.name == 'description':
            field.widget.attrs['size'] = 60
            del field.widget.attrs['class']
        if db_field.name == 'total_points':
            field.widget.attrs['size'] = 3
        if db_field.name == 'time_limit':
            field.widget.attrs['size'] = 20
            del field.widget.attrs['class']
        return field
    class Media:
        js = ["js/save_me_genie.js",]

class AssessmentTypeAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]



admin.site.register(Course, CourseAdmin)
admin.site.register(CourseWithEnrollment, CourseWithEnrollmentAdmin)
#admin.site.register(CourseWithAssessmentThreadContent, CourseWithAssessmentThreadContentAdmin)
admin.site.register(GradeCategory,GradeCategoryAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(AssessmentType, AssessmentTypeAdmin)


