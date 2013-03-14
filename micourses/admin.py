from django.contrib import admin
from django import forms
from django.db import models
from micourses.models import CommentForCredit, QuestionStudentAnswer

admin.site.register(CommentForCredit)
admin.site.register(QuestionStudentAnswer)
