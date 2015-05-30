from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from django import template
from midocs.models import Page, PageType, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, AppletType, Video, EquationTag, ExternalLink, PageCitation, Reference, return_default_page_type
from mitesting.models import Assessment
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from django.utils.encoding import smart_text
from django.template.base import kwarg_re
import re
from django.contrib.sites.models import Site
from django.db.models import  Max
from sympy.printing import StrPrinter
import six

register=template.Library()

def underscore_to_camel(word):
    return ''.join(x.capitalize() for x in  word.split('_'))

def resolve_if_set(variable, context):
    if variable:
        return variable.resolve(context)
    return None


class InternalLinkNode(template.Node):
    def __init__(self, target, kwargs, nodelist):
        self.target=target
        self.kwargs=kwargs
        self.nodelist=nodelist

    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        # check if blank_style is set
        blank_style=context.get("blank_style")

        # get link text
        if kwargs.get("confused"):
            link_text = "(confused?)"
        else:
            try:
                link_text = self.nodelist.render(context)
            except:
                link_text=None
        if link_text:
            kwargs["link_text"]=link_text

        target = self.target.resolve(context)
        
        target_class = None
        
        # check if target is an instance of an object
        if isinstance(target, Page):
            target_class = Page
        elif isinstance(target, Applet):
            target_class = Applet
        elif isinstance(target, Video):
            target_class = Video
        elif isinstance(target, Image):
            target_class = Image
        elif isinstance(target, Assessment):
            target_class = Assessment
            
        # if target is not an object, then check for type kwarg
        # and look for that type of object with code given by target
        # defaults to Page
        if not target_class:
            target_class_string = kwargs.get("class")
            try:
                target_class_string=target_class_string.lower()
            except:
                pass
            if target_class_string=="applet":
                target_class=Applet
            elif target_class_string=="video":
                target_class=Video
            elif target_class_string=="image":
                target_class=Image
            elif target_class_string=="assessment":
                target_class=Assessment
            else:
                target_class=Page
                
            try:

                if target_class != Page:
                    target=target_class.objects.get(code=target)
                    
                else:
                    # for Page, determine page type
                    page_type = kwargs.get("page_type")

                    if page_type is not None and \
                       not isinstance(page_type, PageType):
                        try:
                            page_type = PageType.objects.get(code=page_type)
                        except ObjectDoesNotExist:
                            page_type = None

                    if page_type is None:
                        page_type = return_default_page_type()

                    target=target_class.objects.get(code=target, 
                                                    page_type=page_type)


            # if object does not exist, set link to point to target
            # mark as broken
            except ObjectDoesNotExist:
                if target_class==Page:
                    link_url = "/%s" % target
                else:
                    link_url = "/%s/%s" % \
                        (target_class.__name__.lower(), target)
            
                # if blank style,
                # don't give link, just return the link text
                # and show that it is broken so can search for it
                if(blank_style):
                    return " %s BRKNLNK " % link_text
                else:
                    return '<a href="%s" class="broken">%s</a>' % \
                        (link_url, link_text)

        if target_class==Page:
            equation_code= kwargs.get("equation")
            if equation_code:
                kwargs["blank_style"]=blank_style
                return target.return_equation_link(equation_code,
                                                   **kwargs)
            
        if blank_style:
            return " %s " % link_text

        if kwargs.get("extended"):
            return target.return_extended_link(**kwargs)

        return target.return_link(**kwargs)


@register.tag
def intlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    
    target = parser.compile_filter(bits[1])

    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    nodelist = parser.parse(('endintlink',))
    parser.delete_first_token()

    return InternalLinkNode(target, kwargs, nodelist)



@register.tag
def extendedlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    
    target = parser.compile_filter(bits[1])

    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)

    kwargs["extended"] = parser.compile_filter("1")

    return InternalLinkNode(target, kwargs, "")



@register.tag
def confusedlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    target = parser.compile_filter(bits[1])


    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    kwargs["confused"] = parser.compile_filter("1")

    return InternalLinkNode(target, kwargs, "")



class EquationTagNode(template.Node):
    def __init__(self, code, tag):
        self.code=code
        self.tag=tag
    def render(self, context):
        
        code = self.code.resolve(context)
        tag = self.tag.resolve(context)

        # check to see if the variable process_equation_tags is set
        # if so, add entry to database
        if context.get("process_equation_tags"):
            # get page object, if doesn't exist, just return blank string
            thepage = context.get("thepage")
            if thepage:
                # add equation tag
                EquationTag.objects.create \
                    (page=thepage, code=code, tag=tag)
            else:
                return ""
            
        # check if blank_style is set t
        # if so, return (tag)
        if context.get("blank_style"):
            return " (%s) " % tag

        # return the tag in format for processing by MathJax
        # this will create an equation label using code,
        # display the equation number as tag
        # and create a html anchor of mjx-eqn-tag
        return '\\label{%s}\\tag{%s}' % (code,tag)


@register.tag
def equation_tag(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % bits[0]
    code=parser.compile_filter(bits[1])
    tag=parser.compile_filter(bits[2])
    return EquationTagNode(code,tag)


class ExternalLinkNode(template.Node):
    def __init__(self, external_url, nodelist):
        self.external_url = external_url
        self.nodelist=nodelist
    def render(self, context):
        
        external_url = self.external_url.resolve(context)
        link_text = self.nodelist.render(context)

        # check to see if the variable update_database is set
        if context.get("update_database"):
            # get page object, 
            # and save as linked from that page
            thepage = context.get("thepage")
            if thepage:
                extlink = ExternalLink.objects.create \
                    (external_url=external_url,
                     in_page=thepage, link_text=link_text)
                        
            # if not in a page, save without reference to page
            else:
                extlink = ExternalLink.objects.create \
                    (external_url=external_url,
                     link_text=link_text)

        # check if blank_style is set
        if context.get("blank_style"):
            return "%s %s" %  (external_url, link_text)
        else:
            return '<a href="%s" class="external">%s</a>' % \
                (external_url, link_text)
        

@register.tag
def extlink(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r tag requires one argument" % bits[0]
    external_url = parser.compile_filter(bits[1])

    nodelist = parser.parse(('endextlink',))
    parser.delete_first_token()

    return ExternalLinkNode(external_url,nodelist)


class NavigationTagNode(template.Node):
    def __init__(self,page_anchor, navigation_phrase, navigation_subphrase):
        self.page_anchor=page_anchor
        self.navigation_phrase=navigation_phrase
        self.navigation_subphrase=navigation_subphrase
    def render(self, context):
        page_anchor = self.page_anchor.resolve(context)
        navigation_phrase = self.navigation_phrase.resolve(context)
        navigation_subphrase = resolve_if_set(self.navigation_subphrase, context)
        
        # Render the phrase, subphrase, and page_anchor 
        # as templates under current context.
        # This way, if include template variables like "number {{number}}"
        # in the string, they will be replaced with their values.
        # This is a separate step from the above resolving, which 
        # allows one to pass in a template variable for the entire string
        page_anchor=template.Template(page_anchor).render(context)
        navigation_phrase=template.Template(navigation_phrase).render(context)
        if navigation_subphrase:
            navigation_subphrase=template.Template(navigation_subphrase).render(context)

        # check to see if the variable navigation_tags is set
        # if so, add entry to database
        if context.get("process_navigation_tags"):
            # get page object, if doesn't exist, just return blank string
            thepage = context.get("thepage")
            if not thepage:
                return ""
            
            # add navigation_tag
            if navigation_subphrase:
                # first try to find the phrase already there
                # and just create subphrase entry
                try:
                    navigation_entry = PageNavigation.objects.get \
                        (page=thepage, \
                             navigation_phrase=navigation_phrase)
                    navigation_sub_entry=PageNavigationSub.objects.create \
                        (navigation=navigation_entry, \
                             navigation_subphrase=navigation_subphrase, \
                             page_anchor=page_anchor)
                except:
                    # next try to create both phrase and subphrase entries
                    try:
                        navigation_entry = PageNavigation.objects.create \
                            (page=thepage, \
                                 navigation_phrase=navigation_phrase,\
                                 page_anchor=page_anchor)
                        navigation_sub_entry=PageNavigationSub.objects.create \
                            (navigation=navigation_entry, \
                                 navigation_subphrase=navigation_subphrase, \
                                 page_anchor=page_anchor)
                            
                            
                    except:
                        raise #pass
            else:
                # if no subphrase, just create phrase entry
                try:
                    navigation_entry = PageNavigation.objects.create \
                        (page=thepage, 
                         navigation_phrase=navigation_phrase,
                         page_anchor=page_anchor)
                except:
                    raise #pass
                        

        # check if blank_style is set 
        # if so, return ""
        if context.get("blank_style"):
            return ""

        # return an anchor
        return '<a id="%s" class="anchor"></a>' % page_anchor
 
@register.tag
def navigation_tag(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % bits[0]
    page_anchor=parser.compile_filter(bits[1])
    navigation_phrase=parser.compile_filter(bits[2])
    if len(bits) > 3:
        navigation_subphrase=parser.compile_filter(bits[3])
    else:
        navigation_subphrase = None
    return NavigationTagNode(page_anchor, navigation_phrase, navigation_subphrase)



class FootnoteNode(template.Node):
    def __init__(self,cite_code,footnote_text):
        self.cite_code=cite_code
        self.footnote_text=footnote_text
    def render(self, context):
        # get page object, if doesn't exist, just return blank string
        thepage=context.get("thepage")
        if not thepage:
            return ""
        
        cite_code = self.cite_code.resolve(context)

        # check to see if the variable process_citations is set
        # if so, add entry to database
        if context.get("process_citations"):

            # check to see if page already has citations
            # and if so, what the largest reference number is
            previous_citations=PageCitation.objects.filter(page=thepage)
            previous_reference_number=0
            if previous_citations:
                previous_reference_number=previous_citations.aggregate(Max('reference_number'))['reference_number__max']
                
            try:
                # add footnote entry
                footnote_text = self.footnote_text.resolve(context)
                footnote_entry = PageCitation.objects.create \
                    (page=thepage, \
                         code=cite_code, \
                         footnote_text=footnote_text, \
                         reference_number = previous_reference_number+1)
            
            # fail silently
            except:
                pass

        # find reference number
        reference_number = 0
        footnote_entry = PageCitation.objects.get( \
            page=thepage, code=cite_code)
        reference_number = footnote_entry.reference_number

        # check if blank_style is set 
        # if so, return reference number
        if context.get("blank_style"):
            return "[%s]" % reference_number

        # return link to reference
        return '<a href="#citation:%s"><sup>%s</sup></a>' % (reference_number, reference_number)
 
@register.tag
def footnote(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two argument" % bits[0]

    cite_code=parser.compile_filter(bits[1])
    footnote_text=parser.compile_filter(bits[2])

    return FootnoteNode(cite_code,footnote_text)




class CitationNode(template.Node):
    def __init__(self,cite_codes):
        self.cite_codes=cite_codes

    def render(self, context):
        # get page object, if doesn't exist, just return blank string
        thepage = context.get("thepage")
        if not thepage:
            return ""

        cite_codes = []
        for code in self.cite_codes:
            cite_codes.append(code.resolve(context))

        # check to see if the variable process_citations is set
        # if so, add entry to database
        if context.get("process_citations"):

            # check to see if page already has citations
            # and if so, what the largest reference number is
            previous_citations=PageCitation.objects.filter(page=thepage)
            previous_reference_number=0
            if previous_citations:
                previous_reference_number=previous_citations.aggregate(Max('reference_number'))['reference_number__max']
                
            # find references based on cite_code
            for cite_code in cite_codes:
                try:
                    the_reference=Reference.objects.get(code=cite_code)
                        
                    # add citation entry
                    citation_entry = PageCitation.objects.create \
                        (page=thepage, \
                             code=cite_code, \
                             reference=the_reference, \
                             reference_number = previous_reference_number+1)
                    previous_reference_number += 1

                # fail silently
                except:
                    pass

        # find reference number
        reference_numbers = []
        for cite_code in cite_codes:
            try:
                citation_entry = PageCitation.objects.get( \
                    page=thepage, code=cite_code)
                reference_numbers.append(citation_entry.reference_number)
            except:
                reference_numbers.append('??')
                
        # check if blank_style is set to 1
        # if so, return reference number
        if context.get("blank_style"):
            reference_number_string=""
            for i, rn in enumerate(reference_numbers):
                reference_number_string="%s%s" \
                    %(reference_number_string, rn)
                if i < len(reference_numbers)-1:
                    reference_number_string += ","
            return "[%s]" % reference_number_string

        reference_number_string=""
        for i, rn in enumerate(reference_numbers):
            reference_number_string='%s<a href="#citation:%s">%s</a>' \
                %(reference_number_string, rn,rn)
            if i < len(reference_numbers)-1:
                reference_number_string += ","

        # return links to references
        return '<sup>%s</sup>' % (reference_number_string)

@register.tag
def citation(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]

    cite_codes=[]
    for i in range(1,len(bits)):
        cite_codes.append(parser.compile_filter(bits[i]))
    
    return CitationNode(cite_codes)



class IndexEntryNode(template.Node):
    def __init__(self, indexed_phrase, indexed_subphrase, page_anchor, index_type):
        self.indexed_phrase=indexed_phrase
        self.indexed_subphrase=indexed_subphrase
        self.page_anchor=page_anchor
        self.index_type=index_type
    def render(self, context):
        page_anchor = resolve_if_set(self.page_anchor,context)

        # check to see if the variable process_index_entries is set
        # if so, add entry to database
        if context.get("process_index_entries"):
            # get page object, if doesn't exist, just return blank string
            thepage = context.get("thepage")
            if not thepage:
                return ""

            indexed_phrase = self.indexed_phrase.resolve(context)
            indexed_subphrase = resolve_if_set(self.indexed_subphrase,context)
            index_type = resolve_if_set(self.index_type, context)
                
            # check to see if index_type exists.  If not, make it a general index entry
            if index_type:
                try:
                    index_type = IndexType.objects.get(code=index_type)
                except ObjectDoesNotExist:
                    index_type = IndexType.objects.get(code="general")
            else:
                index_type = IndexType.objects.get(code="general") 
                        
                # add index entry
                index_entry = IndexEntry.objects.create \
                    (page=thepage, index_type=index_type, 
                     indexed_phrase=indexed_phrase,
                     indexed_subphrase=indexed_subphrase,
                     page_anchor=page_anchor)

        # check if blank_style is set
        # if so, return ""
        if context.get("blank_style"):
            return ""

        # if page_anchor is not null, return an anchor, else return nothing
        if(page_anchor):
            return '<a id="%s" class="anchor"></a>' % page_anchor
        else:
            return ""
 
@register.tag
def index_entry(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    indexed_phrase=parser.compile_filter(bits[1])
    if len(bits) >2:
        indexed_subphrase=parser.compile_filter(bits[2])
    else:
        indexed_subphrase = None;
    if len(bits)>3:
        page_anchor=parser.compile_filter(bits[3])
    else:
        page_anchor = None;
    if len(bits)>4:
        index_type=parser.compile_filter(bits[4])
    else:
        index_type = None;
    return IndexEntryNode(indexed_phrase, indexed_subphrase, page_anchor, index_type)



class TitleNode(template.Node):
    def __init__(self, title_text, navigation_phrase):
        self.title_text=title_text
        self.navigation_phrase = navigation_phrase
    def render(self, context):
        
        title_text = self.title_text.resolve(context)

        # check to see if the variable update_database is set
        # if so, add entry to database
        if context.get("update_database"):
            # get page object, 
            # and save title to that database entry
            thepage = context.get("thepage")
            if thepage:
                thepage.title=title_text
                
        # if navigation_phase exists
        # add a navigation tag with that phrase and anchor main
        # if process_navigation_tags is set
        navigation_phrase=resolve_if_set(self.navigation_phrase,context)

        if navigation_phrase:
            if context.get("process_navigation_tags"):
                thepage = context.get("thepage")
                if thepage:
                    try:
                        # add an navigation_entry, ignore any errors
                        navigation_entry = PageNavigation.objects.create \
                            (page=thepage, 
                             navigation_phrase=self.navigation_phrase,
                             page_anchor="main")
                    except:
                        pass
                        

        # check if blank_style is set 
        # if so, return undecorated text
        if context.get("blank_style"):
            return " %s " % self.title_text
        
        return ""

 
@register.tag
def title(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    title_text=parser.compile_filter(bits[1])
    if len(bits) > 2:
        navigation_phrase=parser.compile_filter(bits[2])
    else:
        navigation_phrase = None

    return TitleNode(title_text, navigation_phrase)


class DescriptionNode(template.Node):
    def __init__(self, description_text):
        self.description_text=description_text
    def render(self, context):
        # check to see if the variable update_database is set
        # if so, add entry to database
        if context.get("update_database"):
        
            description_text = self.description_text.resolve(context)
            # get page object, 
            # and save description to that database entry
            thepage = context.get("thepage")
            if thepage:
                thepage.description=description_text

        return ""

@register.tag
def description(parser, token):
    try:
        tag_name, description_text = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    
    description_text = parser.compile_filter(description_text)

    return DescriptionNode(description_text)


class ImageNode(template.Node):
    def __init__(self, image, kwargs):
        self.image= image
        self.kwargs=kwargs
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        image = self.image.resolve(context)

        # if image is not an image instance
        # try to load image with that code
        if not isinstance(image, Image):
            # test if image with image_code exists
            try:
                image=Image.objects.get(code=image)
                # if image does not exist
                # return tag to image code anyway
            except ObjectDoesNotExist:
                return '<img src="/%s" alt="[broken image]" class="broken" />' % image

        imagefile=None
        # check if a notation system is defined in template
        notation_system = context.get("notation_system")
            
        # if notation system defined, check if image has notation_system
        if notation_system:
            try:
                image_notation_system = image.imagenotationsystem_set.get(notation_system=notation_system)
                # if image has notation system, check for alternate image
                if image_notation_system.imagefile:
                    imagefile=image_notation_system.imagefile
                    width=image_notation_system.width*0.75
                    height=image_notation_system.height*0.75
            except:
                pass
        

        #svgfile=None

        # if don't have image from notation system, get default image
        if not imagefile:
            imagefile = image.imagefile
            width = image.width*0.75
            height = image.height*0.75
            
        title = image.title

        # check to see if the variable process_image_entries is set
        if context.get("process_image_entries"):
            # get page object, 
            thepage = context.get("thepage")
            if thepage:
                # add page to in_pages of image
                image.in_pages.add(thepage)

        # check if blank_style is set 
        # if so, just return title of image
        if context.get("blank_style"):
            return " %s " % title
                    
        # return image
        if image.description:
            title = 'title="%s"' % image.description
        else:
            title = ""
        if image.title:
            alt = 'alt="%s"' % image.title
        else:
            alt = ""

        try:
            max_width = int(kwargs["width"])
        except:
            max_width = None
        if max_width and max_width < width:
            reduce_ratio=max_width/float(width)
            width=max_width
            height=int(reduce_ratio*height)

        css = kwargs.get("css")
        if css:
            imageclass=css
        else:
            imageclass="displayed"

        link_url = image.get_absolute_url()
            
        return '<a id="%s" class="anchor"></a><a href="%s" %s><img class="%s" src="%s" %s width ="%s" height="%s" /></a>' % \
            (image.anchor(),link_url, 
             title, imageclass, imagefile.url,
             alt, int(width), int(height))

    
@register.tag
def image(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    image = parser.compile_filter(bits[1])

    kwargs = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  
    return ImageNode(image, kwargs)



class ProcessMiTagsNode(template.Node):
    def __init__(self, the_text_var, blank_style):
        self.the_text_var=the_text_var
        self.blank_style=blank_style
    def render(self, context):
        templatetext=self.the_text_var.resolve(context)
        blank_style = resolve_if_set(self.blank_style, context)

        if not templatetext:
            return ""

        context.push()

        if '_auxiliary_data_' not in context:
            from midocs.functions import return_new_auxiliary_data
            context['_auxiliary_data_'] = return_new_auxiliary_data()
        
        try:
            if blank_style:
                context['blank_style']=1
                rendered_text = template.Template("{% load mi_tags testing_tags %}"+templatetext).render(context)
            else:
                rendered_text = template.Template("{% load mi_tags testing_tags %}"+templatetext).render(context)
        except Exception as e:
            rendered_text = "Template error (TMPLERR): %s" % e

        context.pop()

        return rendered_text


@register.tag
def process_mi_tags(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    the_text_var = parser.compile_filter(bits[1])

    if len(bits) > 2:
        blank_style=parser.compile_filter(bits[2])
    else:
        blank_style = None

    return ProcessMiTagsNode(the_text_var, blank_style)



def return_applet_parameter_string(applet):
    """
    return string of applets parameters.
    If value of parameter defined in applet, use that one,
    else use the value from applet type
    Skip DEFAULT_WIDTH or DEFAULT_HEIGHT

    """
    the_string=""

    # loop through all applet parameters of applet type
    for possible_param in applet.applet_type.valid_parameters.all():
        parameter_name=possible_param.parameter_name
        # skip DEFAULT_WIDTH and DEFAULT_HEIGHT
        if parameter_name != "DEFAULT_WIDTH" and \
                parameter_name != "DEFAULT_HEIGHT":
 
            parameter_value=""
            # check to see if parameter defined for particular applet
            try:
                app_param=applet.appletparameter_set.get(parameter=possible_param)
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value
                
            # if not in particular applet, use default value
            except ObjectDoesNotExist:
                parameter_value=possible_param.default_value

            # if applet parameter is defined twice just take one of the values
            except MultipleObjectsReturned:
                app_param=applet.appletparameter_set.filter(parameter=possible_param)[0]
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value

            # if found a value, add to html string
            if parameter_value:
                the_string = '%s<param name="%s" value="%s" />' \
                    % (the_string, parameter_name, parameter_value)
    
    return the_string



def return_applet_parameter_dictionary(applet):
    """
    return dictionary of applets parameters.
    If value of parameter defined in applet, use that one,
    else use the value from applet type
    Skip DEFAULT_WIDTH or DEFAULT_HEIGHT
    """


    applet_parameters = {}

    # loop through all applet parameters of applet type
    for possible_param in applet.applet_type.valid_parameters.all():
        parameter_name=possible_param.parameter_name
        # skip DEFAULT_WIDTH and DEFAULT_HEIGHT
        if parameter_name != "DEFAULT_WIDTH" and \
                parameter_name != "DEFAULT_HEIGHT" and \
                parameter_name != "code":
 
            parameter_value=""
            # check to see if parameter defined for particular applet
            try:
                app_param=applet.appletparameter_set.get(parameter=possible_param)
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value
                
            # if not in particular applet, use default value
            except ObjectDoesNotExist:
                parameter_value=possible_param.default_value

            # if applet parameter is defined twice just take one of the values
            except MultipleObjectsReturned:
                app_param=applet.appletparameter_set.filter(parameter=possible_param)[0]
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value

            # if found a value, add to dictionary
            if parameter_value:
                applet_parameters[parameter_name] = parameter_value
    
    return applet_parameters

def return_applet_error_string(applet, panel=0):

    the_string='<div class="appleterror">'

    if panel < 2:
        if applet.image:
            the_string = '%s<img class="displayed" src="%s" alt="%s" width ="%s" height="%s" />' \
                %(the_string, applet.image.url, applet.annotated_title(),
                  applet.image_width, applet.image_height)
    else:
        if applet.image2:
            the_string = '%s<img class="displayed" src="%s" alt="%s" width ="%s" height="%s" />' \
                %(the_string, applet.image2.url, applet.annotated_title(),
                  applet.image2_width, applet.image2_height)
    
    if panel !=1:
        the_string= '%s%s' % (the_string,applet.applet_type.error_string)
    
    the_string= '%s</div>' % (the_string)

    return the_string

def return_print_image_string(applet, panel=0):
    the_string='<div class="appletprintimage">'

    if panel !=2:
        if applet.image:
            the_string = '%s<img src="%s" alt="%s" width ="%s" height="%s" />' \
                %(the_string, applet.image.url, applet.annotated_title(),
                  applet.image_width, applet.image_height)
    else:
        if applet.image2:
            the_string = '%s<img src="%s" alt="%s" width ="%s" height="%s" />' \
                %(the_string, applet.image2.url, applet.annotated_title(),
                  applet.image2_width, applet.image2_height)
         
    the_string= '%s</div>' % (the_string)

    return the_string

# Geogebra doesn't understand e in scientific notation but needs E,
# so created a StrPrinterE and function sstrE which uses E
# when printing scientific notation

class StrPrinterE(StrPrinter):
    """
    StrPrinter where Floats in scientific notation are printed
    with an E rather than an e
    """

    def _print_Float(self, expr):
        import sympy.mpmath.libmp as mlib
        from sympy.mpmath.libmp import prec_to_dps

        prec = expr._prec
        if prec < 5:
            dps = 0
        else:
            dps = prec_to_dps(expr._prec)
        if self._settings["full_prec"] is True:
            strip = False
        elif self._settings["full_prec"] is False:
            strip = True
        elif self._settings["full_prec"] == "auto":
            strip = self._print_level > 1
        rv = mlib.to_str(expr._mpf_, dps, strip_zeros=strip)
        if rv.startswith('-.0'):
            rv = '-0.' + rv[3:]
        elif rv.startswith('.0'):
            rv = '0.' + rv[2:]

        # only change from standard StrPrinter is addition of this line
        rv=rv.replace('e','E')
        return rv

def sstrE(expr, **settings):
    """
    Returns the expression as a string, using E in scientific notaiton
    """

    p = StrPrinterE(settings)
    s = p.doprint(expr)

    return s


def Geogebra_change_object_javascript(context, appletobject,applet_variable,
                                      objectvalue, objectvalue_string):
    
    object_type = appletobject.object_type.object_type

    if appletobject.name_for_changes:
        object_name = appletobject.name_for_changes
    else:
        object_name = appletobject.name

    # if objectvalue is math_object, use expression
    try:
        value=objectvalue.return_expression()
    except:
        value = objectvalue

    try:
        if object_type=='Point':
            # sympify to turn strings into tuple
            try:
                from sympy import sympify
                value=sympify(value)
            except:
                return ""

            # try to x and y values from point
            try:
                value_x = value.x
                value_y = value.y
            except AttributeError:
                # else try as a Tuple
                value_x = value[0]
                value_y = value[1]
            try:
                javascript = '%s.setCoords("%s", %E, %E);\n' % \
                    (applet_variable, object_name,
                     float(value_x), float(value_y))
            except:
                return ""
        elif object_type=='Number':
            try:
                javascript = '%s.setValue("%s", %E);\n' % \
                    (applet_variable, object_name,
                     float(value))
            except:
                return ""
        elif object_type=='Boolean':
            javascript = '%s.setValue("%s", %s);\n' % \
                (applet_variable, object_name,
                 value)
        elif object_type=='Text':
            # don't use value, use objectvalue, so math_objects
            # return latex expression
            value_string = "%s" % objectvalue
            # escape \ for javascript
            value_string = value_string.replace('\\','\\\\')
            javascript = '%s.evalCommand(\'%s="%s"\');\n' % \
                (applet_variable, object_name,
                 value_string)  
        elif object_type=='Function':
            from sympy import Symbol
            local_dict=context["_sympy_local_dict_"]
            try:
                the_fun = local_dict[str(objectvalue_string)]
            except KeyError:
                return ""
            try:
                javascript = '%s.evalCommand(\'%s(x)=%s\');\n' % \
                    (applet_variable, object_name,
                    sstrE(the_fun(Symbol('x'))))
            except:
                return ""
        elif object_type=='Function2D':
            from sympy import Symbol
            local_dict=context["_sympy_local_dict_"]
            try:
                the_fun = local_dict[str(objectvalue_string)]
            except KeyError:
                return ""
            try:
                javascript = '%s.evalCommand(\'%s(x,y)=%s\');\n' % \
                    (applet_variable, object_name, \
                    sstrE(the_fun(Symbol('x'),Symbol('y'))))
            except:
                return ""
        elif object_type=='List':
            # sympify to turn strings into tuple (or list if in brackets)
            try:
                from sympy import sympify
                value=sympify(value)
            except:
                return ""

            try:
                the_list = ""
                for element in value:
                    if the_list:
                        the_list += ", "
                    if element.is_Float:
                        the_list += "%E" % element
                    else:
                        the_list += "%s" % element
            except TypeError:
                # if value is not list, just return single value
                if value.is_Float:
                    the_list = "%E" % value
                else:
                    the_list = "%s" % value


            javascript = '%s.evalCommand(\'%s={%s}\');\n' % \
                (applet_variable, object_name,
                 the_list)

        return javascript
    except:
        raise #return ""

def Geogebra_capture_object_javascript(appletobject, applet_variable,
                                       varname, related_objects=[]):
    
    object_type = appletobject.object_type.object_type
    javascript= ""
    if object_type=='Point':
        xcoord = '%s.getXcoord("%s")' % \
            (applet_variable, appletobject.name)
        ycoord = '%s.getYcoord("%s")' % \
            (applet_variable, appletobject.name)
        return '%s="Point("+%s+","+%s+")"' % (varname, xcoord,ycoord)
    elif object_type=='Number' or object_type=='Boolean':
        return '%s=%s.getValue("%s")' % \
            (varname, applet_variable, appletobject.name)
    elif object_type=='Text':
        return '%s=%s.getValueString("%s")' % \
            (varname, applet_variable, appletobject.name)
    elif object_type=='Function':
        inputvarname = appletobject.function_input_variable
        if not inputvarname:
            inputvarname="x"
        return '%s=/%s\(%s\) = (.*)/g.exec(%s.getValueString("%s"))[1]' % \
            (varname, appletobject.name, inputvarname, 
             applet_variable, appletobject.name)
    elif object_type=='List':
        value = '%s.getValueString("%s")' % \
            (applet_variable, appletobject.name)
        # Extract the list within the braces returned by getValueString
        # Replace all curly braces by parentheses so lists will be tuples
        # Add comma at end so single element will still be a tuple (especially
        # important for lists of lists)
        return "try {\n %s=/{(.*)}/.exec(%s)[1].replace(/(\{)/g, '(').replace(/(\})/g, ')')+','\n}\ncatch(e) {\n %s='';\n}\n" % (varname, value, varname)
    elif object_type=='Line':
        if len(related_objects)==2:
            point1=related_objects[0]
            point2=related_objects[1]
            if point1.object_type.object_type=='Point' and \
                    point2.object_type.object_type=='Point':
                xcoord1 = '%s.getXcoord("%s")' % \
                    (applet_variable, point1.name)
                ycoord1 = '%s.getYcoord("%s")' % \
                    (applet_variable, point1.name)
                xcoord2 = '%s.getXcoord("%s")' % \
                    (applet_variable, point2.name)
                ycoord2 = '%s.getYcoord("%s")' % \
                    (applet_variable, point2.name)
                return '%s="Line(Point("+%s+","+%s+"),Point("+%s+","+%s+"))";\n' % \
                        (varname, xcoord1,ycoord1, xcoord2,ycoord2)

    return "%s=''" % varname
    

def GeogebraTube_link(context, applet, applet_identifier, width, height):

    try:
        geogebracode=applet.appletparameter_set.get(parameter__parameter_name ="code").value
    except ObjectDoesNotExist:
        return "[Broken applet]", ""

    applet_parameters = return_applet_parameter_dictionary(applet)

    applet_parameter_string = ""
    for par in applet_parameters.keys():
        applet_parameter_string += "/%s/%s" % (par,applet_parameters[par])

    html_string = '<div class="applet"><iframe scrolling="no" src="//www.geogebratube.org/material/iframe/id/%s/width/%s/height/%s/border/888888%s/at/preferjava" width="%spx" height="%spx" style="border:0px;"> </iframe></div>' %\
        (geogebracode, width, height, applet_parameter_string, width, height)

    return html_string, ''
    

def GeogebraWeb_link(context, applet, applet_identifier, width, height):

    html_string=""
    script_string = ""

    applet_parameters = return_applet_parameter_dictionary(applet)
    applet_parameter_string = ",".join(["%s:%s" % (par,applet_parameters[par]) \
                                        for par in applet_parameters.keys()])

    #html_string += '<div class="javascriptapplet"><article id="%s" class="geogebraweb" data-param-width="%s" data-param-height="%s" data-param-id="%s" data-param-showResetIcon="false" data-param-enableLabelDrags="false" data-param-showMenuBar="false" data-param-showToolBar="false" data-param-showAlgebraInput="false" data-param-useBrowserForJS="true" data-param-enableRightClick="false" data-param-ggbbase64="%s"></article></div>\n' % \
    #    (applet_identifier, width, height, applet_identifier, applet.encoded_content)
    html_string += '<div class="javascriptapplet"><div class="geogebrawebapplet" id="container%s" style="min-width:%spx;min-height:%spx"></div></div>\n' % \
        (applet_identifier, width, height)
    script_string += 'var parameters%s = {"id":"%s","width":%s,"height":%s,%s,"ggbBase64":"%s","language":"en","country":"US","isPreloader":false,"screenshotGenerator":false,"preventFocus":false,"fixApplet":false};\n' % \
                   (applet_identifier, applet_identifier, width, height, applet_parameter_string, applet.encoded_content)
    script_string += 'var applet%s = new GGBApplet( parameters%s, true);\n' % \
                     (applet_identifier, applet_identifier)
                
    script_string += "applet%s.setJavaCodebase('%sgeogebra/Java/5.0', 'true');" % (applet_identifier, context.get("STATIC_URL","/static/"))
    script_string += "applet%s.setHTML5Codebase('%sgeogebra/HTML5/5.0/web/', 'true');" % (applet_identifier, context.get("STATIC_URL","/static/"))
    #html_string += "applet.setPreviewImage('GeoGebra/files/material-49718.png', 'GeoGebra/images/GeoGebra_loading.png');"

    #script_string += "window.onload = function() {\napplet%s.inject('container%s', 'auto');\n}" % (applet_identifier, applet_identifier)
    script_string += "applet%s.inject('container%s', 'auto');\n" % (applet_identifier, applet_identifier)

    return html_string, script_string


def Geogebra_link(context, applet, applet_identifier, width, height):
    # html_string='<div class="applet"><object class="ggbApplet" type="application/x-java-applet" id="%s" height="%s" width="%s"><param name="code" value="geogebra.GeoGebraApplet" /><param name="archive" value="geogebra.jar" /><param name="codebase" value="%sjar/" />' % \
    #     (applet.code, height, width, context.get("STATIC_URL","") )
    html_string='<div class="applet"><applet class="ggbApplet" name="%s" code="geogebra.GeoGebraApplet" archive="geogebra.jar" codebase="%sjar/" width="%s" height="%s">' % \
        (applet.code, context.get("STATIC_URL",""), width, height )
    if applet.javascript:
        html_string='<div class="applet"><applet class="ggbApplet" name="%s" code="geogebra.GeoGebraApplet" archive="geogebra.jar" codebase="%sjar/" width="%s" height="%s">' % \
            (applet.code, context.get("STATIC_URL",""), width, height )
  
    html_string='%s%s' % (html_string, return_applet_parameter_string(applet))

    html_string= '%s<param name="codebase_lookup" value="false"><param name="ggbOnInitParam" value="%s" />' \
        % (html_string,applet.code)
    if applet.applet_file:
        html_string= '%s<param name="filename" value="%s" />' \
            % (html_string,applet.applet_file.url)
    # elif applet.encoded_content:
    #     html_string= '%s<param name="ggbBase64" value="%s" />' \
    #         % (html_string,applet.encoded_content)
    html_string = '%s%s' % (html_string, return_applet_error_string(applet))

    script_string = ''
    if applet.javascript:
        html_string = '%s</applet></div>\n' % html_string

        script_string='var ggbApplet = document.%s;\n%s' % (applet.code, applet.javascript)
    else:
        #html_string = '%s</object></div>' % html_string
        html_string = '%s</applet></div>\n' % html_string

    html_string = '%s%s' % (html_string, return_print_image_string(applet))

    return html_string, script_string




def Three_link(context, applet, applet_identifier, width, height, url_get_parameters):

    applet_id = "three_applet_%s" % applet_identifier

    if applet.child_applet:
        child_width = int(width*applet.child_applet_percent_width/100.0)
        width = int(width*(1.0-applet.child_applet_percent_width/100.0))

    # display an image while applet is loading
    # (actually while mathjax is loading)
    applet_loading_image = ""
    if applet.image:
        applet_loading_image = '<img src="%s" alt="%s" width ="%s" height="%s" />' \
            % (applet.image.url, applet.annotated_title(), width, height)
        
    applet_loading_image = '<div class="appletimagecontainer" style="width:%spx; height:%spx;" >%s<h4 style="position: absolute; top: %spx; width: 100%%;" class="three_applet_loading_message">Applet loading</h4></div>' % (width, height, applet_loading_image, height/2)

    html_string = '<div class="threeapplet" id="container_%s" >%s</div><div class="appleterror three_load_error"></div>' % (applet_id, applet_loading_image)

    if applet.child_applet:

        html_string = '<div class="ym-gl" style="width: %s%%"><div class="ym-gbox-left appletchild-left">%s</div></div>' % (100.0-applet.child_applet_percent_width, html_string)

        # display an image while applet is loading
        # (actually while mathjax is loading)
        # use image2, if it is exists, else the image from the child applet
        if applet.image2:
            image_url = applet.image2.url
        elif applet.child_applet.image:
            image_url = applet.child_applet.image.url
        else:
            image_url = ""
        
        applet_loading_image=""
        if image_url:
            applet_loading_image = '<img src="%s" alt="%s" width ="%s" height="%s" />' \
                % (image_url, applet.child_applet.annotated_title(), \
                       child_width, height)
            
        applet_loading_image = '<div class="appletimagecontainer" style="width:%spx; height:%spx;" >%s<h4 style="position: absolute; top: %spx; width: 100%%;" class="three_applet_loading_message">Applet loading</h4></div>' % (child_width, height, applet_loading_image, height/2)


        html_string +='<div class="ym-gr" style="width: %s%%"><div class="ym-gbox-right appletchild-right"><div class="threeapplet" id="container2_%s">%s</div><div class="appleterror three_load_error"></div></div></div>' % (applet.child_applet_percent_width, applet_id, applet_loading_image)
        
        html_string = '<div class="ym-grid linearize-level-1">%s</div>' % html_string
        
    html_string = '<div class="javascriptapplet">%s</div>' % html_string

    parameters_string = "static_url: '%s', media_url: '%s'" % \
        (context.get("STATIC_URL",""), context.get("MEDIA_URL",""))
    if 'allow_screenshots' in url_get_parameters:
        parameters_string += ", allow_screenshots: true"

    script_string = "\napplet_%s=new MIAppletThree('container_%s', %s, %s, { %s });\n" % (applet_id, applet_id, width, height, parameters_string);

    script_string += "applet_%s.run = function() {\nvar renderer=this.renderer, container=this.container, width=this.width, height=this.height, namedObjects=this.namedObjects, parameters=this.parameters;\n%s\n}\n"  % (applet_id, applet.javascript)
    
    run_script_string = "\njQuery('#container_%s').empty();\napplet_%s.run();\n" % (applet_id, applet_id)
    
    if applet.child_applet:
        child_parameters = parameters_string
        if applet.child_applet_parameters:
            child_parameters += ", " + applet.child_applet_parameters
        script_string += "\napplet2_%s=new MIAppletThree('container2_%s', %s, %s, { %s });\n" % (applet_id, applet_id, child_width, height, child_parameters);
        script_string += "applet2_%s.run = function() {\nvar renderer=this.renderer, container=this.container, width=this.width, height=this.height, namedObjects=this.namedObjects, parameters=this.parameters;\n%s\n}\n"  % (applet_id, applet.child_applet.javascript)

        run_script_string += "\njQuery('#container2_%s').empty();\napplet2_%s.run();\n" % (applet_id, applet_id)

        # insert javascript to link applet and child objects
        for object_link in applet.appletchildobjectlink_set.all():
            # first check if objects exist in applet and child applet
            # if not, ignore
            try:
                applet_object = applet.appletobject_set.get\
                    (name=object_link.object_name)
            except ObjectDoesNotExist:
                continue
            try:
                child_applet_object = applet.child_applet.appletobject_set.get\
                    (name=object_link.child_object_name)
            except ObjectDoesNotExist:
                continue

            # look up object types.  Ignore if not same type
            applet_object_type = applet_object.object_type.object_type
            child_applet_object_type = \
                child_applet_object.object_type.object_type
            if applet_object_type != child_applet_object_type:
                continue
            
            if object_link.applet_to_child_link and \
                    applet_object.capture_changes and \
                    child_applet_object.change_from_javascript:
                    
                if child_applet_object.name_for_changes:
                    child_applet_object_name = \
                        child_applet_object.name_for_changes
                else:
                    child_applet_object_name = child_applet_object.name

                # insert link code, depending on object type
                if applet_object_type == 'Point' or applet_object_type == 'Number' or applet_object_type == 'Array' or applet_object_type == 'Vector':
                    run_script_string += '\napplet_%s.registerObjectUpdateListener("%s", function(event) {\n   applet2_%s.setValue("%s", applet_%s.getValue("%s"));\n });\n' \
                        % (applet_id, applet_object.name, applet_id, 
                           child_applet_object_name, applet_id, 
                           applet_object.name)
                        
            if object_link.child_to_applet_link  and \
                    child_applet_object.capture_changes and \
                    applet_object.change_from_javascript:
                    
                if applet_object.name_for_changes:
                    applet_object_name = \
                        applet_object.name_for_changes
                else:
                    applet_object_name = applet_object.name
                        
                # insert link code, depending on object type
                if applet_object_type == 'Point' or applet_object_type == 'Number' or applet_object_type == 'Array' or applet_object_type == 'Vector':
                    run_script_string += '\napplet2_%s.registerObjectUpdateListener("%s", function(event) {\n   applet_%s.setValue("%s", applet2_%s.getValue("%s"));\n });\n' \
                        % (applet_id, child_applet_object.name, applet_id, 
                           applet_object_name, applet_id, 
                           child_applet_object.name)
                
    
    three_javascript=context.dicts[0].get('three_javascript', '')
    three_javascript += script_string
    context.dicts[0]['three_javascript'] = three_javascript
    run_three_javascript=context.dicts[0].get('run_three_javascript', '')
    run_three_javascript += run_script_string
    context.dicts[0]['run_three_javascript'] = run_three_javascript

    return html_string, ''



def LiveGraphics3D_link(context, applet, applet_identifier, width, height):
    html_string='<div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (height, width, context.get("STATIC_URL",""))

    html_string='%s%s' % (html_string, return_applet_parameter_string(applet))
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
    html_string = '%s%s</object></div>%s' % (html_string, return_applet_error_string(applet), return_print_image_string(applet))

    return html_string, ''

def DoubleLiveGraphics3D_link(context, applet, applet_identifier, width, height):

    # first find all the parameters and put them into 
    # two parameter strings, one for each applet
    param_string1=""
    param_string2=""

   # loop through all applet parameters of applet type
    for possible_param in applet.applet_type.valid_parameters.all():
        parameter_name=possible_param.parameter_name
        # skip DEFAULT_WIDTH and DEFAULT_HEIGHT
        if parameter_name != "DEFAULT_WIDTH" and \
                parameter_name != "DEFAULT_HEIGHT":
 
            parameter_value=""
            # check to see if parameter defined for particular applet
            try:
                app_param=applet.appletparameter_set.get(parameter=possible_param)
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value
                
            # if not in particular applet, use default value
            except ObjectDoesNotExist:
                parameter_value=possible_param.default_value
                
            # if applet parameter is defined twice just take one of the values
            except MultipleObjectsReturned:
                app_param=applet.appletparameter_set.filter(parameter=possible_param)[0]
                parameter_name = possible_param.parameter_name
                parameter_value = app_param.value

            # if found a value, add to html string
            if parameter_value:
                # put it into string based on last digit
                # and ignore last digit
                if parameter_name[-1] == "1":
                    param_string1= '%s<param name="%s" value="%s" />' \
                        % (param_string1, parameter_name[:-1], parameter_value)
                elif parameter_name[-1]=="2":
                    param_string2= '%s<param name="%s" value="%s" />' \
                        % (param_string2, parameter_name[:-1], parameter_value)


    # start string with table and first applet tag
    html_string='<div class="ym-grid linearize-level-2"><div class="ym-g50 ym-gl"><div class="ym-gbox-left"><div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (height, width, context.get("STATIC_URL",""))
    
    # add the parameters for applet 1
    html_string = '%s%s' \
                % (html_string, param_string1)
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
        
    # close off applet 1 and begin tag for applet 2
    html_string = '%s%s</object></div>%s</div></div><div class="ym-g50 ym-gr"><div class="ym-gbox-right"><div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (html_string, return_applet_error_string(applet,1), return_print_image_string(applet,1), height, width, context.get("STATIC_URL",""))
    # add the parameters for applet 2
    html_string = '%s%s' \
                % (html_string, param_string2)
    if applet.applet_file2:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file2.url)
    
    html_string = '%s%s</object></div>%s</div></div></div>' % (html_string, return_applet_error_string(applet,2), return_print_image_string(applet,2))


    return html_string, ''



class AppletNode(template.Node):
    def __init__(self, applet, boxed, kwargs, kwargs_string):
        self.applet= applet
        self.boxed=boxed
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
                              for k, v in self.kwargs_string.items()])

        applet = self.applet.resolve(context)

        try:
            url_get_parameters = context.get('request').GET
        except:
            url_get_parameters = ""

        # if applet is not an applet instance
        # try to load applet with that code
        if not isinstance(applet, Applet):
            # test if applet with applet_code exists
            try:
                applet=Applet.objects.get(code=applet)
                # if applet does not exist
                # return tag to applet code anyway
            except ObjectDoesNotExist:
                return '<p>[Broken applet]</p>'

        # set width and height from kwarg parameters, if exist
        # else get defaults from applet, if exist
        # else get defaults from applettype, if exist
        # use default_size for any values not found
        default_size = 500

        width=0
        try:
            width = int(kwargs['width'])
        except:
            pass

        if width==0:
            try:
                width=int(applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH").value)
            except:
                pass
        if width==0:
            try:
                width=int(applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_WIDTH").default_value)
            except:
                width=default_size

        height=0
        try:
            height = int(kwargs['height'])
        except:
            pass

        if height==0:
            try:
                height=int(applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT").value)
            except:
                pass

        if height==0:
            try:
                height=int(applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_HEIGHT").default_value)
            except:
                height=default_size

        # check to see if the variable process_applet_entries is set
        # if so, add entry to database
        if context.get("process_applet_entries"):
            # get page object, 
            thepage = context.get('thepage')
            # if applet was in a page,  add page to in_pages of applet
            if thepage:
                applet.in_pages.add(thepage)

        answer_data = context.get('_answer_data_')
        
        try:
            applet_data=context['_auxiliary_data_']['applet']
        except (KeyError, TypeError):
            return "[Broken applet: no applet data]"
        
        applet_counter = applet_data['counter']+1
        applet_data['counter']=applet_counter
        applet_suffix = applet_data.get('suffix','')
        applet_identifier = kwargs.get("applet_identifier")
        if not applet_identifier:
            applet_identifier = "Applet%s0%s%s" % (
                applet.code_camel(), applet_counter, 
                underscore_to_camel(applet_suffix))


        caption = None
        description = ""
        if self.boxed:
            caption = kwargs.get('caption')

            if caption is None:

                # add applet info to context for any applet_objects in caption
                context.push()
                context['_the_applet']=applet
                context['_the_applet_identifier'] = applet_identifier

                try:
                    caption = template.Template("{% load mi_tags testing_tags %}"+applet.default_inline_caption).render(context)
                except Exception as e:
                    caption = "Caption template error (TMPLERR): %s" % e

                context.pop()

        else:
            if kwargs.get("include_description", False):
                # add applet info to context for any applet_objects in 
                # description
                context.push()
                context['_the_applet']=applet
                context['_the_applet_identifier'] = applet_identifier

                try:
                    description = template.Template("{% load mi_tags testing_tags %}"+applet.detailed_description).render(context)
                except Exception as e:
                    description = "Template error (TMPLERR): %s" % e

                context.pop()


        # check if blank_style is set
        # if so, just return title, and caption if "boxed"
        blank_style = context.get("blank_style")
        if blank_style:
            if self.boxed:
                return " %s %s " % (applet.title, caption)
            else:
                return " %s %s" % (applet.title, description)


        iframe = kwargs.get("iframe")

        # html for applet inclusion
        # add html for applet embedding based on applet_type


        # keep track of identifiers and applet_id_users specified in tag,
        # so that javascript from other applet_object tags can
        # access the applet
        try:
            applet_id_dict = applet_data['applet_ids']
        except KeyError:
            applet_id_dict={}
            applet_data['applet_ids']=applet_id_dict

        # applet_id_dict is keyed on optional applet_id_user
        this_applet_info=applet_id_dict.get(applet.code, {})

        # applet_id_user is from kwargs applet_id, 
        # or answer_data['question_identifier'], if exists.
        # If none found, None is treated as valid applet_id_user.
        applet_id_user = kwargs.get('applet_id') 
        if applet_id_user is None and answer_data:
            try:
                applet_id_user = answer_data['question_identifier']
            except KeyError:
                pass

        # If previous instance of same applet_id_user found (including None)
        # then don't overwrite so that first instance of applet is used
        if applet_id_user not in this_applet_info:
            this_applet_info[applet_id_user] = applet_identifier
            applet_id_dict[applet.code]=this_applet_info

        # record if applet was in iframe
        applet_iframes = applet_data.get("iframes", {})
        applet_iframes[applet_identifier] = iframe
        applet_data['iframes'] = applet_iframes

        applet_variable = ""
        if applet.applet_type.code == "Geogebra" or \
           applet.applet_type.code == "GeogebraWeb":
            if iframe:
                applet_variable = 'document.getElementById("%s").contentWindow.document.%s' % (applet_identifier, applet_identifier)
            else:
                applet_variable = 'document.%s' % applet_identifier

        if iframe:
            applet_link = '<iframe width=%s height=%s src="%s?width=%s&height=%s&applet_identifier=%s" id="%s" style="display: block; width: 600px; height: 400px;"></iframe>' % \
            (width, height, reverse('mi-applet_bare', kwargs={'applet_code': applet.code}),
             width, height, applet_identifier, applet_identifier)
            script_string=""

        elif applet.applet_type.code == "LiveGraphics3D":
            (applet_link, script_string) = LiveGraphics3D_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "DoubleLiveGraphics3D":
           (applet_link, script_string) = DoubleLiveGraphics3D_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "Geogebra":
           (applet_link, script_string) = Geogebra_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "GeogebraWeb":
           (applet_link, script_string) = GeogebraWeb_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "GeogebraTube":
           (applet_link, script_string) = GeogebraTube_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "Three":
           (applet_link, script_string) = Three_link(context, applet, applet_identifier, width, height, url_get_parameters)
        else:
            # if applet type for which haven't yet coded a link
            # return broken applet text
            return '<p>[Broken applet: unrecognized applet type]</p>'


        # add default applet texts unless specified not
        if kwargs.get("add_default_texts", True):
            top_text=""
            for applet_text in applet.applettext_set\
                                     .filter(default_position="top"):

                top_text = render_applet_text(
                    context, applet_text, applet=applet, 
                    applet_identifier=applet_identifier,
                    hidden=kwargs.get("hidden", True))


            bottom_text = ""
            for applet_text in applet.applettext_set\
                                     .filter(default_position="bottom"):

                bottom_text += render_applet_text(
                    context, applet_text, applet=applet, 
                    applet_identifier=applet_identifier,
                    hidden=kwargs.get("hidden", True))


            applet_link = top_text + applet_link + bottom_text


        prefilled_answers=None
        if answer_data:
            prefilled_answers = answer_data.get('prefilled_answers')

        prefilled_answers_by_object = {}

        # Check if any applet objects are specified 
        # to be captured with javascript to answer blanks.
        # To be captured, the following conditions must hold:
        # 1. the applet object marked with captured_change=True
        # 2. the applet tag must contain a kwargs of the form
        #    answer_[object_name]=[answer_code]
        # 3. answer code must be a valid answer_code in answer_data
        # If an applet object is a state variable, criteria 2 and 3
        # are not required

        appletobjects = []
        if answer_data:
            appletobjects=applet.appletobject_set.filter \
                           (capture_changes=True).order_by(
                               "category_for_capture")

        inputboxlist=''
        capture_javascript={}
        init_javascript = ""
        
        # dictionary to check if have a kwarg of form answer_xxxxx
        # where xxxx is not an applet object that can be changed
        kwarg_answer_keys_not_matched = {}
        for the_kw in kwargs_string.keys():
            if re.match('answer_', the_kw):
                kwarg_answer_keys_not_matched[the_kw]=True

        previous_category=None

        for appletobject in appletobjects:
            the_kw = "answer_%s" % appletobject.name
            
            # check if object is specified to be captured in kwargs
            try:
                answer_code =  kwargs_string[the_kw]
            except KeyError:
                # otherwise, check if object is a state variable
                if appletobject.state_variable:
                    answer_code=None
                else:
                    continue

            if answer_code:
            
                # mark that found an changeable object for the_kw
                del kwarg_answer_keys_not_matched[the_kw]

                # if answer_code is not a valid answer code
                # skip this applet object but register error
                try:
                    answer_code_dict = answer_data['valid_answer_codes']\
                                       [answer_code]
                    answer_type=answer_code_dict['answer_type']
                    expression_type = answer_code_dict.get('expression_type')
                except KeyError:
                    answer_data['error']=True
                    answer_data['answer_errors'].append(\
                        "Invalid answer code from applet: %s" % answer_code)
                    continue

                try:
                    points = float(kwargs['points_'+the_kw])
                except:
                    points = 1

                group = kwargs.get('group_'+the_kw)

            else:
                # if only state variable and not in kwargs
                answer_type=None
                expression_type=None
                points=0
                group=None


            answer_number = len(answer_data['answer_info'])+1
            answer_identifier = "%s_%s" % \
                (answer_number, answer_data['question_identifier'])
            answer_field_name = 'answer_%s' % answer_identifier
            answer_data['answer_info'].append(\
                {'code': answer_code, 'points': points, \
                 'type': answer_type, 'identifier': answer_identifier, \
                 'group': group, 'expression_type': expression_type })

            # check if object is in prefilled_answers
            # if so, use that value for input box
            value_string = ""
            if prefilled_answers:
                try:
                    the_answer_dict = prefilled_answers[answer_number-1]
                    if the_answer_dict["code"] == answer_code:
                        value_string = ' value="%s"' % the_answer_dict["answer"]
                        prefilled_answers_by_object[appletobject.pk] \
                            = the_answer_dict["answer"]
                except (KeyError, IndexError, TypeError):
                    pass

            inputbox_id = "id_%s" % answer_field_name
            inputboxlist += '<input type="hidden" id="%s" maxlength="200" name="%s" size="20"%s />\n' % \
                (inputbox_id, answer_field_name,  value_string)

            if answer_code: # if in kwargs, not just a state variable
                if appletobject.category_for_capture != previous_category:
                    the_category = appletobject.category_for_capture
                    if the_category:
                        inputboxlist += '<br/>%s:' % the_category
                    previous_category=the_category
                inputboxlist += '<span id="%s__binary__feedback"></span>\n' % \
                                answer_field_name

            related_objects=[]
            if appletobject.related_objects:
                related_object_names = \
                    [item.strip() for item in appletobject.related_objects.split(",")]
                for name in related_object_names:
                    try:
                        ro = applet.appletobject_set.get(name=name)
                        related_objects.append(ro)
                    except:
                        pass

            if applet.applet_type.code == "Geogebra" \
                    or applet.applet_type.code == "GeogebraWeb":
                javascript = Geogebra_capture_object_javascript \
                       (appletobject, applet_identifier, 
                        "temp", related_objects)
                this_capture= capture_javascript.get(appletobject.name,"")
                this_capture \
                    += 'var temp;\n%s\njQuery("#%s").val(temp);\n' \
                    % (javascript, inputbox_id,)
                capture_javascript[appletobject.name]=this_capture

        # if there was a kwarg of form answer_xxxx that was not a
        # changeable object, register the error
        for the_kw in kwarg_answer_keys_not_matched.keys():
            answer_data['error']=True
            answer_data['answer_errors'].append(\
                "No captureable applet object to match answer: %s" % the_kw)

        # if call_parent_capture, attempt to call parent version of capture
        if kwargs.get("call_parent_capture"):
            appletobjects=applet.appletobject_set.filter \
                           (capture_changes=True).order_by(
                               "category_for_capture")

            for appletobject in appletobjects:
                this_capture= capture_javascript.get(appletobject.name,"")
                # this exact text is tested against in
                # AccumulatedJavascriptNode to determine if the capture script
                # is only this call.
                this_capture \
                    += 'if(inIframe()) {try {parent.listener%s_%s(obj);} catch(e) {} }\n' % (applet_identifier, appletobject.name)
                capture_javascript[appletobject.name]=this_capture

        # check if any applet objects are specified 
        # to be changed with javascript
        appletobjects=applet.appletobject_set.filter \
            (change_from_javascript=True)

        for appletobject in appletobjects:
            objectvalue = kwargs.get(appletobject.name)
            objectvalue_string = kwargs_string.get(appletobject.name)
            
            # check if object is in prefilled_answers
            # if so, overwrite and use that value instead
            the_prefilled_answer = \
                prefilled_answers_by_object.get(appletobject.pk) 
            if the_prefilled_answer is not None:
                # check if applet object is set to be captured
                # or is a state variable
                the_kw = "answer_%s" % appletobject.name
                if the_kw in kwargs or appletobject.state_variable:
                    # target as it would have been in prefilled_answer
                    objectvalue = the_prefilled_answer

            # if objectvalue is none, set to default value, if exists
            if objectvalue is None:
                if appletobject.default_value:
                    objectvalue=appletobject.default_value

            if objectvalue is not None:
                if applet.applet_type.code == "Geogebra" \
                        or applet.applet_type.code == "GeogebraWeb":
                    init_javascript += Geogebra_change_object_javascript \
                        (context, appletobject, applet_variable, \
                             objectvalue, objectvalue_string)
                    


        if inputboxlist:
            inputboxlist = '<div class="hidden_feedback applet_feedback_%s info"><b>Feedback from applet</b>%s</div>' % (answer_data['question_identifier'], inputboxlist)
        applet_link += inputboxlist


        if applet.applet_type.code == "Geogebra" \
           or applet.applet_type.code == "GeogebraWeb":
            try:
                geogebra_javascript = applet_data['javascript']['Geogebra']
            except KeyError:
                applet_data['javascript']['Geogebra'] = {
                    'on_init_commands': {}}
                geogebra_javascript = applet_data['javascript']['Geogebra']

        if capture_javascript:
            if applet.applet_type.code == "Geogebra" \
               or applet.applet_type.code == "GeogebraWeb":
                all_capture_javascript = geogebra_javascript.get(
                    'capture_javascript',{})
                all_capture_javascript[applet_identifier] = capture_javascript
                geogebra_javascript['capture_javascript'] = all_capture_javascript

        applet_data['javascript']['_initialization'] += script_string


        if init_javascript:
            if applet.applet_type.code == "Geogebra" \
                    or applet.applet_type.code == "GeogebraWeb":

                all_init_javascript = geogebra_javascript.get(
                    'on_init_commands',{})
                all_init_javascript[applet_identifier] = init_javascript
                geogebra_javascript['on_init_commands'] \
                    = all_init_javascript



        # if not boxed, just return code for applet
        if not self.boxed:
            return applet_link+description

        # if boxed, then put in box (from class="appletbox")
        # as well as caption
        html_string = '<a id="%s" class="anchor"></a><section class="appletbox" >%s' % \
            (applet.anchor(), applet_link)
            
        if applet.description:
            title = 'title="%s"' % applet.description
        else:
            title = ""

        video_links = applet.video_links()


        link_url = applet.get_absolute_url()

        return '%s<p><i>%s.</i> %s</p><p><a href="%s" %s class="applet">More information about applet.</a> %s</p></section>' % \
            (html_string, applet.title, caption, link_url, title, video_links)


def applet_sub(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    applet = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value
  
    return (applet, kwargs, kwargs_string)

@register.tag
def applet(parser, token):
# applet tag
    (applet, kwargs, kwargs_string)=applet_sub(parser, token)
    return AppletNode(applet, 0, kwargs, kwargs_string)


@register.tag
def boxedapplet(parser, token):
# boxedapplet tag
    (applet, kwargs, kwargs_string)=applet_sub(parser, token)
    return AppletNode(applet, 1, kwargs, kwargs_string)


class AppletObjectNode(template.Node):
    def __init__(self, object_name, kwargs, kwargs_string):
        self.object_name = object_name
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
                              for k, v in self.kwargs_string.items()])

        object_name = self.object_name.resolve(context)

        # must have applet in kwargs, or specified in context
        applet = kwargs.get('applet')
        if not applet:
            try:
                applet= context['_the_applet']
            except KeyError:
                return "[Broken applet object: no applet specified]"

        # if applet is not an applet instance
        # try to load applet with that code
        if not isinstance(applet, Applet):
            # test if applet with applet_code exists
            try:
                applet=Applet.objects.get(code=applet)
                # if applet does not exist
                # return tag to applet code anyway
            except ObjectDoesNotExist:
                return "[Broken applet object: no applet found]"

        # get applet_id_user optionally from kwargs or context
        applet_id_user = kwargs.get('applet_id', 
                                    context.get('_the_applet_id_user'))
        # if applet_id_user not assigned, try to set it to question identifier
        # from answer_data
        if not applet_id_user:
            try:
                applet_id_user = context['_answer_data_']['question_identifier']
            except KeyError:
                pass


        # get applet_identifier optionally from context
        applet_identifier = context.get('_the_applet_identifier')
        
        try:
            applet_object=applet.appletobject_set.get \
                           (capture_changes=True, name=object_name)
        except ObjectDoesNotExist:
            return "[Broken applet object: no object found]"

        try:
            applet_data=context['_auxiliary_data_']['applet']
        except (KeyError, TypeError):
            return "[Broken applet object: no applet data]"
        
        applet_object_counter = applet_data.get('applet_object_counter',0)+1
        applet_data['applet_object_counter']=applet_object_counter
        
        object_identifier = "appletobject_%s" % applet_object_counter

        try:
            object_list=applet_data['applet_objects']
        except KeyError:
            object_list = []
            applet_data['applet_objects'] = object_list

        render_with_mathjax=False
        math_delims = ""
        mathmode = kwargs.get('math')
        if mathmode == "inline":
            math_delims = "`{}`"
            render_with_mathjax=True
        elif mathmode == "display":
            math_delims = r"\[{}\]"
            render_with_mathjax=True

        # Since applet tag may not have been encountered yet
        # cannot yet form javascript to update object.
        # Record information about applet object for later processing.
        # If applet_identifier is specified, then it overrides applet_id_user
        object_list.append({
            'applet_object': applet_object,
            'object_identifier': object_identifier,
            'applet': applet,
            'applet_id_user': applet_id_user,
            'applet_identifier': applet_identifier,
            'render_with_mathjax': render_with_mathjax,
            'round_decimals': kwargs.get('round'),
            'hidden_section_identifier':\
            context.get('_the_hidden_section_identifier'),
        })
        
        # return container for applet object
        return "<span id='%s'>%s</span>" % (object_identifier, math_delims)

@register.tag
def applet_object(parser,token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]

    object_name = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value

    return AppletObjectNode(object_name, kwargs, kwargs_string)
    

class RenderJavascriptSetAppletObjectNode(template.Node):
    def __init__(self, object_name, kwargs, kwargs_string, nodelist):
        self.object_name = object_name
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
        self.nodelist=nodelist
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
                              for k, v in self.kwargs_string.items()])

        object_name = self.object_name.resolve(context)

        object_value = self.nodelist.render(context)


        # must have applet in kwargs, or specified in context
        applet = kwargs.get('applet')
        if not applet:
            try:
                applet= context['_the_applet']
            except KeyError:
                return "console.log('Broken render_javascript_set_applet_object: no applet specified');"

        # if applet is not an applet instance
        # try to load applet with that code
        if not isinstance(applet, Applet):
            # test if applet with applet_code exists
            try:
                applet=Applet.objects.get(code=applet)
                # if applet does not exist
                # return tag to applet code anyway
            except ObjectDoesNotExist:
                return "console.log('Broken render_javascript_set_applet_object: no applet found');"

        # get applet_id_user optionally from kwargs or context
        applet_id_user = kwargs.get('applet_id', 
                                    context.get('_the_applet_id_user'))
        # if applet_id_user not assigned, try to set it to question identifier
        # from answer_data
        if not applet_id_user:
            try:
                applet_id_user = context['_answer_data_']['question_identifier']
            except KeyError:
                pass


        # get applet_identifier optionally from context
        applet_identifier = context.get('_the_applet_identifier')
        
        try:
            applet_object=applet.appletobject_set.get \
                           (capture_changes=True, name=object_name)
        except ObjectDoesNotExist:
            return "console.log('Broken render_javascript_set_applet_object: no object found');"

        try:
            applet_data=context['_auxiliary_data_']['applet']
        except (KeyError, TypeError):
            return "console.log('Broken render_javascript_set_applet_object: no applet data');"
        
        set_applet_object_counter = applet_data.get('set_applet_object_counter',0)+1
        applet_data['set_applet_object_counter']=set_applet_object_counter
        
        set_object_function_name = "setappletobject_%s" % set_applet_object_counter

        try:
            object_list=applet_data['set_applet_objects']
        except KeyError:
            object_list = []
            applet_data['set_applet_objects'] = object_list


        # Since applet tag may not have been encountered yet
        # cannot yet form javascript to update object.
        # Record information about applet object for later processing.
        # If applet_identifier is specified, then it overrides applet_id_user
        object_list.append({
            'applet_object': applet_object,
            'set_object_function_name': set_object_function_name,
            'applet': applet,
            'applet_id_user': applet_id_user,
            'applet_identifier': applet_identifier,
            'hidden_section_identifier':\
            context.get('_the_hidden_section_identifier'),
        })
        
        # call function to set object value
        return "%s(%s);" % (set_object_function_name, object_value)

@register.tag
def render_javascript_set_applet_object(parser,token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]

    object_name = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value

    nodelist = parser.parse(('end_render_javascript_set_applet_object',))
    parser.delete_first_token()

    return RenderJavascriptSetAppletObjectNode(object_name, kwargs, 
                                               kwargs_string, nodelist)

class AppletTextNode(template.Node):
    def __init__(self, text_code, kwargs, kwargs_string):
        self.text_code = text_code
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
                              for k, v in self.kwargs_string.items()])

        text_code = self.text_code.resolve(context)

        # must have applet in kwargs, or specified in context
        applet = kwargs.get('applet')
        if not applet:
            try:
                applet= context['_the_applet']
            except KeyError:
                return "[Broken applet text: no applet specified]"

        # if applet is not an applet instance
        # try to load applet with that code
        if not isinstance(applet, Applet):
            # test if applet with applet_code exists
            try:
                applet=Applet.objects.get(code=applet)
                # if applet does not exist
                # return tag to applet code anyway
            except ObjectDoesNotExist:
                return "[Broken applet text: no applet found]"

        # get applet_id_user optionally from kwargs or context
        applet_id_user = kwargs.get('applet_id', 
                                    context.get('_the_applet_id_user'))
        # if applet_id_user not assigned, try to set it to question identifier
        # from answer_data
        if not applet_id_user:
            try:
                applet_id_user = context['_answer_data_']['question_identifier']
            except KeyError:
                pass

        # get applet_identifier optionally from context
        applet_identifier = context.get('_the_applet_identifier')
        
        try:
            applet_text=applet.applettext_set.get(code=text_code)
        except ObjectDoesNotExist:
            return "[Broken applet text: no text found]"

        return render_applet_text(context, applet_text, applet=applet, 
                                  applet_id_user=applet_id_user,
                                  applet_identifier=applet_identifier,
                                  hidden=kwargs.get("hidden", True))



def render_applet_text(context, applet_text, applet, applet_id_user=None,
                       applet_identifier=None,
                       hidden=True):

    if hidden is None:
        hidden_section_identifier=""
    else:
        try:
            hidden_info = context["_hidden_section_info"]
        except KeyError:
            hidden_info={}
            context.dicts[0]['_hidden_section_info']=hidden_info

        counter = hidden_info.get('counter',0)+1
        hidden_info['counter']=counter
        hidden_section_identifier= "hidden_section_%s" % counter


    context.push()
    context['_the_applet']=applet
    context['_the_applet_id_user'] = applet_id_user
    context['_the_applet_identifier'] = applet_identifier
    context['_the_hidden_section_identifier']=hidden_section_identifier

    rendered_text = template.Template(
        "{% load mi_tags testing_tags %}"+applet_text.text)\
                                   .render(context)
    context.pop()

    if hidden is None:
        return '<div class="info"><h4>%s</h4>%s</div>' % \
            (applet_text.title, rendered_text)
    else:
        return hidden_text_html(
            content_html = rendered_text, 
            title=applet_text.title, css="applet_text",
            section_identifier = hidden_section_identifier,
            start_revealed = not hidden)


@register.tag
def applet_text(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]

    text_code = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value

    return AppletTextNode(text_code, kwargs, kwargs_string)


def youtube_link(context, video, width, height):
    
    try:
        youtubecode=video.videoparameter_set.get(parameter__parameter_name ="youtubecode").value
    except ObjectDoesNotExist:
        return "[Broken video]"

    html_string='<div class="video"><iframe width="%s" height="%s" src="//www.youtube-nocookie.com/embed/%s?rel=0" frameborder="0" allowfullscreen></iframe></div>' % \
        (width, height, youtubecode )

    return html_string


class VideoNode(template.Node):
    def __init__(self, video, boxed, kwargs):
        self.video= video
        self.boxed=boxed
        self.kwargs=kwargs
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        video = self.video.resolve(context)

        # if video is not an video instance
        # try to load video with that code
        if not isinstance(video, Video):
            # test if video with video_code exists
            try:
                video=Video.objects.get(code=video)
                # if video does not exist
                # return tag to video code anyway
            except ObjectDoesNotExist:
                return '<p>[Broken video]</p>'

        # set width and height from kwarg parameters, if exist
        # else get defaults from video, if exist
        # else get defaults from videotype, if exist
        # use default_size for any values not found
        default_size = 500

        width=0
        try:
            width = int(kwargs['width'])
        except:
            pass

        if width==0:
            try:
                width=video.videoparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH").value
            except ObjectDoesNotExist:
                pass
        if width==0:
            try:
                width=video.video_type.valid_parameters.get(parameter_name ="DEFAULT_WIDTH").default_value
            except ObjectDoesNotExist:
                width=default_size

        height=0
        try:
            height = int(kwargs['height'])
        except:
            pass

        if height==0:
            try:
                height=video.videoparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT").value
            except ObjectDoesNotExist:
                pass

        if height==0:
            try:
                height=video.video_type.valid_parameters.get(parameter_name ="DEFAULT_HEIGHT").default_value
            except ObjectDoesNotExist:
                height=default_size

        caption = None
        if self.boxed:
            caption = kwargs.get('caption')

            if caption is None:
                try:
                    caption = template.Template("{% load mi_tags %}"+video.default_inline_caption).render(context)
                except Exception as e:
                    caption = "Caption template error (TMPLERR): %s" % e


        # check to see if the variable process_video_entries is set
        # if so, add entry to database
        if context.get("process_video_entries"):
            # get page object, 
            thepage = context.get('thepage')
            # if video was in a page, add page to in_pages of video
            if thepage:
                video.in_pages.add(thepage)

        # check if blank_style is set
        # if so, just return title, and caption if "boxed"
        blank_style = context.get("blank_style")
        if blank_style:
            if self.boxed:
                return " %s %s " % (video.title, caption)
            else:
                return " %s " % video.title

            

        # html for video inclusion
        # add html for video embedding based on video_type
        if video.video_type.code == "youtube":
            video_link = youtube_link(context, video, width, height)
        else:
            # if video type for which haven't yet coded a link
            # return broken video text
            return '<p>[Broken video]</p>'

            
        # if not boxed, just return code for video
        if not self.boxed:
            return video_link

        # if boxed, then put in box (from class="videobox")
        # as well as caption
        html_string = '<a id="%s" class="anchor"></a><section class="videobox" >%s' % \
            (video.anchor(), video_link)
            
        if video.description:
            title = 'title="%s"' % video.description
        else:
            title = ""

        link_url = video.get_absolute_url()

        if video.transcript:
            transcript_link = ' <a href="%s#transcript" class="video">Video transcript.</a>' % link_url
        else:
            transcript_link = ''


        return '%s<p><i>%s.</i> %s</p><p><a href="%s" %s class="video">More information about video.</a> %s</p></section>' % \
            (html_string, video.title, caption, link_url, title, transcript_link)


def video_sub(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    video = parser.compile_filter(bits[1])

    kwargs = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  
    return (video, kwargs)


@register.tag
def video(parser, token):
# video tag
    (video, kwargs)=video_sub(parser, token)
    return VideoNode(video, 0, kwargs)


@register.tag
def boxedvideo(parser, token):
# boxedvideo tag
    (video, kwargs)=video_sub(parser, token)
    return VideoNode(video, 1, kwargs)

class TemplateTextNode(template.Node):
    def __init__(self, page_code):
        self.page_code_var=template.Variable("%s.code" % page_code)
        self.page_code_string = page_code
    def render(self, context):
        # first test if page_code_var is a variable
        # if so, page_code will be the resolved variable
        # otherwise, image will be page_code_string
        try:
            page_code=self.page_code_var.resolve(context)
        except template.VariableDoesNotExist:
            page_code=self.page_code_string
        # next, test if page with the_link_code exists
        try:
            thepage=Page.objects.get(code=page_code)
        # if page does not exist, return blank string
        # mark as broken. 
        except ObjectDoesNotExist:
            return ""

        # if page exists, render page's template to string
        # with blank_style set
        from django.template.loader import render_to_string
        template_string = 'midocs/pages/%s/%s.html' % (thepage.template_dir, thepage.code)
        return render_to_string(template_string, {'blank_style': 1,'STATIC_URL': ''})
    
@register.tag
def template_text_blank_style(parser, token):
    try:
        tag_name, page_code = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return TemplateTextNode(page_code)


class TwoColumnNode(template.Node):
    def __init__(self, column1percent, linearizelevel, gstyle, equalize, nodelist1, nodelist2):
        self.column1percent = column1percent
        self.linearizelevel = linearizelevel
        self.gstyle = gstyle
        self.equalize = equalize
        self.nodelist1=nodelist1
        self.nodelist2=nodelist2
    def render(self, context):

        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass
        
        # if blank_style, just return the context for the columns
        if blank_style:
            return "%s %s" % (self.nodelist1.render(context), self.nodelist2.render(context))
        
        
        # select numbers ym-g# that are legal
        if self.column1percent==20:
            column1code="20"
            column2code="80"
        elif self.column1percent==40:
            column1code="40"
            column2code="60"
        elif self.column1percent==60:
            column1code="60"
            column2code="40"
        elif self.column1percent==80:
            column1code="80"
            column2code="20"
        elif self.column1percent==25:
            column1code="25"
            column2code="75"
        elif self.column1percent==33:
            column1code="33"
            column2code="66"
        elif self.column1percent==66:
            column1code="66"
            column2code="33"
        elif self.column1percent==75:
            column1code="75"
            column2code="25"
        elif self.column1percent==38:
            column1code="38"
            column2code="62"
        elif self.column1percent==62:
            column1code="62"
            column2code="38"
        else:
            column1code="50"
            column2code="50"

        if self.gstyle:
            thegstyle = ' style="%s"' % self.gstyle
        else:
            thegstyle = ""

        if self.equalize:
            equalizetext = " ym-equalize"
        else:
            equalizetext = ""

        return '<div class="ym-grid%s linearize-level-%s"> <div class="ym-g%s ym-gl"%s><div class="ym-gbox-left">%s</div></div><div class="ym-g%s ym-gr"%s><div class="ym-gbox-right">%s</div></div></div>' % (equalizetext, self.linearizelevel, column1code, thegstyle, self.nodelist1.render(context), column2code, thegstyle,self.nodelist2.render(context))



@register.tag
def twocolumns(parser, token):
    bits = token.split_contents()
    if len(bits) > 1:
        try:
             column1percent=int(bits[1])
        except:
            column1percent=0
    else:
        column1percent = 0

    if len(bits) > 2:
        try:
            linearizelevel=int(bits[2])
            if linearizelevel !=0 and linearizelevel !=1 and linearizelevel != 2:
                linearizelevel = 2
        except:
            linearizelevel=2
    else:
        linearizelevel = 2
        
    if len(bits) > 3:
        gstyle = bits[3]
        if not (gstyle[0] == gstyle[-1] and gstyle[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's third argument should be in quotes" % bits[0]
        gstyle = gstyle[1:-1] 
    else:
        gstyle=0

    if len(bits) > 4:
        equalize = bits[4]
    else:
        equalize = False
    nodelist1 = parser.parse(('nextcolumn',))
    parser.delete_first_token()
    nodelist2 = parser.parse(('endtwocolumns',))
    parser.delete_first_token()

    return TwoColumnNode(column1percent, linearizelevel, gstyle, equalize, nodelist1, nodelist2)


class CounterNode(template.Node):
    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        try:
            var = template.resolve_variable(self.varname, context)
        except:
            var = 0
        deep = len(context.dicts)-1
        context.dicts[deep][self.varname] = var+1
        return ''

@register.tag
def counter(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'counter' node requires a variable name.")
    return CounterNode(args)


def hidden_text_html(content_html, title, section_identifier,
                     css=None, show_text=None, hide_text=None,
                     start_revealed=False):
    
    if isinstance(css, dict):
        body_css = css.get("body", "info")
        title_css = css.get("title", "")
        container_css = css.get("container", "")
    elif isinstance(css, six.text_type):
        body_css = css
        title_css = ""
        container_css = ""
    else:
        body_css = "info"
        title_css = ""
        container_css = ""

    if show_text is None:
        show_text = "(Show)"
    if hide_text is None:
        hide_text = "(Hide)"

    if start_revealed:
        show_link_style = 'display: none;'
        hide_link_style = 'display: inline;'
        body_style = 'display: block;'
    else:
        show_link_style = 'display: inline;'
        hide_link_style = 'display: none;'
        body_style = 'display: none;'

    bottom_hide_link =  '<p><a id="%s_hide" class="hide_section" onclick="showHide(\'%s\');">%s</a></p>' \
        % (section_identifier, section_identifier, hide_text)

    body_html = '<div id="%s" class="hidden_section %s" style="%s">%s%s</div>' \
        % (section_identifier, body_css, body_style,
           content_html, bottom_hide_link)
    
    title_html = '<div id="%s_header" class="hidden_section_header %s" style="width: 100%%">%s <a onclick="showHide(\'%s\');"><span id="%s_show" class="hidden_section_show" style="%s">%s</span><span id="%s_hide" class="hidden_section_hide" style="%s">%s</span></a></div>' \
        % (section_identifier, title_css, title, 
           section_identifier, 
           section_identifier, show_link_style, show_text, 
           section_identifier, hide_link_style, hide_text)

    return '<div class="hidden_section_container %s">%s%s</div>'\
                  % (container_css, title_html, body_html)


class HiddenNode(template.Node):
    def __init__(self, title, kwargs, nodelist):
        self.title=title
        self.kwargs=kwargs
        self.nodelist=nodelist

    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        
        title = self.title.resolve(context)

        show_text = kwargs.get("show_text", "(Show)")
        hide_text = kwargs.get("hide_text", "(Hide)")

        body_css = kwargs.get("body_css", "info")
        title_css = kwargs.get("title_css", "")
        container_css = kwargs.get("container_css", "")

        css = {'body': body_css, 'title': title_css, 'container': container_css}

        try:
            auxiliary_data = context['_auxiliary_data_']
        except KeyError:
            from midocs.functions import return_new_auxiliary_data
            auxiliary_data = return_new_auxiliary_data()
            context.dicts[0]['_auxiliary_data_'] = auxiliary_data
            
        try:
            hidden_info = auxiliary_data['hidden_section']
        except KeyError:
            hidden_info={}
            auxiliary_data['hidden_section'] = hidden_info

        counter = hidden_info.get('counter',0)+1
        hidden_info['counter']=counter
        hidden_section_identifier= "hidden_section_%s" % counter

        return hidden_text_html(
            content_html=self.nodelist.render(context),
            title = title, section_identifier = hidden_section_identifier,
            css=css, show_text=show_text, hide_text=hide_text)
        

@register.tag
def hidden(parser, token):
    bits = token.split_contents()

    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % bits[0]
    
    title = parser.compile_filter(bits[1])

    kwargs = {}
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
  

    nodelist = parser.parse(('endhidden',))
    parser.delete_first_token()

    return HiddenNode(title, kwargs, nodelist)




def find_applet_identifier(applet_id_dict, applet, applet_id_user=None):

    """
    Try to find applet_identifier.  
    Try to match both applet and applet_id_user in applet_id_dict.
    If no match, try to find arbitrary match of applet in applet_id_dict.

    raises ObjectDoesNotExist if unable to find.
    
    """

    try:
        # information about instances of applet in page
        this_applet_info=applet_id_dict[applet.code]
    except KeyError:
        # if applet code not in applet_id_dict,
        # then applet does not appear in page
        raise ObjectDoesNotExist

    if applet_id_user:
        try:
            # If applet_id_user was found in page
            # use the associated applet_identifier
            return this_applet_info[applet_id_user]
        except KeyError:
            # if applet_id_user was not found, will ignore
            pass

    # try to pick an arbitrary applet_identifier associated with applet
    try:
        return this_applet_info.values()[0]
    except IndexError:
        raise ObjectDoesNotExist



def return_applet_object_javascript(applet_data, capture_javascript):


    # Additional javascript to capture objects from applet_object tags.
    # Now can look up applet information to associate to correct applet
    try:
        applet_objects = applet_data['applet_objects']
        applet_id_dict = applet_data['applet_ids']
        applet_iframes = applet_data['iframes']
    except KeyError:
        return ""

    setup_variables_javascript=""
    error_javascript = ""

    capture_by_hidden_identifier={}

    for ao in applet_objects:
        applet_object = ao['applet_object']
        object_identifier = ao['object_identifier']
        applet = ao['applet']
        applet_id_user = ao['applet_id_user']
        applet_identifier = ao['applet_identifier']
        render_with_mathjax = ao['render_with_mathjax']
        round_decimals = ao['round_decimals']
        hidden_section_identifier = ao['hidden_section_identifier']

        if not applet_identifier:
            try:
                applet_identifier = find_applet_identifier(
                    applet_id_dict=applet_id_dict, applet=applet, 
                    applet_id_user=applet_id_user)
            except ObjectDoesNotExist:
                error_javascript += 'jQuery("#%s").html("<p>[Broken applet object: no applet found]</p>");\n' % object_identifier
                continue

        applet_variable = ""
        if applet.applet_type.code == "Geogebra" or \
           applet.applet_type.code == "GeogebraWeb":
            if applet_iframes[applet_identifier]:
                applet_variable = 'document.getElementById("%s").contentWindow.document.%s' % (applet_identifier, applet_identifier)
            else:
                applet_variable = 'document.%s' % applet_identifier

        if applet.applet_type.code == "Geogebra" \
           or applet.applet_type.code == "GeogebraWeb":

            # find any capture object javascript for the object
            try:
                applet_capture = capture_javascript[applet_identifier]
            except KeyError:
                applet_capture = {}
                capture_javascript[applet_identifier] = applet_capture

            object_capture = applet_capture.get(applet_object.name, "")

            # if object_capture exists, it already has the value
            # of the object assigned to temp, so we only need to
            # add the capture object javascript if it is empty
            if not object_capture:
                related_objects=[]
                if applet_object.related_objects:
                    related_object_names  \
                        = [item.strip() for item in applet_object.related_objects.split(",")]
                    for name in related_object_names:
                        try:
                            ro = applet.appletobject_set.get(name=name)
                            related_objects.append(ro)
                        except:
                            pass

                object_capture += "var temp;\n"
                object_capture += Geogebra_capture_object_javascript(
                    applet_object, applet_variable, 
                    "temp", related_objects)
                object_capture += "\n";

            if render_with_mathjax:
                if round_decimals is not None and \
                   applet_object.object_type.object_type == 'Number':
                    object_capture += "applet_object_content.%s.new = Math.round10(temp, %s);\n" % (object_identifier, round_decimals)
                else:
                    object_capture += "applet_object_content.%s.new = temp;\n" %\
                                      object_identifier

                setup_variables_javascript+='applet_object_content.%s={"new": "", "old": ""};\nmath_elements.%s=null;\nMathJax.Hub.Queue(function() { math_elements.%s= MathJax.Hub.getAllJax("%s")[0]; })\n' % (object_identifier, object_identifier, object_identifier, object_identifier)

            else:
                if round_decimals is not None and \
                   applet_object.object_type.object_type == 'Number':
                    object_capture += 'jQuery("#%s").html(Math.round10(temp,%s));\n' % (object_identifier, round_decimals)
                else:
                    object_capture += 'jQuery("#%s").html(temp);\n' %\
                                       object_identifier

            applet_capture[applet_object.name] = object_capture


    if not setup_variables_javascript:
        return '<div id="applet_object_capture">\n<script>\n%s</script>\n</div>\n' % error_javascript

    setup_variables_javascript = "var applet_object_content={};\nvar math_elements={};\n" + setup_variables_javascript

    interval_javascript = 'for(var object_identifier in math_elements) {\n var content = applet_object_content[object_identifier];\n if(content.new !=content.old) {\n  MathJax.Hub.Queue(["Text", math_elements[object_identifier], content.new]);\n  content.old=content.new; \n}\n}\nMathJax.Hub.Config({ showProcessingMessages: false});'

    interval_javascript = 'window.setInterval(function() {\n%s}, 500);' % interval_javascript

    return '<div id="applet_object_capture">\n<script>\n%s%s%s</script>\n</div>\n' % (error_javascript, setup_variables_javascript, interval_javascript)


def return_modify_applet_object_javascript(applet_data, capture_javascript,
                                           on_init_commands):


    # Additional javascript to modify applet objects from answer blanks
    # Now can look up applet information to associate to correct applet
    try:
        modify_applet_objects = applet_data['modify_applet_objects']
        applet_id_dict = applet_data['applet_ids']
        applet_iframes = applet_data['iframes']
    except KeyError:
        return ""

    modify_javascript = "var isMSIE = /*@cc_on!@*/false || !!document.documentMode;\n"
    capture_by_hidden_identifier={}
    

    for ao in modify_applet_objects:
        applet_object = ao['applet_object']
        answer_field_name = ao['answer_field_name']
        applet = ao['applet']
        applet_id_user = ao['applet_id_user']
        applet_identifier = ao['applet_identifier']
        modify_function_name = ao['modify_function_name']
        bidirectional = ao['bidirectional']
        round_decimals = ao['round_decimals']
        hidden_section_identifier = ao['hidden_section_identifier']

        if not applet_identifier:
            try:
                applet_identifier = find_applet_identifier(
                    applet_id_dict=applet_id_dict, applet=applet, 
                    applet_id_user=applet_id_user)
            except ObjectDoesNotExist:
                continue

        applet_variable = ""
        if applet.applet_type.code == "Geogebra" or \
           applet.applet_type.code == "GeogebraWeb":
            if applet_iframes[applet_identifier]:
                applet_variable = 'document.getElementById("%s").contentWindow.document.%s' % (applet_identifier, applet_identifier)
            else:
                applet_variable = 'document.%s' % applet_identifier

        if applet.applet_type.code == "Geogebra" \
           or applet.applet_type.code == "GeogebraWeb":

            capture_command=""
            if bidirectional and applet_object.capture_changes:

                # capture_command1 is command to capture value of 
                # applet_object and assign it to variable temp
                related_objects=[]
                if applet_object.related_objects:
                    related_object_names  \
                        = [item.strip() for item in applet_object.related_objects.split(",")]
                    for name in related_object_names:
                        try:
                            ro = applet.appletobject_set.get(name=name)
                            related_objects.append(ro)
                        except:
                            pass
                    
                capture_command1 = "var temp;\n"
                capture_command1 += Geogebra_capture_object_javascript(
                    applet_object, applet_variable, 
                    "temp", related_objects)
                capture_command1 += "\n";

                # capture_command2 is command to assign temp 
                # to the value of the answer_field
                if round_decimals is not None and \
                   applet_object.object_type.object_type == 'Number':
                    capture_command2 = 'jQuery("#id_%s").val(Math.round10(temp,%s));\n' % (answer_field_name, round_decimals)
                else:
                    capture_command2= 'jQuery("#id_%s").val(temp);\n' %\
                                    answer_field_name


                capture_command = capture_command1 + capture_command2

                # find any previous capture object javascript for the object
                try:
                    applet_capture = capture_javascript[applet_identifier]
                except KeyError:
                    applet_capture = {}
                    capture_javascript[applet_identifier] = applet_capture

                object_capture = applet_capture.get(applet_object.name, "")

                # if object_capture exists, it already has capture_command1
                # and only needs capture_command2
                if not object_capture:
                    object_capture += capture_command1
                object_capture += capture_command2

                applet_capture[applet_object.name] = object_capture



            object_type = applet_object.object_type.object_type
            if object_type == 'Number' or object_type=='Boolean':
                change_command = '%s.setValue("%s", the_value);' % \
                                 (applet_variable,  applet_object.name)
            elif object_type == 'Function':
                varname = applet_object.function_input_variable
                if varname == "" or varname is None:
                    varname="x"
                change_command = '%s.evalCommand(\'%s(%s) = \' + the_value );'%\
                                 (applet_variable, applet_object.name, varname)
            elif object_type == "Text":
                change_command = '%s.evalCommand(\'%s: \"\' + the_value + \'\"\');'%\
                                 (applet_variable, applet_object.name)
            else:
                change_command = '%s.evalCommand(\'%s: \' + the_value );'%\
                                 (applet_variable, applet_object.name)
                

            if capture_command:
                # if bidirectional and an error, capture value from applet
                change_command = "var status=%s\n" % change_command
                change_command += "if(status==false) {%s}" % \
                                  capture_command

            modify_javascript += 'function %s(the_value) {\n%s}\n' % \
                                 (modify_function_name, change_command)

            modify_javascript +=  'if (isMSIE) {\n id_%s.onkeypress = function () {\n  if (window.event && window.event.keyCode === 13) {this.blur(); this.focus()}\n  }\n}\n' % answer_field_name

            # also, run the change_command on initialization
            initial_change_javascript = re.sub(
                'the_value', 'id_%s.value' % answer_field_name, change_command)
            # only run if value is not blank
            initial_change_javascript = 'if(id_%s.value != "") { %s }\n' % \
                            (answer_field_name, initial_change_javascript)
            on_init=on_init_commands.get(applet_identifier,"")
            on_init += initial_change_javascript
            on_init_commands[applet_identifier] = on_init

            
    return '<div id="modify_applet_objects">\n<script>\n%s</script>\n</div>\n' % modify_javascript


def return_set_object_javascript_functions(applet_data):

    # javascript functions that will be called to set object values 
    # from within other javascript functions
    # Now can look up applet information to associate to correct applet

    # Could probably combine with the modify_applet_object_javascript, 
    # which changes applet objects from answer blanks.
    # At the very least, should change names to make the difference clear.

    try:
        set_applet_objects=applet_data['set_applet_objects']
        applet_id_dict = applet_data['applet_ids']
        applet_iframes = applet_data['iframes']
    except KeyError:
        return ""

    set_object_javascript = ""

    for ao in set_applet_objects:
        applet_object = ao['applet_object']
        set_object_function_name = ao['set_object_function_name']
        applet = ao['applet']
        applet_id_user = ao['applet_id_user']
        applet_identifier = ao['applet_identifier']

        if not applet_identifier:
            try:
                applet_identifier = find_applet_identifier(
                    applet_id_dict=applet_id_dict, applet=applet, 
                    applet_id_user=applet_id_user)
            except ObjectDoesNotExist:
                continue

        applet_variable = ""
        if applet.applet_type.code == "Geogebra" or \
           applet.applet_type.code == "GeogebraWeb":
            if applet_iframes[applet_identifier]:
                applet_variable = 'document.getElementById("%s").contentWindow.document.%s' % (applet_identifier, applet_identifier)
            else:
                applet_variable = 'document.%s' % applet_identifier

        if applet.applet_type.code == "Geogebra" \
           or applet.applet_type.code == "GeogebraWeb":

            object_type = applet_object.object_type.object_type
            if object_type == 'Number' or object_type=='Boolean':
                change_command = '%s.setValue("%s", the_value);' % \
                                 (applet_variable,  applet_object.name)
            elif object_type == 'Function':
                varname = applet_object.function_input_variable
                if varname == "" or varname is None:
                    varname="x"
                change_command = '%s.evalCommand(\'%s(%s) = \' + the_value );'%\
                                 (applet_variable, applet_object.name, varname)
            elif object_type == "Text":
                change_command = '%s.evalCommand(\'%s: \"\' + the_value + \'\"\');'%\
                                 (applet_variable, applet_object.name)
            else:
                change_command = '%s.evalCommand(\'%s: \' + the_value );'%\
                                 (applet_variable, applet_object.name)
                

            set_object_javascript += 'function %s(the_value) {\n%s\n}\n' % \
                                 (set_object_function_name, change_command)
            
    return '<div id="set_applet_objects">\n<script>\n%s</script>\n</div>\n' % set_object_javascript



class AccumulatedJavascriptNode(template.Node):
    def render(self, context):

        script_string = ""
        static_url = context.get("STATIC_URL","")
        try:
            auxiliary_data = context['_auxiliary_data_']
            applet_data = auxiliary_data['applet']
            applet_iframes = applet_data['iframes']
        except KeyError:
            return ""
        

        # initialization scripts that actually start applets
        try:
            initialization_script = applet_data['javascript']['_initialization']
        except:
            pass
        else:
            if initialization_script:
                if auxiliary_data.get('page_type') == "slides":
                    # for slides, MathJax isn't loaded right away
                    # so we can't put initialization as MathJax startup hook
                    script_string += '<div id="applet_initialization">\n<script>\n%s\n</script>\n</div>\n' % initialization_script
                else:
                    script_string += '<div id="applet_initialization">\n<script>\nMathJax.Hub.Register.StartupHook("End",function () {%s});\n</script>\n</div>\n' % initialization_script

        geogebra_javascript = applet_data['javascript'].get('Geogebra',{})

        # find dictionary of javascript to capture applet objects
        capture_javascript = geogebra_javascript.get('capture_javascript',{})

        # return any geogebra_init_javascript
        geogebra_on_init_commands = geogebra_javascript.get('on_init_commands',{})

        script_string += return_modify_applet_object_javascript(
            applet_data=applet_data, capture_javascript=capture_javascript,
            on_init_commands = geogebra_on_init_commands)

        script_string += return_set_object_javascript_functions(applet_data)

        script_string += return_applet_object_javascript(
            applet_data=applet_data, capture_javascript=capture_javascript)

        # collect all capture object javascript for each applet
        the_capture_script =""
        for applet_identifier in capture_javascript:
            
            applet_variable = ""
            if applet_iframes[applet_identifier]:
                applet_variable = 'document.getElementById("%s").contentWindow.document.%s' % (applet_identifier, applet_identifier)
            else:
                applet_variable = 'document.%s' % applet_identifier

            applet_capture = capture_javascript[applet_identifier]
            listener_function_name_base = "listener%s" % applet_identifier
            
            on_init_commands=geogebra_on_init_commands.get(applet_identifier,"")
            
            for applet_object_name in applet_capture:
                listener_function_name = "%s_%s" % \
                            (listener_function_name_base, applet_object_name)

                the_capture_script += 'function %s(obj) {\n%s}\n' % \
                                      (listener_function_name, 
                                       applet_capture[applet_object_name])
            

                # if capture javascript is only a call to a parent listener
                # then don't register listener.
                # Listener will be registered if needed by parent
                empty_capture = applet_capture[applet_object_name] == \
                    'if(inIframe()) {try {parent.listener%s_%s(obj);} catch(e) {} }\n' % (applet_identifier, applet_object_name)

                if not empty_capture:
                    on_init_commands \
                        += '%s.registerObjectUpdateListener("%s","%s");\n'\
                        % (applet_variable, applet_object_name,
                           listener_function_name)
                
                    # run the listener function upon initialization
                    # so values are set at outset
                    on_init_commands += "%s();\n" % listener_function_name

            geogebra_on_init_commands[applet_identifier]=on_init_commands


        if the_capture_script:
            script_string += '<div id="geogebra_capture">\n<script>\n%s\n</script>\n</div>\n' % the_capture_script
        
        all_init_commands=""
        for applet_identifier in geogebra_on_init_commands:
            on_init_commands = geogebra_on_init_commands[applet_identifier]
            all_init_commands += 'if(arg=="%s") {\n%s}\n' % \
                                 (applet_identifier, on_init_commands)
                

        if all_init_commands:
            script_string += '<div id="geogebra_onit"><script type="text/javascript">\nfunction ggbOnInit(arg) {\nconsole.log(arg);\n%s\nif(inIframe()) { parent.ggbOnInit(arg);} \n}\n</script></div>' % all_init_commands

        three_javascript = context.dicts[0].get('three_javascript', '')
        run_three_javascript = context.dicts[0].get('run_three_javascript', '')

        if three_javascript:
            # load in three libraries
            script_string += '<script src="%sjs/three/three.js"></script><script src="%sjs/three/controls/TrackballControls.js"></script><script src="%sjs/three/Detector.js"></script><script src="%sjs/three/MIAppletThree.js"></script><script src="%sjs/three/MIThreeObjects.js"></script><script src="%sjs/three/Axes.js"></script><script src="%sjs/three/Arrow.js"></script><script src="%sjs/three/VectorField.js"></script><script src="%sjs/three/Slider.js"></script><script src="%sjs/three/DragObjects.js"></script><script src="%sjs/three/TextLabel.js"></script>\n' % \
                (static_url,static_url,static_url,static_url,static_url,static_url,static_url,static_url,static_url,static_url,static_url)


            # if webgl is supported, 
            #    then define applets and start after mathjax is finished
            # else remove "applet loading" message from images
            #    and instead add message from three.js error string

            three_error_string = AppletType.objects.get(code="Three").error_string
            script_string += '<script>\nif(Detector.webgl) {\n%s\nMathJax.Hub.Register.StartupHook("End",function () {%s});\n}\nelse {\n jQuery( ".three_applet_loading_message").remove(); jQuery( ".three_load_error" ).append(\'%s<br/> \').append(Detector.getWebGLErrorMessage())\n}\n</script>' % (three_javascript, run_three_javascript, three_error_string )
        

        return script_string


@register.tag
def accumulated_javascript(parser, token):
    return AccumulatedJavascriptNode()
