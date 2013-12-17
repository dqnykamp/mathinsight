from django.conf.urls import patterns, url, include
from django.conf import settings
from midocs.models import Applet, Video, Image, Author, Page, NotationSystem
from django.views.generic import TemplateView, ListView, DetailView
from hitcount.views import update_hit_count_ajax
from midocs.views import MidocsSearchView
from haystack.forms import ModelSearchForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse, reverse_lazy

from django.contrib import admin
admin.autodiscover()
import micomments.admin

from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import datetime

paginate_by=20

#handler500 = 'midocs.views.server_error'

# class ProfileView(TemplateView):
#     template_name = 'registration/profile.html'

#     @method_decorator(login_required)
#     def dispatch(self, *args, **kwargs):
#         return super(ProfileView, self).dispatch(*args, **kwargs)

class AuthorDetailView(DetailView):
    context_object_name = "author"
    model = Author
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the authors
        context['author_list'] = Author.objects.filter(mi_contributor__gte=2)
        return context

urlpatterns = patterns('',
    url(r'^$', 'midocs.views.home', name='mathinsight-home'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    url(r'^(?P<page_code>\w+)$', 'midocs.views.pageview', name='mi-page'),
    url(r'^image/list$', ListView.as_view(template_name="midocs/image_list.html", queryset=Image.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-imagelist"),
    url(r'^image/(?P<image_code>\w+)$', 'midocs.views.imageview', name="mi-image"),
    url(r'^applet/list$', ListView.as_view(template_name="midocs/applet_list.html", queryset=Applet.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-appletlist"),
    url(r'^applet/(?P<applet_code>\w+)$', 'midocs.views.appletview', name="mi-applet"),
    url(r'^video/list$', ListView.as_view(template_name="midocs/video_list.html", queryset=Video.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name="mi-videolist"),
    url(r'^video/(?P<video_code>\w+)$', 'midocs.views.videoview', name="mi-video"),
    url(r'^index/(?P<index_code>\w+)$', 'midocs.views.indexview', name="mi-index"),
    #(r'^search/', include('haystack.urls')),
    url(r'^search/$', MidocsSearchView(form_class=ModelSearchForm), name='haystack_search'),
    url(r'^page/list$', ListView.as_view(template_name="midocs/all_page_list.html", queryset=Page.objects.filter(publish_date__lte=datetime.date.today(),hidden=False), paginate_by=paginate_by), name='mi-allpages'),
    url(r'^similar/(?P<slug>\w+)$', DetailView.as_view(template_name="midocs/similar_page_list.html", model=Page, slug_field='code', context_object_name="thepage"), name="mi-similar"),
    url(r'^contributor/list$', ListView.as_view(template_name="midocs/author_list.html", queryset=Author.objects.filter(mi_contributor__gte =2)), name="mi-authorlist"),
    url(r'^contributor/(?P<slug>\w+)$', AuthorDetailView.as_view(template_name="midocs/author_detail.html", slug_field='code'), name="mi-authordetail"),
    url(r'^accounts/login$', 'midocs.views.login', name='mi-login'),
    url(r'^accounts/logout$', 'django.contrib.auth.views.logout', name='mi-logout'),
    #url(r'^accounts/profile$', 'micourses.views.profileview', name='mi-profile'),
    url(r'^accounts/profile$', RedirectView.as_view(url=reverse_lazy('mic-coursemain'), permanent=False)),
    (r'^comments/', include('django.contrib.comments.urls')),
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    url(r'^ajax/hit/$', update_hit_count_ajax, name='hitcount_update_ajax'), 
    (r'^about/', include('midocs.abouturls')),
    (r'^feed/', include('midocs.feedurls')),
    (r'^assess/', include('mitesting.urls')),
    (r'^thread/', include('mithreads.urls')),
    (r'^course/', include('micourses.urls')),
     
    #(r'^charts/simple.png$', 'midocs.views.simplechart'),
 )

#if settings.SITE_ID==2:
#    urlpatterns += patterns('', (r'^~nykamp/', include('umnmimic.urls')),)


urlpatterns += staticfiles_urlpatterns()
