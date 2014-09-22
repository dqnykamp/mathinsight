from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.conf.urls import patterns, url
from django.views.generic import TemplateView, ListView, DetailView
from midocs.models import Applet, Video, Image, Author, Page, NotationSystem
import datetime
from mathinsight.urls import paginate_by

new_days_past=365


class ContactView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ContactView, self).get_context_data(**kwargs)
        # need some object with which to associate comment
        # use first Author, since that wouldn't be confused with anything else
        comment_object =Author.objects.order_by('id')[0]
        context['comment_object']=comment_object
        return context

urlpatterns = patterns('midocs.views',
 url(r'^mathinsight$', TemplateView.as_view(template_name="about_mathinsight.html"), 
     name='mi-about'),
 url(r'^contact$', ContactView.as_view(template_name="contact.html"),
     name='mi-contact'),
 url(r'^news/(?P<news_code>[\w-]+)$', 'newsview', 
     name='mi-news'),
 url(r'^recent_news$', 'whatsnewview', {'items': 'news'}, 
     name='mi-recentnews'),
 url(r'^new_summary$', 'whatsnewview', {'items': 'summary'},
     name='mi-newsummary'),
 url(r'^new_pages$', ListView.as_view
     (template_name="midocs/whatsnew_pages.html", 
      queryset=Page.objects.exclude(level__code="definition")
      .filter(publish_date__lte=datetime.date.today(),hidden=False)
      .filter(publish_date__gte=datetime.date.today()
              -datetime.timedelta(days=new_days_past))
      .order_by('-publish_date','-pk'),
      paginate_by=paginate_by),
     name='mi-newpages'),
 url(r'^new_applets$', ListView.as_view
     (template_name="midocs/whatsnew_applets.html", 
      queryset=Applet.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)
      .filter(publish_date__gte=datetime.date.today()
              -datetime.timedelta(days=new_days_past))
      .order_by('-publish_date','-pk'),
      paginate_by=paginate_by),
     name='mi-newapplets'),
 url(r'^new_videos$', ListView.as_view
     (template_name="midocs/whatsnew_videos.html", 
      queryset=Video.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)
      .filter(publish_date__gte=datetime.date.today()
              -datetime.timedelta(days=new_days_past))
      .order_by('-publish_date','-pk'),
      paginate_by=paginate_by),
     name='mi-newvideos'),
 url(r'^new_images$', ListView.as_view
     (template_name="midocs/whatsnew_images.html", 
      queryset=Image.objects.filter(publish_date__lte=datetime.date.today(),hidden=False)
      .filter(publish_date__gte=datetime.date.today()
              -datetime.timedelta(days=new_days_past))
      .order_by('-publish_date','-pk'),
      paginate_by=paginate_by),
     name='mi-newimages'),
 url(r'^notationsystems$', ListView.as_view
     (template_name="midocs/notation_list.html", 
      model=NotationSystem),
     name="mi-notationsystem"),
 url(r'^notationsystems/(?P<slug>\w+)$', 
     DetailView.as_view(template_name="midocs/notation_detail.html", 
                        model=NotationSystem,
                        slug_field='code',
                        context_object_name="notationsystem"),
     name="mi-notationsystemdetail"),
)
