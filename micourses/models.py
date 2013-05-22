from django.db import models
from django.contrib.auth.models import User, Group
from midocs.models import Page, Video
from mitesting.models import Question


class CommentForCredit(models.Model):
    page = models.ForeignKey(Page)
    group = models.ForeignKey(Group)
    opendate = models.DateTimeField()
    deadline = models.DateTimeField()
    
    def __unicode__(self):
        return "%s deadline" % self.page.code


class QuestionStudentAnswer(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    answer = models.CharField(max_length=400)
    seed = models.CharField(max_length=50, blank=True, null=True)
    credit = models.FloatField()
    datetime =  models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return  "%s" % self.answer
 
