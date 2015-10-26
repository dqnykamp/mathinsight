from django.db import models, transaction
from django.conf import settings
from django.db.models import Count
from django.template.loader import render_to_string
from django.template import TemplateSyntaxError, TemplateDoesNotExist, Context, loader, Template
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.fields import GenericRelation
import datetime, os
from django.contrib.sites.models import Site
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.db.models import Max
import re
import random
from math import *
from midocs.storage import OverwriteStorage
import os
from PIL import Image as PILImage
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from midocs.functions import author_list_abbreviated, author_list_full, return_extended_link
from mitesting.models import Question

# from django.contrib.comments.moderation import moderator
# from micomments.moderation import ModeratorWithoutObject, ModeratorWithObject

class CopyrightType(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(blank=True, null=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # check if newly default
        if self.default:
            if self.pk is None:
                # mark all page_types as not default
                CopyrightType.objects.update(default=False)
            else:
                orig = CopyrightType.objects.get(pk=self.pk)
                if not orig.default:
                    # since newly default, set all other page_types as not default
                    CopyrightTypes.objects.exclude(pk=self.pk)\
                                          .update(default=False)

        super(CopyrightType, self).save(*args, **kwargs) 

    @classmethod
    def return_default(theclass):
        try:
            return theclass.objects.get(default=True)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

        # if zero or multiple items marked as default
        # return first copyright_type in database (or None if no CopyrightTypes)
        try:
            return theclass.objects.all()[0]
        except IndexError:
            return None

def return_default_copyright_type():
    try:
        return CopyrightType.return_default();
    except:
        return None

class NotationSystem(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=400,blank=True)
    configfile = models.CharField(max_length=20, unique=True)
    detailed_description = models.TextField(blank=True, null=True)
    

    def __str__(self):
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
    display_email = models.BooleanField(default=False)
    # 1 if page author, 2 if on list, 3 if core contributor
    mi_contributor = models.SmallIntegerField(db_index=True, default=0)
    contribution_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        name= "%s, %s %s" % (self.last_name, self.first_name, self.middle_name)
        return smart_text(name)

    def full_name(self):
        return "%s %s %s" % (self.first_name, self.middle_name,self.last_name)

    def core_contributor(self):
        return self.mi_contributor >= 3

    def citename(self):
        return "%s %s%s" % ( self.last_name, self.first_name[:1], self.middle_name[:1])
    
    def published_pages(self):
        return self.page_set.exclude(page_type__code="definition").filter(publish_date__lte=datetime.date.today(),hidden=False)
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

class PageType(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):

        # check if newly default
        if self.default:
            if self.pk is None:
                # mark all page_types as not default
                PageType.objects.update(default=False)
            else:
                orig = PageType.objects.get(pk=self.pk)
                if not orig.default:
                    # since newly default, set all other page_types as not default
                    PageTypes.objects.exclude(pk=self.pk).update(default=False)

        super(PageType, self).save(*args, **kwargs) 

    @classmethod
    def return_default(theclass):
        try:
            return theclass.objects.get(default=True)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

        # if zero or multiple items marked as default
        # return first page_type in database (or None if no PageTypes)
        try:
            return theclass.objects.all()[0]
        except IndexError:
            return None

def return_default_page_type():
    try:
        return PageType.return_default();
    except:
        return None

class Objective(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __str__(self):
        return self.code

class Subject(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    def __str__(self):
        return self.code

class Keyword(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    def __str__(self):
        return self.code
    class Meta:
        ordering = ['code']

class RelationshipType(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __str__(self):
        return self.code

class AuxiliaryFileType(models.Model):
    code = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    heading = models.CharField(max_length=100)
    def __str__(self):
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
    def __str__(self):
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
                

class ActivePageManager(models.Manager):
    def get_queryset(self):
        return super(ActivePageManager, self).get_queryset() \
            .filter(publish_date__lte=datetime.date.today()).filter(hidden=False)

class Page(models.Model):
    code = models.SlugField(max_length=200, db_index=True)
    page_type = models.ForeignKey(PageType, default=return_default_page_type,
                                  db_index=True)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400,blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    authors = models.ManyToManyField(Author, through='PageAuthor', blank=True)
    objectives = models.ManyToManyField(Objective, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    thread_content_set = GenericRelation('micourses.ThreadContent')
    related_pages = models.ManyToManyField("self", symmetrical=False, 
                                           through='PageRelationship', 
                                           related_name='pages_related_from',
                                           blank=True)
    similar_pages = models.ManyToManyField("self", symmetrical=False, 
                                           through='PageSimilar', 
                                           related_name='pages_similar_from',
                                           blank=True)
    related_videos = models.ManyToManyField("Video", blank=True, 
                                            related_name='related_pages')
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True,db_index=True)
    notes = models.TextField(blank=True, null=True)
    highlight = models.BooleanField(db_index=True, default=False)
    copyright_type = models.ForeignKey(CopyrightType, blank=True, null=True,
                                       default=return_default_copyright_type)
    hidden = models.BooleanField(db_index=True, default=False)
    additional_credits = models.TextField(blank=True, null=True)
    notation_systems = models.ManyToManyField(NotationSystem, blank=True)
    detailed_description = models.TextField(blank=True, null=True)
    header = models.TextField(blank=True, null=True)
    javascript = models.TextField(blank=True, null=True)
    objects = models.Manager()
    activepages = ActivePageManager()


    class Meta:
        ordering = ['code', 'page_type' ]
        unique_together = ('code', 'page_type')

    def __str__(self):
        if self.page_type.default:
            return "%s (Page: %s)" % (self.code, self.title)
        else:
            return "%s (Page, %s: %s)" % (self.code, self.page_type, self.title)

    def get_title(self):
        return self.title

    def annotated_title(self):
        return "Page: %s" % self.title

    def return_link(self, **kwargs):
        try:
            link_text=kwargs["link_text"]
        except KeyError:
            if self.page_type.default:
                link_text = self.title
            else:
                link_text = "%s: %s" % (self.page_type.name, self.title)

        link_title="%s: %s" % (self.title,self.description)

        link_class=kwargs.get("link_class", self.page_type.code)
        if kwargs.get("confused"):
            link_class += " confused"


        link_url = self.get_absolute_url()
        
        get_string=kwargs.get("get_string")
        if get_string:
            link_url += "?" + get_string

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
        if self.page_type.default:
            return('mi-page', (), {'page_code': self.code})
        else:
            return('mi-page_with_type', (), {'page_code': self.code, 'page_type_code': self.page_type.code})

    def get_active_thread_content_set(self):
        return self.thread_content_set.filter(course__active=True)

    def title_with_period(self):
        # add period to end of title unless title already ends with 
        # period, exclamation point or question mark
        if self.title[-1]=='.' or self.title[-1]=='?' or self.title[-1]=='!':
            return self.title
        else:
            return self.title+'.'

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.pageauthor_set.filter(
            copyright_only=False),
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.pageauthor_set.filter(
            copyright_only=False),
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.pageauthor_set.filter(
            copyright_only=False),
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.pageauthor_set.filter(
            copyright_only=False),
                                include_link=include_link)

    def author_list_full_copyright(self, include_link=False):
        return author_list_full(self.pageauthor_set.all(),
                                include_link=include_link)

    def save(self, *args, **kwargs):

        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()

        super(Page, self).save(*args, **kwargs) 
        self.update_links()
 
    def update_links(self, force_update=0):
        from midocs.functions import return_new_auxiliary_data
        update_context = {'thepage': self, 'process_image_entries': 1,
                          'process_applet_entries': 1,
                          'process_video_entries': 1,
                          'process_equation_tags': 1,
                          'process_navigation_tags': 1,
                          'process_citations': 1,
                          'update_database': 1,
                          'blank_style': 1,
                          'STATIC_URL': '',
                          '_auxiliary_data_': return_new_auxiliary_data(),
                      }

        # if page is hidden, don't update image/applet/video links
        if self.hidden:
            update_context['process_applet_entries']=0
            update_context['process_video_entries']=0
            update_context['process_image_entries']=0
                

        # delete old data regarding links from templates
        self.embedded_images.clear()
        self.embedded_applets.clear()
        self.embedded_videos.clear()
        self.pagenavigation_set.all().delete()
        self.pagecitation_set.all().delete()
        self.equationtag_set.all().delete()
        self.externallink_set.all().delete()

        # parse the text field with flags to enter links into database
        try:

            Template("{% load mi_tags question_tags %}"+self.text).render(Context(update_context))
            # save without updating links again
            super(Page, self).save() 

            #  update similar pages
            self.update_similar()
            
        except:
            pass


    @classmethod
    def update_all_similar(theclass):
        for thepage in theclass.objects.all():
            print("Updating %s" % thepage.code)
            thepage.update_similar()
            

    def similar_10(self):
        return self.similar.all()[0:10]
    
    @transaction.atomic
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




class PageAuthor(models.Model):
    page = models.ForeignKey(Page)
    author = models.ForeignKey(Author)
    copyright_only = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("page","author")
        ordering = ['sort_order','id']
    def __str__(self):
        return "%s" % self.author
     
class PageRelationship(models.Model):
    origin = models.ForeignKey(Page, related_name='relationships')
    related = models.ForeignKey(Page, related_name = 'reverse_relationships')
    relationship_type = models.ForeignKey(RelationshipType)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("origin","related", "relationship_type")
        ordering = ['relationship_type','sort_order','id']
    def __str__(self):
        return "%s -> %s" % (self.origin.code, self.related.code)



class PageSimilar(models.Model):
    origin = models.ForeignKey(Page, related_name='similar')
    similar = models.ForeignKey(Page, related_name = 'reverse_similar')
    score = models.SmallIntegerField()
    background_page = models.BooleanField(default=False)

    class Meta:
        unique_together = ("origin","similar")
        ordering = ['-score','id']

    def __str__(self):
        return "%s: %s" % (self.origin.code, self.similar.code)
  

class PageNavigation(models.Model):
    page = models.ForeignKey(Page)
    navigation_phrase = models.CharField(max_length=100)
    page_anchor = models.CharField(max_length=100)
    class Meta:
        unique_together = ("page","navigation_phrase")
        ordering = ['id']

    def __str__(self):
        return "%s: %s" % (self.page.code, self.navigation_phrase)


class PageNavigationSub(models.Model):
    navigation = models.ForeignKey(PageNavigation)
    navigation_subphrase = models.CharField(max_length=100)
    page_anchor = models.CharField(max_length=100)
    class Meta:
        unique_together = ("navigation","navigation_subphrase")
        ordering = ['id']
        
    def __str__(self):
        return "%s: %s, %s" % (self.navigation.page.code, self.navigation.navigation_phrase, self.navigation_subphrase)



class IndexType(models.Model):
    code = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __str__(self):
        return self.name


class IndexEntry(models.Model):
    page = models.ForeignKey(Page)
    index_type = models.ForeignKey(IndexType, related_name = "entries", default=1)
    indexed_phrase = models.CharField(max_length=100, db_index=True)
    indexed_subphrase = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    page_anchor = models.CharField(max_length=100, blank=True, null=True)
    
    def indexed_phrase_first_letter(self):
        return self.indexed_phrase[0].upper()

    class Meta:
        verbose_name_plural = "Index entries"
        ordering = ['indexed_phrase','indexed_subphrase']

    def __str__(self):
        if(self.indexed_subphrase):
            return '%s:%s in %s' % (self.indexed_phrase, self.indexed_subphrase, self.page.code)
        else:
            return '%s in %s' % (self.indexed_phrase, self.page.code)

class ImageType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __str__(self):
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

class ActiveImageManager(models.Manager):
    def get_queryset(self):
        return super(ActiveImageManager, self).get_queryset() \
            .filter(publish_date__lte=datetime.date.today()).filter(hidden=False)


class Image(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    imagefile = models.ImageField(upload_to=image_path, height_field='height', width_field='width', db_index=True, storage=OverwriteStorage(), blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    notation_specific = models.BooleanField(default=False)
    in_pages = models.ManyToManyField(Page, blank=True, related_name="embedded_images")
    authors = models.ManyToManyField(Author, through='ImageAuthor', blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    thumbnail = models.ImageField(max_length=150, upload_to=image_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    original_file = models.FileField(max_length=150, upload_to=image_source_path,
                                     blank=True,null=True, storage=OverwriteStorage())
    original_file_type=models.ForeignKey(ImageType,blank=True,null=True)
    copyright_type = models.ForeignKey(CopyrightType, blank=True, null=True,
                                       default=return_default_copyright_type)
    hidden = models.BooleanField(db_index=True, default=False)
    additional_credits = models.TextField(blank=True, null=True)
    auxiliary_files = models.ManyToManyField(AuxiliaryFile, blank=True)
    notation_systems = models.ManyToManyField(NotationSystem, through='ImageNotationSystem', blank=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True,db_index=True)

    objects = models.Manager()
    activeimages = ActiveImageManager()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return "%s (Image: %s)" % (self.code, self.title)

    def annotated_title(self):
          return "Image: %s" % self.title

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "image")
        link_url = self.get_absolute_url()
        get_string=kwargs.get("get_string")
        if get_string:
            link_url += "?" + get_string

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

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.imageauthor_set.filter(
            copyright_only=False), 
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.imageauthor_set.filter(
            copyright_only=False),
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.imageauthor_set.filter(
            copyright_only=False), 
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.imageauthor_set.filter(
            copyright_only=False), 
                                include_link=include_link)

    def author_list_full_copyright(self, include_link=False):
        return author_list_full(self.imageauthor_set.all(), 
                                include_link=include_link)

    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()
            
            
        # check if changed code or changed image file
        # if changed code, may need to change file names after save
        # if changed image, then generate thumbnail
        changed_code=False
        changed_image=False
        if self.pk is not None:
            orig = Image.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True
            if orig.imagefile != self.imagefile:
                changed_image = True

        # create thumbnail
        # adapted from http://djangosnippets.org/snippets/2094/
        # only do this for new file or if have changed the imagefile
        if self.imagefile and (self.pk is None or changed_image):
            image = PILImage.open(self.imagefile)
        
            thumb_size = (200,200)

            image.thumbnail(thumb_size, PILImage.ANTIALIAS)
        
            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0) # rewind the file
        
            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.imagefile.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.thumbnail.save(suf.name+'.png', suf, save=False)



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
                

class ImageAuthor(models.Model):
    image= models.ForeignKey(Image)
    author = models.ForeignKey(Author)
    copyright_only = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("image","author")
        ordering = ['sort_order','id']
    def __str__(self):
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

    def __str__(self):
        return "%s image notation system for %s" % (self.image.code, self.notation_system)
    


class AppletType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    help_text = models.TextField()
    error_string = models.TextField()
    def __str__(self):
        return self.code

class AppletTypeParameter(models.Model):
    applet_type = models.ForeignKey(AppletType, related_name="valid_parameters")
    parameter_name = models.CharField(max_length=50, db_index=True)
    default_value = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ("applet_type", "parameter_name")
    def __str__(self):
        return self.parameter_name
   
class AppletFeature(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    description = models.CharField(max_length=400)
    def __str__(self):
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
    
    def __str__(self):
        return self.object_type

class ActiveAppletManager(models.Manager):
    def get_queryset(self):
        return super(ActiveAppletManager, self).get_queryset() \
            .filter(publish_date__lte=datetime.date.today()).filter(hidden=False)

class Applet(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    applet_type = models.ForeignKey(AppletType, verbose_name="type")
    default_inline_caption = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    thread_content_set = GenericRelation('micourses.ThreadContent')
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
                                        through='AppletParameter', blank=True)
    applet_objects = models.ManyToManyField(AppletObjectType,
                                            through='AppletObject', blank=True)
    in_pages = models.ManyToManyField(Page, blank=True, related_name="embedded_applets")
    authors = models.ManyToManyField(Author, through='AppletAuthor', blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    features = models.ManyToManyField(AppletFeature, blank=True)
    notation_specific = models.BooleanField(default=False)
    notation_systems = models.ManyToManyField(NotationSystem, through='AppletNotationSystem', blank=True)
    highlight = models.BooleanField(db_index=True, default=False)
    javascript = models.TextField(blank=True, null=True)
    child_applet = models.ForeignKey('self', blank=True, null=True)
    child_applet_percent_width = models.IntegerField(default=50)
    child_applet_parameters = models.CharField(max_length=400, blank=True, null=True)

    OVERWRITE_THUMBNAIL_CHOICES = (
        (0, "don't overwrite"),
        (1, "from image 1"),
        (2, "from image 2"),
    )
    overwrite_thumbnail = models.SmallIntegerField(choices=OVERWRITE_THUMBNAIL_CHOICES, default =1)
    thumbnail = models.ImageField(max_length=150, upload_to=applet_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    image = models.ImageField(max_length=150, upload_to=applet_image_path, height_field='image_height', width_field='image_width', null=True,blank=True, storage=OverwriteStorage())
    image_width = models.IntegerField(blank=True,null=True)
    image_height = models.IntegerField(blank=True,null=True)
    image2 = models.ImageField(max_length=150, upload_to=applet_2_image_path, height_field='image2_height', width_field='image2_width', null=True,blank=True, storage=OverwriteStorage())
    image2_width = models.IntegerField(blank=True,null=True)
    image2_height = models.IntegerField(blank=True,null=True)
    copyright_type = models.ForeignKey(CopyrightType, blank=True, null=True,
                                       default=return_default_copyright_type)
    hidden = models.BooleanField(db_index=True, default=False)
    iframe = models.BooleanField(default=False)
    additional_credits = models.TextField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True, db_index=True)

    objects = models.Manager()
    activeapplets = ActiveAppletManager()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return "%s (Applet: %s)" % (self.code, self.title)

    @classmethod
    def return_initial_applet_data(cls):
        return {'javascript': {'_initialization': ''}, 'counter': 0}

    def annotated_title(self):
          return "Applet: %s" % self.title
    def get_title(self):
          return "Applet: %s" % self.title

    def return_link(self, **kwargs):
        link_text=kwargs.get("link_text", self.annotated_title())
        link_title="%s: %s" % (self.annotated_title(),self.description)
        link_class=kwargs.get("link_class", "applet")
        link_url = self.get_absolute_url()
        get_string=kwargs.get("get_string")
        if get_string:
            link_url += "?" + get_string
        
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

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.appletauthor_set.filter(
            copyright_only=False),
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.appletauthor_set.filter(
            copyright_only=False), 
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.appletauthor_set.filter(
            copyright_only=False),
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.appletauthor_set.filter(
            copyright_only=False),
                                include_link=include_link)

    def author_list_full_copyright(self, include_link=False):
        return author_list_full(self.appletauthor_set.all(),
                                include_link=include_link)

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

        # check if changed code, applet file, or image file
        # if changed code, may need to change file names after save
        # if changed file, and Geogebra web, then generate encoded content
        # if changed image, then generate thumbnail
        changed_code=False
        changed_applet=False
        changed_image=False
        changed_image2=False
        changed_thumbnail=False
        if self.pk is not None:
            orig = Applet.objects.get(pk=self.pk)
            if orig.code != self.code:
                changed_code = True
            if orig.applet_file != self.applet_file:
                changed_applet = True
            if orig.image != self.image:
                changed_image = True
            if orig.image2 != self.image2:
                changed_image2 = True
            if orig.thumbnail != self.thumbnail:
                changed_thumbnail = True

        # create encoded content if applet_file exists
        # only do this for new file or if have changed the applet_file
        # and if is GeogebraWeb applet
        if (self.pk is None or changed_applet or not self.encoded_content)\
                and self.applet_file:
            # check if GeogebraWeb applet
            gw_type=AppletType.objects.get(code="GeogebraWeb")
            if(self.applet_type == gw_type):
                try:
                    self.applet_file.open()
                    import base64
                    self.encoded_content = base64.b64encode\
                        (self.applet_file.read())
                    #self.applet_file.close()
                except:
                    raise

        # if thumbnail is added explicitly (or changed)
        # then mark thumbnail not to be overwritten from image
        if changed_thumbnail or (self.pk is None and self.thumbnail):
            self.overwrite_thumbnail = 0
                
        # if thumbnail marked to be overwritten
        # and corresponding image has been added or changed, then
        # create thumbnail from image file
        # adapted from http://djangosnippets.org/snippets/2094/
        # only do this for new file or if have changed the image
        if (self.overwrite_thumbnail==1 and \
            (self.pk is None or changed_image) \
            and self.image) \
            or (self.overwrite_thumbnail==2 and \
                (self.pk is None or changed_image2) \
                and self.image2):

            if self.overwrite_thumbnail==2:
                image = self.image2
            else:
                image = self.image

            image = PILImage.open(image)
        
            thumb_size = (200,200)

            image.thumbnail(thumb_size, PILImage.ANTIALIAS)
        
            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0) # rewind the file
        
            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.image.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.thumbnail.save(suf.name+'.png', suf, save=False)

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


class AppletParameter(models.Model):
    applet = models.ForeignKey(Applet)
    parameter = models.ForeignKey(AppletTypeParameter)
    value = models.CharField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("applet", "parameter")

    def __str__(self):
        return "%s for %s" % (self.parameter, self.applet)

    def clean(self):

        # check if parameter is for applet_type of applet.  If not, raise exception
        try:
            if self.applet.applet_type != self.parameter.applet_type:
                raise ValidationError("Incorrect parameter for applet of type %s"\
                    % self.applet.applet_type)

        except ObjectDoesNotExist:
            # When save as new applet, get applet doesn't exist exception.
            # Not sure what to do, but ignoring seems to work.
            pass

class AppletObject(models.Model):
    applet = models.ForeignKey(Applet)
    object_type = models.ForeignKey(AppletObjectType)
    name = models.CharField(max_length=100)
    change_from_javascript = models.BooleanField(default=True)
    capture_changes = models.BooleanField(default=False)
    state_variable = models.BooleanField(default=False)
    related_objects = models.CharField(max_length=200, blank=True, null=True)
    name_for_changes = models.CharField(max_length=100, blank=True, null=True)
    category_for_capture = models.CharField(max_length=100, blank=True, null=True)
    function_input_variable= models.CharField(max_length=1, blank=True, null=True)
    default_value = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return "%s: %s" % (self.object_type, self.name)


class AppletChildObjectLink(models.Model):
    applet = models.ForeignKey(Applet)
    object_name = models.CharField(max_length=100)
    child_object_name = models.CharField(max_length=100)
    applet_to_child_link = models.BooleanField(default=True)
    child_to_applet_link = models.BooleanField(default=True)

    def __str__(self):
        return "link %s to %s" % (self.object_name, self.child_object_name)


class AppletText(models.Model):
    POSITION_CHOICES = (
        ('top', 'top'),
        ('bottom', 'bottom'),
        )

    applet = models.ForeignKey(Applet)
    code = models.SlugField(max_length=100)
    title = models.CharField(max_length=100)
    text = models.TextField()
    default_position = models.CharField(max_length=6, choices=POSITION_CHOICES,
                                        blank=True, null=True)
    sort_order = models.FloatField(blank=True)

    class Meta:
        unique_together = ("applet", "code")
        ordering = ['sort_order','id']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        # if sort_order is null, make it one more than the max
        if self.sort_order is None:
            max_sort_order = self.applet.applettext_set\
                .aggregate(Max('sort_order'))['sort_order__max']
            if max_sort_order:
                self.sort_order = ceil(max_sort_order+1)
            else:
                self.sort_order = 1
        super(AppletText, self).save(*args, **kwargs)


class AppletAuthor(models.Model):
    applet= models.ForeignKey(Applet)
    author = models.ForeignKey(Author)
    copyright_only = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("applet","author")
        ordering = ['sort_order','id']
    def __str__(self):
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

    def __str__(self):
        return "%s applet notation system for %s" % (self.applet.code, self.notation_system)
    

class VideoType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    def __str__(self):
        return self.code

class VideoTypeParameter(models.Model):
    video_type = models.ForeignKey(VideoType, related_name="valid_parameters")
    parameter_name = models.CharField(max_length=50, db_index=True)
    default_value = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ("video_type", "parameter_name")
    def __str__(self):
        return self.parameter_name

def video_thumbnail_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return os.path.join(settings.VIDEO_UPLOAD_TO, "image/small", "%s%s" % (instance.code, extension))

class ActiveVideoManager(models.Manager):
    def get_queryset(self):
        return super(ActiveVideoManager, self).get_queryset() \
            .filter(publish_date__lte=datetime.date.today()).filter(hidden=False)

class Video(models.Model):
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=100, unique=True)
    video_type = models.ForeignKey(VideoType, verbose_name="type")
    default_inline_caption = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=400,blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    thread_content_set = GenericRelation('micourses.ThreadContent')
    parameters = models.ManyToManyField(VideoTypeParameter, 
                                        through='VideoParameter', blank=True)
    in_pages = models.ManyToManyField(Page, blank=True, related_name="embedded_videos")
    authors = models.ManyToManyField(Author, through='VideoAuthor', blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    associated_applet = models.ForeignKey(Applet, blank=True, null=True)
    highlight = models.BooleanField(db_index=True, default=False)
    thumbnail = models.ImageField(max_length=150, upload_to=video_thumbnail_path, height_field='thumbnail_height', width_field='thumbnail_width', null=True,blank=True, storage=OverwriteStorage())
    thumbnail_width = models.IntegerField(blank=True,null=True)
    thumbnail_height = models.IntegerField(blank=True,null=True)
    copyright_type = models.ForeignKey(CopyrightType, blank=True, null=True,
                                       default=return_default_copyright_type)
    hidden = models.BooleanField(db_index=True, default=False)
    additional_credits = models.TextField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True, db_index=True)
    questions = models.ManyToManyField(Question,
                                       through = 'VideoQuestion', blank=True)

    objects = models.Manager()
    activevideos = ActiveVideoManager()

    class Meta:
        ordering = ["code"]

    def __str__(self):
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
        get_string=kwargs.get("get_string")
        if get_string:
            link_url += "?" + get_string
        
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

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.videoauthor_set.filter(
            copyright_only=False),
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.videoauthor_set.filter(
            copyright_only=False),
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.videoauthor_set.filter(
            copyright_only=False),
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.videoauthor_set.filter(
            copyright_only=False),
                                include_link=include_link)

    def author_list_full_copyright(self, include_link=False):
        return author_list_full(self.videoauthor_set.all(), 
                                include_link=include_link)

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


class VideoParameter(models.Model):
    video = models.ForeignKey(Video)
    parameter = models.ForeignKey(VideoTypeParameter)
    value = models.CharField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("video", "parameter")

    # need to figure out why this breaks for moebius strip with unicode error
    def __str__(self):
        return "%s for %s" % (self.parameter, self.video)

    def clean(self):

        # check if parameter is for video_type of video.  If not, raise exception
        if self.video.video_type != self.parameter.video_type:
            raise ValidationError("Incorrect parameter for video of type %s"\
                % self.video.video_type)
        
class VideoQuestion(models.Model):
    video = models.ForeignKey(Video)
    question = models.ForeignKey(Question)
    sort_order = models.FloatField(default=0)
    
    class Meta:
        unique_together = ("video", "question")
        ordering = ['sort_order', 'id']
    def __str__(self):
        return "%s" % self.question


class VideoAuthor(models.Model):
    video= models.ForeignKey(Video)
    author = models.ForeignKey(Author)
    copyright_only = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("video","author")
        ordering = ['sort_order','id']
    def __str__(self):
        return "%s" % self.author




class NewsItem(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400)
    content=models.TextField()
    authors = models.ManyToManyField(Author, through='NewsAuthor', blank=True)
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(blank=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return('mi-news', (), {'news_code': self.code})

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.newsauthor_set.filter(
            copyright_only=False),
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.newsauthor_set.filter(
            copyright_only=False),
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.newsauthor_set.filter(
            copyright_only=False),
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.newsauthor_set.filter(
            copyright_only=False),
                                include_link=include_link)

    def author_list_full_copyright(self, include_link=False):
        return author_list_full(self.newsauthor_set.all(), 
                                include_link=include_link)

    def save(self, *args, **kwargs):
        # if publish_date is empty, set it to be today
        if self.publish_date is None:
            self.publish_date = datetime.date.today()
        super(NewsItem, self).save(*args, **kwargs) 
        

class NewsAuthor(models.Model):
    newsitem = models.ForeignKey(NewsItem)
    author = models.ForeignKey(Author)
    copyright_only = models.BooleanField(default=False)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("newsitem","author")
        ordering = ['sort_order','id']
    def __str__(self):
        return "%s" % self.author


class ExternalLink(models.Model):
    external_url = models.URLField()
    in_page = models.ForeignKey(Page, blank=True, null=True)
    link_text = models.CharField(max_length=200)

    def __str__(self):
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
            except ValidationError as e:
                if e.code == 'invalid':
                    invalid_links += 1
                    print("%s is invalid." % the_link.external_url)
                elif e.code == 'invalid_link':
                    links_not_found +=1
                    print("%s was not found." % the_link.external_url)
                else:
                    other_errors +1
                    print("Other error with %s" % the_link.external.url)
            else:
                valid_links +=1
                print("Valid link: %s" % the_link.external_url)

        print("\nFinished validating all external links")
        print("Valid links: %s" % valid_links)
        print("Invalid links: %s" % invalid_links)
        print("Links not found: %s" % links_not_found)
        if other_errors:
            print("Other errors : %s" % other_errors)



class ReferenceType(models.Model):
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.code


class Reference(models.Model):
    code = models.SlugField(max_length=50, db_index=True)
    reference_type = models.ForeignKey(ReferenceType, verbose_name="type")
    authors = models.ManyToManyField(Author, through='ReferenceAuthor', related_name="references_authored", blank=True)
    title = models.CharField(max_length=400,blank=True,null=True)
    booktitle = models.CharField(max_length=400,blank=True,null=True)
    journal = models.CharField(max_length=200,blank=True,null=True)
    year = models.IntegerField(blank=True,null=True)
    volume = models.IntegerField(blank=True,null=True)
    number = models.IntegerField(blank=True,null=True)
    pages = models.CharField(max_length=20,blank=True,null=True)
    editors = models.ManyToManyField(Author, through='ReferenceEditor', related_name="references_edited", blank=True)
    publisher = models.CharField(max_length=100,blank=True,null=True)
    address = models.CharField(max_length=100,blank=True,null=True)
    published_web_address = models.URLField(blank=True, null=True)
    preprint_web_address = models.URLField(blank=True, null=True)
    notes = models.CharField(max_length=100,blank=True,null=True)
    def __str__(self):
        return self.code

    def author_list_abbreviated_link(self):
        return author_list_abbreviated(self.referenceauthor_set.all(), 
                                       include_link=True)

    def author_list_abbreviated(self, include_link=False):
        return author_list_abbreviated(self.referenceauthor_set.all(), 
                                       include_link=include_link)

    def author_list_full_link(self):
        return author_list_full(self.referenceauthor_set.all(), 
                                include_link=True)

    def author_list_full(self, include_link=False):
        return author_list_full(self.referenceauthor_set.all(), 
                                include_link=include_link)


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
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("reference","author")
        ordering = ['sort_order','id']
    def __str__(self):
        return smart_text(self.author)


class ReferenceEditor(models.Model):
    reference = models.ForeignKey(Reference)
    editor = models.ForeignKey(Author)
    sort_order = models.FloatField(default=0)

    class Meta:
        unique_together = ("reference","editor")
        ordering = ['sort_order','id']
    def __str__(self):
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

    def __str__(self):
        return "%s: %s" % (self.page.code, self.code)

    def reference_text(self):
        if self.footnote_text:
            return self.footnote_text
        elif self.reference:
            return self.reference.compiled_reference()
        else:
            return "?"

