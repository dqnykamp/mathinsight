from django.contrib import admin
from django.contrib.comments.models import Comment
from django.utils.translation import ugettext_lazy as _, ungettext

class MyCommentsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type',  'content_object')}
        ),
        (_('Content'),
           {'fields': ('user', 'user_name', 'user_email', 'user_url', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        ),
     )

    readonly_fields= ('content_object','content_type')
    list_display = ('name', 'content_type', 'content_object', 'ip_address', 'submit_date','comment')
    list_filter = ('submit_date',)
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email', 'user_url', 'ip_address')

admin.site.unregister(Comment)
admin.site.register(Comment, MyCommentsAdmin)
