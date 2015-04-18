from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.contrib.syndication.views import Feed
from midocs.models import Page, Image, Applet, Video, NewsItem
import re
import datetime
from django.core.urlresolvers import reverse

def convertCamelWords(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).lower()


class LatestItemsFeed(Feed):

    def get_object(self, request, item_type):
        if item_type=='page':
            return Page
        elif item_type=='applet':
            return Applet
        elif item_type=='video':
            return Video
        elif item_type=='image':
            return Image
        else:
            return NewsItem
        
    def title(self, obj):
        if obj.__name__ == 'NewsItem':
            return  "Math Insight recent news"
        else:
            return "Math Insight newest %ss" % convertCamelWords(obj.__name__)

    def link(self, obj):
        if obj.__name__ == 'NewsItem':
            return  reverse('mi-recentnews')
        else:
            return reverse('mi-new%ss' % convertCamelWords(obj.__name__))
    
    def description(self, obj):
        "Newest %ss added to mathinsight.org."% convertCamelWords(obj.__name__)

    def items(self,obj):
        today = datetime.date.today()
        object_list = obj.objects
        if obj.__name__ == 'Page':
            object_list = object_list.exclude(page_type__code="definition")
        return object_list.filter(publish_date__lte=today).order_by('-publish_date')[:10]
    
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description
