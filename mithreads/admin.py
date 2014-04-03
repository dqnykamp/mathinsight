from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib import admin
from django import forms
from django.db import models
from mithreads.models import Thread, ThreadSection, ThreadContent
import reversion
#from django.contrib.contenttypes import generic

class ThreadSectionInline(admin.TabularInline):
    model = ThreadSection

class ThreadAdmin(reversion.VersionAdmin):
    inlines=[ThreadSectionInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }

class ThreadContentInline(admin.TabularInline):
    model = ThreadContent

class ThreadSectionAdmin(reversion.VersionAdmin):
    inlines=[ThreadContentInline]
    list_display = ('__unicode__', 'thread', 'first_content_title')
    list_filter = ('thread',)

    search_fields = ['name','thread__name','code',
                     ]
    save_on_top=True

admin.site.register(Thread,ThreadAdmin)
admin.site.register(ThreadSection,ThreadSectionAdmin)
