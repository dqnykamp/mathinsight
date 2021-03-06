from django.test import TestCase
from midocs.models import Page, Applet, AppletType, PageType, Image, Video, VideoType
import datetime
from django.core.urlresolvers import reverse
#from PIL import Image as PILImage
#import StringIO
#from django.core.files.uploadedfile import SimpleUploadedFile
#from mathinsight.settings import STATIC_ROOT


def create_page(code, title="test page", highlight=False, publish_date=None, 
                hidden=False, page_type=None):
    if page_type:
        return Page.objects.create(code=code, title=title,
                                   highlight=highlight, hidden=hidden,
                                   publish_date=publish_date, page_type=page_type)
    else:
        return Page.objects.create(code=code, title=title,
                                   highlight=highlight, hidden=hidden,
                                   publish_date=publish_date)

def create_applet(code, applet_type, title="test applet", highlight=False, 
                  publish_date=None, hidden=False):
    return Applet.objects.create(code=code, title=title, 
                                 applet_type=applet_type,
                                 highlight=highlight, hidden=hidden,
                                 publish_date=publish_date)

def create_an_applet_type(code="sometype", name="applet type",
                          description="none", help_text="none",
                          error_string="none"):
    return AppletType.objects.create(code=code, name=name,
                                     description=description,
                                     help_text=help_text,
                                     error_string=error_string)

def create_image(code, title="test image", 
                  publish_date=None, hidden=False):
    return Image.objects.create(code=code, title=title, 
                                hidden=hidden,
                                publish_date=publish_date)

def create_video(code, video_type, title="test video", 
                  publish_date=None, hidden=False):
    return Video.objects.create(code=code, title=title, 
                                video_type = video_type,
                                hidden=hidden,
                                publish_date=publish_date)

def create_a_video_type(code="sometype", name="video type",
                          description="none"):
    return VideoType.objects.create(code=code, name=name,
                                     description=description)


class PageTypeTests(TestCase):
    def test_behavior_of_default_page_types(self):
        # with no page_types returns none
        self.assertEqual(PageType.return_default(), None)
        # with page_type not marked as default, returns that one
        firstpage_type = PageType.objects.create(code="firstone", name="First PageType")
        self.assertEqual(PageType.return_default(), firstpage_type)
        # when add second page_type not marked as default, returns first
        # (could remove this test if don't care about tihs ordering)
        secondpage_type = PageType.objects.create(code="secondone", name="Second PageType")
        self.assertEqual(PageType.return_default(), firstpage_type)
        # when add page_type marked as default, it should be returned
        firstdefaultpage_type = PageType.objects.create(code="thedefault", name="The first default", default=True)
        self.assertEqual(PageType.return_default(), firstdefaultpage_type)
        # when add fourth page_type, still return default
        fourthpage_type = PageType.objects.create(code="fourthone", name="Fourth PageType")
        self.assertEqual(PageType.return_default(), firstdefaultpage_type)
        # when then add a new default, it overrides old default
        newdefaultpage_type = PageType.objects.create(code="thenewdefault", name="The new default", default=True)
        self.assertEqual(PageType.return_default(), newdefaultpage_type)
        # old default is now marked as not default
        olddefault = PageType.objects.get(pk = firstdefaultpage_type.pk)
        self.assertFalse(olddefault.default)
        # if remove default setting from newdefault, 
        # should return first page_type again
        newdefaultpage_type.default = False
        newdefaultpage_type.save()
        self.assertEqual(PageType.return_default(), firstpage_type)


def create_a_page_type():
    defaultpage_type = PageType.objects.create(code="thedefault", name="The default", default=True)



class HomePageTests(TestCase):

    def test_home_page_with_no_content(self):
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_past_page(self):
        create_a_page_type()
        thepage=create_page("the_page")
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[repr(thepage)])

    def test_home_page_with_one_highlighted_page(self):
        create_a_page_type()
        thepage=create_page("the_page", highlight=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[repr(thepage)])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[repr(thepage)])

    def test_home_page_with_one_hidden_highlighted_page(self):
        create_a_page_type()
        thepage=create_page("the_page", highlight=True, hidden=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_future_highlighted_page(self):
        create_a_page_type()
        thepage=create_page("the_page", publish_date = datetime.date.today()+datetime.timedelta(days=1), highlight=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

        
    def test_home_page_with_one_applet(self):
        atype=create_an_applet_type()
        theapplet=create_applet(code="theapplet", applet_type=atype)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_highlighted_applet(self):
        atype=create_an_applet_type()
        theapplet=create_applet(code="theapplet", applet_type=atype, highlight=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[repr(theapplet)])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_hidden_highlighted_applet(self):
        atype=create_an_applet_type()
        theapplet=create_applet(code="theapplet", applet_type=atype, highlight=True, hidden=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_future_highlighted_applet(self):
        atype=create_an_applet_type()
        theapplet=create_applet(code="theapplet", applet_type=atype, highlight=True, publish_date = datetime.date.today()+datetime.timedelta(days=1))
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])


class ActiveManagerTests(TestCase):
    
    def test_active_page_manager(self):
        create_a_page_type()
        # with no pages
        active_pages = Page.activepages.all()
        self.assertQuerysetEqual(active_pages,[])
        # add a page
        currentpage=create_page(code="currentpage", title="Current Page")
        active_pages = Page.activepages.all()
        self.assertQuerysetEqual(active_pages,[repr(currentpage)])
        # add a future page
        futurepage=create_page(code="futurepage", title="Future Page", publish_date = datetime.date.today()+datetime.timedelta(days=1))
        active_pages = Page.activepages.all()
        self.assertQuerysetEqual(active_pages,[repr(currentpage)])
        # add a hidden page
        hiddenpage=create_page(code="hiddenpage", title="Hidden Page", hidden=True)
        active_pages = Page.activepages.all()
        self.assertQuerysetEqual(active_pages,[repr(currentpage)])
        # add a page from the past
        pastpage=create_page(code="pastpage", title="Past Page", publish_date = datetime.date.today()-datetime.timedelta(days=1))
        active_pages = Page.activepages.all()
        self.assertQuerysetEqual(active_pages,[repr(currentpage), repr(pastpage)], ordered=False)
        

    def test_active_applet_manager(self):
        atype=create_an_applet_type()
        # with no applets
        active_applets = Applet.activeapplets.all()
        self.assertQuerysetEqual(active_applets,[])
        # add a applet
        currentapplet=create_applet(code="currentapplet", title="Current Applet", applet_type = atype)
        active_applets = Applet.activeapplets.all()
        self.assertQuerysetEqual(active_applets,[repr(currentapplet)])
        # add a future applet
        futureapplet=create_applet(code="futureapplet", title="Future Applet", publish_date = datetime.date.today()+datetime.timedelta(days=1), applet_type = atype)
        active_applets = Applet.activeapplets.all()
        self.assertQuerysetEqual(active_applets,[repr(currentapplet)])
        # add a hidden applet
        hiddenapplet=create_applet(code="hiddenapplet", title="Hidden Applet", hidden=True, applet_type = atype)
        active_applets = Applet.activeapplets.all()
        self.assertQuerysetEqual(active_applets,[repr(currentapplet)])
        # add a applet from the past
        pastapplet=create_applet(code="pastapplet", title="Past Applet", publish_date = datetime.date.today()-datetime.timedelta(days=1), applet_type = atype)
        active_applets = Applet.activeapplets.all()
        self.assertQuerysetEqual(active_applets,[repr(currentapplet), repr(pastapplet)], ordered=False)
        

    def test_active_image_manager(self):
        # with no images
        active_images = Image.activeimages.all()
        self.assertQuerysetEqual(active_images,[])
        # add a image
        currentimage=create_image(code="currentimage", title="Current Image")
        active_images = Image.activeimages.all()
        self.assertQuerysetEqual(active_images,[repr(currentimage)])
        # add a future image
        futureimage=create_image(code="futureimage", title="Future Image", publish_date = datetime.date.today()+datetime.timedelta(days=1))
        active_images = Image.activeimages.all()
        self.assertQuerysetEqual(active_images,[repr(currentimage)])
        # add a hidden image
        hiddenimage=create_image(code="hiddenimage", title="Hidden Image", hidden=True)
        active_images = Image.activeimages.all()
        self.assertQuerysetEqual(active_images,[repr(currentimage)])
        # add a image from the past
        pastimage=create_image(code="pastimage", title="Past Image", publish_date = datetime.date.today()-datetime.timedelta(days=1))
        active_images = Image.activeimages.all()
        self.assertQuerysetEqual(active_images,[repr(currentimage), repr(pastimage)], ordered=False)


    def test_active_video_manager(self):
        vtype = create_a_video_type();
        # with no videos
        active_videos = Video.activevideos.all()
        self.assertQuerysetEqual(active_videos,[])
        # add a video
        currentvideo=create_video(code="currentvideo", title="Current Video", video_type = vtype)
        active_videos = Video.activevideos.all()
        self.assertQuerysetEqual(active_videos,[repr(currentvideo)])
        # add a future video
        futurevideo=create_video(code="futurevideo", title="Future Video", publish_date = datetime.date.today()+datetime.timedelta(days=1), video_type = vtype)
        active_videos = Video.activevideos.all()
        self.assertQuerysetEqual(active_videos,[repr(currentvideo)])
        # add a hidden video
        hiddenvideo=create_video(code="hiddenvideo", title="Hidden Video", hidden=True, video_type = vtype)
        active_videos = Video.activevideos.all()
        self.assertQuerysetEqual(active_videos,[repr(currentvideo)])
        # add a video from the past
        pastvideo=create_video(code="pastvideo", title="Past Video", publish_date = datetime.date.today()-datetime.timedelta(days=1), video_type = vtype)
        active_videos = Video.activevideos.all()
        self.assertQuerysetEqual(active_videos,[repr(currentvideo), repr(pastvideo)], ordered=False)
