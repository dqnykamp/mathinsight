from django.contrib import admin
#from django.contrib.comments.models import Comment
from django.utils.translation import ugettext_lazy as _, ungettext
from micomments.models import MiComment
from micomments.views.moderation import perform_credit

class MiCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type',  'content_object')}
        ),
        (_('Content'),
           {'fields': ('user', 'user_name', 'user_email', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'ip_address', 'credit', 'credit_eligible', 'credit_group',)}
        ),
     )

    readonly_fields= ('content_object','content_type')
    list_display = ('name', 'content_type', 'content_object', 'ip_address', 'submit_date','comment')
    list_filter = ('submit_date',)
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email', 'user_url', 'ip_address')


class MiCommentToCredit(MiComment):
    class Meta:
        proxy = True
        verbose_name_plural = "Mi comments to credit"


class MiCommentToCreditAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type',  'content_object')}
        ),
        (_('Content'),
           {'fields': ('user', 'user_name', 'user_email', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'ip_address', 'credit', 'credit_eligible', 'credit_group',)}
        ),
     )

    readonly_fields= ('content_object','content_type')
    list_display = ('name', 'content_type', 'content_object', 'submit_date','credit','comment')
    list_editable = ('credit',)
    list_filter = ('submit_date','user__groups')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email')
    actions = ["credit_comments", ]


    # only include comments eligible for credit
    def queryset(self, request):
        qs = super(MiCommentToCreditAdmin, self).queryset(request)
        return qs.filter(credit_eligible=True)



    def get_actions(self, request):
        actions = super(MiCommentToCreditAdmin, self).get_actions(request)
        actions.pop('delete_selected')  # don't delete from this view
        if not request.user.has_perm('comments.can_moderate'):
            if 'credit_comments' in actions:
                actions.pop('credit_comments')
        return actions

    def credit_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_credit,
                        lambda n: ungettext('creditd', 'creditd', n))
    credit_comments.short_description = _("Credit selected comments")

    def _bulk_flag(self, request, queryset, action, done_message):
        """
        Credit some comments from an admin action. Actually
        calls the `action` argument to perform the heavy lifting.
        """
        n_comments = 0
        for comment in queryset:
            action(request, comment)
            n_comments += 1

        msg = ungettext(u'1 comment was successfully %(action)s.',
                        u'%(count)s comments were successfully %(action)s.',
                        n_comments)
        self.message_user(request, msg % {'count': n_comments, 'action': done_message(n_comments)})

#admin.site.unregister(Comment)
admin.site.register(MiComment, MiCommentAdmin)
admin.site.register(MiCommentToCredit, MiCommentToCreditAdmin)
