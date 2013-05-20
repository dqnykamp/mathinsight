from django.db import models, transaction
from django.conf import settings
from django.db.models import Count
from django.template.loader import render_to_string
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.contenttypes import generic
import datetime, os
from django.contrib.sites.models import Site
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
import re
import random
from math import *
from storage import OverwriteStorage
import os
# from django.contrib.comments.moderation import moderator
# from micomments.moderation import ModeratorWithoutObject, ModeratorWithObject


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


class NotationSystem(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=400,blank=True)
    configfile = models.CharField(max_length=20, unique=True)
    detailed_description = models.TextField(blank=True, null=True)
    

    def __unicode__(self):
        return self.name

class EquationTag(models.Model):
    code = models.SlugField(max_length=50, db_index=True)
    page = models.ForeignKey("Page")
    tag = models.CharField(max_length=20)


class Author(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50,db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, db_index=True)
    title = models.CharField(max_length=200,blank=True,null=True)
    institution = models.CharField(max_length=200,blank=True, null=True)
    web_address = models.URLField(blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    display_email = models.BooleanField()
    # 1 if page author, 2 if on list, 3 if core contributor
    mi_contributor = models.SmallIntegerField(db_index=True, default=0)
    contribution_summary = models.TextField(blank=True, null=True)

    def __unicode__(self):
        name= "%s, %s %s" % (self.last_name, self.first_name, self.middle_name)
        return smart_unicode(name)

    def full_name(self):
        return "%s %s %s" % (self.first_name, self.middle_name,self.last_name)

    def core_contributor(self):
        return self.mi_contributor >= 3

    def citename(self):
        return "%s %s%s" % ( self.last_name, self.first_name[:1], self.middle_name[:1])
    
    def published_pages(self):
        return self.page_set.exclude(level__code="definition").filter(publish_date__lte=datetime.date.today(),hidden=False)
    def published_applets(self):
        return self.applet_set.filter(publish_date__lte=datetime.date.today(),hidden=False)
    def published_videos(self):
        return self.video_set.filter(publish_date__lte=datetime.date.today(),hidden=False)
    def published_images(self):
        return self.image_set.filter(publish_date__lte=datetime.date.today(),hidden=False)

    @models.permalink
    def get_absolute_url(self):
        return('mi-authordetail', (), {'slug': self.code})

    class Meta:
        ordering = ['last_name','first_name','middle_name']

class Level(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code

class Objective(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code

class Subject(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    def __unicode__(self):
        return self.code

class Keyword(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    def __unicode__(self):
        return self.code
    class Meta:
        ordering = ['code']

# class ContentType(models.Model):
#     code = models.CharField(max_length=50, db_index=True, unique=True)
#     description = models.CharField(max_length=400)
#     def __unicode__(self):
#         return self.code

class RelationshipType(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code

class AuxiliaryFileType(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    heading = models.CharField(max_length=100)
    def __unicode__(self):
        return self.code

def auxiliary_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.AUXILIARY_UPLOAD_TO, "%s%s" % (instance.code, extension))

class AuxiliaryFile(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    file_type = models.ForeignKey(AuxiliaryFileType)
    description = models.CharField(max_length=400)
    auxiliary_file = models.FileField(max_length=150, 
                                      upload_to=auxiliary_path, 
                                      blank=True, verbose_name="file",
                                      storage=OverwriteStorage())
    def __unicode__(self):
        return self.code
    def get_filename(self):
        return re.sub(settings.AUXILIARY_UPLOAD_TO,"", self.auxiliary_file.name)  # get rid of upload path

    def save(self, *args, **kwargs):
        # check if changed code
        # if so, may need to change file names after save
        changed_code=False
        if self.pk is not None:
            orig = AuxiliaryFile.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True

        super(AuxiliaryFile, self).save(*args, **kwargs) 

        # if changed code, check to see if need to change files
        if changed_code:
        
            resave_needed=False
            if self.auxiliary_file.name and self.auxiliary_file.name != auxiliary_path(self,self.auxiliary_file.name):
                new_name= auxiliary_path(self,self.auxiliary_file.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.auxiliary_file.name)
                os.rename(old_filename, new_filename)
                self.auxiliary_file.name = new_name
                resave_needed=True
            if resave_needed:
                super(AuxiliaryFile, self).save(*args, **kwargs) 
                

class Page(models.Model):
    code = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    authors = models.ManyToManyField(Author, through='PageAuthor')
    level = models.ForeignKey(Level, default="i")
    objectives = models.ManyToManyField(Objective, blank=True, null=True)
    subjects = models.ManyToManyField(Subject, blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    #content_types = models.ManyToManyField(ContentType, blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    related_pages = models.ManyToManyField("self", symmetrical=False, 
                                           through='PageRelationship', 
                                           related_name='pages_related_from')
    similar_pages = models.ManyToManyField("self", symmetrical=False, 
                                           through='PageSimilar', 
                                           related_name='pages_similar_from')
    template_dir = models.CharField(max_length=200)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True,db_index=True)
    template_modified = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    highlight = models.BooleanField(db_index=True)
    worksheet = models.BooleanField()
    author_copyright = models.BooleanField(default=True)
    hidden = models.BooleanField(db_index=True)
    additional_credits = models.TextField(blank=True, null=True)
    notation_systems = models.ManyToManyField(NotationSystem, blank=True, null=True)

    class Meta:
        ordering = ['code']

    def __unicode__(self):
        return "%s (%s)" % (self.code, self.title)

    def get_title(self):
        return self.title

    def annotated_title(self):
        return "Page: %s" % self.title
    
    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.title)
        link_title="%s: %s" % (self.title,self.description)

        link_class=kwargs.get("link_class", self.level.code)
        if kwargs.get("confused"):
            link_class += " confused"


        link_url = self.get_absolute_url()
        
        anchor=kwargs.get("anchor")
        if anchor:
            link_url += "#%s" % anchor
        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))

    def return_extended_link(self, **kwargs):
        return return_extended_link(self, **kwargs)

    def return_extended_link_added(self, **kwargs):
        kwargs["added"]=True
        return return_extended_link(self, **kwargs)

  
    def return_equation_link(self, equation_code, **kwargs):
        try:
            equation_tag=EquationTag.objects.get\
                (code=equation_code, page=self).tag
        except ObjectDoesNotExist:
            equation_tag = "???"
        equation_tag = "(%s)" % equation_tag

        kwargs["anchor"] = "mjx-eqn-%s" % equation_code

        # replace (tag) with equation tag
        link_text = kwargs.get("link_text")
        if link_text:
            link_text= re.sub("\(tag\)", equation_tag, link_text)
            kwargs["link_text"]=link_text

        if kwargs.get("blank_style"):
            return link_text
        else:
            return self.return_link(**kwargs)


    @models.permalink
    def get_absolute_url(self):
        return('mi-page', (), {'page_code': self.code})

    def title_with_period(self):
        # add period to end of title unless title already ends with 
        # period, exclamation point or question mark
        if self.title[-1]=='.' or self.title[-1]=='?' or self.title[-1]=='!':
            return self.title
        else:
            return self.title+'.'

    def author_list_abbreviated_link(self):
        return self.author_list_abbreviated(1)

    def author_list_abbreviated(self, include_link=0):
        the_authors=self.pageauthor_set.all()
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

    def author_list_full_link(self):
        return self.author_list_full(1)

    def author_list_full(self, include_link=0):
        the_authors=self.pageauthor_set.all()
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

    # def thread_pages(self):
    #     thelist=list(self.threadsectionpage_set.all())
    #     thelist.extend(list(self.threadsubsectionpage_set.all()))
    #     thelist.extend(list(self.threadsubsubsectionpage_set.all()))
    #     return thelist
    
        

    def save(self, *args, **kwargs):
        # if template filename has changed, reset template_modifed to None
        if self.pk is not None:
            orig = Page.objects.get(pk=self.pk)
            if orig.template_dir != self.template_dir \
                    or orig.code != self.code :
                self.template_modified=None

        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()

        super(Page, self).save(*args, **kwargs) 
        updated=self.update_template_links()
        if updated !=1:
            self.update_similar()
 
    def update_template_links(self, force_update=0):
        # return 1 if updated_template_links
        # return 0 if template links already up-to-date
        # return -1 if did not find template
        # return -2 if there was a template error 
        # return -3 if page isn't to be published yet
        # return -4 if page is hideen
        

        full_template_name = 'midocs/pages/%s/%s.html' % (self.template_dir, self.code)
         # find template filename
        found_template=0
        for template_dir in settings.TEMPLATE_DIRS:
            if(template_dir[-1] == '/'):
                template_filename = "%s%s" % \
                    (template_dir, full_template_name)
            else:
                template_filename = "%s/%s" % \
                    (template_dir, full_template_name)
            try:
                template_mtime=datetime.datetime.fromtimestamp \
                    (os.path.getmtime(template_filename))
            except:
                continue
            found_template=1
            break

        if(not found_template):
            print "No template found for %s" % self.code
            return -1


        # update links if don't have template modified recorded
        # or if force_upate is True
        # or if recorded template modified time is more than 
        # a second older than the file's modification time
        # (need 1 second as template_modified truncates to integer seconds)
        if(self.template_modified==None or force_update \
               or template_mtime - self.template_modified \
               > datetime.timedelta(seconds=1)):
            print "Updating %s" % self.code
            print "last updated: %s" % self.template_modified
            print "template timestamp: %s" % template_mtime

            update_context = {'thepage': self, 'process_image_entries': 1,
                              'process_applet_entries': 1,
                              'process_video_entries': 1,
                              'process_index_entries': 1,
                              'process_equation_tags': 1,
                              'process_navigation_tags': 1,
                              'process_citations': 1,
                              'update_database': 1,
                              'blank_style': 1,
                              'STATIC_URL': ''}

            # if page isn't to be published yet or is hidden, 
            # don't add index entries or image/applet/video links
            if(self.publish_date > datetime.date.today() or self.hidden):
                if self.publish_date > datetime.date.today():
                    print "Publish date %s is later than today, not adding links" % str(self.publish_date)
                else:
                    print "Page is hidden, not adding links"
                
                update_context['process_image_entries']=0
                update_context['process_applet_entries']=0
                update_context['process_video_entries']=0
                update_context['process_index_entries']=0
                

            # delete old data regarding links from templates
            self.image_set.clear()
            self.applet_set.clear()
            self.video_set.clear()
            self.indexentry_set.all().delete()
            self.pagenavigation_set.all().delete()
            self.pagecitation_set.all().delete()
            self.equationtag_set.all().delete()
            self.externallink_set.all().delete()

            # parse the template with flags to enter links into database
            try:
                render_to_string(full_template_name, update_context)
                self.template_modified=template_mtime
            
                # save without updating links again
                super(Page, self).save() 

                #  update similar pages
                self.update_similar()
                
                if self.hidden:
                    return -4
                if self.publish_date > datetime.date.today():
                    return -3

                return 1
 
            except:
                print "Error in template of %s" % self.code
                #raise
                return -2
        else:
            return 0


    @classmethod
    def update_all_template_links(theclass, force_update=0):
        templates_updated=0
        templates_not_found=0
        template_errors=0
        future_pages=0
        hidden_pages=0
        for thepage in theclass.objects.all():
            status=thepage.update_template_links(force_update)
            if(status==1):
                templates_updated += 1
            elif(status==-1):
                templates_not_found +=1
            elif(status==-2):
                template_errors += 1
            elif(status==-3):
                future_pages += 1
            elif(status==-4):
                hidden_pages += 1

        print "\nFinished updating all links"
        print "Templates updated: %s" % templates_updated
        print "Templates not found: %s" % templates_not_found
        print "Template errors: %s" % template_errors
        print "Future pages: %s" % future_pages
        print "Hidden pages: %s" % hidden_pages
            

    def similar_10(self):
        return self.similar.all()[0:10]
    
    @transaction.commit_on_success
    def update_similar(self):
        """ Update all similar pages for page """
        # delete old similar pages
        self.similar.all().delete()

        related_pages={}
        today=datetime.date.today()


        background_relationship = RelationshipType.objects.get(code="background")
        
        background_pages = Page.objects.filter \
            (reverse_relationships__origin=self,
             reverse_relationships__relationship_type=
             background_relationship) \
             .filter(publish_date__lte=today, hidden=False) \
             .order_by('pk')
       
        # find related pages based on keywords
        # list of keywords in page
        keyword_list = self.keywords.all().values_list('pk', flat=True)
  
        # get pages with keyword list, ordered in reverse by number 
        # of matching keywords it had
        pages_with_keywords =Page.objects.exclude(pk=self.pk) \
            .filter(publish_date__lte=today,hidden=False) \
            .filter(keywords__in=keyword_list) \
            .annotate(hits=Count('keywords')).order_by('-hits')
        try:
            max_keyword_hits=pages_with_keywords[0].hits
        except:
            max_keyword_hits=0
        pages_with_keywords=pages_with_keywords.order_by('pk')
        
        # find related pages based on subjects
        # list of subjects in page
        subject_list = self.subjects.all().values_list('pk', flat=True)
 
        # get pages with subject list, ordered in reverse by number 
        # of matching subjects it had
        pages_with_subjects =Page.objects.exclude(pk=self.pk) \
            .filter(publish_date__lte=today,hidden=False) \
            .filter(subjects__in=subject_list) \
            .annotate(hits=Count('subjects')).order_by('-hits')
        try:
            max_subject_hits=pages_with_subjects[0].hits
        except:
            max_subject_hits=0
        pages_with_subjects=pages_with_subjects.order_by('pk')

  
        # find pages that match via full text search indexing
        try:
            from midocs.search_functions import midocsSearchQuerySet
            pages_mlt=midocsSearchQuerySet().models(Page).more_like_this(self)[:100]
            max_mlt_score = pages_mlt[0].score
            mlt_score_10 = pages_mlt[9].score

            pages_mlt_list = []
            for mp in pages_mlt:
                pages_mlt_list.append((mp.object.pk,mp.object,mp.score))
            pages_mlt_list=sorted(pages_mlt_list, key=lambda page: page[0])


        except:
            pages_mlt_list=[]
            max_mlt_score = 1
            mlt_score_10 = 0
            
            
        # print pages_with_keywords[0].pk, pages_with_keywords[1].pk
        # print pages_with_subjects[0].pk, pages_with_subjects[1].pk
        # print pages_mlt_list[0][0]

        try:
            keyword_subject_weight=4*(max_mlt_score-mlt_score_10)/(max_keyword_hits+max_subject_hits)
        except:
            keyword_subject_weight=0
        i_keyword=0
        i_subject=0
        i_mlt=0
        i_background=0

        overall_list=[]

        #pages_with_keywords=pages_with_keywords[:2]
        #pages_with_subjects=pages_with_subjects[:2]
        #pages_mlt_list=pages_mlt_list[:2]

        while(True):
            try:
                page_keyword = pages_with_keywords[i_keyword]
            except:
                i_keyword=-1
            try:
                page_subject = pages_with_subjects[i_subject]
            except:
                i_subject=-1
            try:
                page_mlt = pages_mlt_list[i_mlt]
            except:
                i_mlt=-1
            try:
                page_background = background_pages[i_background]
            except:
                i_background=-1
  
            #print (i_keyword,i_subject,i_mlt)

            if i_keyword==-1 and i_subject==-1 and i_mlt==-1:
                break

            pks=[]
            if i_keyword>=0:
                pks.append(page_keyword.pk)
            if i_subject>=0:
                pks.append(page_subject.pk)
            if i_mlt>=0:
                pks.append(page_mlt[0])
            if i_background>=0:
                pks.append(page_background.pk)
            
            min_pk = min(pks)
            
            page_score=0
            thepage=None
            is_background=False
            if i_keyword>=0 and page_keyword.pk==min_pk:
                thepage=page_keyword
                page_score += page_keyword.hits*keyword_subject_weight
                i_keyword+=1
            if i_subject>=0 and page_subject.pk==min_pk:
                thepage=page_subject
                page_score += page_subject.hits*keyword_subject_weight
                i_subject+=1
            if i_mlt>=0 and page_mlt[0]==min_pk:
                thepage=page_mlt[1]
                page_score += page_mlt[2]
                i_mlt+=1
            if i_background>=0 and page_background.pk==min_pk:
                is_background=True
                i_background+=1
                
            overall_list.append((thepage,page_score,is_background))

        overall_list=sorted(overall_list,  key=lambda page: page[1], reverse=True)[:20]

        for thepage in overall_list:
            PageSimilar.objects.create \
                (origin=self, similar=thepage[0], \
                     score=thepage[1], background_page=thepage[2])





        # pages_keyword_list = []
        # for pkey in pages_with_keywords:
        #     pages_keyword_list.append((pkey.pk, pkey, pkey.hits))
        # pages_keyword_list=sorted(pages_keyword_list, key=lambda page: page[0])

        # pages_subject_list = []
        # for psub in pages_with_subjects:
        #     pages_subject_list.append((psub.pk, psub, psub.hits))
        # pages_subject_list=sorted(pages_subject_list, key=lambda page: page[0])



        # return { 'pages_with_keywords': pages_with_keywords,
        #          'pages_with_subjects': pages_with_subjects,
        #          'pages_mlt_list': pages_mlt_list,
        #          'overall_list': overall_list
        #          }





class PageAuthor(models.Model):
    page = models.ForeignKey(Page)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("page","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author
     
class PageRelationship(models.Model):
    origin = models.ForeignKey(Page, related_name='relationships')
    related = models.ForeignKey(Page, related_name = 'reverse_relationships')
    relationship_type = models.ForeignKey(RelationshipType)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("origin","related", "relationship_type")
        ordering = ['relationship_type','sort_order','id']
    def __unicode__(self):
        return "%s -> %s" % (self.origin.code, self.related.code)



class PageSimilar(models.Model):
    origin = models.ForeignKey(Page, related_name='similar')
    similar = models.ForeignKey(Page, related_name = 'reverse_similar')
    score = models.SmallIntegerField()
    background_page = models.BooleanField(default=False)

    class Meta:
        unique_together = ("origin","similar")
        ordering = ['-score','id']

    def __unicode__(self):
        return "%s: %s" % (self.origin.code, self.similar.code)
  
class PageNavigation(models.Model):
    page = models.ForeignKey(Page)
    navigation_phrase = models.CharField(max_length=100)
    page_anchor = models.CharField(max_length=100)
    class Meta:
        unique_together = ("page","navigation_phrase")
        ordering = ['id']

    def __unicode__(self):
        return "%s: %s" % (self.page.code, self.navigation_phrase)


class PageNavigationSub(models.Model):
    navigation = models.ForeignKey(PageNavigation)
    navigation_subphrase = models.CharField(max_length=100)
    page_anchor = models.CharField(max_length=100)
    class Meta:
        unique_together = ("navigation","navigation_subphrase")
        ordering = ['id']
        
    def __unicode__(self):
        return "%s: %s, %s" % (self.navigation.page.code, self.navigation.navigation_phrase, self.navigation_subphrase)



class IndexType(models.Model):
    code = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.name


class IndexEntry(models.Model):
    page = models.ForeignKey(Page)
    index_type = models.ForeignKey(IndexType, related_name = "entries")
    indexed_phrase = models.CharField(max_length=100, db_index=True)
    indexed_subphrase = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    page_anchor = models.CharField(max_length=100, blank=True, null=True)
    
    def indexed_phrase_first_letter(self):
        return self.indexed_phrase[0].upper()

    class Meta:
        verbose_name_plural = "Index entries"
        ordering = ['indexed_phrase','indexed_subphrase']

    def __unicode__(self):
        if(self.indexed_subphrase):
            return '%s:%s in %s' % (self.indexed_phrase, self.indexed_subphrase, self.page.code)
        else:
            return '%s in %s' % (self.indexed_phrase, self.page.code)

class ImageType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code


def image_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.IMAGE_UPLOAD_TO, 'image', "%s%s" % (instance.code, extension))

def image_thumbnail_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.IMAGE_UPLOAD_TO, 'thumbnail', "%s%s" % (instance.code, extension))

def image_source_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.IMAGE_UPLOAD_TO, 'source', "%s%s" % (instance.code, extension))

class Image(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    imagefile = models.ImageField(upload_to=image_path, height_field='height', width_field='width', db_index=True, storage=OverwriteStorage())
    height = models.IntegerField(blank=True)
    width = models.IntegerField(blank=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    notation_specific = models.BooleanField(default=False)
    in_pages = models.ManyToManyField(Page, blank=True, null=True)
    authors = models.ManyToManyField(Author, through='ImageAuthor')
    subjects = models.ManyToManyField(Subject, blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    thumbnail = models.ImageField(max_length=150, upload_to=image_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    original_file = models.FileField(max_length=150, upload_to=image_source_path,
                                     blank=True,null=True, storage=OverwriteStorage())
    original_file_type=models.ForeignKey(ImageType,blank=True,null=True)
    author_copyright = models.BooleanField(default=True)
    hidden = models.BooleanField(db_index=True)
    additional_credits = models.TextField(blank=True, null=True)
    auxiliary_files = models.ManyToManyField(AuxiliaryFile, blank=True, null=True)
    notation_systems = models.ManyToManyField(NotationSystem, through='ImageNotationSystem')
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True,db_index=True)
#    notation_systems = models.ManyToManyField(NotationSystem, blank=True, null=True)


    class Meta:
        ordering = ["code"]

    def __unicode__(self):
        return "%s (Image: %s)" % (self.code, self.title)

    def annotated_title(self):
          return "Image: %s" % self.title

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "image")
        link_url = self.get_absolute_url()
        
        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))

    def return_extended_link(self, **kwargs):
        return return_extended_link(self, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return('mi-image', (), {'image_code': self.code})
    
    def get_image_filename(self):
        if self.imagefile:
            return re.sub(settings.IMAGE_UPLOAD_TO,"", self.imagefile.name)  # get rid of upload path
        else:
            return ""
    
    def get_original_image_filename(self):
        if self.original_file:
            return re.sub(settings.IMAGE_UPLOAD_TO+"source/","", self.original_file.name)  # get rid of upload path
        else:
            return ""

    def anchor(self):
        return "image:%s" % self.code

    def thumbnail_large_width(self):
        return min(self.thumbnail_width, 200)
    def thumbnail_large_height(self):
        return int(self.thumbnail_height*min(self.thumbnail_width, 200) \
                       / float(self.thumbnail_width))
    def thumbnail_large_width_buffer(self):
        return min(self.thumbnail_width, 200)+10
    
    def thumbnail_medium_width(self):
        return 100
    def thumbnail_medium_height(self):
        return int(min(100*self.thumbnail_height/float(self.thumbnail_width),100))
    def thumbnail_medium_width_buffer(self):
        return 110

    def thumbnail_small_width(self):
        return 50
    def thumbnail_small_height(self):
        return int(min(50*self.thumbnail_height/float(self.thumbnail_width),50))
    def thumbnail_small_width_buffer(self):
        return 60
    
    def title_with_period(self):
        # add period to end of title unless title already ends with 
        # period, exclamation point or question mark
        if self.title[-1]=='.' or self.title[-1]=='?' or self.title[-1]=='!':
            return self.title
        else:
            return self.title+'.'

    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()

        # check if changed code
        # if so, may need to change file names after save
        changed_code=False
        if self.pk is not None:
            orig = Image.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True


        super(Image, self).save(*args, **kwargs) 

        # if changed code, check to see if need to change files
        if changed_code:
        
            resave_needed=False
            if self.imagefile.name and self.imagefile.name != image_path(self,self.imagefile.name):
                new_name= image_path(self,self.imagefile.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.imagefile.name)
                os.rename(old_filename, new_filename)
                self.imagefile.name = new_name
                resave_needed=True
                
            if self.thumbnail.name and self.thumbnail.name != image_thumbnail_path(self, self.thumbnail.name):
                new_name= image_thumbnail_path(self, self.thumbnail.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.thumbnail.name)
                os.rename(old_filename, new_filename)
                self.thumbnail.name = new_name
                resave_needed=True

            if self.original_file.name and self.original_file.name != image_source_path(self,self.original_file.name):
                new_name= image_source_path(self,self.original_file.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename =  os.path.join(settings.MEDIA_ROOT, self.original_file.name )
                os.rename(old_filename, new_filename)
                self.original_file.name = new_name
                resave_needed=True

            if resave_needed:
                super(Image, self).save(*args, **kwargs) 
                

    def author_list_abbreviated_link(self):
        return self.author_list_abbreviated(1)

    def author_list_abbreviated(self, include_link=0):
        the_authors=self.imageauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_abbreviated = "%s %s%s" % \
                (the_author.author.last_name, \
                     the_author.author.first_name[:1], \
                     the_author.author.middle_name[:1])
            if include_link and the_author.author.mi_contributor >=2:
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

    def author_list_full_link(self):
        return self.author_list_full(1)

    def author_list_full(self,include_link=0):
        the_authors=self.imageauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_full = "%s %s %s" % \
                (the_author.author.first_name, the_author.author.middle_name, \
                     the_author.author.last_name) 
            if include_link and the_author.author.mi_contributor >=2:
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


class ImageAuthor(models.Model):
    image= models.ForeignKey(Image)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("image","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author

def image_notation_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.IMAGE_UPLOAD_TO, "notation", instance.notation_system.code, "%s%s" % (instance.image.code, extension))

class ImageNotationSystem(models.Model):
    image = models.ForeignKey(Image)
    notation_system = models.ForeignKey(NotationSystem)
    imagefile = models.ImageField(upload_to=image_notation_path, height_field='height', width_field='width', db_index=True,blank=True)
    height = models.IntegerField(blank=True,null=True)
    width = models.IntegerField(blank=True,null=True)

    class Meta:
        unique_together = ("image","notation_system")

    def __unicode__(self):
        return "%s image notation system for %s" % (self.image.code, self.notation_system)
    


class AppletType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    help_text = models.TextField()
    error_string = models.TextField()
    def __unicode__(self):
        return self.code

class AppletTypeParameter(models.Model):
    applet_type = models.ForeignKey(AppletType, related_name="valid_parameters")
    parameter_name = models.CharField(max_length=50, db_index=True)
    default_value = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ("applet_type", "parameter_name")
    def __unicode__(self):
        return self.parameter_name
   
class AppletFeature(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code

def applet_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "applet", "%s%s" % (instance.code, extension))
def applet_2_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "applet2", "%s%s" % (instance.code, extension))
def applet_thumbnail_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "image/small", "%s%s" % (instance.code, extension))
def applet_image_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "image/large", "%s%s" % (instance.code, extension))
def applet_2_image_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "image/large2", "%s%s" % (instance.code, extension))


class AppletObjectType(models.Model):
    object_type = models.CharField(max_length=50, unique=True)
    
    def __unicode__(self):
        return self.object_type

class Applet(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    applet_type = models.ForeignKey(AppletType, verbose_name="type")
    default_inline_caption = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    applet_file = models.FileField(max_length=150, 
                                   upload_to=applet_path,
                                   blank=True, verbose_name="file", 
                                   storage=OverwriteStorage())
    applet_file2 = models.FileField(max_length=150, 
                                    upload_to=applet_2_path, 
                                    blank=True,
                                    verbose_name="file2 (for double)", 
                                    storage=OverwriteStorage())

    encoded_content=models.TextField(blank=True, null=True)
    parameters = models.ManyToManyField(AppletTypeParameter, 
                                        through='AppletParameter', 
                                        null=True, blank=True)
    applet_objects = models.ManyToManyField(AppletObjectType,
                                        through='AppletObject',
                                        null=True, blank=True)
    in_pages = models.ManyToManyField(Page, blank=True, null=True)
    authors = models.ManyToManyField(Author, through='AppletAuthor')
    subjects = models.ManyToManyField(Subject, blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    features = models.ManyToManyField(AppletFeature, blank=True, null=True)
    notation_specific = models.BooleanField(default=False)
    notation_systems = models.ManyToManyField(NotationSystem, through='AppletNotationSystem')
    highlight = models.BooleanField(db_index=True)
    javascript = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(max_length=150, upload_to=applet_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    image = models.ImageField(max_length=150, upload_to=applet_image_path, height_field='image_height', width_field='image_width', null=True,blank=True, storage=OverwriteStorage())
    image_width = models.IntegerField(blank=True,null=True)
    image_height = models.IntegerField(blank=True,null=True)
    image2 = models.ImageField(max_length=150, upload_to=applet_2_image_path, height_field='image2_height', width_field='image2_width', null=True,blank=True, storage=OverwriteStorage())
    image2_width = models.IntegerField(blank=True,null=True)
    image2_height = models.IntegerField(blank=True,null=True)
    author_copyright = models.BooleanField(default=True)
    hidden = models.BooleanField(db_index=True)
    additional_credits = models.TextField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True, db_index=True)

    class Meta:
        ordering = ["code"]

    def __unicode__(self):
        return "%s (Applet: %s)" % (self.code, self.title)

    def annotated_title(self):
          return "Applet: %s" % self.title
    def get_title(self):
          return "Applet: %s" % self.title

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "applet")
        link_url = self.get_absolute_url()
        
        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))

    def return_extended_link(self, **kwargs):
        return return_extended_link(self, **kwargs)
      
    @models.permalink
    def get_absolute_url(self):
        return('mi-applet', (), {'applet_code': self.code})

    def get_applet_filename(self):
        if self.applet_file:
            return re.sub(settings.APPLET_UPLOAD_TO,"", self.applet_file.name)  # get rid of upload path
        else:
            return ""

    def get_applet_filename2(self):
        if self.applet_file2:
            return re.sub(settings.APPLET_UPLOAD_TO,"", self.applet_file2.name)  # get rid of upload path
        else:
            return ""

    def code_camel(self):
        return ''.join(x.capitalize() for x in  self.code.split('_'))

    def anchor(self):
        return "applet:%s" % self.code

    def thumbnail_large_width(self):
        return min(self.thumbnail_width, 200)
    def thumbnail_large_height(self):
        return int(self.thumbnail_height*min(self.thumbnail_width, 200) \
                       / float(self.thumbnail_width))
    def thumbnail_large_width_buffer(self):
        return min(self.thumbnail_width, 200)+15
    
    def thumbnail_medium_width(self):
        return 100
    def thumbnail_medium_height(self):
        return int(min(100*self.thumbnail_height/float(self.thumbnail_width),100))
    def thumbnail_medium_width_buffer(self):
        return 110

    def thumbnail_small_width(self):
        return 50
    def thumbnail_small_height(self):
        return int(min(50*self.thumbnail_height/float(self.thumbnail_width),50))
    def thumbnail_small_width_buffer(self):
        return 60
    
    def title_with_period(self):
        # add period to end of title unless title already ends with 
        # period, exclamation point or question mark
        if self.title[-1]=='.' or self.title[-1]=='?' or self.title[-1]=='!':
            return self.title
        else:
            return self.title+'.'

    def feature_list(self):
        the_list="";
        the_features = self.features.all()
        if the_features:
            for feature in the_features:
                if(the_list):
                    the_list="%s, " % the_list
                the_list = "%s%s" % (the_list, feature)
            return "(%s)" % the_list
        else:
            return ""
        
    def video_links(self):
        video_links=""
        n_video_links = self.video_set.count()
        for link_num in range(n_video_links):
            video = self.video_set.all()[0]
            if video.description:
                videotitle = 'title="%s"' % video.description
            else:
                videotitle = ""
                
            video_link_text = "Video introduction"
            if n_video_links > 1:
                video_link_text = "%s %s" % (video_link_text, link_num)
                
            video_links = '%s<a class="video" href="%s" %s>%s.</a> ' % \
                (video_links, video.get_absolute_url(), videotitle, video_link_text)

        return video_links

    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()

        # check if changed code
        # if so, may need to change file names after save
        changed_code=False
        if self.pk is not None:
            orig = Applet.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True

        super(Applet, self).save(*args, **kwargs) 

        # if changed code, check to see if need to change files
        if changed_code:
        
            resave_needed=False
            if self.applet_file.name and self.applet_file.name != applet_path(self,self.applet_file.name):
                new_name= applet_path(self,self.applet_file.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.applet_file.name)
                os.rename(old_filename, new_filename)
                self.applet_file.name = new_name
                resave_needed=True
                
            if self.applet_file2.name and self.applet_file2.name != applet_2_path(self,self.applet_file2.name):
                new_name= applet_2_path(self,self.applet_file2.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.applet_file2.name)
                os.rename(old_filename, new_filename)
                self.applet_file2.name = new_name
                resave_needed=True

            if self.thumbnail.name and self.thumbnail.name != applet_thumbnail_path(self, self.thumbnail.name):
                new_name= applet_thumbnail_path(self, self.thumbnail.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.thumbnail.name)
                os.rename(old_filename, new_filename)
                self.thumbnail.name = new_name
                resave_needed=True

            if self.image.name and self.image.name != applet_image_path(self, self.image.name):
                new_name= applet_image_path(self, self.image.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.image.name)
                os.rename(old_filename, new_filename)
                self.image.name = new_name
                resave_needed=True

            if self.image2.name and self.image2.name != applet_2_image_path(self, self.image2.name):
                new_name= applet_2_image_path(self, self.image2.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.image2.name)
                os.rename(old_filename, new_filename)
                self.image2.name = new_name
                resave_needed=True


            if resave_needed:
                super(Applet, self).save(*args, **kwargs) 





    def author_list_abbreviated_link(self):
        return self.author_list_abbreviated(1)

    def author_list_abbreviated(self, include_link=0):
        the_authors=self.appletauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_abbreviated = '%s %s%s' % \
                (the_author.author.last_name, \
                     the_author.author.first_name[:1], \
                     the_author.author.middle_name[:1])
            if include_link and the_author.author.mi_contributor >=2:
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

    def author_list_full_link(self):
        return self.author_list_full(1)

    def author_list_full(self,include_link=0):
        the_authors=self.appletauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_full = "%s %s %s" % \
                (the_author.author.first_name, the_author.author.middle_name, \
                     the_author.author.last_name) 
            if include_link and the_author.author.mi_contributor >=2:
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


class AppletParameter(models.Model):
    applet = models.ForeignKey(Applet)
    parameter = models.ForeignKey(AppletTypeParameter)
    value = models.CharField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("applet", "parameter")

    # need to figure out why this breaks for moebius strip with unicode error
    def __unicode__(self):
        return "%s for %s" % (self.parameter, self.applet)

    def clean(self):

        # check if parameter is for applet_type of applet.  If not, raise exception
        if self.applet.applet_type != self.parameter.applet_type:
            raise ValidationError, "Incorrect parameter for applet of type %s"\
                % self.applet.applet_type


class AppletObject(models.Model):
    applet = models.ForeignKey(Applet)
    object_type = models.ForeignKey(AppletObjectType)
    name = models.CharField(max_length=100)
    change_from_javascript = models.BooleanField(default=True)
    capture_changes = models.BooleanField()
    related_objects = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.object_type, self.name)

class AppletAuthor(models.Model):
    applet= models.ForeignKey(Applet)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("applet","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author


def applet_notation_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "notation", instance.notation_system.code, "%s%s" % (instance.applet.code, extension))
def applet_2_notation_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.APPLET_UPLOAD_TO, "notation2", instance.notation_system.code, "%s%s" % (instance.applet.code, extension))

class AppletNotationSystem(models.Model):
    applet = models.ForeignKey(Applet)
    notation_system = models.ForeignKey(NotationSystem)
    applet_file = models.FileField(upload_to=applet_notation_path,
                                   blank=True, verbose_name="file", 
                                   storage=OverwriteStorage())
    applet_file2 = models.FileField(upload_to=applet_2_notation_path,
                                    blank=True, 
                                    verbose_name="file2 (for double)", 
                                    storage=OverwriteStorage())

    # encoded_content=models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("applet","notation_system")

    def __unicode__(self):
        return "%s applet notation system for %s" % (self.applet.code, self.notation_system)
    

class VideoType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __unicode__(self):
        return self.code

class VideoTypeParameter(models.Model):
    video_type = models.ForeignKey(VideoType, related_name="valid_parameters")
    parameter_name = models.CharField(max_length=50, db_index=True)
    default_value = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ("video_type", "parameter_name")
    def __unicode__(self):
        return self.parameter_name

def video_thumbnail_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.VIDEO_UPLOAD_TO, "image/small", "%s%s" % (instance.code, extension))

class Video(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    video_type = models.ForeignKey(VideoType, verbose_name="type")
    default_inline_caption = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    thread_content_set = generic.GenericRelation('mithreads.ThreadContent')
    parameters = models.ManyToManyField(VideoTypeParameter, 
                                        through='VideoParameter', 
                                        null=True, blank=True)
    in_pages = models.ManyToManyField(Page, blank=True, null=True)
    authors = models.ManyToManyField(Author, through='VideoAuthor')
    subjects = models.ManyToManyField(Subject, blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    associated_applet = models.ForeignKey(Applet, blank=True, null=True)
    highlight = models.BooleanField(db_index=True)
    thumbnail = models.ImageField(max_length=150, upload_to=video_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    author_copyright = models.BooleanField(default=True)
    hidden = models.BooleanField(db_index=True)
    additional_credits = models.TextField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True, db_index=True)

    class Meta:
        ordering = ["code"]

    def __unicode__(self):
        return "%s (Video: %s)" % (self.code, self.title)

    def annotated_title(self):
        if self.associated_applet:
            return "Applet Introduction Video: %s" % self.title
        return "Video: %s" % self.title
      
    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "video")
        link_url = self.get_absolute_url()
        
        return mark_safe('<a href="%s" class="%s" title="%s">%s</a>' % \
                             (link_url, link_class,  link_title, link_text))

    def return_extended_link(self, **kwargs):
        return return_extended_link(self, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return('mi-video', (), {'video_code': self.code})

    def anchor(self):
        return "video:%s" % self.code

    def thumbnail_large_width(self):
        return min(self.thumbnail_width, 200)
    def thumbnail_large_height(self):
        return int(self.thumbnail_height*min(self.thumbnail_width, 200) \
                       / float(self.thumbnail_width))
    def thumbnail_large_width_buffer(self):
        return min(self.thumbnail_width, 200)+15
    
    def thumbnail_medium_width(self):
        return 100
    def thumbnail_medium_height(self):
        return int(min(100*self.thumbnail_height/float(self.thumbnail_width),100))
    def thumbnail_medium_width_buffer(self):
        return 110

    def thumbnail_small_width(self):
        return 50
    def thumbnail_small_height(self):
        return int(min(50*self.thumbnail_height/float(self.thumbnail_width),50))
    def thumbnail_small_width_buffer(self):
        return 60
    
    def title_with_period(self):
        # add period to end of title unless title already ends with 
        # period, exclamation point or question mark
        if self.title[-1]=='.' or self.title[-1]=='?' or self.title[-1]=='!':
            return self.title
        else:
            return self.title+'.'


    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()

        # check if changed code
        # if so, may need to change file names after save
        changed_code=False
        if self.pk is not None:
            orig = Video.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True

        super(Video, self).save(*args, **kwargs) 

        # if changed code, check to see if need to change files
        if changed_code:
        
            resave_needed=False
            if self.thumbnail.name and self.thumbnail.name != video_thumbnail_path(self, self.thumbnail.name):
                new_name= video_thumbnail_path(self, self.thumbnail.name)
                new_filename = os.path.join(settings.MEDIA_ROOT,new_name)
                old_filename = os.path.join(settings.MEDIA_ROOT, self.thumbnail.name)
                os.rename(old_filename, new_filename)
                self.thumbnail.name = new_name
                resave_needed=True

            if resave_needed:
                super(Video, self).save(*args, **kwargs) 
                

    def author_list_abbreviated_link(self):
        return self.author_list_abbreviated(1)

    def author_list_abbreviated(self, include_link=0):
        the_authors=self.videoauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_abbreviated = '%s %s%s' % \
                (the_author.author.last_name, \
                     the_author.author.first_name[:1], \
                     the_author.author.middle_name[:1])
            if include_link and the_author.author.mi_contributor >=2:
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

    def author_list_full_link(self):
        return self.author_list_full(1)

    def author_list_full(self,include_link=0):
        the_authors=self.videoauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_full = "%s %s %s" % \
                (the_author.author.first_name, the_author.author.middle_name, \
                     the_author.author.last_name) 
            if include_link and the_author.author.mi_contributor >=2:
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


class VideoParameter(models.Model):
    video = models.ForeignKey(Video)
    parameter = models.ForeignKey(VideoTypeParameter)
    value = models.CharField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("video", "parameter")

    # need to figure out why this breaks for moebius strip with unicode error
    def __unicode__(self):
        return "%s for %s" % (self.parameter, self.video)

    def clean(self):

        # check if parameter is for video_type of video.  If not, raise exception
        if self.video.video_type != self.parameter.video_type:
            raise ValidationError, "Incorrect parameter for video of type %s"\
                % self.video.video_type
        

class VideoAuthor(models.Model):
    video= models.ForeignKey(Video)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("video","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author




class NewsItem(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400)
    content=models.TextField()
    authors = models.ManyToManyField(Author, through='NewsAuthor')
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True)

    class Meta:
        ordering = ["-date_created"]

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return('mi-news', (), {'news_code': self.code})

    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()
        super(NewsItem, self).save(*args, **kwargs) 
        
    def author_list_abbreviated_link(self):
        return self.author_list_abbreviated(1)

    def author_list_abbreviated(self, include_link=0):
        the_authors=self.newsauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_abbreviated = "%s %s%s" % \
                (the_author.author.last_name, \
                     the_author.author.first_name[:1], \
                     the_author.author.middle_name[:1])
            if include_link and the_author.author.mi_contributor >=2:
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

    def author_list_full_link(self):
        return self.author_list_full(1)

    def author_list_full(self,include_link=0):
        the_authors=self.newsauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_full = "%s %s %s" % \
                (the_author.author.first_name, the_author.author.middle_name, \
                     the_author.author.last_name)
            if include_link and the_author.author.mi_contributor >=2:
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


class NewsAuthor(models.Model):
    newsitem = models.ForeignKey(NewsItem)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("newsitem","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.author


class ExternalLink(models.Model):
    external_url = models.URLField()
    in_page = models.ForeignKey(Page, blank=True, null=True)
    link_text = models.CharField(max_length=200)

    def __unicode__(self):
        return self.external_url

    def validate(self):
        from django.core.validators import URLValidator        
        validator_user_agent = "Math Insight (http://mathinsight.org)"
        the_validator = URLValidator(verify_exists=True, 
                                     validator_user_agent=validator_user_agent)
        the_validator(self.external_url)
        return 0
    
        
    @classmethod
    def validate_all_links(theclass):
        valid_links=0
        invalid_links=0
        links_not_found=0
        other_errors=0
        for the_link in theclass.objects.all():
            try:
                the_link.validate()
            except ValidationError, e:
                if e.code == 'invalid':
                    invalid_links += 1
                    print "%s is invalid." % the_link.external_url 
                elif e.code == 'invalid_link':
                    links_not_found +=1
                    print "%s was not found." % the_link.external_url
                else:
                    other_errors +1
                    print "Other error with %s" % the_link.external.url
            else:
                valid_links +=1
                print "Valid link: %s" % the_link.external_url

        print "\nFinished validating all external links"
        print "Valid links: %s" % valid_links
        print "Invalid links: %s" % invalid_links
        print "Links not found: %s" % links_not_found
        if other_errors:
            print "Other errors : %s" % other_errors



class ReferenceType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.code


class Reference(models.Model):
    code = models.SlugField(max_length=50, db_index=True)
    reference_type = models.ForeignKey(ReferenceType, verbose_name="type")
    authors = models.ManyToManyField(Author, through='ReferenceAuthor', related_name="references_authored",blank=True,null=True)
    title = models.CharField(max_length=400,blank=True,null=True)
    booktitle = models.CharField(max_length=400,blank=True,null=True)
    journal = models.CharField(max_length=200,blank=True,null=True)
    year = models.IntegerField(blank=True,null=True)
    volume = models.IntegerField(blank=True,null=True)
    number = models.IntegerField(blank=True,null=True)
    pages = models.CharField(max_length=20,blank=True,null=True)
    editors = models.ManyToManyField(Author, through='ReferenceEditor', related_name="references_edited",blank=True,null=True)
    publisher = models.CharField(max_length=100,blank=True,null=True)
    address = models.CharField(max_length=100,blank=True,null=True)
    published_web_address = models.URLField(blank=True, null=True)
    preprint_web_address = models.URLField(blank=True, null=True)
    notes = models.CharField(max_length=100,blank=True,null=True)
    def __unicode__(self):
        return self.code

    def author_list_abbreviated(self):
        the_authors=self.referenceauthor_set.all()
        n_authors = len(the_authors)
        author_list="";

        for i, the_author in enumerate(the_authors):
            author_name_abbreviated = "%s %s%s" % \
                (the_author.author.last_name, \
                     the_author.author.first_name[:1], \
                     the_author.author.middle_name[:1])
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

    def compiled_reference(self):
        reference_text='??'
        if self.reference_type.code=='journal_article':
            reference_text=self.author_list_abbreviated()
            if reference_text:
                reference_text += '.'
            reference_text="%s %s. <em>%s</em>" \
                % (reference_text, self.title, self.journal)
            if self.volume:
                if self.pages:
                    reference_text="%s, %s:%s" \
                        % (reference_text, self.volume, self.pages)
                else:
                    reference_text="%s, %s" \
                        % (reference_text, self.volume)
            elif self.pages:
                reference_text="%s, %s" \
                    % (reference_text, self.pages)
            if self.year:
                reference_text="%s, %s" \
                    % (reference_text, self.year)
            reference_text=reference_text+'.'
            
            if self.published_web_address:
                reference_text="%s <a href='%s' class='external'>Publisher's web site</a>" % (reference_text, self.published_web_address)
                if self.preprint_web_address:
                    reference_text=reference_text+','
            if self.preprint_web_address:
                reference_text="%s <a href='%s' class='external'>Preprint</a>" % (reference_text, self.preprint_web_address)

        return reference_text
                
    
            

class ReferenceAuthor(models.Model):
    reference = models.ForeignKey(Reference)
    author = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("reference","author")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return smart_unicode(self.author)


class ReferenceEditor(models.Model):
    reference = models.ForeignKey(Reference)
    editor = models.ForeignKey(Author)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("reference","editor")
        ordering = ['sort_order','id']
    def __unicode__(self):
        return "%s" % self.editor


class PageCitation(models.Model):
    page = models.ForeignKey(Page)
    code = models.SlugField(max_length=50, db_index=True)
    reference = models.ForeignKey(Reference,blank=True,null=True)
    footnote_text = models.TextField(blank=True,null=True)
    reference_number = models.SmallIntegerField()

    class Meta:
        unique_together = ("page","code")
        ordering = ['id']

    def __unicode__(self):
        return "%s: %s" % (self.page.code, self.code)

    def reference_text(self):
        if self.footnote_text:
            return self.footnote_text
        elif self.reference:
            return self.reference.compiled_reference()
        else:
            return "?"
