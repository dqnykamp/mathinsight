from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django.utils.safestring import mark_safe

def author_list_abbreviated(the_authors, include_link=False):
    n_authors = len(the_authors)
    author_list="";

    for i, the_author in enumerate(the_authors):
        author_name_abbreviated = "%s %s%s" % \
            (the_author.author.last_name, \
                 the_author.author.first_name[:1], \
                 the_author.author.middle_name[:1])
        if include_link and the_author.author.mi_contributor >= 2:
            author_name_abbreviated = '<a href="%s" class="normaltext">%s</a>' % (the_author.author.get_absolute_url(), author_name_abbreviated)
        if(i==0):
            conjunction = ""
        elif(i==n_authors-1):
            if(i==1):
                conjunction = " and "
            else:
                conjunction = ", and "
        else:
            conjunction = ", "
        author_list= "%s%s%s" % (author_list, conjunction, 
                                 author_name_abbreviated)
    return author_list

def author_list_full(the_authors, include_link=False):
    n_authors = len(the_authors)
    author_list="";

    for i, the_author in enumerate(the_authors):
        author_name_full = "%s %s %s" % \
            (the_author.author.first_name, the_author.author.middle_name, \
                 the_author.author.last_name) 
        if include_link and the_author.author.mi_contributor >= 2:
            author_name_full = '<a href="%s" class="normaltext">%s</a>' % (the_author.author.get_absolute_url(), author_name_full)
        if(i==0):
            conjunction = ""
        elif(i==n_authors-1):
            if(i==1):
                conjunction = " and "
            else:
                conjunction = ", and "
        else:
            conjunction = ", "
        author_list = "%s%s%s" % (author_list, conjunction, author_name_full)
    return author_list


def return_extended_link(obj, **kwargs):
    
    link_url = obj.get_absolute_url()

    # in extended mode, include thumbnail, if exists
    icon_size = kwargs.get("icon_size","small")
    try:
        thumbnail = obj.thumbnail
    except AttributeError:
        thumbnail = None

    if thumbnail:
        if icon_size == 'large':
            thumbnail_width_buffer = obj.thumbnail_large_width_buffer()
            thumbnail_width=obj.thumbnail_large_width()
            thumbnail_height=obj.thumbnail_large_height()
        elif icon_size == 'small':
            thumbnail_width_buffer = obj.thumbnail_small_width_buffer()
            thumbnail_width=obj.thumbnail_small_width()
            thumbnail_height=obj.thumbnail_small_height()
        else:
            thumbnail_width_buffer = obj.thumbnail_medium_width_buffer()
            thumbnail_width=obj.thumbnail_medium_width()
            thumbnail_height=obj.thumbnail_medium_height()


        html_thumbnail = '<div style="width: %spx; float: left;"><a href="%s"><img src="%s" alt="%s" width ="%s" height="%s" /></a></div>' % \
            (thumbnail_width_buffer, link_url, thumbnail.url, \
                 obj.title, thumbnail_width,thumbnail_height)
    else:
        html_thumbnail = ""
        

    html_link = obj.return_link(**kwargs)

    try:
        html_link += ' %s' % obj.feature_list()
    except AttributeError:
        pass

    html_link += '<br/>%s' % obj.description
        
    if kwargs.get("added"):
        html_link += "<br/>Added "
        author_list = obj.author_list_full(include_link = True)
        if author_list:
            html_link += "by %s " % author_list
        html_link += "on %s" % obj.publish_date

    if thumbnail and icon_size != 'small':
        html_link = '<div style="width: 75%%; float: left;">%s</div>' % \
            html_link

    if  thumbnail:
        html_string = '<div class="ym-clearfix">%s%s</div>' % \
        (html_thumbnail, html_link)
    else:
        html_string = html_link

    return mark_safe(html_string)


