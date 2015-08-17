from django.contrib import admin
from django import forms
from django.db import models
from mitesting.models import Question, Expression, QuestionType, QuestionReferencePage, QuestionSubpart, QuestionAuthor, QuestionAnswerOption, SympyCommandSet
from django.conf import settings
import reversion


class ExpressionInline(admin.TabularInline):
    model = Expression
    fields = ('name', 'expression_type', 'expression', 
              'evaluate_level', 
              'function_inputs', 'random_list_group',
              'post_user_response', 'parse_subscripts', 'sort_order')
    # for now, don't have real_variables showing,
    # as don't have reason for non-real variables

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
        if db_field.name == 'random_list_group':
            field.widget.attrs['size'] = 2
            del field.widget.attrs['class']
        if db_field.name == 'sort_order':
            field.widget.attrs['size'] = 3
        return field


class QuestionSubpartInline(admin.StackedInline):
    model = QuestionSubpart

class QuestionReferencePageInline(admin.TabularInline):
    model = QuestionReferencePage

class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswerOption
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 
                                                           'cols': 10})},
        }
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(QuestionAnswerInline, self).formfield_for_dbfield(
            db_field, **kwargs)
        if db_field.name == 'answer_code':
            field.widget.attrs['size'] = 10
            del field.widget.attrs['class']
        if db_field.name == 'answer':
            field.widget = forms.Textarea(attrs={'rows': 3, 'cols': 15})
        if db_field.name == 'sort_order':
            field.widget.attrs['size'] = 3
        if db_field.name == 'round_on_compare':
            field.widget.attrs['size'] = 3
            del field.widget.attrs['class']
        if db_field.name == 'round_partial_credit':
            field.widget.attrs['size'] = 6
            del field.widget.attrs['class']
        return field

class QuestionAuthorInline(admin.TabularInline):
    model = QuestionAuthor

class QuestionAdmin(reversion.VersionAdmin):
    inlines = [QuestionSubpartInline,ExpressionInline, QuestionAnswerInline, QuestionReferencePageInline, QuestionAuthorInline]
    filter_horizontal = ['allowed_sympy_commands','allowed_user_sympy_commands',
                         'keywords','subjects']
    list_display = ("question_with_number","question_type", "computer_graded", "question_privacy", "solution_privacy")
    list_filter = ("course", "question_type", "question_privacy", "solution_privacy",)
    search_fields = ['id', 'name']
    readonly_fields = ['course', 'base_question']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    fieldsets = (
        (None, {
                'fields': (('name', 'course'),
                           ('base_question'),
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
        ('User commands', {
                'classes': ('collapse',),
                'fields': ('customize_user_sympy_commands', 
                           'allowed_user_sympy_commands',)
                }),
        )


    save_on_top=True
    save_as = True

    class Media:
        js = ["js/django_admin_collapsed_inlines.js",
              "js/save_me_genie.js",
              "mitesting/preselect_sympy_options.js",]


    def save_related(self, request, form, formsets, change):
        super(QuestionAdmin, self).save_related(request, form, formsets, change)

        from mitesting.render_questions import process_expressions_from_answers
        process_expressions_from_answers(form.instance)


class QuestionDatabase(Question):
    class Meta:
        proxy = True
        verbose_name_plural = "Question database"

class QuestionDatabaseAdmin(admin.ModelAdmin):
    inlines = [QuestionSubpartInline,ExpressionInline, QuestionAnswerInline, QuestionReferencePageInline, QuestionAuthorInline]
    filter_horizontal = ['allowed_sympy_commands','allowed_user_sympy_commands',
                         'keywords','subjects']
    list_display = ("question_with_number","question_type", "computer_graded", "question_privacy", "solution_privacy")
    list_filter = ("question_type", "question_privacy", "solution_privacy",)
    search_fields = ['id', 'name']
    readonly_fields = ['course', 'base_question']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    def get_queryset(self, request):
        qs = self.model.question_database.get_queryset()

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    fieldsets = (
        (None, {
                'fields': (('name'),
                           ('base_question'),
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
        ('User commands', {
                'classes': ('collapse',),
                'fields': ('customize_user_sympy_commands', 
                           'allowed_user_sympy_commands',)
                }),
        )


    save_on_top=True
    save_as = True

    class Media:
        js = ["js/django_admin_collapsed_inlines.js",
              "js/save_me_genie.js",
              "mitesting/preselect_sympy_options.js",]


    def save_related(self, request, form, formsets, change):
        super(QuestionAdmin, self).save_related(request, form, formsets, change)

        from mitesting.render_assessments import process_expressions_from_answers
        process_expressions_from_answers(form.instance)



class QuestionTypeAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]

class SympyCommandSetAdmin(reversion.VersionAdmin):
    class Media:
        js = ["js/save_me_genie.js",]



admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionDatabase, QuestionDatabaseAdmin)
admin.site.register(QuestionType, QuestionTypeAdmin)
admin.site.register(SympyCommandSet, SympyCommandSetAdmin)
