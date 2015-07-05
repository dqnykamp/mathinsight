from haystack import indexes
from midocs.models import Page, Applet, Video, Image
import datetime



class ContentIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    code = indexes.CharField(model_attr='code')
    title = indexes.CharField(model_attr='title', boost=1.2)
    description = indexes.CharField(model_attr='description', boost=1.1, null=True)
    publish_date = indexes.DateField(model_attr='publish_date')

    def get_model(self):
        return Page

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(publish_date__lte=datetime.date.today(),hidden=False)


class PageIndex(ContentIndex, indexes.Indexable):
    def get_model(self):
        return Page

    def prepare(self, obj):
        data = super(PageIndex, self).prepare(obj)
        if(obj.page_type.code=='definition'):
            data['boost']=0.6
        else:
            data['boost']=1.5
            
        return data


class AppletIndex(ContentIndex, indexes.Indexable):
    def get_model(self):
        return Applet

class VideoIndex(ContentIndex, indexes.Indexable):
    def get_model(self):
        return Video

class ImageIndex(ContentIndex, indexes.Indexable):
    def get_model(self):
        return Image

