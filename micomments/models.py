from django.db import models
from django_comments.models import Comment
from django.core.exceptions import ObjectDoesNotExist
import datetime
from django.contrib.auth.models import Group

class MiComment(Comment):
    credit_eligible = models.BooleanField(default=False)
    credit = models.BooleanField(default=False)
    credit_group = models.ForeignKey(Group, null=True, blank=True)

    # def save(self, *args, **kwargs):
    #     # if it is being saved for the first time
    #     if not self.pk:
    #         # if posted by an authenticated user
    #         if self.user:
    #             # if posted on a Page
    #             if self.content_type.model=='page':
    #                 thepage=self.content_object
                  
    #                 # set credit eligible if before deadline
    #                 # of a comment for credit entry of user's group
    #                 for thegroup in self.user.groups.all():
    #                     try:
    #                         cfc = CommentForCredit.objects.get(page=thepage, 
    #                                                            group=thegroup)
    #                         if datetime.datetime.now() < cfc.deadline \
    #                                 and datetime.datetime.now() > cfc.opendate:
    #                             self.credit_eligible=True
    #                             self.credit_group=thegroup
    #                             break
    #                     except ObjectDoesNotExist:
    #                         pass


    #     super(MiComment, self).save(*args, **kwargs) 
 



