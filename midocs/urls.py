from django.conf.urls import patterns, url
from django.views.generic import ListView, DetailView
from midocs.models import Applet, Video, Image, Page
from midocs import views
from midocs.views import AuxiliaryFileView
import datetime

paginate_by=20

urlpatterns = [
    url(r'^(?P<page_code>\w+)$', views.pageview, name='mi-page'),
    url(r'^image/list$', ListView.as_view(template_name="midocs/image_list.html", queryset=Image.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-imagelist"),
    url(r'^image/(?P<image_code>\w+)$', views.imageview, name="mi-image"),
    url(r'^applet/list$', ListView.as_view(template_name="midocs/applet_list.html", queryset=Applet.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-appletlist"),
    url(r'^applet/(?P<applet_code>\w+)$', views.appletview, name="mi-applet"),
    url(r'^applet/(?P<applet_code>\w+)/bare$', views.appletview_bare, name="mi-applet_bare"),
    url(r'^video/list$', ListView.as_view(template_name="midocs/video_list.html", queryset=Video.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-videolist"),
    url(r'^video/(?P<video_code>\w+)$', views.videoview, name="mi-video"),
    url(r'^index/(?P<index_code>\w+)$', views.indexview, name="mi-index"),
    url(r'^page/list$', ListView.as_view(template_name="midocs/all_page_list.html", queryset=Page.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name='mi-allpages'),
    url(r'^similar/(?P<slug>\w+)$', DetailView.as_view(template_name="midocs/similar_page_list.html", model=Page, slug_field='code', context_object_name="thepage"), name="mi-similar"),
    url(r'^auxiliary/(?P<file_type_code>\w+)/(?P<file_code>\w+)$', 
        AuxiliaryFileView.as_view(), name="mi-auxiliary"),
    url(r'^(?P<page_type_code>\w+)/(?P<page_code>\w+)$', views.pageview, name='mi-page_with_type'),
]

