from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from micourses.models import Course, ThreadSection, ThreadContent, Assessment, AssessmentType, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from midocs.models import Page, Image, Video, PageType, VideoType, Applet
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.utils import timezone

edit_section_url = reverse('mithreads:edit-section')
edit_content_url = reverse('mithreads:edit-content')
return_content_form_url = reverse('mithreads:return-content-form')
return_options_url = reverse('mithreads:return-options')


def set_up_data(tcase):
    tcase.course = Course.objects.create(
        code="the_course",
        name="The Course",
    )
    tcase.sectionA = tcase.course.thread_sections.create(name='Section A')
    tcase.sectionB = tcase.course.thread_sections.create(name='Section B')
    tcase.sectionC = tcase.course.thread_sections.create(name='Section C')

    tcase.sectionAA = tcase.sectionA.child_sections.create(name='Section AA')

    tcase.sectionBA = tcase.sectionB.child_sections.create(name='Section BA')

    tcase.sectionCA = tcase.sectionC.child_sections.create(name='Section CA')

    tcase.course.reset_thread_section_sort_order()

    tcase.page_contenttype = ContentType.objects.get_for_model(Page)
    tcase.image_contenttype = ContentType.objects.get_for_model(Image)
    tcase.video_contenttype = ContentType.objects.get_for_model(Video)
    tcase.assessment_contenttype = ContentType.objects.get_for_model(Assessment)

    PageType.objects.create(code="pagetype", name="Page Type", default=True)
    video_type = VideoType.objects.create(code="videotype", 
                                         name="Video Type",
                                         description="hi")
    quiz = AssessmentType.objects.create(code="quiz", name="Quiz")

    tcase.contentlist = []
    page = Page.objects.create(code="pagea", title="Page a")
    
    thecontent = tcase.sectionAA.thread_contents.create(
        content_type =  tcase.page_contenttype,
        object_id = page.id,
    )
    tcase.contentlist.append(thecontent)

    assessment = Assessment.objects.create(code="assessmenta",
                        name="Assessment a", assessment_type=quiz,
                        course=tcase.course,
    )
    thecontent = tcase.sectionBA.thread_contents.create(
        content_type =  tcase.assessment_contenttype,
        object_id = assessment.id,
    )
    tcase.contentlist.append(thecontent)

    page = Page.objects.create(code="pageb", title="Page b")
    thecontent = tcase.sectionBA.thread_contents.create(
        content_type =  tcase.page_contenttype,
        object_id = page.id,
    )
    tcase.contentlist.append(thecontent)

    thecontent = tcase.sectionBA.thread_contents.create(
        content_type =  tcase.assessment_contenttype,
        object_id = assessment.id,
        substitute_title = "new time for assessment",
    )
    tcase.contentlist.append(thecontent)


    image = Image.objects.create(code="imagea", title="Image a")

    thecontent = tcase.sectionC.thread_contents.create(
        content_type =  tcase.image_contenttype,
        object_id = image.id,
    )
    tcase.contentlist.append(thecontent)


    video = Video.objects.create(code="videoa", title="Video a", 
                                 video_type=video_type )
    thecontent = tcase.sectionC.thread_contents.create(
        content_type =  tcase.video_contenttype,
        object_id = video.id,
    )
    tcase.contentlist.append(thecontent)

    for tc in tcase.contentlist:
        tc.refresh_from_db()
    
    tcase.thread_url = reverse('mithreads:thread', 
                              kwargs={'course_code': tcase.course.code})
    tcase.thread_edit_url = reverse('mithreads:thread-edit', 
                                   kwargs={'course_code': tcase.course.code})

    u=User.objects.create_user("student", password="pass")
    tcase.student = u.courseuser
    u=User.objects.create_user("instructor", password="pass")
    tcase.instructor = u.courseuser
    u=User.objects.create_user("designer", password="pass")
    tcase.designer = u.courseuser


    tcase.course.courseenrollment_set.create(
        student=tcase.student, date_enrolled=timezone.now())
    tcase.course.courseenrollment_set.create(
        student=tcase.instructor, date_enrolled=timezone.now(),
        role=INSTRUCTOR_ROLE)
    tcase.course.courseenrollment_set.create(
        student=tcase.designer, date_enrolled=timezone.now(),
        role=DESIGNER_ROLE)

    # run return_selected_course() so that course will be selected by default
    tcase.student.return_selected_course()
    tcase.instructor.return_selected_course()
    tcase.designer.return_selected_course()




class TestThreadConstruction(TestCase):
    def setUp(self):
        set_up_data(self)

    def test_render_thread(self):
        response = self.client.get(self.thread_url)
        self.assertEqual(response.context['course'],self.course)
        self.assertTemplateUsed(response,"micourses/threads/thread_detail.html")
        for tc in self.contentlist:
            self.assertContains(response, tc.return_link())


    def test_thread_edit_access(self):
        response = self.client.get(self.thread_edit_url)
        self.assertRedirects(response, self.thread_url)
        
        self.client.login(username="student",password="pass")
        response = self.client.get(self.thread_edit_url)
        self.assertRedirects(response, self.thread_url)

        self.client.login(username="instructor",password="pass")
        response = self.client.get(self.thread_edit_url)
        self.assertRedirects(response, self.thread_url)

        self.client.login(username="designer",password="pass")
        response = self.client.get(self.thread_edit_url)
        self.assertEqual(response.context['course'],self.course)
        self.assertTemplateUsed(response,"micourses/threads/thread_edit.html")
        for tc in self.contentlist:
            self.assertContains(response, tc.return_link())




class SeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumTests, cls).setUpClass()
        cls.selenium = WebDriver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def setUp(self):
        set_up_data(self)
        self.login_url= reverse("mi-login")

    def test_thread(self):
        self.selenium.get('%s%s' % (self.live_server_url, self.thread_url))

        
        def test_section(section):
            section_elt = self.selenium.find_element_by_id(
                'thread_section_%s' % section.id)
            for cs in section.child_sections.all():
                test_section(cs)
            self.assertTrue(section.name in section_elt.text)
            for content in section.thread_contents.all():
                if content.substitute_title:
                    self.assertTrue(content.substitute_title in section_elt.text)
                else:
                    try:
                        title = content.content_object.get_title()
                    except AttributeError:
                        title = content.content_object.get_annotated_title()
                    self.assertTrue(title in section_elt.text)
            
        
        for section in self.course.thread_sections.all()[:2]:
            test_section(section)


    def test_edit_thread_sections(self):
        from selenium.webdriver.common.by import By
        timeout=10
        wait = WebDriverWait(self.selenium, timeout)

        self.selenium.get('%s%s?next=%s' %
                (self.live_server_url, self.login_url, self.thread_edit_url))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('designer')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('pass')
  
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()

        ######################################
        # check commands and relationship of first few elements
        ######################################

        base_sections = self.course.thread_sections.all()

        # commands of first section and child
        first_section = base_sections[0]
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section.id)
        self.assertEqual(commands.text, "[down] [delete] [change name]")

        first_section_child = first_section.child_sections.first()
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [down] [delete] [change name]")

        # verify that first section is indeed first thread_section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        section_elt_from_xpath = self.selenium.find_element_by_xpath(
            '//ol[@id="child_sections_top"]/li[1]')
        self.assertEqual(section_elt, section_elt_from_xpath)

        
        # verify that child is indeed child of first section
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)


        # commands of second section
        second_section = base_sections[1]

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % second_section.id)
        self.assertEqual(commands.text, 
                         "[right] [up] [down] [delete] [change name]")


        # verify that second section is indeed sibling of first section
        second_from_xpath = section_elt.find_element_by_xpath(
            'following-sibling::li')
        second_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % second_section.id)
        self.assertEqual(second_from_xpath, second_from_id)

        child = second_section.child_sections.first()
        
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % child.id)

        self.assertEqual(commands.text, 
                         "[left] [up] [down] [delete] [change name]")



        ##################################################
        # insert section at top and check changed commands and relationship
        ##################################################

        insert_section_command =self.selenium.find_element_by_id(
            "insert_section_top")
        insert_section_command.click()
        
        section_name = self.selenium.find_element_by_id(
            "insert_section_form_top_section_name")
        section_name.send_keys('new top section')

        section_name.submit()
        #self.selenium.find_element_by_xpath('//form[@id="insert_section_form_top"]//input[@type="submit"]').click()


        # not sure why these attempts for waiting didn't work....
        #self.selenium.implicitly_wait(10)
        #WebDriverWait(self.selenium, timeout).until(EC.text_to_be_present_in_element((By.ID,'child_sections_top'), "new top section"))

        wait.until(EC.visibility_of(insert_section_command))


        new_first_section = base_sections[0]
        self.assertNotEqual(new_first_section, first_section)
        self.assertEqual(new_first_section.name, "new top section")


        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % new_first_section.id)
        self.assertEqual(commands.text, "[down] [delete] [change name]")
        
        
        # should have added new commands to first section and child
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section.id)
        self.assertEqual(commands.text, 
                         "[right] [up] [down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [up] [down] [delete] [change name]")

        # verify that new_first section is indeed first thread_section
        new_first_section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % new_first_section.id)
        section_elt_from_xpath = self.selenium.find_element_by_xpath(
            '//ol[@id="child_sections_top"]/li[1]')
        self.assertEqual(new_first_section_elt, section_elt_from_xpath)

        
        # verify that original first section is first sibling of new first section
        section_from_xpath = new_first_section_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        self.assertEqual(section_from_xpath, section_from_id)
        


        ##################################################
        # insert section as child of original first section 
        # and check changed commands and relationships
        ##################################################

        # if add section to original first section,
        # then original first child section should add a [right]

        insert_section_command =self.selenium.find_element_by_id(
            "insert_section_%s" % first_section.id)
        insert_section_command.click()
        section_name = self.selenium.find_element_by_id(
            "insert_section_form_%s_section_name" % first_section.id)
        section_name.send_keys('new child section')
        section_name.submit()
        wait.until(EC.visibility_of(insert_section_command))

        new_first_section_child = first_section.child_sections.first()
        self.assertNotEqual(new_first_section_child, first_section_child)
        self.assertEqual(new_first_section_child.name, "new child section")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % new_first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [up] [down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [right] [up] [down] [delete] [change name]")

        # verify that child is indeed child of first section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % new_first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)

        # verify the original first child is sibling of new first section
        new_first_section_child_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % new_first_section_child.id)
        section_from_xpath = new_first_section_child_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(section_from_xpath, section_from_id)


        ###################################################
        # delete added sections, commands and relationships should change back
        ###################################################

        # delete new first section
        
        delete_section_command =self.selenium.find_element_by_id(
            "thread_section_delete_%s" % new_first_section.id)
        delete_section_command.click()
        delete_section_command_submit =self.selenium.find_element_by_id(
            "thread_section_delete_submit_%s" % new_first_section.id)
        delete_section_command_submit.click()
        
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
        
        deleted_section = ThreadSection.deleted_objects.get(
            id=new_first_section.id)
        self.assertEqual(deleted_section.name,
                         new_first_section.name)
        new_first_section = base_sections[0]
        self.assertEqual(new_first_section, first_section)

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section.id)
        self.assertEqual(commands.text, 
                         "[down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % new_first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [right] [up] [down] [delete] [change name]")

        
        # verify that first section is indeed first thread_section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        section_elt_from_xpath = self.selenium.find_element_by_xpath(
            '//ol[@id="child_sections_top"]/li[1]')
        self.assertEqual(section_elt, section_elt_from_xpath)

        
        # delete new first child section
        
        delete_section_command =self.selenium.find_element_by_id(
            "thread_section_delete_%s" % new_first_section_child.id)
        delete_section_command.click()
        delete_section_command_submit =self.selenium.find_element_by_id(
            "thread_section_delete_submit_%s" % new_first_section_child.id)
        delete_section_command_submit.click()
        
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        deleted_section = ThreadSection.deleted_objects.get(
            id=new_first_section_child.id)
        self.assertEqual(deleted_section.name,
                         new_first_section_child.name)
        new_first_section_child = first_section.child_sections.first()
        self.assertEqual(new_first_section_child, first_section_child)

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, 
                         "[left] [down] [delete] [change name]")


        # verify that first_section_child is first child for first section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)


        ###########################################################
        # move original first section back to down then back to top
        ###########################################################

        move_down_section_command =self.selenium.find_element_by_id(
            "thread_section_down_%s" % first_section.id)
        move_down_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
        
        self.assertEqual(list(base_sections[:2]), [second_section, first_section])

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section.id)
        self.assertEqual(commands.text,
                         "[right] [up] [down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [up] [down] [delete] [change name]")

        # verify that first_section is first sibling of second_section
        second_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % second_section.id)
        section_from_xpath = second_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        self.assertEqual(section_from_xpath, section_from_id)


        move_up_section_command =self.selenium.find_element_by_id(
            "thread_section_up_%s" % first_section.id)
        move_up_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
                
        self.assertEqual(list(base_sections[:2]), [first_section, second_section])

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section.id)
        self.assertEqual(commands.text, "[down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [down] [delete] [change name]")
        
        
        # verify that second_section is first sibling of first_section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        section_from_xpath = section_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % second_section.id)
        self.assertEqual(section_from_xpath, section_from_id)


        ########################################
        # add second child to first section and move sections left/right
        ########################################

        insert_section_command =self.selenium.find_element_by_id(
            "insert_section_%s" % first_section.id)
        insert_section_command.click()
        section_name = self.selenium.find_element_by_id(
            "insert_section_form_%s_section_name" % first_section.id)
        section_name.send_keys('new child section')
        section_name.submit()
        wait.until(EC.visibility_of(insert_section_command))

        first_section_child2 = first_section.child_sections.first()
        self.assertEqual(first_section_child2.name, "new child section")

        # verify commands
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [right] [up] [down] [delete] [change name]")

        # move first child right
        move_right_section_command =self.selenium.find_element_by_id(
            "thread_section_right_%s" % first_section_child.id)
        move_right_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(first_section_child2.child_sections.first(),
                         first_section_child)

        # verify commands
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child2.id)
        self.assertEqual(commands.text, "[left] [down] [delete] [change name]")


        # verify relationships
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)
        
        section_elt = child_elt_from_id
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)
        
        
        # move child 2 left
        move_left_section_command =self.selenium.find_element_by_id(
            "thread_section_left_%s" % first_section_child2.id)
        move_left_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(list(base_sections[:2]), 
                         [first_section, first_section_child2])
        self.assertEqual(first_section_child2.child_sections.first(),
                         first_section_child)

        # verify commands
        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child.id)
        self.assertEqual(commands.text, "[left] [up] [down] [delete] [change name]")

        commands = self.selenium.find_element_by_id(
            "thread_section_commands_%s" % first_section_child2.id)
        self.assertEqual(commands.text, 
                         "[right] [up] [down] [delete] [change name]")

        
        # verify relationship
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        section_from_xpath = section_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertEqual(section_from_xpath, section_from_id)

        section_elt = section_from_id
        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)


        # move child2 back right, child left, then child2 left
        move_right_section_command =self.selenium.find_element_by_id(
            "thread_section_right_%s" % first_section_child2.id)
        move_right_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(first_section.child_sections.first(),
                         first_section_child2)
        self.assertEqual(first_section_child2.child_sections.first(),
                         first_section_child)

        move_left_section_command =self.selenium.find_element_by_id(
            "thread_section_left_%s" % first_section_child.id)
        move_left_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
        self.assertEqual(list(first_section.child_sections.all()),
                         [first_section_child2, first_section_child])

        move_left_section_command =self.selenium.find_element_by_id(
            "thread_section_left_%s" % first_section_child2.id)
        move_left_section_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(list(first_section.child_sections.all()),
                         [first_section_child])
        self.assertEqual(list(base_sections[:2]), 
                         [first_section, first_section_child2])
        
        # now child should be child of first section
        # and child2 should be first sibling of first section
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section.id)
        section_from_xpath = section_elt.find_element_by_xpath(
            'following-sibling::li')
        section_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertEqual(section_from_xpath, section_from_id)

        child_elt_from_xpath = section_elt.find_element_by_xpath('ol/li[1]')
        child_elt_from_id = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child.id)
        self.assertEqual(child_elt_from_xpath, child_elt_from_id)


        ################
        # rename section
        ################
        
        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertTrue("new child section" in section_elt.text)
        
        change_name_command =self.selenium.find_element_by_id(
            "thread_section_edit_%s" % first_section_child2.id)
        change_name_command.click()
        section_name = self.selenium.find_element_by_id(
            "edit_section_form_%s_section_name" % first_section_child2.id)
        section_name.send_keys('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b')
        section_name.send_keys('a brand new name')
        section_name.submit()
        wait.until(EC.visibility_of(change_name_command))

        first_section_child2.refresh_from_db()
        self.assertEqual(first_section_child2.name, "a brand new name")

        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertTrue("a brand new name" in section_elt.text)
        self.assertFalse("child" in section_elt.text)
        
        # change again but cancel
        change_name_command =self.selenium.find_element_by_id(
            "thread_section_edit_%s" % first_section_child2.id)
        change_name_command.click()
        section_name = self.selenium.find_element_by_id(
            "edit_section_form_%s_section_name" % first_section_child2.id)
        section_name.send_keys('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b')
        section_name.send_keys('just kidding')
        self.selenium.find_element_by_xpath(
            '//form[@id="edit_section_form_%s"]/input[@value="Cancel"]' % \
            first_section_child2.id).click()
        
        wait.until(EC.visibility_of(change_name_command))

        first_section_child2.refresh_from_db()
        self.assertEqual(first_section_child2.name, "a brand new name")

        section_elt = self.selenium.find_element_by_id(
            "thread_section_%s" % first_section_child2.id)
        self.assertTrue("a brand new name" in section_elt.text)
        self.assertFalse("kidding" in section_elt.text)



    def test_edit_thread_content(self):
        from selenium.webdriver.common.by import By
        timeout=10
        wait = WebDriverWait(self.selenium, timeout)

        self.selenium.get('%s%s?next=%s' %
                (self.live_server_url, self.login_url, self.thread_edit_url))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('designer')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('pass')
  
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()

        ######################################
        # check location of first content
        ######################################

        base_sections = self.course.thread_sections.all()
        all_content = self.course.thread_contents.all()

        first_section = base_sections[0]
        second_section = base_sections[1]
        first_section_child = first_section.child_sections.first()

        first_content = all_content[0]
        
        # first section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        self.assertEqual(content_section.text, "")

        # child section contains first_content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section_child.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % first_content.id)
        self.assertEqual(content_by_xpath, content_by_id)

        # second section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % second_section.id)
        self.assertEqual(content_section.text, "")
        
        # check commands
        commands = self.selenium.find_element_by_id(
            "thread_content_commands_%s" % first_content.id)
        self.assertEqual(commands.text, "[up] [down] [delete] [edit]")

        ########################
        # move content up
        ########################

        move_up_content_command =self.selenium.find_element_by_id(
            "thread_content_up_%s" % first_content.id)
        move_up_content_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(list(first_section.thread_contents.all()), [first_content])
        self.assertEqual(list(first_section_child.thread_contents.all()), [])
        self.assertEqual(list(second_section.thread_contents.all()), [])
        

        # first section contains first_content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % first_content.id)
        self.assertEqual(content_by_xpath, content_by_id)
        
        # child section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section_child.id)
        self.assertEqual(content_section.text, "")

        # second section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % second_section.id)
        self.assertEqual(content_section.text, "")

        # check commands
        commands = self.selenium.find_element_by_id(
            "thread_content_commands_%s" % first_content.id)
        self.assertEqual(commands.text, "[down] [delete] [edit]")


        ########################
        # move content down
        ########################

        move_down_content_command =self.selenium.find_element_by_id(
            "thread_content_down_%s" % first_content.id)
        move_down_content_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
        self.assertEqual(list(first_section.thread_contents.all()), [])
        self.assertEqual(list(first_section_child.thread_contents.all()), 
                         [first_content])
        self.assertEqual(list(second_section.thread_contents.all()), [])

        # first section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        self.assertEqual(content_section.text, "")

        # child section contains first_content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section_child.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % first_content.id)
        self.assertEqual(content_by_xpath, content_by_id)

        # second section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % second_section.id)
        self.assertEqual(content_section.text, "")
        
        # check commands
        commands = self.selenium.find_element_by_id(
            "thread_content_commands_%s" % first_content.id)
        self.assertEqual(commands.text, "[up] [down] [delete] [edit]")


        move_down_content_command =self.selenium.find_element_by_id(
            "thread_content_down_%s" % first_content.id)
        move_down_content_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        self.assertEqual(list(first_section.thread_contents.all()), [])
        self.assertEqual(list(first_section_child.thread_contents.all()), [])
        self.assertEqual(list(second_section.thread_contents.all()), 
                         [first_content])

        # first section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        self.assertEqual(content_section.text, "")

        # child section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section_child.id)
        self.assertEqual(content_section.text, "")

        # second section contains first_content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % second_section.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % first_content.id)
        self.assertEqual(content_by_xpath, content_by_id)

        # check commands
        commands = self.selenium.find_element_by_id(
            "thread_content_commands_%s" % first_content.id)
        self.assertEqual(commands.text, "[up] [down] [delete] [edit]")


        # move back up to original position
        move_up_content_command =self.selenium.find_element_by_id(
            "thread_content_up_%s" % first_content.id)
        move_up_content_command.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        ##########################
        # add content to first section
        ##########################

        insert_content_command =self.selenium.find_element_by_id(
            "insert_content_%s" % first_section.id)
        insert_content_command.click()

        insert_content_form = self.selenium.find_element_by_id(
            "content_form_insert_%s" % first_section.id)

        wait.until(EC.visibility_of(insert_content_form))
        
        content_to_add = Video.objects.first()
        
        content_type = insert_content_form.find_element_by_id(
            "content_form_insert_%s_content_type" % first_section.id)
        content_type.send_keys('video')
        
        substitute_title = insert_content_form.find_element_by_id(
            "content_form_insert_%s_substitute_title" % first_section.id)
        substitute_title.send_keys("A cool video: %s" % content_to_add.title)

        object_id = insert_content_form.find_element_by_id(
            "content_form_insert_%s_object_id" % first_section.id)
        object_id.send_keys(content_to_add.code)

        object_id.submit()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        new_content = first_section.thread_contents.first()
        self.assertEqual(new_content.content_object, content_to_add)
        self.assertEqual(new_content.substitute_title,
                         "A cool video: %s" % content_to_add.title)

        # first section contains added content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % new_content.id)
        self.assertEqual(content_by_xpath, content_by_id)
        self.assertTrue("A cool video: %s" % content_to_add.title in \
                        content_by_id.text)

        ##########################
        # cancel add content to second section
        ##########################

        insert_content_command =self.selenium.find_element_by_id(
            "insert_content_%s" % second_section.id)
        insert_content_command.click()

        insert_content_form = self.selenium.find_element_by_id(
            "content_form_insert_%s" % second_section.id)

        wait.until(EC.visibility_of(insert_content_form))

        content_not_to_add = Applet.objects.first()

        content_type = insert_content_form.find_element_by_id(
            "content_form_insert_%s_content_type" % second_section.id)
        content_type.send_keys('applet')
        
        substitute_title = insert_content_form.find_element_by_id(
            "content_form_insert_%s_substitute_title" % second_section.id)
        substitute_title.send_keys("Won't add applet: %s" % content_to_add.title)

        object_id = insert_content_form.find_element_by_id(
            "content_form_insert_%s_object_id" % second_section.id)
        object_id.send_keys(content_to_add.code)

        insert_content_form.find_element_by_xpath(
            'p/input[@value="Cancel"]').click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))


        self.assertEqual(second_section.thread_contents.first(), None)

        # second section content is blank
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % second_section.id)
        self.assertEqual(content_section.text, "")


        ##########################
        # add content to child section
        ##########################

        insert_content_command =self.selenium.find_element_by_id(
            "insert_content_%s" % first_section_child.id)
        insert_content_command.click()

        insert_content_form = self.selenium.find_element_by_id(
            "content_form_insert_%s" % first_section_child.id)

        wait.until(EC.visibility_of(insert_content_form))

        content_to_add = Assessment.objects.first()

        content_type = insert_content_form.find_element_by_id(
            "content_form_insert_%s_content_type" % first_section_child.id)
        content_type.send_keys('assessment')

        substitute_title = insert_content_form.find_element_by_id(
            "content_form_insert_%s_substitute_title" % first_section_child.id)
        substitute_title.send_keys("This assessment isn't bad")
        
        content_type.submit()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".errorlist")))

        error_message = self.selenium.find_element_by_xpath(
            "//div[@id='content_form_inner_insert_%s']/ul[1]/li" % \
            first_section_child.id)

        self.assertEqual(error_message.text, "This field is required.")

        object_id = insert_content_form.find_element_by_id(
            "content_form_insert_%s_object_id" % first_section_child.id)
        object_id.send_keys(content_to_add.code)

        object_id.submit()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        new_content = first_section_child.thread_contents.last()
        self.assertEqual(new_content.content_object, content_to_add)
        self.assertEqual(new_content.substitute_title,
                         "This assessment isn't bad")

        other_content = first_section_child.thread_contents.first()

        # first section contains added content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section_child.id)
        content_by_xpath=content_section.find_elements_by_xpath('li')
        content_by_id = [self.selenium.find_element_by_id( \
                            'thread_content_%s' % other_content.id),
                         self.selenium.find_element_by_id(
                             'thread_content_%s' % new_content.id)]
        
        self.assertEqual(content_by_xpath, content_by_id)

        self.assertTrue("This assessment isn't bad" in \
                        content_by_id[1].text)



        ##########################
        # delete new content from child section
        ##########################
        
        
        delete_content_command =self.selenium.find_element_by_id(
            "thread_content_delete_%s" % new_content.id)
        delete_content_command.click()
        delete_content_command_submit =self.selenium.find_element_by_id(
            "thread_content_delete_submit_%s" % new_content.id)
        delete_content_command_submit.click()
        
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))
        
        deleted_content = ThreadContent.deleted_objects.get(
            id=new_content.id)
        self.assertEqual(deleted_content.content_object,
                         new_content.content_object)
        self.assertEqual(list(first_section_child.thread_contents.all()),
                         [other_content])


        ###################################
        # edit content added to first section
        ###################################
        
        new_content = first_section.thread_contents.first()
        
        edit_content_command =self.selenium.find_element_by_id(
            "thread_content_edit_%s" % new_content.id)
        edit_content_command.click()

        edit_content_form = self.selenium.find_element_by_id(
            "content_form_edit_%s" % new_content.id)

        wait.until(EC.visibility_of(edit_content_form))
        
        substitute_title = edit_content_form.find_element_by_id(
            "content_form_edit_%s_substitute_title" % new_content.id)
        substitute_title.send_keys("\b"*50)
        substitute_title.send_keys("replacement title")
        
        substitute_title.submit()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                                                     ".edit_link")))

        new_content.refresh_from_db()
        self.assertEqual(new_content.substitute_title, "replacement title")

        
        # first section contains added content
        content_section = self.selenium.find_element_by_id(
            'thread_content_section_%s' % first_section.id)
        content_by_xpath=content_section.find_element_by_xpath('li')
        content_by_id = self.selenium.find_element_by_id(
            'thread_content_%s' % new_content.id)
        self.assertEqual(content_by_xpath, content_by_id)
        self.assertTrue("replacement title" in content_by_id.text)
