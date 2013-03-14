from django.test import TestCase
from midocs.models import Page

def template_compile(TestCase):
    def test_all_pages(self):
        for page in Page.objects.all():
            resp = self.client.get(page.get_absolute_url())
            self.assertEqual(resp.status_code, 200)
            
