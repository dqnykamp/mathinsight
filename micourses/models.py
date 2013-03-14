from django.db import models
from django.contrib.auth.models import User, Group
from midocs.models import Page, Video, Question, QuestionAnswerOption


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
    answer = models.ForeignKey(QuestionAnswerOption)
    datetime =  models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return  "%s" % self.answer

    def clean(self):
        # check if answer is for the question.  If not, raise exception
        if self.question != self.answer.question:
            raise ValidationError, "Not a possible answer for question: %s"\
                % self.question
 
