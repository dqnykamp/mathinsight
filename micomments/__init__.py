from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from micomments.models import MiComment
from micomments.forms import MiCommentForm

def get_model():
    return MiComment

def get_form():
    return MiCommentForm
