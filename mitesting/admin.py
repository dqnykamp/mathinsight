from django.contrib import admin
from django import forms
from django.db import models
from mitesting.models import Question, Assessment,  QuestionAssigned, QuestionSetDetail, RandomNumber, RandomWord, Expression, QuestionType, QuestionPermission, QuestionReferencePage, QuestionSubpart, AssessmentType, QuestionSpacing, QuestionAnswerOption, SympyCommandSet, PlotFunction, AssessmentBackgroundPage
import settings
import reversion

class QuestionAssignedInline(admin.TabularInline):
    model = QuestionAssigned
class QuestionSetDeatilInline(admin.TabularInline):
    model = QuestionSetDetail
class AssessmentBackgroundPageInline(admin.TabularInline):
    model = AssessmentBackgroundPage
class AssessmentAdmin(reversion.VersionAdmin):
    inlines = [QuestionAssignedInline,QuestionSetDeatilInline,AssessmentBackgroundPageInline]
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


class QuestionAdmin(reversion.VersionAdmin):
    inlines = [QuestionSubpartInline,RandomNumberInline,RandomWordInline,ExpressionInline, PlotFunctionInline, QuestionAnswerInline, QuestionReferencePageInline]
    filter_horizontal = ['allowed_sympy_commands','keywords','subjects']
    search_fields = ['id', 'name']
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    fieldsets = (
        (None, {
                'fields': ('name', 'question_type', 'question_permission',
                           'description', 'video', 'question_spacing', 'css_class',
                           'question_text', 'solution_text',
                           'hint_text', 'notes',
                           'show_solution_button_after_attempts',
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


class QuestionTypeAdmin(reversion.VersionAdmin):
    pass

class QuestionPermissionAdmin(reversion.VersionAdmin):
    pass

class AssessmentTypeAdmin(reversion.VersionAdmin):
    pass

class QuestionSpacingAdmin(reversion.VersionAdmin):
    pass

class SympyCommandSetAdmin(reversion.VersionAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(QuestionType, QuestionTypeAdmin)
admin.site.register(QuestionPermission, QuestionPermissionAdmin)
admin.site.register(AssessmentType, AssessmentTypeAdmin)
admin.site.register(QuestionSpacing, QuestionSpacingAdmin)
admin.site.register(SympyCommandSet, SympyCommandSetAdmin)
