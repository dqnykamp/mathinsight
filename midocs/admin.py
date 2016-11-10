from django.contrib import admin
from django import forms
from django.db import models
from midocs.models import NotationSystem, Author, PageType, Objective, Subject, Keyword, RelationshipType, Page, PageAuthor, PageRelationship, IndexType, IndexEntry, ImageType, Image, ImageAuthor, ImageNotationSystem, AppletType, AppletTypeParameter, AppletFeature, Applet, AppletParameter, AppletAuthor, AppletNotationSystem, VideoType, VideoTypeParameter, Video, VideoParameter, VideoAuthor, VideoQuestion, NewsItem, NewsAuthor, Reference, ReferenceType, ReferenceAuthor, AuxiliaryFile, AuxiliaryFileType, AppletObjectType, AppletObject, AppletChildObjectLink, AppletText, CopyrightType

from django.conf import settings
import reversion

class AppletTypeParameterInline(admin.TabularInline):
    model = AppletTypeParameter
    extra = 3

class AppletTypeAdmin(reversion.VersionAdmin):
    inlines = [AppletTypeParameterInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }


def applet_parameter_form_factory(applet_type):
    class RuntimeAppletParameterForm(forms.ModelForm):
        
        parameter = forms.ModelChoiceField(label="Parameter",
                queryset=AppletTypeParameter.objects.filter(applet_type=applet_type))
 
        class Meta:
            fields='__all__'
            model = AppletParameter
 
    return RuntimeAppletParameterForm
 
class AppletParameterInline(admin.TabularInline):
    model = AppletParameter
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }
 
    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.form = applet_parameter_form_factory(obj.applet_type) # obj is a Applet
        return super(AppletParameterInline, self).get_formset(request, obj,
                **kwargs)

# class AppletInPagesInline(admin.TabularInline):
#     model = Applet.in_pages.through

class AppletObjectInline(admin.TabularInline):
    model = AppletObject
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(AppletObjectInline, self).formfield_for_dbfield(db_field,
                                                                      **kwargs)
        if db_field.name == 'name':
            field.widget.attrs['size'] = 15
            del field.widget.attrs['class']
        if db_field.name == 'related_objects':
            field.widget.attrs['size'] = 10
            del field.widget.attrs['class']
        if db_field.name == 'name_for_changes':
            field.widget.attrs['size'] = 10
            del field.widget.attrs['class']
        if db_field.name == 'category_for_capture':
            field.widget.attrs['size'] = 20
            del field.widget.attrs['class']
        if db_field.name == 'function_input_variable':
            field.widget.attrs['size'] = 2
            del field.widget.attrs['class']
        if db_field.name == 'default_value':
            field.widget.attrs['size'] = 5
            del field.widget.attrs['class']
        if db_field.name == 'sort_order':
            field.widget.attrs['size'] = 3
        return field

class AppletChildObjectLinkInline(admin.TabularInline):
    model = AppletChildObjectLink

class AppletAuthorInline(admin.TabularInline):
    model = AppletAuthor

class AppletNotationSystemInline(admin.TabularInline):
    model = AppletNotationSystem

class AppletTextInline(admin.StackedInline):
    model = AppletText

class AppletAdmin(reversion.VersionAdmin):
    inlines = [AppletParameterInline, AppletObjectInline, AppletChildObjectLinkInline, AppletTextInline, AppletAuthorInline,AppletNotationSystemInline]
    # inlines = [AppletParameterInline, AppletInPagesInline]
    exclude = ('in_pages',)
    list_filter = ("applet_type",)
    list_display = ("code","title","applet_type")
    filter_horizontal = ['features','keywords','subjects']
    search_fields = ['code', 'title','applet_type__code']
    save_on_top=True
    save_as=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }

    class Media:
        js = [
            "%sjs/django_admin_collapsed_inlines.js" % settings.STATIC_URL,
            "%sjs/save_me_genie.js" % settings.STATIC_URL,
        ]

class AppletHighlight(Applet):
    class Meta:
        proxy = True


class AppletHighlightAdmin(admin.ModelAdmin):
    list_display = ('code','title', 'highlight')
    list_editable = ('highlight',)
    search_fields = ['code', 'title']
    fields=('code','title','description','highlight','thumbnail','thumbnail_width','thumbnail_height')
    readonly_fields = ('code','title','description',)
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    ordering=('-highlight',)
    

    def has_add_permission(self, request):
        return False


class VideoTypeParameterInline(admin.TabularInline):
    model = VideoTypeParameter
    extra = 3

class VideoTypeAdmin(reversion.VersionAdmin):
    inlines = [VideoTypeParameterInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }


def video_parameter_form_factory(video_type):
    class RuntimeVideoParameterForm(forms.ModelForm):
        
        parameter = forms.ModelChoiceField(label="Parameter",
                queryset=VideoTypeParameter.objects.filter(video_type=video_type))
 
        class Meta:
            model = VideoParameter
            fields='__all__'
 
    return RuntimeVideoParameterForm
 
class VideoParameterInline(admin.TabularInline):
    model = VideoParameter
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }
 
    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.form = video_parameter_form_factory(obj.video_type) # obj is a Video
        return super(VideoParameterInline, self).get_formset(request, obj,
                **kwargs)

# class VideoInPagesInline(admin.TabularInline):
#     model = Video.in_pages.through

class VideoAuthorInline(admin.TabularInline):
    model = VideoAuthor

class VideoQuestionInline(admin.TabularInline):
    model = VideoQuestion


class VideoAdmin(reversion.VersionAdmin):
    inlines = [VideoParameterInline, VideoAuthorInline, VideoQuestionInline]
    # inlines = [VideoParameterInline, VideoInPagesInline]
    exclude = ('in_pages',)
    list_display = ("code","title","video_type")
    filter_horizontal = ['keywords','subjects']
    search_fields = ['code', 'title','video_type__code']
    save_on_top=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }

    class Media:
        js = [
            "%sjs/save_me_genie.js" % settings.STATIC_URL,
        ]

class VideoHighlight(Video):
    class Meta:
        proxy = True


class VideoHighlightAdmin(admin.ModelAdmin):
    list_display = ('code','title', 'highlight')
    list_editable = ('highlight',)
    search_fields = ['code', 'title']
    fields=('code','title','description','highlight','thumbnail','thumbnail_width','thumbnail_height')
    readonly_fields = ('code','title','description',)
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    ordering=('-highlight',)
    

    def has_add_permission(self, request):
        return False



# class ImageInPagesInline(admin.TabularInline):
#     model = Image.in_pages.through

class ImageAuthorInline(admin.TabularInline):
    model = ImageAuthor

class ImageNotationSystemInline(admin.TabularInline):
    model = ImageNotationSystem

class ImageAdmin(reversion.VersionAdmin):
    inlines = [ImageAuthorInline,ImageNotationSystemInline]
    exclude = ('in_pages',)
    list_display = ("code", "title", "imagefile")
    filter_horizontal = ['keywords','subjects']
    search_fields = ['code', 'title', 'imagefile']
    save_on_top=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }

    class Media:
        js = [
            "%sjs/save_me_genie.js" % settings.STATIC_URL,
        ]

class PageRelationshipInline(admin.TabularInline):
    model = PageRelationship
    fk_name='origin'



def page_author_form_factory():
    class RuntimePageAuthorForm(forms.ModelForm):
        
        author = forms.ModelChoiceField(label="Author",
                queryset=Author.objects.filter(mi_contributor__gte=1))
 
        class Meta:
            model = PageAuthor
            fields='__all__'
        
    return RuntimePageAuthorForm
 
class PageAuthorInline(admin.TabularInline):
    model = PageAuthor
    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.form = page_author_form_factory()
        return super(PageAuthorInline, self).get_formset(request, obj,
                **kwargs)


class IndexEntryInline(admin.TabularInline):
    model = IndexEntry

class PageAdmin(reversion.VersionAdmin):
    list_display = ('code','title', 'page_type')
    inlines = [IndexEntryInline,PageAuthorInline,PageRelationshipInline]
    search_fields = ['code', 'title']
    filter_horizontal = ['keywords','subjects','related_videos']
    #exclude = ('objectives','subjects','content_types')
    fieldsets = (
        (None, {
            'fields': ('code', 
                       'title', 'description', 'page_type','text', 'keywords',
                       'subjects',)
        }),
        ('Detailed description', {
            'classes': ('collapse',),
            'fields': ('detailed_description',),
        }),
        ('Javascript', {
            'classes': ('collapse',),
            'fields': ('javascript',),
        }),
        ('Header', {
            'classes': ('collapse',),
            'fields': ('header',),
        }),
        ('Notes', {
            'classes': ('collapse',),
            'fields': ('notes',),
        }),
        ('Copyright and credits', {
            'classes': ('collapse',),
            'fields': ('copyright_type', 'additional_credits',),
        }),
        ('Misc', {
            'classes': ('collapse',),
            'fields': ('publish_date', 'highlight', 'hidden', 'notation_systems', 'related_videos'),
        }),
    )
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 25, 'cols': 120})},
        }
    save_on_top=True

    class Media:
        js = [
            "%sjs/save_me_genie.js" % settings.STATIC_URL,
        ]

class PageWithNotes(Page):
    class Meta:
        proxy = True
        verbose_name_plural = "Pages with notes"


class PageWithNotesAdmin(admin.ModelAdmin):
    list_display = ('code','title', 'notes')
    search_fields = ['code', 'title']
    fields=('code','title','description','notes',)
    readonly_fields = ('code','title','description',)
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True


    def has_add_permission(self, request):
        return False
    
    # exclude pages without notes
    def get_queryset(self, request):
        qs = super(PageWithNotesAdmin, self).queryset(request)
        return qs.exclude(notes=None).exclude(notes="")


class PageHighlight(Page):
    class Meta:
        proxy = True


class PageHighlightAdmin(admin.ModelAdmin):
    list_display = ('code','title', 'highlight')
    list_editable = ('highlight',)
    search_fields = ['code', 'title']
    fields=('code','title','description','highlight',)
    readonly_fields = ('code','title','description',)
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    ordering=('-highlight',)
    

    def has_add_permission(self, request):
        return False
    
class ReferenceAuthorInline(admin.TabularInline):
    model = ReferenceAuthor

class ReferenceAdmin(reversion.VersionAdmin):
    inlines = [ReferenceAuthorInline,]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True

 
class NewsAuthorInline(admin.TabularInline):
    model = NewsAuthor

class NewsAdmin(reversion.VersionAdmin):
    inlines = [NewsAuthorInline]
    list_display = ("code","title")
    save_on_top=True
    prepopulated_fields = {"code": ("title",)}


class NotationSystemAdmin(reversion.VersionAdmin):
    pass
class AuthorAdmin(reversion.VersionAdmin):
    pass
class PageTypeAdmin(reversion.VersionAdmin):
    pass
class ObjectiveAdmin(reversion.VersionAdmin):
    pass
class SubjectAdmin(reversion.VersionAdmin):
    pass
class KeywordAdmin(reversion.VersionAdmin):
    pass
class RelationshipTypeAdmin(reversion.VersionAdmin):
    pass
class IndexTypeAdmin(reversion.VersionAdmin):
    pass
class IndexEntryAdmin(reversion.VersionAdmin):
    pass
class ImageTypeAdmin(reversion.VersionAdmin):
    pass
class AppletFeatureAdmin(reversion.VersionAdmin):
    pass
class AppletObjectTypeAdmin(reversion.VersionAdmin):
    pass
class ReferenceTypeAdmin(reversion.VersionAdmin):
    pass
class AuxiliaryFileTypeAdmin(reversion.VersionAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('code',)
        return self.readonly_fields

class AuxiliaryFileAdmin(reversion.VersionAdmin):
    pass
class CopyrightTypeAdmin(reversion.VersionAdmin):
    pass

admin.site.register(NotationSystem,NotationSystemAdmin)
admin.site.register(Author,AuthorAdmin)
admin.site.register(PageType,PageTypeAdmin)
admin.site.register(Objective,ObjectiveAdmin)
admin.site.register(Subject,SubjectAdmin)
admin.site.register(Keyword,KeywordAdmin)
admin.site.register(RelationshipType,RelationshipTypeAdmin)
admin.site.register(Page,PageAdmin)
admin.site.register(PageWithNotes,PageWithNotesAdmin)
admin.site.register(PageHighlight,PageHighlightAdmin)
admin.site.register(IndexType,IndexTypeAdmin)
admin.site.register(IndexEntry,IndexEntryAdmin)
admin.site.register(ImageType,ImageTypeAdmin)
admin.site.register(Image,ImageAdmin)
admin.site.register(AppletType,AppletTypeAdmin)
admin.site.register(AppletFeature,AppletFeatureAdmin)
admin.site.register(Applet,AppletAdmin)
admin.site.register(AppletHighlight,AppletHighlightAdmin)
admin.site.register(AppletObjectType,AppletObjectTypeAdmin)
admin.site.register(VideoType,VideoTypeAdmin)
admin.site.register(Video,VideoAdmin)
admin.site.register(VideoHighlight,VideoHighlightAdmin)
admin.site.register(NewsItem,NewsAdmin)
admin.site.register(Reference,ReferenceAdmin)
admin.site.register(ReferenceType,ReferenceTypeAdmin)
admin.site.register(AuxiliaryFileType,AuxiliaryFileTypeAdmin)
admin.site.register(AuxiliaryFile,AuxiliaryFileAdmin)
admin.site.register(CopyrightType, CopyrightTypeAdmin)
