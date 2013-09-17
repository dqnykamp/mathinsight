from midocs.models import NotationSystem, Author, Level, Objective, Subject, Keyword, RelationshipType, Page, PageRelationship, Image, Applet, Video, IndexType, IndexEntry, NewsItem
from django import http, forms
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.http import last_modified
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, TemplateDoesNotExist, Template, Context
from django.db.models import Count, Q
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.contrib import auth
import django.contrib.auth.views
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from midocs.search_functions import midocsSearchQuerySet
from itertools import chain
from haystack.views import SearchView
import datetime
import re
import random
#import numpy




# def get_related_pages(thepage, relationship_type):
#     return Page.objects.filter(reverse_relationships__origin=thepage, reverse_relationships__relationship_type__code=relationship_type)


def get_all_related_pages(thepage, max_keyword_matches=0, max_total_related=0):
    related_pages={}
    today=datetime.date.today()
    for relationship_type in RelationshipType.objects.all():
        related_pages[relationship_type.code] = \
            Page.objects.filter \
            (reverse_relationships__origin=thepage,
             reverse_relationships__relationship_type=
             relationship_type) \
             .filter(publish_date__lte=today, hidden=False) \
             .order_by('reverse_relationships__sort_order',
                       'reverse_relationships__id')

    return related_pages

# calculate date of page as the last date_modified 
# of the page itself or its included applets, videos, and images
def date_page(request, page_code):
    try: 
        thepage=Page.objects.get(code=page_code)
    except:
        return None
    latest_date=thepage.date_modified
    try:
        last_image=thepage.image_set.latest("date_modified").date_modified
        latest_date=max(latest_date,last_image)
    except:
        pass
    try:
        last_applet=thepage.applet_set.latest("date_modified").date_modified
        latest_date=max(latest_date,last_applet)
    except:
        pass
    try:
        last_video=thepage.video_set.latest("date_modified").date_modified
        latest_date=max(latest_date,last_video)
    except:
        pass
    return latest_date


@last_modified(date_page)
def pageview(request, page_code):
    thepage = get_object_or_404(Page, code=page_code)
    
    # get related pages
    max_keyword_matches=5
    max_total_related=10
    related_pages = get_all_related_pages(thepage,max_keyword_matches,max_total_related)
    if related_pages['generic'] or related_pages['lighter'] \
            or related_pages['depth']:
        manual_links=True
    else:
        manual_links=False
    
    
    # turn off google analytics for localhost or hidden page
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3 or thepage.hidden:
        noanalytics=True
        
        
    if request.method == 'GET':
        if "logout" in request.GET:
            auth.logout(request)

    
    notation_system=None
    notation_config=None
    notation_system_form=None

    if(thepage.notation_systems.all()):
        class NotationSystemForm(forms.Form):
            notation_system = forms.ModelChoiceField(queryset=thepage.notation_systems.all(), initial=1)


        # if submitted the notation_system form
        if request.method == 'POST':
            notation_system_form = NotationSystemForm(request.POST)
            if notation_system_form.is_valid():
                notation_system = notation_system_form.cleaned_data['notation_system']
                request.session['notation_config'] = notation_system.configfile
                notation_config = notation_system.configfile
            # if invalid form, get notation config from session
            else:
                notation_config = request.session.get('notation_config', '')

        # if did not submit the notation_system form
        else:
            notation_config = request.session.get('notation_config', None)
            if(notation_config):
                try:
                    notation_system = thepage.notation_systems.get(configfile=notation_config)
                except:
                    notation_system = None
                    notation_config = None

            # if got the notation sytem from the session,
            # show that system selected in the form
            if(notation_system):
                notation_system_form = NotationSystemForm({'notation_system': notation_system.pk})
            # otherwise show an unbound form with default as initial value
            else:
                notation_system_form = NotationSystemForm()

        # if have midefault system, delete it from notation_config
        # since template already has midefault hard coded in it
        if(notation_config=='midefault'):
            notation_config=None
    
    # render page text with extra template tags
    context=RequestContext(request)
    rendered_text = Template("{% load mi_tags testing_tags %}"+thepage.text).render(context)
        
    # get any geogebra javascript init commands from rendering tags in text
    geogebra_oninit_commands=context.dicts[0].get('geogebra_oninit_commands')

    return render_to_response \
        ("midocs/page_detail.html", 
         {'thepage': thepage, 'related_pages': related_pages,
          'manual_links': manual_links,
          'notation_system': notation_system,
          'notation_config': notation_config,
          'notation_system_form': notation_system_form,
          'noanalytics': noanalytics,
          'geogebra_oninit_commands': geogebra_oninit_commands,
          'rendered_text': rendered_text,
          },
         context_instance=RequestContext(request))




# calculate date of image as the date_modified 
def date_image(request, image_code):
    try:
        return Image.objects.get(code=image_code).date_modified
    except:
        return None

@last_modified(date_image)
def imageview(request, image_code):

    theimage = get_object_or_404(Image, code=image_code)
    
    in_pages=theimage.in_pages.all()

    # turn off google analytics for localhost or hidden
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3 or theimage.hidden:
        noanalytics=True

    if request.method == 'GET':
        if "logout" in request.GET:
            auth.logout(request)


    notation_system=None
    notation_config=None
    notation_system_form=None
    imagefile=None

    if(theimage.notation_systems.all()):
        class NotationSystemForm(forms.Form):
            notation_system = forms.ModelChoiceField(queryset=theimage.notation_systems.all(), initial=1)


        # if submitted the notation_system form
        if request.method == 'POST':
            notation_system_form = NotationSystemForm(request.POST)
            if notation_system_form.is_valid():
                notation_system = notation_system_form.cleaned_data['notation_system']
                request.session['notation_config'] = notation_system.configfile
                notation_config = notation_system.configfile
            # if invalid form, get notation config from session
            else:
                notation_config = request.session.get('notation_config', '')

        # if did not submit the notation_system form
        else:
            notation_config = request.session.get('notation_config', None)
            if(notation_config):
                try:
                    notation_system = theimage.notation_systems.get(configfile=notation_config)
                except:
                    notation_system = None
                    notation_config = None

            # if got the notation sytem from the session,
            # show that system selected in the form
            if(notation_system):
                notation_system_form = NotationSystemForm({'notation_system': notation_system.pk})
            # otherwise show an unbound form with default as initial value
            else:
                notation_system_form = NotationSystemForm()

        # if have midefault system, delete it from notation_config
        # since template already has midefault hard coded in it
        if(notation_config=='midefault'):
            notation_config=None
    
        # check for alternative image
        if notation_system:
            try:
                image_notation_system = theimage.imagenotationsystem_set.get(notation_system=notation_system)
                if image_notation_system.imagefile:
                    imagefile=image_notation_system.imagefile
                    width=image_notation_system.width
                    height=image_notation_system.height
            except:
                pass

    if not imagefile:
        imagefile=theimage.imagefile
        width=theimage.width
        height=theimage.height
        
    image_filename = re.sub(settings.IMAGE_UPLOAD_TO,"", imagefile.name)  # get rid of upload path

    original_image_filename = None
    if theimage.original_file:
        original_image_filename = re.sub(settings.IMAGE_UPLOAD_TO+"source/","", theimage.original_file.name)  # get rid of upload path


    return render_to_response("midocs/image_detail.html", 
                              {'image': theimage, 'in_pages': in_pages, 
                               'imagefile': imagefile,
                               'image_filename': image_filename,
                               'original_image_filename': original_image_filename,
                               'width': width, 'height': height,
                               'notation_config': notation_config,
                               'notation_system_form': notation_system_form, 
                               'noanalytics': noanalytics,
                              },
                              context_instance=RequestContext(request))

# calculate date of applet as the date_modified 
def date_applet(request, applet_code):
    try:
        return Applet.objects.get(code=applet_code).date_modified
    except:
        return None

@last_modified(date_applet)
def appletview(request, applet_code):

    theapplet = get_object_or_404(Applet, code=applet_code)
    
    in_pages=theapplet.in_pages.all()

    # turn off google analytics for localhost or hidden applet
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3 or theapplet.hidden:
        noanalytics=True

    if request.method == 'GET':
        if "logout" in request.GET:
            auth.logout(request)

    notation_system=None
    notation_config=None
    notation_system_form=None

    if(theapplet.notation_systems.all()):
        class NotationSystemForm(forms.Form):
            notation_system = forms.ModelChoiceField(queryset=theapplet.notation_systems.all(), initial=1)


        # if submitted the notation_system form
        if request.method == 'POST':
            notation_system_form = NotationSystemForm(request.POST)
            if notation_system_form.is_valid():
                notation_system = notation_system_form.cleaned_data['notation_system']
                request.session['notation_config'] = notation_system.configfile
                notation_config = notation_system.configfile
            # if invalid form, get notation config from session
            else:
                notation_config = request.session.get('notation_config', '')

        # if did not submit the notation_system form
        else:
            notation_config = request.session.get('notation_config', None)
            if(notation_config):
                try:
                    notation_system = theapplet.notation_systems.get(configfile=notation_config)
                except:
                    notation_system = None
                    notation_config = None

            # if got the notation sytem from the session,
            # show that system selected in the form
            if(notation_system):
                notation_system_form = NotationSystemForm({'notation_system': notation_system.pk})
            # otherwise show an unbound form with default as initial value
            else:
                notation_system_form = NotationSystemForm()

        # if have midefault system, delete it from notation_config
        # since template already has midefault hard coded in it
        if(notation_config=='midefault'):
            notation_config=None
    

    applet_filename = re.sub(settings.APPLET_UPLOAD_TO,"", theapplet.applet_file.name)  # get rid of upload path

    applet_filename2=None
    if theapplet.applet_file2:
        applet_filename2 = re.sub(settings.APPLET_UPLOAD_TO,"", theapplet.applet_file2.name)  # get rid of upload path

    return render_to_response("midocs/applet_detail.html", 
                              {'applet': theapplet, 'in_pages': in_pages,
                               'applet_filename': applet_filename,
                               'applet_filename2': applet_filename2,
                               'notation_config': notation_config,
                               'notation_system_form': notation_system_form,
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))


# calculate date of video as the date_modified 
def date_video(request, video_code):
    try:
        return Video.objects.get(code=video_code).date_modified
    except:
        return None

@last_modified(date_video)
def videoview(request, video_code):

    thevideo = get_object_or_404(Video, code=video_code)
    
    in_pages=thevideo.in_pages.all()

    # turn off google analytics for localhost or hidden video
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3 or thevideo.hidden:
        noanalytics=True

    if request.method == 'GET':
        if "logout" in request.GET:
            auth.logout(request)


    return render_to_response("midocs/video_detail.html", 
                              {'video': thevideo, 'in_pages': in_pages,
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))


def indexview(request, index_code):

    index_type = get_object_or_404(IndexType, code=index_code)
    
    index_entries = index_type.entries.all()

    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    return render_to_response("midocs/index_detail.html", 
                              {'index_type': index_type,
                               'index_entries': index_entries,
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))

def newsview(request, news_code):

    newsitem = get_object_or_404(NewsItem, code=news_code)
    today = datetime.date.today()

    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    return render_to_response("midocs/news_detail.html", 
                              {'newsitem': newsitem,
                               'news_list': 
                               NewsItem.objects.filter(publish_date__lte=today).order_by('-publish_date','-pk')[0:10],
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))


# calculate date of applet as the date_modified 
def date_whatsnew(request, items):
    if items=='news':
        return NewsItem.objects.latest("date_modified").date_modified
    else:
        last_page=Page.objects.latest("date_modified").date_modified
        last_applet=Applet.objects.latest("date_modified").date_modified
        last_video=Video.objects.latest("date_modified").date_modified
        last_image=Image.objects.latest("date_modified").date_modified
        return max(last_page,last_applet,last_video,last_image)

@last_modified(date_whatsnew)
def whatsnewview(request, items):
    # now only summary and news is used
    
    max_items=20
    
    includenews=False
    includepages=False
    includeapplets=False
    includevideos=False
    includeimages=False
    the_template="midocs/whatsnew_detail.html"
    if items=='summary':
        the_template="midocs/whatsnew_summary.html"
        max_items=5
        includepages=True
        includeapplets=True
        includevideos=True
        includeimages=True
    elif items=='pages':
        includepages=True
    elif items=='applets':
        includeapplets=True
    elif items=='videos':
        includevideos=True
    elif items=='images':
        includeimages=True
    else:
        the_template="midocs/recent_news_list.html"
        includenews=True
    
    today = datetime.date.today()

    if includepages:
        newpages=Page.objects.exclude(level__code="definition").filter(publish_date__lte= today,hidden=False).order_by('-publish_date','-pk')[0:max_items]
    else:
        newpages=None
    if includeapplets:
        newapplets=Applet.objects.filter(publish_date__lte=today,hidden=False).order_by('-publish_date','-pk')[0:max_items]
    else:
        newapplets=None
    if includevideos:
        newvideos=Video.objects.filter(publish_date__lte=today,hidden=False).order_by('-publish_date','-pk')[0:max_items]
    else:
        newvideos=None
    if includeimages:
        newimages=Image.objects.filter(publish_date__lte=today,hidden=False).order_by('-publish_date','-pk')[0:max_items]
    else:
        newimages=None
    if includenews:
        recent_news = NewsItem.objects.filter(publish_date__lte=today).order_by('-publish_date','-pk')[0:max_items]
    else:
        recent_news=None


    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    return render_to_response(the_template, 
                              {'newpages': newpages,
                               'newapplets': newapplets,
                               'newvideos': newvideos,
                               'newimages': newimages,
                               'recent_news': recent_news,
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))



# calculate date of applet as the date_modified 
def date_home(request):
    last_page=Page.objects.latest("date_modified").date_modified
    last_news=NewsItem.objects.latest("date_modified").date_modified
    last_applet=Applet.objects.latest("date_modified").date_modified
    return max(last_page,last_news,last_applet)

@last_modified(date_home)
def home(request):
    max_highlights=5
    max_highlighted_applets=2
    max_new_pages=3;
    max_news=2;


    highlighted_pages = Page.objects.filter(highlight=True)
    num_highlights=highlighted_pages.count()
    max_highlights=min(max_highlights,num_highlights)
    highlighted_pages = random.sample(highlighted_pages,max_highlights)

    highlighted_applets=Applet.objects.filter(highlight=True)
    num_highlighted_applets=highlighted_applets.count()
    max_highlighted_applets=min(max_highlighted_applets,num_highlighted_applets)
    highlighted_applets=random.sample(highlighted_applets,max_highlighted_applets)

    today = datetime.date.today()

    news = NewsItem.objects.filter(publish_date__lte=today).order_by('-publish_date','-pk')[:max_news]
    newpages=Page.objects.exclude(level__code="definition").filter(publish_date__lte= today,hidden=False).order_by('-publish_date','-pk')[0:max_new_pages]

    # turn off google analytics for localhost
    noanalytics=False
    if settings.SITE_ID==2 or settings.SITE_ID==3:
        noanalytics=True

    return render_to_response("home.html", 
                              {'highlight_list': highlighted_pages,
                               'highlighted_applets': highlighted_applets,
                               'news_list': news,
                               'new_pages': newpages,
                               'noanalytics': noanalytics,
                               },
                              context_instance=RequestContext(request))



class MidocsSearchView(SearchView):
    __name__ = 'MidocsSearchView'

    def extra_context(self):
        """
        Allows the addition of more context variables as needed.
        
        Must return a dictionary.
        """
        
        include_pages=False
        include_others=False
        models_restrict = ""
        try:
            for model in self.form.cleaned_data['models']:
                models_restrict = "%s&models=%s" % (models_restrict,model )
                if model == 'midocs.page':
                    include_pages=True
                if model == 'midocs.applet' or model == 'midocs.image':
                    include_others=True
        except:
            pass

        if not include_others:
            include_pages=True

        # if include_pages:
        #     thumbnail_mode=2
        # else:
        #     thumbnail_mode=1

        if include_pages:
            icon_size='small'
        else:
            icon_size='medium'

        return {'models_restrict': models_restrict, 
                'icon_size': icon_size,
                }


def login(request, *args, **kwargs):
    if request.method == 'POST':
        if not request.POST.get('remember_me', None):
            request.session.set_expiry(0)
    
    return django.contrib.auth.views.login(request, *args, **kwargs)
