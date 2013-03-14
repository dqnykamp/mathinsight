from haystack.indexes import *
from haystack import site
from midocs.models import Page, Applet, Video, Image
import datetime

class PageSearchIndex(SearchIndex):
    text = CharField(document=True, use_template=True,boost=5)
    code = CharField(model_attr='code',boost=5)
    title = CharField(model_attr='title', boost=10)
    description = CharField(model_attr='description', boost=8)
    publish_date = DateField(model_attr='publish_date')
    def index_queryset(self):
        return Page.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)

    # def prepare(self, obj):
    #     data = super(PageSearchIndex, self).prepare(obj)
    #     if(obj.level.code=='definition'):
    #         data['boost'] = 0.5
    #         print obj
    #     return data

class AppletSearchIndex(SearchIndex):
    text = CharField(document=True, use_template=True,boost=0.9)
    code = CharField(model_attr='code',boost=0.9)
    title = CharField(model_attr='title',boost=1)
    description = CharField(model_attr='description',boost=1, null=True)
    publish_date = DateField(model_attr='publish_date')
    def index_queryset(self):
        return Applet.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)

class VideoSearchIndex(SearchIndex):
    text = CharField(document=True, use_template=True,boost=0.9)
    code = CharField(model_attr='code',boost=0.9)
    title = CharField(model_attr='title',boost=1)
    description = CharField(model_attr='description',boost=1, null=True)
    publish_date = DateField(model_attr='publish_date')
    def index_queryset(self):
        return Video.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)

class ImageSearchIndex(SearchIndex):
    text = CharField(document=True, use_template=True,boost=0.9)
    code = CharField(model_attr='code',boost=0.9)
    title = CharField(model_attr='title', boost=1)
    description = CharField(model_attr='description',boost=1, null=True)
    publish_date = DateField(model_attr='publish_date')
    def index_queryset(self):
        return Image.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)

site.register(Page, PageSearchIndex)
site.register(Applet, AppletSearchIndex)
site.register(Video, VideoSearchIndex)
site.register(Image, ImageSearchIndex)
