from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from micourses.models import Course, ThreadSection, ThreadContent, STUDENT_ROLE, INSTRUCTOR_ROLE
from midocs.models import Page, Image, Video, PageType, VideoType
from mitesting.models import Assessment, AssessmentType
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.utils import timezone

edit_section_url = reverse('mithreads:edit-section')
edit_content_url = reverse('mithreads:edit-content')
return_content_form_url = reverse('mithreads:return-content-form')
return_options_url = reverse('mithreads:return-options')

class TextThreadContruction(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            code="the_course",
            name="The Course",
        )
        self.sectionA = self.course.thread_sections.create(name='Section A')
        self.sectionB = self.course.thread_sections.create(name='Section B')
        self.sectionC = self.course.thread_sections.create(name='Section C')
        
        self.sectionAA = self.sectionA.child_sections.create(name='Section AA')
        self.sectionAB = self.sectionA.child_sections.create(name='Section AB')

        self.sectionBA = self.sectionB.child_sections.create(name='Section BA')
        
        self.course.reset_thread_section_sort_order()

        self.page_contenttype = ContentType.objects.get(model='page')
        self.image_contenttype = ContentType.objects.get(model='image')
        self.video_contenttype = ContentType.objects.get(model='video')
        self.assessment_contenttype = ContentType.objects.get(model='assessment')
        
        PageType.objects.create(code="pagetype", name="Page Type", default=True)
        video_type = VideoType.objects.create(code="videotype", 
                                             name="Video Type",
                                             description="hi")
        quiz = AssessmentType.objects.create(code="quiz", name="Quiz")

        self.contentlist = []
        page = Page.objects.create(code="pagea", title="Page a")
        self.contentlist.append({
            'content_type': self.page_contenttype,
            'object_id': page.id,
            'content_object': page,
        })
        page = Page.objects.create(code="pageb", title="Page b")
        self.contentlist.append({
            'content_type': self.page_contenttype,
            'object_id': page.id,
            'content_object': page,
        })
        image = Image.objects.create(code="imagea", title="Image a")
        self.contentlist.append({
            'content_type': self.image_contenttype,
            'object_id': image.id,
            'content_object': image,
        })
        video = Video.objects.create(code="videoa", title="Video a", 
                                     video_type=video_type )
        self.contentlist.append({
            'content_type': self.video_contenttype,
            'object_id': video.id,
            'content_object': video,
        })
        assessment = Assessment.objects.create(code="assessmenta",
                            name="Assessment a", assessment_type=quiz)
        self.contentlist.append({
            'content_type': self.assessment_contenttype,
            'object_id': assessment.id,
            'content_object': assessment,
        })


        content = self.contentlist[0]
        self.contentAa = self.sectionA.thread_contents.create(
            content_type = content['content_type'],
            object_id = content['object_id']
        )
        content = self.contentlist[1]
        self.contentAb = self.sectionA.thread_contents.create(
            content_type = content['content_type'],
            object_id = content['object_id']
        )
        content = self.contentlist[2]
        self.contentAAa = self.sectionAA.thread_contents.create(
            content_type = content['content_type'],
            object_id = content['object_id']
        )
        content = self.contentlist[3]
        self.contentABa = self.sectionAB.thread_contents.create(
            content_type = content['content_type'],
            object_id = content['object_id']
        )
        content = self.contentlist[4]
        self.contentABb = self.sectionAB.thread_contents.create(
            content_type = content['content_type'],
            object_id = content['object_id']
        )

        self.thread_url = reverse('mithreads:thread', 
                                  kwargs={'course_code': self.course.code})
        self.thread_edit_url = reverse('mithreads:thread-edit', 
                                       kwargs={'course_code': self.course.code})

        u=User.objects.create_user("student", password="pass")
        self.student = u.courseuser
        u=User.objects.create_user("instructor", password="pass")
        self.instructor = u.courseuser
        
        
        self.course.courseenrollment_set.create(
            student=self.student, date_enrolled=timezone.now().date())
        self.course.courseenrollment_set.create(
            student=self.instructor, date_enrolled=timezone.now().date(),
            role=INSTRUCTOR_ROLE)

        # run return_selected_course() so that course will be selected by default
        self.student.return_selected_course()
        self.instructor.return_selected_course()


    def test_render_thread(self):
        response = self.client.get(self.thread_url)
        self.assertEqual(response.context['course'],self.course)
        self.assertTemplateUsed(response,"micourses/thread_detail.html")
        for i in range(5):
            self.assertContains(response, self.contentlist[i]['content_object'].return_link())


    def test_thread_edit_access(self):
        response = self.client.get(self.thread_edit_url)
        self.assertRedirects(response, '/accounts/login?next=' + self.thread_edit_url)
        
        self.client.login(username="student",password="pass")
        response = self.client.get(self.thread_edit_url)
        self.assertRedirects(response, '/accounts/login?next=' + self.thread_edit_url)

        self.client.login(username="instructor",password="pass")
        response = self.client.get(self.thread_edit_url)
        self.assertEqual(response.context['course'],self.course)
        self.assertTemplateUsed(response,"micourses/thread_edit.html")
        for i in range(5):
            self.assertContains(response, self.contentlist[i]['content_object'].return_link())




class MySeleniumTests(StaticLiveServerTestCase):
    fixtures = ['sample_course.json']

    @classmethod
    def setUpClass(cls):
        super(MySeleniumTests, cls).setUpClass()
        cls.selenium = WebDriver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MySeleniumTests, cls).tearDownClass()

    def setUp(self):
        # self.course = Course.objects.create(
        #     code="the_course",
        #     name="The Course",
        # )
        # self.sectionA = self.course.thread_sections.create(name='Section A')
        # self.sectionB = self.course.thread_sections.create(name='Section B')
        # self.sectionC = self.course.thread_sections.create(name='Section C')
        
        # self.sectionAA = self.sectionA.child_sections.create(name='Section AA')
        # self.sectionAB = self.sectionA.child_sections.create(name='Section AB')

        # self.sectionBA = self.sectionB.child_sections.create(name='Section BA')
        
        # self.course.reset_thread_section_sort_order()

        # self.page_contenttype = ContentType.objects.get(model='page')
        # self.image_contenttype = ContentType.objects.get(model='image')
        # self.video_contenttype = ContentType.objects.get(model='video')
        # self.assessment_contenttype = ContentType.objects.get(model='assessment')
        
        # PageType.objects.create(code="pagetype", name="Page Type", default=True)
        # video_type = VideoType.objects.create(code="videotype", 
        #                                      name="Video Type",
        #                                      description="hi")
        # quiz = AssessmentType.objects.create(code="quiz", name="Quiz")

        # self.contentlist = []
        # page = Page.objects.create(code="pagea", title="Page a")
        # self.contentlist.append({
        #     'content_type': self.page_contenttype,
        #     'object_id': page.id,
        #     'content_object': page,
        # })
        # page = Page.objects.create(code="pageb", title="Page b")
        # self.contentlist.append({
        #     'content_type': self.page_contenttype,
        #     'object_id': page.id,
        #     'content_object': page,
        # })
        # image = Image.objects.create(code="imagea", title="Image a")
        # self.contentlist.append({
        #     'content_type': self.image_contenttype,
        #     'object_id': image.id,
        #     'content_object': image,
        # })
        # video = Video.objects.create(code="videoa", title="Video a", 
        #                              video_type=video_type )
        # self.contentlist.append({
        #     'content_type': self.video_contenttype,
        #     'object_id': video.id,
        #     'content_object': video,
        # })
        # assessment = Assessment.objects.create(code="assessmenta",
        #                     name="Assessment a", assessment_type=quiz)
        # self.contentlist.append({
        #     'content_type': self.assessment_contenttype,
        #     'object_id': assessment.id,
        #     'content_object': assessment,
        # })


        # content = self.contentlist[0]
        # self.contentAa = self.sectionA.thread_contents.create(
        #     content_type = content['content_type'],
        #     object_id = content['object_id']
        # )
        # content = self.contentlist[1]
        # self.contentAb = self.sectionA.thread_contents.create(
        #     content_type = content['content_type'],
        #     object_id = content['object_id']
        # )
        # content = self.contentlist[2]
        # self.contentAAa = self.sectionAA.thread_contents.create(
        #     content_type = content['content_type'],
        #     object_id = content['object_id']
        # )
        # content = self.contentlist[3]
        # self.contentABa = self.sectionAB.thread_contents.create(
        #     content_type = content['content_type'],
        #     object_id = content['object_id']
        # )
        # content = self.contentlist[4]
        # self.contentABb = self.sectionAB.thread_contents.create(
        #     content_type = content['content_type'],
        #     object_id = content['object_id']
        # )

        # self.thread_url = reverse('mithreads:thread', 
        #                           kwargs={'course_code': self.course.code})
        # self.thread_edit_url = reverse('mithreads:thread-edit', 
        #                                kwargs={'course_code': self.course.code})

        # u=User.objects.create_user("student", password="pass")
        # self.student = u.courseuser
        # u=User.objects.create_user("instructor", password="pass")
        # self.instructor = u.courseuser
        
        
        # self.course.courseenrollment_set.create(
        #     student=self.student, date_enrolled=timezone.now().date())
        # self.course.courseenrollment_set.create(
        #     student=self.instructor, date_enrolled=timezone.now().date(),
        #     role=INSTRUCTOR_ROLE)

        # # run return_selected_course() so that course will be selected by default
        # self.student.return_selected_course()
        # self.instructor.return_selected_course()

        self.thread_url = reverse('mithreads:thread', 
                                   kwargs={'course_code': 'math_1241_fall_14'})

    def test_page(self):
        self.selenium.get('%s%s' % (self.live_server_url, self.thread_url))
