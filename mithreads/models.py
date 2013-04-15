from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from mithreads.utils import HTMLOutliner


class Thread(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    sort_order = models.SmallIntegerField(default=0)
    numbered = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['sort_order','id']

    @models.permalink
    def get_absolute_url(self):
        return('mithreads-thread', (), {'thread_code': self.code})

    def listtag(self):
        if self.numbered:
            return "ol"
        else:
            return "ul"

    def top_section_insert_html(self):
        click_command = "Dajaxice.midocs.insert_section_form_top" + "(Dajax.process,{'thread_code': '%s'})" % (self.code)
        html_string = '<a onclick="%s;" class="edit_link"> [insert section]</a>' \
                % (click_command)
        return html_string

    def render_html_string(self, edit=False):
        html_string=""
        if edit:
            html_string = '%s <p style="margin-top: 2em;"><span id="top_section_insert">%s</span></p>' \
                % (html_string, self.top_section_insert_html())
            
        outliner=HTMLOutliner(numbered=self.numbered, default_css_class="threadsections")
        
        for thread_section in self.thread_sections.all():
            html_string = html_string + \
                thread_section.return_html_transition_string(outliner,edit)

        html_string = html_string + outliner.return_html_close_string()
        return html_string

    def render_html_edit_string(self):
        return self.render_html_string(edit=True)

    def save_as(self, new_code, new_name):
        original_code = self.code

        new_thread=self
        new_thread.pk=None
        new_thread.code = new_code
        new_thread.name = new_name
        new_thread.save()

        original_thread=Thread.objects.get(code=original_code)
        
        # copy all thread sections
        for thread_section in original_thread.thread_sections.all():
            thread_section.save_to_new_thread(new_thread)

        
    
class ThreadSection(models.Model):
    name =  models.CharField(max_length=100, db_index=True)
    code = models.SlugField(max_length=50)
    thread = models.ForeignKey(Thread, related_name = "thread_sections")
    sort_order = models.FloatField(default=0)
    level = models.IntegerField(default=1)

    def __unicode__(self):
        return "%s (%s/%s)" % (self.code,self.thread, self.name)
    __unicode__.admin_order_field = 'code'


    class Meta:
        unique_together = (('code', 'thread'),)
        ordering = ['sort_order','id']
    

    def save_to_new_thread(self, thread):
        original_thread_section_pk = self.pk

        new_thread_section = self
        new_thread_section.pk=None
        new_thread_section.thread = thread
        new_thread_section.save()
        
        original_thread_section=ThreadSection.objects.get(pk=original_thread_section_pk)
        

        # copy thread content
        for threadcontent in original_thread_section.threadcontent_set.all():
            threadcontent.save_to_new_thread_section(new_thread_section)
        
    

    def first_content_title(self):
        try:
            the_content = self.threadcontent_set.all()[0]
            if the_content:
                return the_content.get_title()

        except:
            pass
    
        return ""

    def find_next_section(self):
        thread_section_list = list(self.thread.thread_sections.all())
        this_section_index = thread_section_list.index(self)
        try:
            return thread_section_list[this_section_index+1]
        except:
            return None

    def find_previous_section(self):
        thread_section_list = list(self.thread.thread_sections.all())
        this_section_index = thread_section_list.index(self)
        if this_section_index > 0:
            return thread_section_list[this_section_index-1]
        else:
            return None

    def find_next_with_content(self):
        thread_section_list = list(self.thread.thread_sections.all())
        this_section_index = thread_section_list.index(self)
        for section in thread_section_list[this_section_index+1:]:
            if section.threadcontent_set.all():
                return section
        return None

    def find_previous_with_content(self):
        thread_section_list = list(self.thread.thread_sections.all())
        this_section_index = thread_section_list.index(self)
        if this_section_index > 0:
            for section in thread_section_list[this_section_index-1::-1]:
                if section.threadcontent_set.all():
                    return section
        return None

    def get_click_command_base(self):
        return "Dajaxice.midocs.%s" + "(Dajax.process,{'section_code': '%s', 'thread_code': '%s'})" % (self.code, self.thread.code)


    def section_insert_below_html(self):
        click_command_base = self.get_click_command_base()
        click_command = click_command_base % 'insert_section_form_below'
        return '<a onclick="%s;" class="edit_link">[insert section]</a>' \
                % (click_command)

    def content_insert_below_section_html(self):
        click_command_base = self.get_click_command_base()
        click_command = click_command_base % 'insert_content_form_below_section'
        return  '<a onclick="%s;" class="edit_link">[insert content]</a>' \
                % (click_command)

    def return_html_transition_string(self, outliner, edit=False):

        html_string=outliner.return_html_transition_string(self.level)
            
        html_string += '<div id="thread_section_%s">%s</div>' \
            % (self.code, self.return_html_innerstring(edit))

        if edit:
            html_string = '%s <div id="%s_section_info_box"></div>' \
                % (html_string, self.code)
                
        # now add content links
        html_string += '\n<ul class="threadcontent" id = "threadcontent_%s">\n' % self.code
        html_string += self.return_content_html_string(edit)
        html_string += "</ul>\n"

        if edit:
            html_string = '%s <div id="%s_content_insert_below_section">%s</div>' \
                % (html_string, self.code, self.content_insert_below_section_html())

            html_string = '%s <div id="%s_section_insert_below">%s</div>' \
                % (html_string, self.code, self.section_insert_below_html())
        return html_string

    def return_content_html_string(self, edit=False):
        html_string=''
        for content in self.threadcontent_set.all():
            html_string += content.return_html_string(edit)
        return html_string

    def return_html_innerstring(self, edit=False):
        
        html_string = '<a id="%s" class="anchor"></a>%s\n' \
            % ( self.code, self.name)

        if edit:
            html_string = "%s (code: %s)" % (html_string, self.code)

            click_command_base = self.get_click_command_base()

            if self.level > 1:
                click_command = click_command_base % 'dec_section_level'
                html_string = '%s <a onclick="%s;" class="edit_link">[left]</a>' \
                    % (html_string, click_command)
            click_command = click_command_base % 'inc_section_level'
            html_string = '%s <a onclick="%s;" class="edit_link">[right]</a>' \
                % (html_string, click_command)
            if self.find_previous_section():
                click_command = click_command_base % 'move_section_up'
                html_string = '%s <a onclick="%s;" class="edit_link">[up]</a>' \
                    % (html_string, click_command)
            if self.find_next_section():
                click_command = click_command_base % 'move_section_down'
                html_string = '%s <a onclick="%s;" class="edit_link">[down]</a>' \
                    % (html_string, click_command)
            click_command = click_command_base % 'delete_section'
            html_string = '%s <a onclick="%s;" class="edit_link">[delete]</a>' \
                % (html_string, click_command)
            click_command = click_command_base % 'edit_section'
            html_string = '%s <a onclick="%s;" class="edit_link">[edit]</a>' \
                % (html_string, click_command)
                
        return html_string

    def return_html_transition_edit_string(self, outliner):
        return self.return_html_transition_string(outliner, edit=True)
        
class ThreadContent(models.Model):
    section = models.ForeignKey(ThreadSection)
    content_type = models.ForeignKey(ContentType, default=19)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    sort_order = models.FloatField(default=0)
    substitute_title = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return unicode(self.content_object)

    class Meta:
        ordering = ['sort_order']

    def save_to_new_thread_section(self, thread_section):
        new_threadcontent = self
        new_threadcontent.pk = None
        new_threadcontent.section = thread_section
        new_threadcontent.save()


    def get_title(self):
        if(self.substitute_title):
            return self.substitute_title
        else:
            try:
                return self.content_object.get_title()
            except:
                return unicode(self.content_object)


    def return_link(self):
        try:
            if self.substitute_title:
                return self.content_object.return_link(link_text=self.substitute_title)
            else:
                return self.content_object.return_link() 
        except:
            return self.get_title()
        

    def save(self, *args, **kwargs):
        super(ThreadContent, self).save(*args, **kwargs) 
        # try running update_links on object, if such a function exists
        try:
            self.content_object.update_links()
        except:
            pass


    def get_thread(self):
        return self.section.thread

    def find_next_in_section(self):
        content_list = list(self.section.threadcontent_set.all())
        this_index = content_list.index(self)
        try:
            return content_list[this_index+1]
        except:
            return None
  
    def find_previous_in_section(self):
        content_list = list(self.section.threadcontent_set.all())
        this_index = content_list.index(self)
        if this_index >0:
            return content_list[this_index-1]
        else:
            return None
    
    def find_next(self):
        # find next in section, if exists
        the_next=self.find_next_in_section()
        if the_next:
            return the_next

        # otherwise, find next section with content
        next_section = self.section.find_next_with_content()
        if next_section:
            return next_section.threadcontent_set.all()[0]
        # if can't find anything, return null
        return None

    def find_previous(self):
        # find previous in section, if exists
        the_previous=self.find_previous_in_section()
        if the_previous:
            return the_previous
        # otherwise, find previous section with content
        previous_section = self.section.find_previous_with_content()
        if previous_section:
            return previous_section.threadcontent_set.reverse()[0]
        # if can't find anything, return null
        return None

    def get_click_command_base(self):
        return "Dajaxice.midocs.%s" + "(Dajax.process,{'threadcontent_id': '%s'})" % (self.id)

    def content_insert_below_content_html(self):
        # click_command_base = self.get_click_command_base()
        # click_command = click_command_base % 'insert_content_form_below_content'
        # return '<a onclick="%s;" class="edit_link">[insert content]</a>' \
        #         % (click_command)
        return ''


    def return_html_string(self, edit=False):
        if self.content_object or edit:
            return "<li><div id='thread_content_%s'>%s</div></li>\n" \
                % (self.id, self.return_html_innerstring(edit))
            
        else: 
            return ""

    def return_html_innerstring(self, edit=False):
        html_string = self.return_link()
                    
        if edit:
            click_command_base = self.get_click_command_base()
            if self.find_previous_in_section() or \
                    self.section.find_previous_section():
                click_command = click_command_base % 'move_content_up'
                html_string = '%s <a onclick="%s;" class="edit_link">[up]</a>' \
                    % (html_string, click_command)

            if self.find_next_in_section() or \
                    self.section.find_next_section():
                click_command = click_command_base % 'move_content_down'
                html_string = '%s <a onclick="%s;" class="edit_link">[down]</a>' \
                    % (html_string, click_command)

            click_command = click_command_base % 'delete_content'
            html_string = '%s <a onclick="%s;" class="edit_link">[delete]</a>' \
                % (html_string, click_command)

            click_command = click_command_base % 'edit_content'
            html_string = '%s <a onclick="%s;" class="edit_link">[edit]</a>' \
                % (html_string, click_command)

            html_string = html_string + "<br/>"

            html_string = '%s <div id="%s_content_insert_below_content">%s</div>' \
                % (html_string, self.id, self.content_insert_below_content_html())


        return html_string

