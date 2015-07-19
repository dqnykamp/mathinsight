from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from mithreads.utils import HTMLOutliner, return_section_insert_html, return_section_delete_html, return_section_edit_html, return_content_insert_html
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType

class ActiveThreadManager(models.Manager):
    def get_queryset(self):
        return super(ActiveThreadManager, self).get_queryset() \
            .filter(active=True)

class Thread(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    sort_order = models.FloatField(default=0)
    numbered = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    activethreads = ActiveThreadManager()

    def __str__(self):
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


    def render_html_string(self, student=None, course=None, edit=False):

        html_string=""
        if edit:
            html_string = '%s <div style="margin-top: 2em;" id="top_section_insert">%s</div>' \
                % (html_string, return_section_insert_html("top", self.id))
            
        outliner=HTMLOutliner(numbered=self.numbered, default_css_class="threadsections")
        
        for thread_section in self.thread_sections.all():
            html_string = html_string + \
                thread_section.return_html_transition_string\
                (outliner, student, course, edit)

        html_string = html_string + outliner.return_html_close_string()


        return mark_safe(html_string)

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

        return new_thread

    def save_to_course(self, course):
        sort_order = 0
        for thread_section in self.thread_sections.all():
            sort_order = thread_section.save_to_course(course, sort_order)
        return sort_order
    
    def render_save_changes_course_button_html_string(self, course):
        click_command = "Dajaxice.midocs.save_thread_changes_to_course"\
            + "(Dajax.process,{'thread_code': '%s',  })" \
            % (self.code, )
        
        html_string =  \
            '<input type="button" value="Save changes to course: %s" onclick="%s;">' \
            % (course, click_command)
        html_string += '<div class="info" id="message_save_changes_%s"></div>' \
            % (self.code)
        
        return html_string


class ThreadSection(models.Model):
    name =  models.CharField(max_length=100, db_index=True)
    code = models.SlugField(max_length=50)
    thread = models.ForeignKey(Thread, related_name = "thread_sections")
    sort_order = models.FloatField(default=0)
    level = models.IntegerField(default=1)

    def __str__(self):
        return "%s (%s/%s)" % (self.code,self.thread, self.name)
    __str__.admin_order_field = 'code'


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
        for threadcontent in original_thread_section.thread_contents.all():
            threadcontent.save_to_new_thread_section(new_thread_section)
        
    def save_to_course(self, course, sort_order):

        for thread_content in self.thread_contents.all():
            sort_order += 1
            try:
                # see if content exists
                ctc = course.coursethread_contents.get\
                    (thread_content=thread_content)
                ctc.sort_order=sort_order
                ctc.save()

            except ObjectDoesNotExist:
                # if not already in course, add
                course.coursethread_content.create\
                    (thread_content=thread_content, sort_order=sort_order)

        return sort_order


    def first_content_title(self):
        try:
            the_content = self.thread_contents.all()[0]
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
            if section.thread_contents.all():
                return section
        return None

    def find_previous_with_content(self):
        thread_section_list = list(self.thread.thread_sections.all())
        this_section_index = thread_section_list.index(self)
        if this_section_index > 0:
            for section in thread_section_list[this_section_index-1::-1]:
                if section.thread_contents.all():
                    return section
        return None


    def find_children(self):
        # find all child sections
        next_section=self
        children = []
        while True:
            next_section = next_section.find_next_section()
            if not next_section:
                break
            if next_section.level <= self.level:
                break
            children.append(next_section)
        return children


    def get_click_command_base(self):
        return "Dajaxice.midocs.%s" + "(Dajax.process,{'section_code': '%s', 'thread_code': '%s'})" % (self.code, self.thread.code)



    def content_insert_below_section_html(self):
        click_command_base = self.get_click_command_base()
        click_command = click_command_base % 'insert_content_form_below_section'
        return  '<a onclick="%s;" class="edit_link">[insert content]</a>' \
                % (click_command)

    def return_html_transition_string(self, outliner, student=None, 
                                      course=None, edit=False):

        html_string=outliner.return_html_transition_string(self.level)
            
        html_string += '<div id="thread_section_%s">%s</div>' \
            % (self.code, self.return_html_innerstring(edit))

        # now add content links
        html_string += '\n<ul class="threadcontent" id = "threadcontent_%s">\n' % self.code
        html_string += self.return_content_html_string(student, course, edit)
        html_string += "</ul>\n"

        if edit:
            html_string += return_content_insert_html(self.id)
            html_string += return_section_insert_html(self.id)
        return html_string

    def return_content_html_string(self, student=None, course=None, edit=False):
        html_string=''
        for content in self.thread_contents.all():
            html_string += content.return_html_string(student, course, edit)
        return html_string

    def return_html_innerstring(self, edit=False):
        
        html_string = '<a id="%s" class="anchor"></a>%s\n' \
            % ( self.code, self.name)

        if edit:
            html_string = "%s (code: %s)" % (html_string, self.code)

            click_command_base = self.get_click_command_base()

            if self.level > 1:
                click_command = "post_edit_section(%s, 'dec_level')" % self.id
                html_string = '%s <a onclick="%s;" class="edit_link">[left]</a>' \
                    % (html_string, click_command)
            click_command = "post_edit_section(%s, 'inc_level')" % self.id
            html_string = '%s <a onclick="%s;" class="edit_link">[right]</a>' \
                % (html_string, click_command)
            if self.find_previous_section():
                click_command = "post_edit_section(%s, 'move_up')" % self.id
                html_string = '%s <a onclick="%s;" class="edit_link">[up]</a>' \
                    % (html_string, click_command)
            if self.find_next_section():
                click_command = "post_edit_section(%s, 'move_down')" % self.id
                html_string = '%s <a onclick="%s;" class="edit_link">[down]</a>' \
                    % (html_string, click_command)

            (delete_link, delete_form) = return_section_delete_html(self)
            html_string += delete_link
            html_string += return_section_edit_html(self)
            html_string += delete_form

        return html_string

    def return_html_transition_edit_string(self, outliner):
        return self.return_html_transition_string(outliner, edit=True)
        
class ThreadContent(models.Model):
    section = models.ForeignKey(ThreadSection)
    content_type = models.ForeignKey(ContentType, default=19, related_name="threadcontent_original")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    sort_order = models.FloatField(default=0)
    substitute_title = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return str(self.content_object)

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
                return str(self.content_object)


    def return_link(self):
        try:
            if self.substitute_title:
                return self.content_object.return_link(link_text=self.substitute_title)
            else:
                return self.content_object.return_link() 
        except:
            return self.get_title()
        

    # def save(self, *args, **kwargs):
    #     super(ThreadContent, self).save(*args, **kwargs) 
    #     # try running update_links on object, if such a function exists
    #     try:
    #         self.content_object.update_links()
    #     except:
    #         pass

    def validate_unique(self, exclude=None):
        # check to make sure that the same content object 
        # is not in the same thread twice
        if 'section' not in exclude:
            if ThreadContent.objects.exclude(id = self.id)\
                    .filter(content_type=self.content_type, \
                                object_id = self.object_id,\
                                section__thread=self.section.thread).exists():
                raise ValidationError("Duplicate entries of %s in thread %s" \
                    % (self.content_object, self.section.thread))



    def get_thread(self):
        return self.section.thread

    def find_next_in_section(self):
        content_list = list(self.section.thread_contents.all())
        this_index = content_list.index(self)
        try:
            return content_list[this_index+1]
        except:
            return None
  
    def find_previous_in_section(self):
        content_list = list(self.section.thread_contents.all())
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
            return next_section.thread_contents.all()[0]
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
            return previous_section.thread_contents.reverse()[0]
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


    def return_html_string(self, student=None, course=None, edit=False):
        if self.content_object or edit:
            return "<li><div id='thread_content_%s'>%s</div></li>\n" \
                % (self.id, self.return_html_innerstring(student, course, edit))
            
        else: 
            return ""

    def return_html_innerstring(self, student=None, course=None, edit=False):
        html_string = self.return_link()


        if not edit and course:
            try:
                ctc = self.coursethread_content.get(course=course)
                html_string += " " + ctc.complete_skip_button_html\
                    (student=student, full_html=True)
            except:
                pass

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

