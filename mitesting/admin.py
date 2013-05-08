from django.contrib import admin
from django import forms
from django.db import models
from mitesting.models import Question, Assessment,  QuestionAssigned, QuestionSetDetail, RandomNumber, RandomWord, Expression, QuestionType, QuestionReferencePage, QuestionSubpart, AssessmentType, QuestionSpacing, QuestionAnswerOption, SympyCommandSet, PlotFunction
import settings

class QuestionAssignedInline(admin.TabularInline):
    model = QuestionAssigned
class QuestionSetDeatilInline(admin.TabularInline):
    model = QuestionSetDetail

class AssessmentAdmin(admin.ModelAdmin):
    inlines = [QuestionAssignedInline,QuestionSetDeatilInline]
    list_display = ("code","name")
    search_fields = ['code', 'name']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True
    save_as = True


class RandomNumberInline(admin.TabularInline):
    model = RandomNumber

class RandomWordInline(admin.TabularInline):
    model = RandomWord

class ExpressionInline(admin.TabularInline):
    model = Expression
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

class PlotFunctionInline(admin.TabularInline):
    model = PlotFunction
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

class QuestionSubpartInline(admin.StackedInline):
    model = QuestionSubpart

class QuestionReferencePageInline(admin.TabularInline):
    model = QuestionReferencePage

class QuestionAnswerInline(admin.StackedInline):
    model = QuestionAnswerOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionSubpartInline,RandomNumberInline,RandomWordInline,ExpressionInline, PlotFunctionInline, QuestionAnswerInline, QuestionReferencePageInline]
    filter_horizontal = ['allowed_sympy_commands','keywords','subjects']
    search_fields = ['id', 'name']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    fieldsets = (
        (None, {
                'fields': ('name', 'question_type', 
                           'description', 'video', 'question_spacing', 'css_class',
                           'question_text', 'solution_text',
                           'hint_text', 'notes',
                           'question_javascript', 'solution_javascript', 'show_solution_button_after_attempts',
                           'allowed_sympy_commands', 'keywords', 'subjects',)
                }),
        # ('Optional', {
        #         'classes': ('collapse',),
        #         'fields': ('publish_date','notes', 'author_copyright','worksheet', 'hidden', 'additional_credits','level','objectives','notation_systems','highlight'),
        #         }),
        )


    save_on_top=True
    save_as = True

    class Media:
        js = [
            "%sjs/jquery-latest.js" % settings.STATIC_URL,
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
        ]


admin.site.register(Question, QuestionAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(QuestionType)
admin.site.register(AssessmentType)
admin.site.register(QuestionSpacing)
admin.site.register(SympyCommandSet)
