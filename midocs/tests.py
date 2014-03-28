from django.test import TestCase
from midocs.models import Page, Applet, Level
import datetime
from django.core.urlresolvers import reverse

def create_page(code, title="test page", highlight=False, publish_date=None, hidden=False):
    return Page.objects.create(code=code, title=title,
                               highlight=highlight, hidden=hidden,
                               publish_date=publish_date)

class LevelTests(TestCase):
    def test_behavior_of_default_levels(self):
        # with no levels returns none
        self.assertEqual(Level.return_default(), None)
        # with level not marked as default, returns that one
        firstlevel = Level.objects.create(code="firstone", description="First Level")
        self.assertEqual(Level.return_default(), firstlevel)
        # when add second level not marked as default, returns first
        # (could remove this test if don't care about tihs ordering)
        secondlevel = Level.objects.create(code="secondone", description="Second Level")
        self.assertEqual(Level.return_default(), firstlevel)
        # when add level marked as default, it should be returned
        firstdefaultlevel = Level.objects.create(code="thedefault", description="The first default", default=True)
        self.assertEqual(Level.return_default(), firstdefaultlevel)
        # when add fourth level, still return default
        fourthlevel = Level.objects.create(code="fourthone", description="Fourth Level")
        self.assertEqual(Level.return_default(), firstdefaultlevel)
        # when then add a new default, it overrides old default
        newdefaultlevel = Level.objects.create(code="thenewdefault", description="The new default", default=True)
        self.assertEqual(Level.return_default(), newdefaultlevel)
        # old default is now marked as not default
        olddefault = Level.objects.get(pk = firstdefaultlevel.pk)
        assertEqual(olddefault.default, False)
        # if remove default setting from newdefault, 
        # should return first level again
        newdefaultlevel.default = False
        newdefaultlevel.save()
        assertEqual(Level.return_default, firstlevel)


class HomePageTests(TestCase):

    def test_home_page_with_no_content(self):
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_past_page(self):
        thepage=create_page("the_page")
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[thepage])

    def test_home_page_with_one_highlighted_page(self):
        thepage=create_page("the_page", highlight=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[thepage])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[thepage])

    def test_home_page_with_one_hidden_page(self):
        thepage=create_page("the_page", hidden=True)
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

    def test_home_page_with_one_future_page(self):
        thepage=create_page("the_page", publish_date = datetime.date.today()+datetime.timedelta(days=1))
        response = self.client.get(reverse('mathinsight-home'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['highlight_list'],[])
        self.assertQuerysetEqual(response.context['highlighted_applets'],[])
        self.assertQuerysetEqual(response.context['news_list'],[])
        self.assertQuerysetEqual(response.context['new_pages'],[])

        



class PageMethodTests(TestCase):

    def all_pages_load_without_error(self):
        for page in Page.objects.all():
            resp = self.client.get(page.get_absolute_url())
            self.assertEqual(resp.status_code, 200)
            
    


    
