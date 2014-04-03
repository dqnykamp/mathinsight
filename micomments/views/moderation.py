from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from django.conf import settings
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.comments.views.utils import next_redirect, confirmation_view
from django.contrib import comments
from django.contrib.comments import signals
from django.views.decorators.csrf import csrf_protect

@csrf_protect
@permission_required("comments.can_moderate")
def credit(request, comment_id, next=None):
    """
    Credit a comment (that is, mark it as public and non-removed). Confirmation
    on GET, action on POST. Requires the "can moderate comments" permission.

    Templates: `comments/credit.html`,
    Context:
        comment
            the `comments.comment` object for approval
    """
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    # Delete on POST
    if request.method == 'POST':
        # Flag the comment as creditd.
        perform_credit(request, comment)
        return next_redirect(request.POST.copy(), next, credit_done, c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/credit.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )

# The following functions actually perform the various flag/aprove/delete
# actions. They've been broken out into seperate functions to that they
# may be called from admin actions.

def perform_credit(request, comment):
    flag, created = comments.models.CommentFlag.objects.get_or_create(
        comment = comment,
        user    = request.user,
        flag    = comments.models.CommentFlag.MODERATOR_APPROVAL,
    )

    comment.credit = True
    comment.save()

    signals.comment_was_flagged.send(
        sender  = comment.__class__,
        comment = comment,
        flag    = flag,
        created = created,
        request = request,
    )

# Confirmation views.

credit_done = confirmation_view(
    template = "comments/credited.html",
    doc = 'Displays a "comment was credited" success page.'
)
