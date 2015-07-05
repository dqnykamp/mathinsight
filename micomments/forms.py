from django import forms
from django_comments.forms import CommentForm
from micomments.models import MiComment
import re

class MiCommentForm(CommentForm):
    def get_comment_model(self):
        # Use our custom comment model instead of the built-in one.
        return MiComment

    def get_comment_create_data(self):
        # Use the data of the superclass, and add in the credit field
        data = super(MiCommentForm, self).get_comment_create_data()
        data['credit'] = False
        
        return data

    def clean_comment(self):
        """
        Don't allow any hyperlinks in comments
        """
        comment = self.cleaned_data["comment"]
        if "http://" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "https://" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "http&gt;//" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "http>//" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "<a href" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "&lt;a href" in comment.lower():
            raise forms.ValidationError("Sorry, links are not allowed in messages.")
        if "mathinsight.org" in comment.lower():
            raise forms.ValidationError("Sorry, we're now rejecting messages containing 'mathinsight.org' since many spammers seem to be using that.")

        return comment
