from django.contrib import admin
from django import forms
from django.db import models
from midocs.models import NotationSystem, Author, Level, Objective, Subject, Keyword, RelationshipType, Page, PageAuthor, PageRelationship, IndexType, IndexEntry, ImageType, Image, ImageAuthor, ImageNotationSystem, AppletType, AppletTypeParameter, AppletFeature, Applet, AppletParameter, AppletAuthor, AppletNotationSystem, VideoType, VideoTypeParameter, Video, VideoParameter, VideoAuthor, NewsItem, NewsAuthor, Reference, ReferenceType, ReferenceAuthor, AuxiliaryFile, AuxiliaryFileType, Question, QuestionAnswerOption

class AppletTypeParameterInline(admin.TabularInline):
    model = AppletTypeParameter
    extra = 3

class AppletTypeAdmin(admin.ModelAdmin):
    inlines = [AppletTypeParameterInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }


def applet_parameter_form_factory(applet_type):
    class RuntimeAppletParameterForm(forms.ModelForm):
        
        parameter = forms.ModelChoiceField(label="Parameter",
                queryset=AppletTypeParameter.objects.filter(applet_type=applet_type))
 
        class Meta:
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

class AppletAuthorInline(admin.TabularInline):
    model = AppletAuthor

class AppletNotationSystemInline(admin.TabularInline):
    model = AppletNotationSystem

class AppletAdmin(admin.ModelAdmin):
    inlines = [AppletParameterInline, AppletAuthorInline,AppletNotationSystemInline]
    # inlines = [AppletParameterInline, AppletInPagesInline]
    exclude = ('in_pages',)
    list_display = ("code","title","applet_type")
    filter_horizontal = ['features','keywords','subjects']
    search_fields = ['code', 'title','applet_type__code']
    save_on_top=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }


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

class VideoTypeAdmin(admin.ModelAdmin):
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


class VideoAdmin(admin.ModelAdmin):
    inlines = [VideoParameterInline, VideoAuthorInline]
    # inlines = [VideoParameterInline, VideoInPagesInline]
    exclude = ('in_pages',)
    list_display = ("code","title","video_type")
    filter_horizontal = ['keywords','subjects']
    search_fields = ['code', 'title','video_type__code']
    save_on_top=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }


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

class ImageAdmin(admin.ModelAdmin):
    inlines = [ImageAuthorInline,ImageNotationSystemInline]
    exclude = ('in_pages',)
    list_display = ("code", "title", "imagefile")
    filter_horizontal = ['keywords','subjects']
    search_fields = ['code', 'title', 'imagefile']
    save_on_top=True
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 100})},
        }

class PageRelationshipInline(admin.TabularInline):
    model = PageRelationship
    fk_name='origin'



def page_author_form_factory():
    class RuntimePageAuthorForm(forms.ModelForm):
        
        author = forms.ModelChoiceField(label="Author",
                queryset=Author.objects.filter(mi_contributor__gte=1))
 
        class Meta:
            model = PageAuthor
 
    return RuntimePageAuthorForm
 
class PageAuthorInline(admin.TabularInline):
    model = PageAuthor
    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.form = page_author_form_factory()
        return super(PageAuthorInline, self).get_formset(request, obj,
                **kwargs)


    
class PageAdmin(admin.ModelAdmin):
    list_display = ('code','title', 'level')
    inlines = [PageAuthorInline,PageRelationshipInline]
    search_fields = ['code', 'title']
    filter_horizontal = ['keywords','subjects']
    #exclude = ('objectives','subjects','content_types')
    readonly_fields = ('title','description','template_modified',)
    fieldsets = (
        (None, {
                'fields': ('code', 
                           ('template_dir','template_modified'),
                           'title', 'description', 'keywords',
                           'subjects',)
                }),
        ('Optional', {
                'classes': ('collapse',),
                'fields': ('publish_date','notes', 'author_copyright','worksheet', 'hidden', 'additional_credits','level','objectives','notation_systems','highlight'),
                }),
        )
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True

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
    def queryset(self, request):
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

class ReferenceAdmin(admin.ModelAdmin):
    inlines = [ReferenceAuthorInline,]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True

 
class NewsAuthorInline(admin.TabularInline):
    model = NewsAuthor

class NewsAdmin(admin.ModelAdmin):
    inlines = [NewsAuthorInline]
    list_display = ("code","title")
    save_on_top=True
    prepopulated_fields = {"code": ("title",)}

class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswerOption

class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionAnswerInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'size': 60})},
        }
    save_on_top=True


admin.site.register(NotationSystem)
admin.site.register(Author)
admin.site.register(Level)
admin.site.register(Objective)
admin.site.register(Subject)
admin.site.register(Keyword)
admin.site.register(RelationshipType)
admin.site.register(Page,PageAdmin)
admin.site.register(PageWithNotes,PageWithNotesAdmin)
admin.site.register(PageHighlight,PageHighlightAdmin)
admin.site.register(IndexType)
admin.site.register(IndexEntry)
admin.site.register(ImageType)
admin.site.register(Image,ImageAdmin)
admin.site.register(AppletType,AppletTypeAdmin)
admin.site.register(AppletFeature)
admin.site.register(Applet,AppletAdmin)
admin.site.register(AppletHighlight,AppletHighlightAdmin)
admin.site.register(VideoType,VideoTypeAdmin)
admin.site.register(Video,VideoAdmin)
admin.site.register(VideoHighlight,VideoHighlightAdmin)
admin.site.register(NewsItem,NewsAdmin)
admin.site.register(Reference,ReferenceAdmin)
admin.site.register(ReferenceType)
admin.site.register(AuxiliaryFileType)
admin.site.register(AuxiliaryFile)
admin.site.register(Question, QuestionAdmin)
