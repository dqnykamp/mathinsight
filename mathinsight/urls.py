from django.conf.urls import  url, include
from django.conf import settings
from midocs.models import Author
import midocs
from django.views.generic import TemplateView, ListView, DetailView
#from hitcount.views import update_hit_count_ajax
from midocs.views import MidocsSearchView
from haystack.forms import ModelSearchForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.views import logout as logout_view
from django.contrib import admin
admin.autodiscover()
import micomments.admin

#from dajaxice.core import dajaxice_autodiscover, dajaxice_config
#dajaxice_autodiscover()

from django.conf.urls.static import static

import datetime

paginate_by=20

class AuthorDetailView(DetailView):
    context_object_name = "author"
    model = Author
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the authors
        context['author_list'] = Author.objects.filter(mi_contributor__gte=2)
        return context

urlpatterns = [
    url(r'^$', midocs.views.home, name='mathinsight-home'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    #(r'^search/', include('haystack.urls')),
    url(r'^search/$', MidocsSearchView(form_class=ModelSearchForm), name='haystack_search'),
    url(r'^contributor/list$', ListView.as_view(template_name="midocs/author_list.html", queryset=Author.objects.filter(mi_contributor__gte =2)), name="mi-authorlist"),
    url(r'^contributor/(?P<slug>\w+)$', AuthorDetailView.as_view(template_name="midocs/author_detail.html", slug_field='code'), name="mi-authordetail"),
    url(r'^accounts/login$', midocs.views.login, name='mi-login'),
    url(r'^accounts/logout$', logout_view, name='mi-logout'),
    #url(r'^accounts/profile$', 'micourses.views.profileview', name='mi-profile'),
    url(r'^accounts/profile$', RedirectView.as_view(url=reverse_lazy('mic-coursemain'), permanent=False)),
    url(r'^comments/', include('django_comments.urls')),
#    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
#    url(r'^ajax/hit/$', update_hit_count_ajax, name='hitcount_update_ajax'), 
    url(r'^about/', include('midocs.abouturls')),
    url(r'^feed/', include('midocs.feedurls')),
    url(r'^assess/', include('mitesting.urls')),
    url(r'^thread/', include('mithreads.urls')),
    url(r'^course/', include('micourses.urls')),
    url(r'^', include('midocs.urls')), # include last as will absorb xx/xx urls
] \
+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

