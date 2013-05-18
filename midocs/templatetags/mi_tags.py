from django import template
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Assessment
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from django.utils.encoding import smart_text
from django.template.base import kwarg_re
import re
import random
from django.contrib.sites.models import Site
from django.db.models import  Max
from mitesting.math_objects import underscore_to_camel

register=template.Library()

def resolve_if_set(variable, context):
    if variable:
        return variable.resolve(context)
    return None


class InternalLinkNode(template.Node):
    def __init__(self, link_code, link_anchor, link_class, equation_pos, equation_code, confused, nodelist):
        self.link_code_var=template.Variable("%s.code" % link_code)
        self.link_code_string = link_code
        if(link_anchor):
            self.link_anchor_var=template.Variable(link_anchor)
            self.link_anchor_template_string=template.Template(link_anchor)
        self.link_anchor_string=link_anchor
        if(link_class):
            self.link_class_var=template.Variable(link_class)
        self.link_class_string=link_class
        self.equation_pos=equation_pos
        self.equation_code=equation_code
        self.confused=confused
        self.nodelist=nodelist
    def render(self, context):
        the_equation_tag="???"

        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

        # get link text
        if self.confused:
            link_text = "(confused?)"
        else:
            link_text = self.nodelist.render(context)

        # first test if link_code_var is a variable
        # if so, link_code will be the resolved varialbe
        # otherwise, link_code will be link_code_string
        try:
            link_code=self.link_code_var.resolve(context)
        except template.VariableDoesNotExist:
            link_code=self.link_code_string
        # next, test if page with the_link_code exists
        try:
            thepage=Page.objects.get(code=link_code)
        # if page does not exist, set link to point to /link_code
        # mark as broken. 
        except ObjectDoesNotExist:
            link_url = "/%s" % link_code
            link_title=""
            link_class="broken"
            
            # if blank style,
            # don't give link, just return the link text
            # and show that it is broken so can search for it
            if(blank_style):
                return " %s BRKNLNK" % link_text

        else:
            # if equation_pos, look up equation_tag based on equation_code
            if(self.equation_pos):
                try:
                    the_equation_tag=EquationTag.objects.get\
                        (code=self.equation_code, page=thepage).tag
                    
                # if equation code does not exist,
                except ObjectDoesNotExist:
                    # if blank style,
                    # show that it is broken so can search for it
                    if(blank_style):
                        return "equation (??) %s BRKNEQNREF" \
                            % link_text
                    
            
            # if blank style, 
            # don't give link, just return the link text
            if(blank_style): 
                if(self.equation_pos):
                    if(self.equation_pos==2):
                        return " %s equation (%s) " % \
                            (link_text,the_equation_tag)
                    elif(self.equation_pos==1):
                        return " equation (%s) %s " % \
                            (the_equation_tag,link_text)
                
                # if no equation_pos or equation_pos isn't 1 or 2
                return " %s " % link_text

            # if page exist, set link_title to page title description
            link_title="%s: %s" % (thepage.title,thepage.description)
            
            # if link_class not specified, use level of page
            if self.link_class_string:
                try:
                    link_class=self.link_class_var.resolve(context)
                except template.VariableDoesNotExist:
                    link_class=self.link_class_string
            else:
                link_class = ""

            if(not link_class):
                link_class = thepage.level
            
            if self.confused:
                link_class = "%s confused" % link_class

            link_url = thepage.get_absolute_url()
            
        link_anchor=""
        if(self.equation_pos):
            link_anchor = "mjx-eqn-%s" % self.equation_code
        elif self.link_anchor_string:
            try:
                link_anchor=self.link_anchor_var.resolve(context)
            except template.VariableDoesNotExist:
                link_anchor=self.link_anchor_template_string.render(context)

        if(link_anchor):
            link_url = "%s#%s" % (link_url, link_anchor)

        if(self.equation_pos):
            if(self.equation_pos==2):
                link_text = "%s equation (%s)" % \
                            (link_text,the_equation_tag)
            elif(self.equation_pos==1):
                link_text = "equation (%s) %s" % \
                    (the_equation_tag,link_text)
                       
        return '<a href="%s" class="%s" title="%s">%s</a>' % (link_url, link_class, link_title, link_text)


@register.tag
def intlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    link_code = bits[1]
    if len(bits) > 2:
        link_anchor = bits[2]
    else:
        link_anchor = ""
    if len(bits) > 3:
        link_class = bits[3]
    else:
        link_class = ""

    nodelist = parser.parse(('endintlink',))
    parser.delete_first_token()

    return InternalLinkNode(link_code, link_anchor, link_class, 0, "", 0, nodelist)


@register.tag
def confusedlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    link_code = bits[1]
    if len(bits) > 2:
        link_anchor = bits[2]
    else:
        link_anchor = ""
    if len(bits) > 3:
        link_class = bits[3]
    else:
        link_class = ""

    return InternalLinkNode(link_code, link_anchor, link_class, 0, "", 1, "")



@register.tag
def intlinkeq(parser, token):
    """ intlinkeq template tag
    Syntax: {% intlinkeq page_code equation_code [equation_pos] %}link text{%endintlinkeq%}
    
    equation_pos determines where the reference such as "equation (1)" 
    will appear in the link text
    
    equation_pos=1 means "equation (1)" will appear before link text (default)
    equation_pos=2 means "equation (1)" will appear after link text
    equation_pos=-1 means "equation (1)" will not appear
    
    """
    
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % bits[0]

    link_code = bits[1]
    equation_code = bits[2]

    if len(bits) > 3:
        try:
            equation_pos = int(bits[3])
        except:
            equation_pos = 1
    else:
        equation_pos=1
        
    if len(bits) > 4:
        link_class = bits[4]
    else:
        link_class = ""

    nodelist = parser.parse(('endintlinkeq',))
    parser.delete_first_token()
    
    return InternalLinkNode(link_code,"",link_class,equation_pos,equation_code,0,nodelist)




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
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
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
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
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
    def __init__(self, image, kwargs, kwargs_string):
        self.image= image
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
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
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    image = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value
  
    return ImageNode(image, kwargs, kwargs_string)



class ProcessMiTagsNode(template.Node):
    def __init__(self, the_text_var):
        self.the_text_var=the_text_var
    def render(self, context):
        try:
            templatetext=self.the_text_var.resolve(context)
        except template.VariableDoesNotExist:
            return ""
        
        try:
            rendered_text = template.Template("{% load mi_tags %}"+templatetext).render(context)
        except:
            rendered_text = templatetext

        return rendered_text


@register.tag
def process_mi_tags(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r tag requires one argument" % bits[0]
    the_text_var = parser.compile_filter(bits[1])
    return ProcessMiTagsNode(the_text_var)




def return_applet_parameter_string(applet):
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

def Geogebra_change_object_javascript(context, appletobject,applet_identifier,
                                      objectvalue):
    
    object_type = appletobject.object_type.object_type
    
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

            javascript = 'document.%s.setCoords("%s", "%s", "%s");\n' % \
                (applet_identifier, appletobject.name,
                  value[0], value[1])
        elif object_type=='Number' or object_type=='Boolean':
            javascript = 'document.%s.setValue("%s", %s);\n' % \
                (applet_identifier, appletobject.name,
                 value)
        elif object_type=='Text':
            javascript = 'document.%s.evalCommand(\'%s="%s"\');\n' % \
                (applet_identifier, appletobject.name,
                 value)
        return javascript
    except:
        raise #return ""

def Geogebra_capture_object_javascript(context, appletobject, applet_identifier,
                                       target, related_objects=[]):
    
    object_type = appletobject.object_type.object_type
    javascript= ""
    if object_type=='Point':
        xcoord = 'document.%s.getXcoord("%s")' % \
            (applet_identifier, appletobject.name)
        ycoord = 'document.%s.getYcoord("%s")' % \
            (applet_identifier, appletobject.name)

        javascript='$("#%s").val("Point("+%s+","+%s+")");\n' % \
            (target, xcoord,ycoord)
    elif object_type=='Number' or object_type=='Boolean':
        value = 'document.%s.getValue("%s")' % \
            (applet_identifier, appletobject.name)
        javascript='$("#%s").val(%s);\n' % (target, value)
    elif object_type=='Text':
        value = 'document.%s.getValueString("%s")' % \
            (applet_identifier, appletobject.name)
        javascript='$("#%s").val(%s);\n' % (target, value)
    elif object_type=='Line':
        if len(related_objects)==2:
            point1=related_objects[0]
            point2=related_objects[1]
            if point1.object_type.object_type=='Point' and \
                    point2.object_type.object_type=='Point':
                xcoord1 = 'document.%s.getXcoord("%s")' % \
                    (applet_identifier, point1.name)
                ycoord1 = 'document.%s.getYcoord("%s")' % \
                    (applet_identifier, point1.name)
                xcoord2 = 'document.%s.getXcoord("%s")' % \
                    (applet_identifier, point2.name)
                ycoord2 = 'document.%s.getYcoord("%s")' % \
                    (applet_identifier, point2.name)
                javascript='$("#%s").val("Line(Point("+%s+","+%s+"),Point("+%s+","+%s+"))");\n' % \
                    (target, xcoord1,ycoord1, xcoord2,ycoord2)
                
                
    return javascript
    
def GeogebraWeb_link(context, applet, applet_identifier, width, height):

    html_string=""
    geogebra_javascript_included=context.get('geogebra_javascript_included',False)
    n_geogebra_web_applets=context.get('n_geogebra_web_applets', 0)

    if n_geogebra_web_applets==0:
        html_string+='<script type="text/javascript" language="javascript" src="http://www.geogebra.org/web/4.2/web/web.nocache.js"></script>'

    n_geogebra_web_applets += 1
    context['n_geogebra_web_applets']=n_geogebra_web_applets


    html_string += '<div class="javascriptapplet"><article class="geogebraweb" data-param-width="%s" data-param-height="%s" data-param-id="%s" data-param-showResetIcon="false" data-param-enableLabelDrags="false" data-param-showMenuBar="false" data-param-showToolBar="false" data-param-showAlgebraInput="false" data-param-useBrowserForJS="true" data-param-ggbbase64="%s"></article></div>\n' % \
        (width, height, applet_identifier, applet.encoded_content)

    return html_string


def Geogebra_link(context, applet, applet_identifier, width, height):
    # html_string='<div class="applet"><object class="ggbApplet" type="application/x-java-applet" id="%s" height="%s" width="%s"><param name="code" value="geogebra.GeoGebraApplet" /><param name="archive" value="geogebra.jar" /><param name="codebase" value="%sjar/" />' % \
    #     (applet.code, height, width, context["STATIC_URL"] )
    html_string='<div class="applet"><applet class="ggbApplet" name="%s" code="geogebra.GeoGebraApplet" archive="geogebra.jar" codebase="%sjar/" width="%s" height="%s">' % \
        (applet.code, context["STATIC_URL"], width, height )
    if applet.javascript:
        html_string='<div class="applet"><applet class="ggbApplet" name="%s" code="geogebra.GeoGebraApplet" archive="geogebra.jar" codebase="%sjar/" width="%s" height="%s">' % \
            (applet.code, context["STATIC_URL"], width, height )
  
    html_string='%s%s' % (html_string, return_applet_parameter_string(applet))

    html_string= '%s<param name="ggbOnInitParam" value="%s" />' \
        % (html_string,applet.code)
    if applet.applet_file:
        html_string= '%s<param name="filename" value="%s" />' \
            % (html_string,applet.applet_file.url)
    # elif applet.encoded_content:
    #     html_string= '%s<param name="ggbBase64" value="%s" />' \
    #         % (html_string,applet.encoded_content)
    html_string = '%s%s' % (html_string, return_applet_error_string(applet))

    if applet.javascript:
        javascript_string='</applet></div>\n<script type="text/javascript">\nvar ggbApplet = document.%s;\n%s</script>' % (applet.code, applet.javascript)
        html_string = '%s%s' % (html_string, javascript_string)
    else:
        #html_string = '%s</object></div>' % html_string
        html_string = '%s</applet></div>\n' % html_string

    html_string = '%s%s' % (html_string, return_print_image_string(applet))
    return html_string



def LiveGraphics3D_link(context, applet, applet_identifier, width, height):
    html_string='<div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (height, width, context["STATIC_URL"])

    html_string='%s%s' % (html_string, return_applet_parameter_string(applet))
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
    html_string = '%s%s</object></div>%s' % (html_string, return_applet_error_string(applet), return_print_image_string(applet))

    return html_string

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
        (height, width, context["STATIC_URL"])
    
    # add the parameters for applet 1
    html_string = '%s%s' \
                % (html_string, param_string1)
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
        
    # close off applet 1 and begin tag for applet 2
    html_string = '%s%s</object></div>%s</div></div><div class="ym-g50 ym-gr"><div class="ym-gbox-right"><div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (html_string, return_applet_error_string(applet,1), return_print_image_string(applet,1), height, width, context["STATIC_URL"])
    # add the parameters for applet 2
    html_string = '%s%s' \
                % (html_string, param_string2)
    if applet.applet_file2:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file2.url)
    
    html_string = '%s%s</object></div>%s</div></div></div>' % (html_string, return_applet_error_string(applet,2), return_print_image_string(applet,2))


    return html_string



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
                              for k, v in self.kwargs.items()])

        applet = self.applet.resolve(context)

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
                width=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH").value
            except ObjectDoesNotExist:
                pass
        if width==0:
            try:
                width=applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_WIDTH").default_value
            except ObjectDoesNotExist:
                width=default_size

        height=0
        try:
            height = int(kwargs['height'])
        except:
            pass

        if height==0:
            try:
                height=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT").value
            except ObjectDoesNotExist:
                pass

        if height==0:
            try:
                height=applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_HEIGHT").default_value
            except ObjectDoesNotExist:
                height=default_size

        caption = None
        if self.boxed:
            caption = kwargs.get('caption')

            if caption is None:
                try:
                    caption = template.Template("{% load mi_tags %}"+applet.default_inline_caption).render(context)
                except:
                    caption = applet.default_inline_caption
                    

        # check to see if the variable process_applet_entries is set
        # if so, add entry to database
        if context.get("process_applet_entries"):
            # get page object, 
            thepage = context.get('thepage')
            # if applet wasn in a page,  add page to in_pages of applet
            if thepage:
                applet.in_pages.add(thepage)

        # check if blank_style is set
        # if so, just return title, and caption if "boxed"
        blank_style = context.get("blank_style")
        if blank_style:
            if self.boxed:
                return " %s %s " % (applet.title, caption)
            else:
                return " %s " % applet.title

            
        # html for applet inclusion
        # add html for applet embedding based on applet_type
        identifier = context.get('identifier','')
        applet_identifier = "%s00%s" % (applet.code_camel(), 
                                        underscore_to_camel(identifier))

        if applet.applet_type.code == "LiveGraphics3D":
            applet_link = LiveGraphics3D_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "DoubleLiveGraphics3D":
           applet_link = DoubleLiveGraphics3D_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "Geogebra":
           applet_link = Geogebra_link(context, applet, applet_identifier, width, height)
        elif applet.applet_type.code == "GeogebraWeb":
           applet_link = GeogebraWeb_link(context, applet, applet_identifier, width, height)
        else:
            # if applet type for which haven't yet coded a link
            # return broken applet text
            return '<p>[Broken applet]</p>'

        # check if any applet objects are specified 
        # to be changed with javascript
        appletobjects=applet.appletobject_set.filter \
            (change_from_javascript=True)
        init_javascript = ""
        for appletobject in appletobjects:
            objectvalue = kwargs.get(appletobject.name)
            if objectvalue is not None:
                if applet.applet_type.code == "Geogebra" \
                        or applet.applet_type.code == "GeogebraWeb":
                    init_javascript += Geogebra_change_object_javascript \
                        (context, appletobject, applet_identifier, objectvalue)
                    

        # check if any applet objects are specified 
        # to be captured with javascript
        appletobjects=applet.appletobject_set.filter \
            (capture_changes=True)
        inputboxlist=''
        capture_javascript=''
        answer_list = context.get('answer_list',[])

        for appletobject in appletobjects:
            the_kw = "answer_blank_%s" % appletobject.name
            expression_for_object = kwargs.get(the_kw)
            if expression_for_object is not None:
                expression_string =  kwargs_string.get(the_kw)

                target = "answer_%s_%s" % (expression_string, identifier)
                target_id = "id_" + target
                inputboxlist += '<input type="hidden" id="%s" maxlength="20" name="%s" size="20" />\n' % (target_id, target)
                    
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
                    capture_javascript += Geogebra_capture_object_javascript \
                        (context, appletobject, applet_identifier, 
                         target_id, related_objects)

                try:
                    points = int(kwargs['points_'+the_kw])
                except:
                    points = 1

                answer_list.append((expression_string, expression_for_object,
                                    points))
        
        context['answer_list'] = answer_list


                        
        applet_link += inputboxlist
        if applet.applet_type.code == "Geogebra" \
                or applet.applet_type.code == "GeogebraWeb":
            if capture_javascript:
                listener_function_name = "listener%s" % applet_identifier
                init_javascript += 'document.%s.registerUpdateListener("%s");\n' \
                    % (applet_identifier, listener_function_name)
                
                # run the listener function upon initialization
                # so answer_blanks have values
                init_javascript += "%s();\n" % listener_function_name

                listener_function_script = '<script type="text/javascript">\nfunction %s(obj) {\n%s}\n</script>\n' %(listener_function_name, capture_javascript)
                applet_link += listener_function_script


        if init_javascript:
            if applet.applet_type.code == "Geogebra" \
                    or applet.applet_type.code == "GeogebraWeb":
                # since javascript has to be combined in ggbOnInit
                # add javascript to geogebra_init_javascript in context
                # use context.dicts[0] so available outside template block
                all_init_javascript = context.dicts[0].get('geogebra_oninit_commands','')
                all_init_javascript += 'if(arg=="%s") {\n%s}\n' % \
                    (applet_identifier, init_javascript)
                context.dicts[0]['geogebra_oninit_commands'] = all_init_javascript
        

        # if not boxed, just return code for applet
        if not self.boxed:
            return applet_link

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
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    applet = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
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


class AppletLinkNode(template.Node):
    def __init__(self, applet, extended_mode, nodelist):
        self.applet = applet
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=context.get("blank_style",0)

        link_text = self.nodelist.render(context)

        applet = self.applet.resolve(context)

        # if applet is not an Applet, then look for applet with that code
        if not isinstance(applet,Applet):
            try:
                applet=Applet.objects.get(code=applet)
            # if applet does not exist
            # return tag to applet code anyway
            except ObjectDoesNotExist:
                if(blank_style):
                    return " %s BRKNAPPLNK" % link_text
                else:
                    return '<a href="applet/%s" class="broken">%s</a>' % (applet, link_text)
            
        link_title="%s. %s" % (applet.annotated_title(),applet.description)
        
        link_url = applet.get_absolute_url()

        extended_mode = resolve_if_set(self.extended_mode, context)

        if not extended_mode:
            return '<a href="%s" class="applet" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if applet.thumbnail:
            if extended_mode == '2':
                thumbnail_width_buffer = applet.thumbnail_small_width_buffer()
                thumbnail_width=applet.thumbnail_small_width()
                thumbnail_height=applet.thumbnail_small_height()
            else:
                thumbnail_width_buffer = applet.thumbnail_medium_width_buffer()
                thumbnail_width=applet.thumbnail_medium_width()
                thumbnail_height=applet.thumbnail_medium_height()

            html_text = '%s<div style="width: %spx; float: left;"><a href="%s"><img src="%s" alt="%s" width ="%s" height="%s" /></a></div>' % \
                (html_text,thumbnail_width_buffer, link_url,\
                     applet.thumbnail.url, \
                     applet.title, thumbnail_width,thumbnail_height)
            
        if extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="applet" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        html_text= '%s %s' % (html_text,  applet.feature_list())
        
        if applet.description:
            html_text= '%s<br/>%s' % (html_text, applet.description)
            

        if extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if applet.author_list_full():
               html_text= '%sby %s' % (html_text, applet.author_list_full())
           html_text = '%s on %s' % (html_text, applet.publish_date)

        if extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def appletlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    applet = parser.compile_filter(bits[1])
    if len(bits) > 2:
        extended_mode = parser.compile_filter(bits[2])
    else:
        extended_mode=None

    nodelist = parser.parse(('endappletlink',))
    parser.delete_first_token()

    return AppletLinkNode(applet, extended_mode, nodelist)




def youtube_link(context, video, width, height):
    
    try:
        youtubecode=video.videoparameter_set.get(parameter__parameter_name ="youtubecode").value
    except ObjectDoesNotExist:
        return "[Broken video]"

    html_string='<div class="video"><iframe width="%s" height="%s" src="http://www.youtube-nocookie.com/embed/%s?rel=0" frameborder="0" allowfullscreen></iframe></div>' % \
        (width, height, youtubecode )

    return html_string


class VideoNode(template.Node):
    def __init__(self, video, boxed, kwargs, kwargs_string):
        self.video= video
        self.boxed=boxed
        self.kwargs=kwargs
        self.kwargs_string=kwargs_string
    def render(self, context):

        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        kwargs_string = dict([(smart_text(k, 'ascii'), v)
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
                except:
                    caption = video.default_inline_caption
                    

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
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    video = parser.compile_filter(bits[1])

    kwargs = {}
    kwargs_string = {}
    
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to %s tag" % bits[0])
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
                kwargs_string[name] = value
  
    return (video, kwargs, kwargs_string)


@register.tag
def video(parser, token):
# video tag
    (video, kwargs, kwargs_string)=video_sub(parser, token)
    return VideoNode(video, 0, kwargs, kwargs_string)


@register.tag
def boxedvideo(parser, token):
# boxedvideo tag
    (video, kwargs, kwargs_string)=video_sub(parser, token)
    return VideoNode(video, 1, kwargs, kwargs_string)


class VideoLinkNode(template.Node):
    def __init__(self, video, extended_mode, nodelist):
        self.video = video
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is se
        blank_style=context.get("blank_style")

        link_text = self.nodelist.render(context)

        video = self.video.resolve(context)
        
        # if video is not an Video, then look for video with that code
        if not isinstance(video,Video):
            try:
                video=Video.objects.get(code=video)
            # if video does not exist
            # return tag to video anyway
            except ObjectDoesNotExist:
                if(blank_style):
                    return " %s BRKNIMGLNK" % link_text
                else:
                    return '<a href="video/%s" class="broken">%s</a>' % (video, link_text)
            
        link_title="%s. %s" % (video.annotated_title(),video.description)
        
        link_url = video.get_absolute_url()

        extended_mode = resolve_if_set(self.extended_mode, context)

        if not extended_mode:
            return '<a href="%s" class="video" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if video.thumbnail:
            if extended_mode == '2':
                thumbnail_width_buffer = video.thumbnail_small_width_buffer()
                thumbnail_width=video.thumbnail_small_width()
                thumbnail_height=video.thumbnail_small_height()
            else:
                thumbnail_width_buffer = video.thumbnail_medium_width_buffer()
                thumbnail_width=video.thumbnail_medium_width()
                thumbnail_height=video.thumbnail_medium_height()

            html_text = '%s<div style="width: %spx; float: left;"><a href="%s"><img src="%s" alt="%s" width ="%s" height="%s" /></a></div>' % \
                (html_text,thumbnail_width_buffer, link_url,\
                     video.thumbnail.url, \
                     video.title, thumbnail_width,thumbnail_height)
            
        if extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="video" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        if video.description:
            html_text= '%s<br/>%s' % (html_text, video.description)
            

        if extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if video.author_list_full():
               html_text= '%sby %s' % (html_text, video.author_list_full())
           html_text = '%s on %s' % (html_text, video.publish_date)

        if extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def videolink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    video = parser.compile_filter(bits[1])
    if len(bits) > 2:
        extended_mode = parser.compile_filter(bits[2])
    else:
        extended_mode=None

    nodelist = parser.parse(('endvideolink',))
    parser.delete_first_token()

    return VideoLinkNode(video, extended_mode, nodelist)




class ImageLinkNode(template.Node):
    def __init__(self, image, extended_mode, nodelist):
        self.image = image
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set
        blank_style=context.get("blank_style")

        link_text = self.nodelist.render(context)

        image = self.image.resolve(context)
        
        # if image is not an Image, then look for image with that code
        if not isinstance(image,Image):
            try:
                image=Image.objects.get(code=image)
            # if image does not exist
            # return tag to image anyway
            except ObjectDoesNotExist:
                if(blank_style):
                    return " %s BRKNIMGLNK" % link_text
                else:
                    return '<a href="image/%s" class="broken">%s</a>' % (image, link_text)

        link_title="%s. %s" % (image.annotated_title(),image.description)
        
        link_url = image.get_absolute_url()

        extended_mode = resolve_if_set(self.extended_mode, context)

        if not extended_mode:
            return '<a href="%s" class="image" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if image.thumbnail:
            if extended_mode == '2':
                thumbnail_width_buffer = image.thumbnail_small_width_buffer()
                thumbnail_width=image.thumbnail_small_width()
                thumbnail_height=image.thumbnail_small_height()
            else:
                thumbnail_width_buffer = image.thumbnail_medium_width_buffer()
                thumbnail_width=image.thumbnail_medium_width()
                thumbnail_height=image.thumbnail_medium_height()

            html_text = '%s<div class="ym-clearfix"><div style="width: %spx; float: left;"><a href="%s"><img src="%s" alt="%s" width ="%s" height="%s" /></a></div>' % \
                (html_text,thumbnail_width_buffer, link_url, image.thumbnail.url, \
                     image.title, thumbnail_width,thumbnail_height)
            
        if extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="image" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        if image.description:
            html_text= '%s<br/>%s' % (html_text, image.description)
            
        if extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if image.author_list_full():
               html_text= '%sby %s' % (html_text, image.author_list_full())
           html_text = '%s on %s' % (html_text, image.publish_date)

        if extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def imagelink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    image = parser.compile_filter(bits[1])
    if len(bits) > 2:
        extended_mode = parser.compile_filter(bits[2])
    else:
        extended_mode=None

    nodelist = parser.parse(('endimagelink',))
    parser.delete_first_token()

    return ImageLinkNode(image, extended_mode, nodelist)


class AssessmentLinkNode(template.Node):
    def __init__(self, the_assessment, nodelist):
        self.the_assessment = the_assessment
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set
        blank_style=context.get("blank_style")

        link_text = self.nodelist.render(context)
        the_assessment = self.the_assessment.resolve(context)

        # if assessment is not already an instance of an assessment
        # find assessment with that code
        if not isinstance(the_assessment, Assessment):
            try:
                the_assessment = Assessment.objects.get(code=the_assessment)
            except:
                if(blank_style):
                    return " %s BRKNASMTLNK" % link_text
                else:
                    return '<a href="assessment/%s" class="broken">%s</a>' % (the_assessment, link_text)
                
        link_title="%s. %s" % (the_assessment.name,the_assessment.description)
        
        link_url = the_assessment.get_absolute_url()

        return '<a href="%s" class="assessment" title="%s">%s</a>' \
            % (link_url, link_title, link_text)

@register.tag
def assessmentlink(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r tag requires one argument" % bits[0]
    the_assessment=parser.compile_filter(bits[1])
    nodelist = parser.parse(('endassessmentlink',))
    parser.delete_first_token()

    return AssessmentLinkNode(the_assessment, nodelist)


                                                                      
@register.inclusion_tag('midocs/thread_section_contents.html')
def thread_section_contents(thread_section, recursion, max_recursions):
    recursion += 1
    child_sections = thread_section.child_sections.all() 
    thread_pages = thread_section.thread_pages.all()
    if recursion < max_recursions and child_sections:
        include_children=True
    else:
        include_children=False
    return {'thread_section': thread_section,
            'child_sections': child_sections,
            'thread_pages': thread_pages,
            'include_children': include_children,
            'recursion': recursion,
            'max_recursions': max_recursions,
            }


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


class AccumulatedJavascriptNode(template.Node):
    def render(self, context):
        # return any geogebra_init_javascript
        init_javascript = context.get('geogebra_oninit_commands','')
        if init_javascript:
            return '<script type="text/javascript">\nfunction ggbOnInit(arg) {\n%s}\n</script>' % init_javascript
        else:
            return ''


@register.tag
def accumulated_javascript(parser, token):
    return AccumulatedJavascriptNode()
