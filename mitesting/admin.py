from django.contrib import admin
from django import forms
from django.db import models
from mitesting.models import Question, Assessment,  QuestionAssigned, QuestionSetDetail, RandomNumber, RandomWord, Expression, QuestionType, QuestionReferencePage, QuestionSubpart, AssessmentType, QuestionSpacing, QuestionAnswerOption, SympyCommandSet, MathWriteinAnswer
import settings

class QuestionAssignedInline(admin.TabularInline):
    model = QuestionAssigned
class QuestionSetDeatilInline(admin.TabularInline):
    model = QuestionSetDetail

class AssessmentAdmin(admin.ModelAdmin):
    inlines = [QuestionAssignedInline,QuestionSetDeatilInline]
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

class QuestionSubpartInline(admin.StackedInline):
    model = QuestionSubpart

class QuestionReferencePageInline(admin.TabularInline):
    model = QuestionReferencePage

class QuestionAnswerInline(admin.StackedInline):
    model = QuestionAnswerOption

class MathWriteinAnswer(admin.TabularInline):
    model = MathWriteinAnswer

class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionSubpartInline,RandomNumberInline,RandomWordInline,ExpressionInline, QuestionAnswerInline, MathWriteinAnswer,QuestionReferencePageInline]
    filter_horizontal = ['allowed_sympy_commands',]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }

    fieldsets = (
        (None, {
                'fields': ('name', 'question_type', 
                           'description', 'video', 'question_spacing', 'css_class',
                           'question_text', 'solution_text',
                           'hint_text', 'allow_expand',
                           'allowed_sympy_commands',)
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
