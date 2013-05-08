from django import template
from midocs.models import Page, PageNavigation, PageNavigationSub, IndexEntry, IndexType, Image, ImageType, Applet, Video, EquationTag, ExternalLink, PageCitation, Reference
from mitesting.models import Assessment
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
import re
import random
from django.contrib.sites.models import Site
from django.db.models import  Max

register=template.Library()

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

            #link_url = thepage.get_absolute_url()
            link_url = 'http://%s%s' % (Site.objects.get_current().domain, thepage.get_absolute_url())
            
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
        # check to see if the variable process_equation_tags==1
        # if so, add entry to database
        try:
             process_equation_tags = template.Variable("process_equation_tags").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_equation_tags == 1:
                # get page object, if doesn't exist, just return blank string
                try:
                    thepage = template.Variable("thepage").resolve(context)
                except template.VariableDoesNotExist:
                    return ""
                
                # add equation tag
                EquationTag.objects.create \
                    (page=thepage, code=self.code, tag=self.tag)

        # check if blank_style is set to 1
        # if so, return (tag)
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return " (%s) " % self.tag
        except template.VariableDoesNotExist:
            pass

        # return the tag in format for processing by MathJax
        # this will create an equation label using code,
        # display the equation number as tag
        # and create a html anchor of mjx-eqn-tag
        return '\\label{%s}\\tag{%s}' % (self.code,self.tag)

@register.tag
def equation_tag(parser, token):
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % bits[0]
    code=bits[1]
    tag=bits[2]
    return EquationTagNode(code,tag)


class ExternalLinkNode(template.Node):
    def __init__(self, external_url, nodelist):
        self.external_url = external_url
        self.nodelist=nodelist
    def render(self, context):
        
        link_text = self.nodelist.render(context)

        # check to see if the variable update_database==1
        # if so, add entry to database
        try:
             update_database = template.Variable("update_database").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if update_database == 1:
                # get page object, 
                # and save as linked from that page
                try:
                    thepage = template.Variable("thepage").resolve(context)
                    extlink = ExternalLink.objects.create \
                        (external_url=self.external_url,
                         in_page=thepage, link_text=link_text)
                        
                # if not in a page, save without reference to page
                except:
                    extlink = ExternalLink.objects.create \
                        (external_url=self.external_url,
                         link_text=link_text)


        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

        if blank_style:
            return "%s %s" %  (self.external_url, link_text)
        else:
            return '<a href="%s" class="external">%s</a>' % \
                (self.external_url, link_text)
        

@register.tag
def extlink(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r tag requires one argument" % bits[0]
    external_url = bits[1]
    if not (external_url[0] == external_url[-1] and external_url[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % bits[0]
    external_url = external_url[1:-1]

    nodelist = parser.parse(('endextlink',))
    parser.delete_first_token()
    

    return ExternalLinkNode(external_url,nodelist)

class NavigationTagNode(template.Node):
    def __init__(self,page_anchor, navigation_phrase, navigation_subphrase):
        self.navigation_phrase=template.Template(navigation_phrase)
        self.navigation_subphrase=template.Template(navigation_subphrase)
        self.have_subphrase=navigation_subphrase
        self.page_anchor=template.Template(page_anchor)
    def render(self, context):
        # render the phrase, subphrase, and page_anchor under current context
        the_navigation_phrase=self.navigation_phrase.render(context)
        the_navigation_subphrase=self.navigation_subphrase.render(context)
        the_page_anchor=self.page_anchor.render(context)

        # check to see if the variable navigation_tags==1
        # if so, add entry to database
        try:
             process_navigation_tags = template.Variable("process_navigation_tags").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_navigation_tags == 1:
                # get page object, if doesn't exist, just return blank string
                try:
                    thepage = template.Variable("thepage").resolve(context)
                except template.VariableDoesNotExist:
                    return ""
            
                # add navigation_tag
                if(self.have_subphrase):
                    # first try to find the phrase already there
                    # and just create subphrase entry
                    try:
                        navigation_entry = PageNavigation.objects.get \
                            (page=thepage, \
                                 navigation_phrase=the_navigation_phrase)
                        navigation_sub_entry=PageNavigationSub.objects.create \
                            (navigation=navigation_entry, \
                                 navigation_subphrase=the_navigation_subphrase, \
                                 page_anchor=the_page_anchor)
                    except:
                        # next try to create both phrase and subphrase entries
                        try:
                            navigation_entry = PageNavigation.objects.create \
                                (page=thepage, \
                                     navigation_phrase=the_navigation_phrase,\
                                     page_anchor=the_page_anchor)
                            navigation_sub_entry=PageNavigationSub.objects.create \
                                (navigation=navigation_entry, \
                                     navigation_subphrase=the_navigation_subphrase, \
                                     page_anchor=the_page_anchor)
                            
                            
                        except:
                            pass
                else:
                    # if no subphrase, just create phrase entry
                    try:
                        navigation_entry = PageNavigation.objects.create \
                            (page=thepage, 
                             navigation_phrase=the_navigation_phrase,
                             page_anchor=the_page_anchor)
                    except:
                        pass
                        

        # check if blank_style is set to 1
        # if so, return ""
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return ""
        except template.VariableDoesNotExist:
            pass

        # if page_anchor is not null, return an anchor, else return nothing
        return '<a id="%s" class="anchor"></a>' % the_page_anchor
 
@register.tag
def navigation_tag(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two arguments" % bits[0]
    page_anchor=bits[1]
    if not (page_anchor[0] == page_anchor[-1] and page_anchor[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's first argument should be in quotes" % bits[0]
    page_anchor = page_anchor[1:-1]
    navigation_phrase=bits[2]
    if not (navigation_phrase[0] == navigation_phrase[-1] and navigation_phrase[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % bits[0]
    navigation_phrase = navigation_phrase[1:-1]
    if len(bits) > 3:
        navigation_subphrase=bits[3]
        if not (navigation_subphrase[0] == navigation_subphrase[-1] and navigation_subphrase[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's third argument should be in quotes" % bits[0]
        navigation_subphrase = navigation_subphrase[1:-1]
    else:
        navigation_subphrase = ""
    return NavigationTagNode(page_anchor, navigation_phrase, navigation_subphrase)



class FootnoteNode(template.Node):
    def __init__(self,cite_code,footnote_text):
        self.cite_code=cite_code
        self.footnote_text=footnote_text
    def render(self, context):
        # get page object, if doesn't exist, just return blank string
        try:
            thepage = template.Variable("thepage").resolve(context)
        except template.VariableDoesNotExist:
            return ""


        # check to see if the variable process_citations==1
        # if so, add entry to database
        try:
             process_citations = template.Variable("process_citations").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_citations == 1:

                # check to see if page already has citations
                # and if so, what the largest reference number is
                previous_citations=PageCitation.objects.filter(page=thepage)
                previous_reference_number=0
                if previous_citations:
                    previous_reference_number=previous_citations.aggregate(Max('reference_number'))['reference_number__max']
                
                try:
                    # add footnote entry
                    footnote_entry = PageCitation.objects.create \
                        (page=thepage, \
                             code=self.cite_code, \
                             footnote_text=self.footnote_text, \
                             reference_number = previous_reference_number+1)
            
                # fail silently
                except:
                    pass

        # find reference number
        reference_number = 0
        footnote_entry = PageCitation.objects.get( \
            page=thepage, code=self.cite_code)
        reference_number = footnote_entry.reference_number


        # check if blank_style is set to 1
        # if so, return reference number
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return "[%s]" % reference_number
        except template.VariableDoesNotExist:
            pass

        # return link to reference
        return '<a href="#citation:%s"><sup>%s</sup></a>' % (reference_number, reference_number)
 
@register.tag
def footnote(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError, "%r tag requires at least two argument" % bits[0]
    cite_code=bits[1]
    footnote_text=bits[2]
    if not (footnote_text[0] == footnote_text[-1] and footnote_text[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % bits[0]
    footnote_text = footnote_text[1:-1]

    return FootnoteNode(cite_code,footnote_text)




class CitationNode(template.Node):
    def __init__(self,cite_codes):
        self.cite_codes=cite_codes

    def render(self, context):
        # get page object, if doesn't exist, just return blank string
        try:
            thepage = template.Variable("thepage").resolve(context)
        except template.VariableDoesNotExist:
            return ""


        # check to see if the variable process_citations==1
        # if so, add entry to database
        try:
             process_citations = template.Variable("process_citations").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_citations == 1:

                # check to see if page already has citations
                # and if so, what the largest reference number is
                previous_citations=PageCitation.objects.filter(page=thepage)
                previous_reference_number=0
                if previous_citations:
                    previous_reference_number=previous_citations.aggregate(Max('reference_number'))['reference_number__max']
                
                # find references based on cite_code
                for cite_code in self.cite_codes:
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
        for cite_code in self.cite_codes:
            try:
                citation_entry = PageCitation.objects.get( \
                    page=thepage, code=cite_code)
                reference_numbers.append(citation_entry.reference_number)
            except:
                reference_numbers.append('??')
                
        # check if blank_style is set to 1
        # if so, return reference number
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                reference_number_string=""
                for i, rn in enumerate(reference_numbers):
                    reference_number_string="%s%s" \
                        %(reference_number_string, rn)
                    if i < len(reference_numbers)-1:
                        reference_number_string += ","
                return "[%s]" % reference_number_string
        except template.VariableDoesNotExist:
            pass

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
        cite_codes.append(bits[i])
    
    return CitationNode(cite_codes)



class IndexEntryNode(template.Node):
    def __init__(self, indexed_phrase, indexed_subphrase, page_anchor, index_type):
        self.indexed_phrase=indexed_phrase
        self.indexed_subphrase=indexed_subphrase
        self.page_anchor=page_anchor
        self.index_type=index_type
    def render(self, context):
        # check to see if the variable process_index_entries==1
        # if so, add entry to database
        try:
             process_index_entries = template.Variable("process_index_entries").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_index_entries == 1:
                # get page object, if doesn't exist, just return blank string
                try:
                    thepage = template.Variable("thepage").resolve(context)
                except template.VariableDoesNotExist:
                    return ""
                
                # check to see if index_type exists.  If not, make it a general index entry
                if self.index_type:
                    try:
                        index_type = IndexType.objects.get(code=self.index_type)
                    except ObjectDoesNotExist:
                        index_type = IndexType.objects.get(code="general")
                else:
                    index_type = IndexType.objects.get(code="general") 
                        
                # add index entry
                index_entry = IndexEntry.objects.create \
                    (page=thepage, index_type=index_type, 
                     indexed_phrase=self.indexed_phrase,
                     indexed_subphrase=self.indexed_subphrase,
                     page_anchor=self.page_anchor)

        # check if blank_style is set to 1
        # if so, return ""
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return ""
        except template.VariableDoesNotExist:
            pass

        # if page_anchor is not null, return an anchor, else return nothing
        if(self.page_anchor):
            return '<a id="%s" class="anchor"></a>' % self.page_anchor
        else:
            return ""
 
@register.tag
def index_entry(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    indexed_phrase=bits[1]
    if not (indexed_phrase[0] == indexed_phrase[-1] and indexed_phrase[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's first argument should be in quotes" % bits[0]
    indexed_phrase = indexed_phrase[1:-1]
    if len(bits) >2:
        indexed_subphrase=bits[2]
        if not (indexed_subphrase[0] == indexed_subphrase[-1] and indexed_subphrase[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % bits[0]
        indexed_subphrase = indexed_subphrase[1:-1]
    else:
        indexed_subphrase = "";
    if len(bits)>3:
        page_anchor=bits[3]
        if not (page_anchor[0] == page_anchor[-1] and page_anchor[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's third argument should be in quotes" % bits[0]
        page_anchor = page_anchor[1:-1]
    else:
        page_anchor = "";
    if len(bits)>4:
        index_type=bits[4]
        if not (index_type[0] == index_type[-1] and index_type[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's fourth argument should be in quotes" % bits[0]
        index_type = index_type[1:-1]
    else:
        index_type = "";
    return IndexEntryNode(indexed_phrase, indexed_subphrase, page_anchor, index_type)



class TitleNode(template.Node):
    def __init__(self, title_text, navigation_phrase):
        self.title_text=title_text
        self.navigation_phrase = navigation_phrase
    def render(self, context):
        # check to see if the variable update_database==1
        # if so, add entry to database
        try:
             update_database = template.Variable("update_database").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if update_database == 1:
                # get page object, 
                # and save title to that database entry
                try:
                    thepage = template.Variable("thepage").resolve(context)
                    thepage.title=self.title_text
                # ignore any errors
                except:
                    pass
                
        # if navigation_phase is nonzero
        # add a navigation tag with that phrase and anchor main
        # if process_navigation_tags==1
        if self.navigation_phrase:
            try:
                process_navigation_tags = template.Variable("process_navigation_tags").resolve(context)
            except template.VariableDoesNotExist:
                pass
            else:
                if process_navigation_tags == 1:
                    try:
                        # add an navigation_entry, ignore any errors
                        thepage = template.Variable("thepage").resolve(context)
                        navigation_entry = PageNavigation.objects.create \
                            (page=thepage, 
                             navigation_phrase=self.navigation_phrase,
                             page_anchor="main")
                    except:
                        pass
                        

        # check if blank_style is set to 1
        # if so, return undecorated text
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return " %s " % self.title_text
        except template.VariableDoesNotExist:
            pass
        
        return ""
        #return "<h3>%s</h3>" % self.title_text

 
@register.tag
def title(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    title_text=bits[1]
    if not (title_text[0] == title_text[-1] and title_text[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's first argument should be in quotes" % bits[0]
    title_text = title_text[1:-1]
    if len(bits) > 2:
        navigation_phrase=bits[2]
        if not (navigation_phrase[0] == navigation_phrase[-1] and navigation_phrase[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % bits[0]
        navigation_phrase = navigation_phrase[1:-1]
    else:
        navigation_phrase = ""


    return TitleNode(title_text, navigation_phrase)

class DescriptionNode(template.Node):
    def __init__(self, description_text):
        self.description_text=description_text
    def render(self, context):
        # check to see if the variable update_database==1
        # if so, add entry to database
        try:
             update_database = template.Variable("update_database").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if update_database == 1:
                # get page object, 
                # and save description to that database entry
                try:
                    thepage = template.Variable("thepage").resolve(context)
                    thepage.description=self.description_text
                # ignore any errors
                except:
                    pass
        return ""

@register.tag
def description(parser, token):
    try:
        tag_name, description_text = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    if not (description_text[0] == description_text[-1] and description_text[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % bits[0]
    description_text = description_text[1:-1]

    return DescriptionNode(description_text)



class ImageNode(template.Node):
    def __init__(self, image_code, max_width, float_direction):
        self.image_code_var=template.Variable("%s.code" % image_code)
        self.image_code_string = image_code
        self.max_width=max_width
        self.float_direction=float_direction
    def render(self, context):
        # first test if image_code_var is a variable
        # if so, image_code will be the resolved variable
        # otherwise, image will be image_code_string
        try:
            image_code=self.image_code_var.resolve(context)
        except template.VariableDoesNotExist:
            image_code=self.image_code_string
        # next, test if image with image_code exists
        try:
            image=Image.objects.get(code=image_code)
        # if image does not exist
        # return tag to image code anyway
        except ObjectDoesNotExist:
            return '<img src="/%s" alt="[broken image]" class="broken" />' % image_code

        imagefile=None
        # check if a notation system is defined in template
        try:
            notation_system = template.Variable("notation_system").resolve(context)
        except template.VariableDoesNotExist:
            notation_system = None
            
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
            
            # # if didn't get an alternative image from notation system
            # # and have an SVG file from inkscape, display that instead
            # svgimagetype= ImageType.objects.get(code='inkscape')
            # if image.original_file_type == svgimagetype and image.original_file:
            #     svgfile = image.original_file
        
        title = image.title

        # check to see if the variable process_image_entries==1
        # if so, add entry to database
        try:
             process_image_entries = template.Variable("process_image_entries").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_image_entries == 1:
                # get page object, 
                try:
                    thepage = template.Variable("thepage").resolve(context)
                except template.VariableDoesNotExist:
                    pass
                else:
                    # add page to in_pages of image
                    image.in_pages.add(thepage)

        # check if blank_style is set to 1
        # if so, just return title of image
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                return " %s " % title
        except template.VariableDoesNotExist:
            pass
                    
        # return image
        if image.description:
            title = 'title="%s"' % image.description
        else:
            title = ""
        if image.title:
            alt = 'alt="%s"' % image.title
        else:
            alt = ""

        if self.max_width and self.max_width < width:
            reduce_ratio=self.max_width/float(width)
            width=self.max_width
            height=int(reduce_ratio*height)

        if self.float_direction:
            imageclass=self.float_direction
        else:
            imageclass="displayed"

        #link_url = image.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, image.get_absolute_url())
        return '<a id="%s" class="anchor"></a><a href="%s" %s><img class="%s" src="%s" %s width ="%s" height="%s" /></a>' % \
            (image.anchor(),link_url, 
             title, imageclass, imagefile.url,
             alt, int(width), int(height))

    
@register.tag
def image(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    image_code = bits[1]
    if len(bits) > 2:
        try:
            max_width=int(bits[2])
        except:
            max_width=0
    else:
        max_width=0
    if len(bits) > 3:
        float_direction=bits[3]
        if not (float_direction[0] == float_direction[-1] and float_direction[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's third argument should be in quotes" % bits[0]
        float_direction = float_direction[1:-1] 
    else:
        float_direction = ""

    return ImageNode(image_code, max_width, float_direction)



class ProcessMiTagsNode(template.Node):
    def __init__(self, the_text_var):
        self.the_text_var=template.Variable(the_text_var)
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
    the_text_var = bits[1]
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


def GeogebraWeb_link(context, applet, width, height):

    html_string=""
    geogebra_javascript_included=context.get('geogebra_javascript_included',False)
    if not geogebra_javascript_included:
        context['geogebra_javascript_included']=True
        html_string+='<script type="text/javascript" language="javascript" src="http://www.geogebra.org/web/4.2/web/web.nocache.js"></script>'

    html_string += '<div class="applet"><article class="geogebraweb" data-param-width="%s" data-param-height="%s" data-param-id="%s" data-param-showResetIcon="false" data-param-enableLabelDrags="false" data-param-showMenuBar="false" data-param-showToolBar="false" data-param-showAlgebraInput="false" data-param-useBrowserForJS="true" data-param-ggbbase64="%s"></article></div>' % \
        (width, height, applet.code, applet.encoded_content)

    return html_string


def Geogebra_link(context, applet, width, height):
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
        html_string = '%s</applet></div>' % html_string

    html_string = '%s%s' % (html_string, return_print_image_string(applet))
    return html_string



def LiveGraphics3D_link(context, applet, width, height):
    html_string='<div class="applet"><object class="liveGraphics3D" type="application/x-java-applet" height="%s" width="%s"><param name="code" value="Live.class" /> <param name="archive" value="live.jar" /><param name="codebase" value="%sjar/" />' % \
        (height, width, context["STATIC_URL"])

    html_string='%s%s' % (html_string, return_applet_parameter_string(applet))
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
    html_string = '%s%s</object></div>%s' % (html_string, return_applet_error_string(applet), return_print_image_string(applet))

    return html_string

def DoubleLiveGraphics3D_link(context, applet, width, height):

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
    def __init__(self, applet_code, width, height,caption,boxed):
        self.applet_code_var=template.Variable("%s.code" % applet_code)
        self.applet_code_string = applet_code
        self.width=width
        self.height=height
        self.caption=caption
        self.boxed=boxed
    def render(self, context):
        # first test if applet_code_var is a variable
        # if so, applet_code will be the resolved variable
        # otherwise, applet will be applet_code_string
        try:
            applet_code=self.applet_code_var.resolve(context)
        except template.VariableDoesNotExist:
            applet_code=self.applet_code_string
        # next, test if applet with applet_code exists
        try:
            applet=Applet.objects.get(code=applet_code)
        # if applet does not exist
        # return tag to applet code anyway
        except ObjectDoesNotExist:
            return '<p>[Broken applet]</p>'
           #return '<applet archive="/%s" class="broken"></applet>' % applet_code

        # set width and height from tag parameters, if exist
        # else get defaults from applet, if exist
        # else get defaults from applettype, if exist
        # use default_size for any values not found
        default_size = 500
        if self.width:
            width=self.width
        else:
            try:
                width=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH").value
            except ObjectDoesNotExist:
                width=0
        if width==0:
            try:
                width=applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_WIDTH").default_value
            except ObjectDoesNotExist:
                width=default_size

        if self.height:
            height=self.height
        else:
            try:
                height=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT").value
            except ObjectDoesNotExist:
                height=0

        if height==0:
            try:
                height=applet.applet_type.valid_parameters.get(parameter_name ="DEFAULT_HEIGHT").default_value
            except ObjectDoesNotExist:
                height=default_size

        if self.caption:
            caption = self.caption
        else:
            try:
                caption = template.Template("{% load mi_tags %}"+applet.default_inline_caption).render(context)
            except:
                caption = applet.default_inline_caption

        # check to see if the variable process_applet_entries==1
        # if so, add entry to database
        try:
            process_applet_entries = template.Variable("process_applet_entries").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_applet_entries == 1:
                # get page object, 
                try:
                    thepage = template.Variable("thepage").resolve(context)
                # if applet wasn't in a page, just pass
                except template.VariableDoesNotExist:
                    pass
                else:
                    # add page to in_pages of applet
                    applet.in_pages.add(thepage)

        # check if blank_style is set to 1
        # if so, just return title, and caption if "boxed"
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                if self.boxed:
                    return " %s %s " % (applet.title, caption)
                else:
                    return " %s " % applet.title
        except template.VariableDoesNotExist:
            pass

            
        # html for applet inclusion
        # add html for applet embedding based on applet_type
        if applet.applet_type.code == "LiveGraphics3D":
            applet_link = LiveGraphics3D_link(context, applet, width, height)
        elif applet.applet_type.code == "DoubleLiveGraphics3D":
           applet_link = DoubleLiveGraphics3D_link(context, applet, width, height)
        elif applet.applet_type.code == "Geogebra":
           applet_link = Geogebra_link(context, applet, width, height)
        elif applet.applet_type.code == "GeogebraWeb":
           applet_link = GeogebraWeb_link(context, applet, width, height)
        else:
            # if applet type for which haven't yet coded a link
            # return broken applet text
            return '<p>[Broken applet]</p>'

            
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


        #link_url = applet.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, applet.get_absolute_url())

        return '%s<p><i>%s.</i> %s</p><p><a href="%s" %s class="applet">More information about applet.</a> %s</p></section>' % \
            (html_string, applet.title, caption, link_url, title, video_links)


def applet_sub(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    applet_code = bits[1]
    if len(bits) > 2:
        try:
            width = float(bits[2])
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag's second argument (width) should be a number" % (bits[0],bits[2])
    else:
        width=0
    if len(bits) > 3:
        try:
            height = float(bits[3])
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag's third argument (width) should be a number" % (bits[0],bits[3])
    else:
        height=0
    if len(bits) > 4:
        caption = bits[4]
        if not (caption[0] == caption[-1] and caption[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's fourth argument should be in quotes" % bits[0]
        caption = caption[1:-1] 
    else:
        caption = ""
  
    return (applet_code, width, height,caption)

@register.tag
def applet(parser, token):
# applet tag
# syntax: {% applet applet_code [width] [height] [caption] %}
    (applet_code, width, height,caption)=applet_sub(parser, token)
    return AppletNode(applet_code, width, height,caption,0)


@register.tag
def boxedapplet(parser, token):
# boxedapplet tag
# syntax: {% boxedapplet applet_code [width] [height] [caption] %}
    (applet_code, width, height,caption)=applet_sub(parser, token)
    return AppletNode(applet_code, width, height,caption,1)

class AppletLinkNode(template.Node):
    def __init__(self, applet_code, extended_mode, nodelist):
        self.applet_code_var=template.Variable("%s.code" % applet_code)
        self.applet_code_string = applet_code
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

        link_text = self.nodelist.render(context)

        # first test if applet_code_var is a variable
        # if so, applet_code will be the resolved variable
        # otherwise, applet will be applet_code_string
        try:
            applet_code=self.applet_code_var.resolve(context)
        except template.VariableDoesNotExist:
            applet_code=self.applet_code_string
        # next, test if applet with applet_code exists
        try:
            applet=Applet.objects.get(code=applet_code)
        # if applet does not exist
        # return tag to applet code anyway
        except ObjectDoesNotExist:
            if(blank_style):
                return " %s BRKNAPPLNK" % link_text
            else:
                return '<a href="applet/%s" class="broken">%s</a>' % (self.applet_code_string, link_text)
            
        link_title="%s. %s" % (applet.annotated_title(),applet.description)
        
        #link_url = applet.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, applet.get_absolute_url())

        if not self.extended_mode:
            return '<a href="%s" class="applet" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if applet.thumbnail:
            if self.extended_mode == '2':
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
            
        if self.extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="applet" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        html_text= '%s %s' % (html_text,  applet.feature_list())
        
        if applet.description:
            html_text= '%s<br/>%s' % (html_text, applet.description)
            

        if self.extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if applet.author_list_full():
               html_text= '%sby %s' % (html_text, applet.author_list_full())
           html_text = '%s on %s' % (html_text, applet.publish_date)

        if self.extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def appletlink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    applet_code = bits[1]
    if len(bits) > 2:
        extended_mode = bits[2]
    else:
        extended_mode=None

    nodelist = parser.parse(('endappletlink',))
    parser.delete_first_token()

    return AppletLinkNode(applet_code, extended_mode, nodelist)




def youtube_link(context, video, width, height):
    
    try:
        youtubecode=video.videoparameter_set.get(parameter__parameter_name ="youtubecode").value
    except ObjectDoesNotExist:
        return "[Broken video]"

    html_string='<div class="video"><iframe width="%s" height="%s" src="http://www.youtube-nocookie.com/embed/%s?rel=0" frameborder="0" allowfullscreen></iframe></div>' % \
        (width, height, youtubecode )

    return html_string



class VideoNode(template.Node):
    def __init__(self, video_code, width, height,caption,boxed):
        self.video_code_var=template.Variable("%s.code" % video_code)
        self.video_code_string = video_code
        self.width=width
        self.height=height
        self.caption=caption
        self.boxed=boxed
    def render(self, context):
        # first test if video_code_var is a variable
        # if so, video_code will be the resolved variable
        # otherwise, video will be video_code_string
        try:
            video_code=self.video_code_var.resolve(context)
        except template.VariableDoesNotExist:
            video_code=self.video_code_string
        # next, test if video with video_code exists
        try:
            video=Video.objects.get(code=video_code)
        # if video does not exist
        # return tag to video code anyway
        except ObjectDoesNotExist:
            return '<p>[Broken video]</p>'
           #return '<video archive="/%s" class="broken"></video>' % video_code

        # set width and height from tag parameters, if exist
        # else get defaults from video, if exist
        # else get defaults from videotype, if exist
        # use default_size for any values not found
        default_size = 500
        if self.width:
            width=self.width
        else:
            try:
                width=video.videoparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH").value
            except ObjectDoesNotExist:
                width=0
        if width==0:
            try:
                width=video.video_type.valid_parameters.get(parameter_name ="DEFAULT_WIDTH").default_value
            except ObjectDoesNotExist:
                width=default_size

        if self.height:
            height=self.height
        else:
            try:
                height=video.videoparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT").value
            except ObjectDoesNotExist:
                height=0

        if height==0:
            try:
                height=video.video_type.valid_parameters.get(parameter_name ="DEFAULT_HEIGHT").default_value
            except ObjectDoesNotExist:
                height=default_size

        if self.caption:
            caption = self.caption
        else:
            try:
                caption = template.Template("{% load mi_tags %}"+video.default_inline_caption).render(context)
            except:
                caption = video.default_inline_caption

        # check to see if the variable process_video_entries==1
        # if so, add entry to database
        try:
            process_video_entries = template.Variable("process_video_entries").resolve(context)
        except template.VariableDoesNotExist:
            pass
        else:
            if process_video_entries == 1:
                # get page object, 
                try:
                    thepage = template.Variable("thepage").resolve(context)
                # if video wasn't in a page, just pass
                except template.VariableDoesNotExist:
                    pass
                else:
                    # add page to in_pages of video
                    video.in_pages.add(thepage)

        # check if blank_style is set to 1
        # if so, just return title, and caption if "boxed"
        try:
            blank_style = template.Variable("blank_style").resolve(context)
            if(blank_style):
                if self.boxed:
                    return " %s %s " % (video.title, caption)
                else:
                    return " %s " % video.title
        except template.VariableDoesNotExist:
            pass

            
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


        #link_url = video.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, video.get_absolute_url())

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
    video_code = bits[1]
    if len(bits) > 2:
        try:
            width = float(bits[2])
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag's second argument (width) should be a number" % (bits[0],bits[2])
    else:
        width=0
    if len(bits) > 3:
        try:
            height = float(bits[3])
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag's third argument (width) should be a number" % (bits[0],bits[3])
    else:
        height=0
    if len(bits) > 4:
        caption = bits[4]
        if not (caption[0] == caption[-1] and caption[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's fourth argument should be in quotes" % bits[0]
        caption = caption[1:-1] 
    else:
        caption = ""
  
    return (video_code, width, height,caption)

@register.tag
def video(parser, token):
# video tag
# syntax: {% video video_code [width] [height] [caption] %}
    (video_code, width, height,caption)=video_sub(parser, token)
    return VideoNode(video_code, width, height,caption,0)


@register.tag
def boxedvideo(parser, token):
# boxedvideo tag
# syntax: {% boxedvideo video_code [width] [height] [caption] %}
    (video_code, width, height,caption)=video_sub(parser, token)
    return VideoNode(video_code, width, height,caption,1)

class VideoLinkNode(template.Node):
    def __init__(self, video_code, extended_mode, nodelist):
        self.video_code_var=template.Variable("%s.code" % video_code)
        self.video_code_string = video_code
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

        link_text = self.nodelist.render(context)

        # first test if video_code_var is a variable
        # if so, video_code will be the resolved variable
        # otherwise, video will be video_code_string
        try:
            video_code=self.video_code_var.resolve(context)
        except template.VariableDoesNotExist:
            video_code=self.video_code_string
        # next, test if video with video_code exists
        try:
            video=Video.objects.get(code=video_code)
        # if video does not exist
        # return tag to video code anyway
        except ObjectDoesNotExist:
            if(blank_style):
                return " %s BRKNVIDEOLNK" % link_text
            else:
                return '<a href="video/%s" class="broken">%s</a>' % (self.video_code_string, link_text)
            
        link_title="%s. %s" % (video.annotated_title(),video.description)
        
        #link_url = video.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, video.get_absolute_url())

        if not self.extended_mode:
            return '<a href="%s" class="video" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if video.thumbnail:
            if self.extended_mode == '2':
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
            
        if self.extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="video" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        if video.description:
            html_text= '%s<br/>%s' % (html_text, video.description)
            

        if self.extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if video.author_list_full():
               html_text= '%sby %s' % (html_text, video.author_list_full())
           html_text = '%s on %s' % (html_text, video.publish_date)

        if self.extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def videolink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    video_code = bits[1]
    if len(bits) > 2:
        extended_mode = bits[2]
    else:
        extended_mode=None

    nodelist = parser.parse(('endvideolink',))
    parser.delete_first_token()

    return VideoLinkNode(video_code, extended_mode, nodelist)




class ImageLinkNode(template.Node):
    def __init__(self, image_code, extended_mode, nodelist):
        self.image_code_var=template.Variable("%s.code" % image_code)
        self.image_code_string = image_code
        self.extended_mode = extended_mode
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

        link_text = self.nodelist.render(context)

        # first test if image_code_var is a variable
        # if so, image_code will be the resolved variable
        # otherwise, image will be image_code_string
        try:
            image_code=self.image_code_var.resolve(context)
        except template.VariableDoesNotExist:
            image_code=self.image_code_string
        # next, test if image with image_code exists
        try:
            image=Image.objects.get(code=image_code)
        # if image does not exist
        # return tag to image code anyway
        except ObjectDoesNotExist:
            if(blank_style):
                return " %s BRKNIMGLNK" % link_text
            else:
                return '<a href="image/%s" class="broken">%s</a>' % (self.image_code_string, link_text)
            
        link_title="%s. %s" % (image.annotated_title(),image.description)
        
        #link_url = image.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, image.get_absolute_url())

        if not self.extended_mode:
            return '<a href="%s" class="image" title="%s">%s</a>' \
                % (link_url, link_title, link_text)
    
        # in extended mode, include thumbnail, if exists
        html_text = '<div class="ym-clearfix">'
        if image.thumbnail:
            if self.extended_mode == '2':
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
            
        if self.extended_mode != '2':
            html_text += '<div style="width: 75%; float: left;">' 

        html_text= '%s<a href="%s" class="image" title="%s">%s</a>' \
            % (html_text, link_url, link_title, link_text)
        
        if image.description:
            html_text= '%s<br/>%s' % (html_text, image.description)
            

        if self.extended_mode == '3':
           html_text= '%s<br/>Added ' % html_text
           if image.author_list_full():
               html_text= '%sby %s' % (html_text, image.author_list_full())
           html_text = '%s on %s' % (html_text, image.publish_date)

        if self.extended_mode != '2':
            html_text = '%s</div>' % html_text

        html_text = '%s</div>' % html_text

        return html_text
    

@register.tag
def imagelink(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    image_code = bits[1]
    if len(bits) > 2:
        extended_mode = bits[2]
    else:
        extended_mode=None

    nodelist = parser.parse(('endimagelink',))
    parser.delete_first_token()

    return ImageLinkNode(image_code, extended_mode, nodelist)


class AssessmentLinkNode(template.Node):
    def __init__(self, the_assessment, nodelist):
        self.the_assessment = the_assessment
        self.nodelist=nodelist
    def render(self, context):
        # check if blank_style is set to 1
        blank_style=0
        try:
            blank_style = template.Variable("blank_style").resolve(context)
        except template.VariableDoesNotExist:
            pass

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
        
        #link_url = the_assessment.get_absolute_url()
        link_url = 'http://%s%s' % (Site.objects.get_current().domain, the_assessment.get_absolute_url())

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

