from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib import admin
from django import forms
from django.db import models
from mitesting.models import Question, Assessment,  QuestionAssigned, QuestionSetDetail, Expression, QuestionType, QuestionReferencePage, QuestionSubpart, QuestionAuthor, AssessmentType, QuestionAnswerOption, SympyCommandSet, PlotFunction, AssessmentBackgroundPage
from django.conf import settings
import reversion

class QuestionAssignedInline(admin.TabularInline):
    model = QuestionAssigned
class QuestionSetDetailInline(admin.TabularInline):
    model = QuestionSetDetail
class AssessmentBackgroundPageInline(admin.TabularInline):
    model = AssessmentBackgroundPage
class AssessmentAdmin(reversion.VersionAdmin):
    inlines = [QuestionAssignedInline,QuestionSetDetailInline,AssessmentBackgroundPageInline]
    list_display = ("code","name", "assessment_type")
    list_filter = ("assessment_type",)
    search_fields = ['code', 'name', 'short_name']
    readonly_fields = ('privacy_level_description',
                       'privacy_level_solution_description',)
    save_on_top=True
    save_as = True

    fieldsets = (
        (None, {
                'fields': (('code', 'short_name'),
                           'name', 
                          'assessment_type', 
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
                'fields': ('description', 'detailed_description', )
                }),
        ('Instructions', {
                'classes': ('collapse',),
                'fields': ('instructions', 'instructions2' )
                }),
        ('Notes', {
                'classes': ('collapse',),
                'fields': ('notes', )
                }),
        ('Other configurations', {
                'fields': (('total_points', 'time_limit',),
                           ('allow_solution_buttons', 'fixed_order', 'nothing_random'),
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

class ExpressionInline(admin.TabularInline):
    model = Expression
    fields = ('name', 'expression_type', 'expression', 'expand',
              'evaluate_level', 'n_digits', 'round_decimals', 
              'use_ln', 'function_inputs', 'collapse_equal_tuple_elements',
              'output_no_delimiters', 'group', 'sort_order')

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ExpressionInline, self).formfield_for_dbfield(db_field,
                                                                    **kwargs)
        if db_field.name == 'name':
            field.widget.attrs['size'] = 10
            del field.widget.attrs['class']
        if db_field.name == 'expression':
            field.widget = forms.Textarea(attrs={'rows': 2, 'cols': 30})
        if db_field.name == 'function_inputs':
            field.widget.attrs['size'] = 5
            del field.widget.attrs['class']
        if db_field.name == 'group':
            field.widget.attrs['size'] = 2
            del field.widget.attrs['class']
        if db_field.name == 'sort_order':
            field.widget.attrs['size'] = 3
        if db_field.name == 'n_digits':
            field.widget.attrs['size'] = 3
            del field.widget.attrs['class']
        if db_field.name == 'round_decimals':
            field.widget.attrs['size'] = 3
            del field.widget.attrs['class']
        return field

class PlotFunctionInline(admin.TabularInline):
    model = PlotFunction
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

class QuestionSubpartInline(admin.StackedInline):
    model = QuestionSubpart

class QuestionReferencePageInline(admin.TabularInline):
    model = QuestionReferencePage

class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswerOption
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'cols': 30})},
        }

class QuestionAuthorInline(admin.TabularInline):
    model = QuestionAuthor

class QuestionAdmin(reversion.VersionAdmin):
    inlines = [QuestionSubpartInline,ExpressionInline, PlotFunctionInline, QuestionAnswerInline, QuestionReferencePageInline, QuestionAuthorInline]
    filter_horizontal = ['allowed_sympy_commands','keywords','subjects']
    list_display = ("question_with_number","question_type", "question_privacy", "solution_privacy")
    list_filter = ("question_type", "question_privacy", "solution_privacy",)
    search_fields = ['id', 'name']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    fieldsets = (
        (None, {
                'fields': ('name', 
                           ('question_type', 'question_privacy', 'solution_privacy'),
                           ('computer_graded',
                            'show_solution_button_after_attempts',),
                           'description', 
                           ('question_spacing', 'css_class',),
                           'question_text', 
                           )
                }),
        ('Solution', {
                'classes': ('collapse',),
                'fields': ('solution_text', )
                }),
        ('Hint', {
                'classes': ('collapse',),
                'fields': ('hint_text', )
                }),
        ('Notes', {
                'classes': ('collapse',),
                'fields': ('notes', )
                }),
        ('Meta data', {
                'classes': ('collapse',),
                'fields': ('keywords', 'subjects',)
                }),
        ('Commands', {
                'fields': ('allowed_sympy_commands',)
                }),
        )


    save_on_top=True
    save_as = True

    class Media:
        js = ["js/django_admin_collapsed_inlines.js",
              "js/save_me_genie.js",
              "mitesting/preselect_sympy_options.js",]


class QuestionTypeAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]

class AssessmentTypeAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]

class SympyCommandSetAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]



admin.site.register(Question, QuestionAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(QuestionType, QuestionTypeAdmin)
admin.site.register(AssessmentType, AssessmentTypeAdmin)
admin.site.register(SympyCommandSet, SympyCommandSetAdmin)
