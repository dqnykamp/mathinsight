from django.conf.urls import patterns, url
from midocs.feeds import LatestItemsFeed


urlpatterns = patterns('',
 url(r'^new_pages$', LatestItemsFeed(),{'item_type':'page'}, 
     name='mi-newpagefeed'),
 url(r'^new_applets$', LatestItemsFeed(),{'item_type':'applet'}, 
     name='mi-newappletfeed'),
 url(r'^new_videos$', LatestItemsFeed(),{'item_type':'video'}, 
     name='mi-newvideofeed'),
 url(r'^new_images$', LatestItemsFeed(),{'item_type':'image'}, 
     name='mi-newimagefeed'),
 url(r'^news$', LatestItemsFeed(),{'item_type':'news'}, 
     name='mi-newsfeed'),
)
