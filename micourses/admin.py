from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import CommentForCredit, QuestionStudentAnswer
import reversion

class QuestionStudentAnswerAdmin(reversion.VersionAdmin):
    pass

class CommentForCreditAdmin(reversion.VersionAdmin):
    pass


admin.site.register(CommentForCredit,CommentForCreditAdmin)
admin.site.register(QuestionStudentAnswer,QuestionStudentAnswerAdmin)
