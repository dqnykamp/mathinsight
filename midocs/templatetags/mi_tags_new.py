from django import template
from mathinsight.midocs.models import Notation, Page, IndexEntry, IndexType, Image, Applet
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import re

register=template.Library()

class InternalLinkNode(template.Node):
    def __init__(self, link_code, link_anchor, nodelist):
        self.link_code_var=template.Variable("%s.code" % link_code)
        self.link_code_string = link_code
        self.link_anchor_var=template.Variable(link_anchor)
        self.link_anchor_string=link_anchor
        self.nodelist=nodelist
    def render(self, context):
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
        else:
            # if page exist, set link_title to description
            link_title=thepage.description
            link_class = thepage.level
            # set link_url to match the page specified by link_code
            try:
                link_url = reverse('mi-page', kwargs={'page_code': link_code})
            # since page exists, shouldn't get no match
            # but test for it anyway
            except NoReverseMatch:
                link_url = "/%s" % link_code
                link_class = "broken"
        # test if link anchor is variable, otherwise use string
        try:
            link_anchor=self.link_anchor_var.resolve(context)
        except template.VariableDoesNotExist:
            link_anchor=self.link_anchor_string
        if link_anchor:
            link_url = "%s#%s" % (link_url, link_anchor)

        # process nodelist, as that will be link text
        link_text = self.nodelist.render(context)

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

    nodelist = parser.parse(('endintlink',))
    parser.delete_first_token()

    return InternalLinkNode(link_code, link_anchor, nodelist)


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
                    page = template.Variable("page").resolve(context)
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
                        
                # check if index entry is already in database
                try:
                    index_entry = IndexEntry.objects.get(page=page, index_type=index_type, 
                                                         indexed_phrase=self.indexed_phrase,
                                                         indexed_subphrase=self.indexed_subphrase)
                except ObjectDoesNotExist:
                    # add index entry
                    index_entry = IndexEntry.objects.create(page=page, index_type=index_type, 
                                                            indexed_phrase=self.indexed_phrase,
                                                            indexed_subphrase=self.indexed_subphrase,
                                                            page_anchor=self.page_anchor)
                else:
                    # if index entry was already in the database, update page_anchor from the tag
                    index_entry.page_anchor = self.page_anchor
                    index_entry.save()
            
                


        # if page_anchor is not null, return an anchor, else return nothing
        if(self.page_anchor):
            return "<a id=%s></a>" % self.page_anchor
        else:
            return ""
 
@register.tag
def index_entry(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    indexed_phrase=bits[1]
    if not (indexed_phrase[0] == indexed_phrase[-1] and indexed_phrase[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % bits[0]
    indexed_phrase = indexed_phrase[1:-1]
    if len(bits) >2:
        indexed_subphrase=bits[2]
        if not (indexed_subphrase[0] == indexed_subphrase[-1] and indexed_subphrase[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's third argument should be in quotes" % bits[0]
        indexed_subphrase = indexed_subphrase[1:-1]
    else:
        indexed_subphrase = "";
    if len(bits)>3:
        page_anchor=bits[3]
        if not (page_anchor[0] == page_anchor[-1] and page_anchor[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's fourth argument should be in quotes" % bits[0]
        page_anchor = page_anchor[1:-1]
    else:
        page_anchor = "";
    if len(bits)>4:
        index_type=bits[4]
        if not (index_type[0] == index_type[-1] and index_type[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's fifth argument should be in quotes" % bits[0]
        index_type = index_type[1:-1]
    else:
        index_type = "";
    return IndexEntryNode(indexed_phrase, indexed_subphrase, page_anchor, index_type)


class ImageNode(template.Node):
    def __init__(self, image_name):
        self.image_name_var=template.Variable("%s.imagefile.name" % image_name)
        self.image_name_string = "%s%s" % (settings.IMAGE_UPLOAD_TO,image_name)
    def render(self, context):
        # first test if image_name_var is a variable
        # if so, image_name will be the resolved variable
        # otherwise, image will be image_name_tring
        try:
            image_name=self.image_name_var.resolve(context)
        except template.VariableDoesNotExist:
            image_name=self.image_name_string
        # next, test if image with image_name exists
        try:
            image=Image.objects.get(imagefile=image_name)
        # if image does not exist
        # return tag to image name anyway
        except ObjectDoesNotExist:
            return '<img src="/%s" class="broken" />' % image_name

        # if image exists, then get information from database
        width = image.width
        height = image.height
        alt_text = image.alt_text
        caption = image.caption

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
                    page = template.Variable("page").resolve(context)
                except template.VariableDoesNotExist:
                    pass
                else:
                    # add page to in_pages of image
                    image.in_pages.add(page)
                    
        # return image
        image_url = image.imagefile.url
        image_filename = re.sub(settings.IMAGE_UPLOAD_TO,"", image.imagefile.name)  # get rid of upload path
        viewimage_url = reverse('mi-image', kwargs={'image_name': image_filename})
        return '<a href="%s" title="%s"><img src="%s" alt="%s" width ="%s" height="%s" /></a>' % \
            (viewimage_url, caption, image_url, alt_text, 0.75*width, 0.75*height)

        # image_url = "%simage/%s" % (settings.MEDIA_URL, self.image_file)
        # return '<a href="%s" title="%s"><img src="%s" alt="%s" class="graphics" width="%s" height="%s" /></a>' \
        #     % (image_url, self.image_caption, image_url, self.image_alt_text, self.image_width*.8,
        #        self.image_height*.8)
    
@register.tag
def image(parser, token):
    try:
        tag_name, image_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return ImageNode(image_name)

def LiveGraphics3D_link(context, applet, width, height):
    html_string='<div style="height:%spx"><applet class="afterMathJax" archive="live.jar" codebase="%sjar/" code="Live.class" width="%s" height="%s">' % \
        (height, context["MEDIA_URL"], width, height)
    for app_param in applet.appletparameter_set.all():
        parameter_name = app_param.parameter.parameter_name
        if parameter_name != "DEFAULT_WIDTH" and \
                parameter_name != "DEFAULT_HEIGHT":
            html_string = '%s<param name="%s" value="%s" />' \
                % (html_string, parameter_name, app_param.value)
    if applet.applet_file:
        html_string= '%s<param name="INPUT_FILE" value="%s" />' \
            % (html_string,applet.applet_file.url)
    html_string = '%s</applet></div>' % html_string

    return html_string


class AppletNode(template.Node):
    def __init__(self, applet_name, width, height):
        self.applet_name_var=template.Variable("%s.name" % applet_name)
        self.applet_name_string = applet_name
        self.width=width
        self.height=height
    def render(self, context):
        # first test if applet_name_var is a variable
        # if so, applet_name will be the resolved variable
        # otherwise, applet will be applet_name_tring
        try:
            applet_name=self.applet_name_var.resolve(context)
        except template.VariableDoesNotExist:
            applet_name=self.applet_name_string
        # next, test if applet with applet_name exists
        try:
            applet=Applet.objects.get(name=applet_name)
        # if applet does not exist
        # return tag to applet name anyway
        except ObjectDoesNotExist:
            return '<applet archive="/%s" class="broken"></applet>' % applet_name

        # set width and height from tag parameters, if exist
        # else get defaults from applet
        # if one of width or height exists, set both equal
        # if neither exist, use default_size for both
        default_size = 500
        if self.width:
            width=self.width
        else:
            try:
                width=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_WIDTH")
            except ObjectDoesNotExist:
                width=0
        if self.height:
            height=self.height
        else:
            try:
                height=applet.appletparameter_set.get(parameter__parameter_name ="DEFAULT_HEIGHT")
            except ObjectDoesNotExist:
                height=0

        if width and not height:
            height=width
        elif height and not width:
            width=height
        elif not(width or height):
            width=default_size
            height=default_size

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
                    page = template.Variable("page").resolve(context)
                except template.VariableDoesNotExist:
                    pass
                else:
                    # add page to in_pages of applet
                    applet.in_pages.add(page)
        
        # add html for applet embedding based on applet_type
        if applet.applet_type.code == "LiveGraphics3D":
            return LiveGraphics3D_link(context, applet, width, height)

        # if applet type for which haven't yet coded a link
        # return tag anyway
        else:
            return '<applet archive="/%s" applet_type="%s" class="broken"></applet>' % (applet_name, applet.applet_type)


@register.tag
def applet(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "%r tag requires at least one arguments" % bits[0]
    applet_name = bits[1]
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
    return AppletNode(applet_name, width, height)


@register.inclusion_tag('mathinsight/thread_section_contents.html')
def thread_section_contents(thread_section, recursion, max_recursions):
    recursion += 1
    child_sections = thread_section.child_sections.all() 
    pages = thread_section.pages.all()
    if recursion < max_recursions and child_sections:
        include_children=True
    else:
        include_children=False
    return {'thread_section': thread_section,
            'child_sections': child_sections,
            'pages': pages,
            'include_children': include_children,
            'recursion': recursion,
            'max_recursions': max_recursions,
            }



  
class LineIntegralNode(template.Node):
    def __init__(self, curve_symbol, integrand):
        self.curve_symbol_var=template.Variable(curve_symbol)
        self.curve_symbol_string=curve_symbol
        self.integrand_var=template.Variable(integrand)
        self.integrand_string=integrand
    def render(self, context):
        try:
            the_curve_symbol = self.curve_symbol_var.resolve(context)
        except template.VariableDoesNotExist:
            the_curve_symbol = self.curve_symbol_string
        try:
            the_integrand = self.integrand_var.resolve(context)
        except template.VariableDoesNotExist:
            the_integrand = self.integrand_string
        try:
            the_diffsymbol=template.Variable("mi.ds_lineint_diff").resolve(context)
        except template.VariableDoesNotExist:
            the_diffsymbol = "s"
        return "\int_{%s} %s \cdot d%s" % (the_curve_symbol, the_integrand,
                                           the_diffsymbol)

@register.tag
def line_integral(parser, token):
    bits = token.split_contents()
    if len(bits) > 1:
        curve_symbol=bits[1]
    else:
        curve_symbol="mi.ds_curve"
    if len(bits) > 2:
        integrand=bits[2]
    else:
        integrand = "mi.ds_vector_field"
        
    return LineIntegralNode(curve_symbol, integrand)

