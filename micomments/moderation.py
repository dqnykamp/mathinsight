from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib.comments.moderation import CommentModerator
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template import Context, loader
from django.contrib.sites.models import Site

class ModeratorWithoutObject(CommentModerator):
    email_notification = True

    def email(self, comment, content_object, request):
        """
        Send email notification of a new comment to site staff when email
        notifications have been requested.

        """
        if not self.email_notification:
            return
        recipient_list = [manager_tuple[1] for manager_tuple in settings.MANAGERS]
        t = loader.get_template('comments/comment_notification_email_without_object.txt')
        c = Context({ 'comment': comment,
                      'content_object': content_object })
        subject = '[%s] New message posted' % (Site.objects.get_current().name)
        message = t.render(c)
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL,
                             recipient_list,
                             headers = {'Reply-To': comment.user_email})
        email.send(fail_silently=True)
        #send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)

class ModeratorWithObject(CommentModerator):
    email_notification = True

    def email(self, comment, content_object, request):
        """
        Send email notification of a new comment to site staff when email
        notifications have been requested.

        """
        if not self.email_notification:
            return
        recipient_list = [manager_tuple[1] for manager_tuple in settings.MANAGERS]
        t = loader.get_template('comments/comment_notification_email.txt')
        c = Context({ 'comment': comment,
                      'content_object': content_object,
                      'hostname': Site.objects.get_current().domain })
        if comment.credit_eligible:
            subject = '[%s] New %s message posted on "%s"'\
                % (Site.objects.get_current().name,
                   comment.credit_group,
                   content_object.annotated_title())

        else:
            subject = '[%s] New message posted on "%s"' \
                % (Site.objects.get_current().name,
                   content_object.annotated_title())
        message = t.render(c)
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL,
                             recipient_list,
                             headers = {'Reply-To': comment.user_email})
        email.send(fail_silently=True)
        #send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)


