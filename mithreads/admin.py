from django.contrib import admin
from django import forms
from django.db import models
from mithreads.models import Thread, ThreadSection, ThreadContent
#from django.contrib.contenttypes import generic

class ThreadSectionInline(admin.TabularInline):
    model = ThreadSection

class ThreadAdmin(admin.ModelAdmin):
    inlines=[ThreadSectionInline]

class ThreadContentInline(admin.TabularInline):
    model = ThreadContent

class ThreadSectionAdmin(admin.ModelAdmin):
    inlines=[ThreadContentInline]
    list_display = ('__unicode__', 'thread', 'first_content_title')
    list_filter = ('thread',)

    search_fields = ['name','thread__name','code',
                     ]
    save_on_top=True

admin.site.register(Thread,ThreadAdmin)
admin.site.register(ThreadSection,ThreadSectionAdmin)
