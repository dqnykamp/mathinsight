from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax
#from dajaxice.utils import deserialize_form
from mitesting.forms import MultipleChoiceQuestionForm, MathWriteInForm
from mitesting.models import Question
from midocs.models import Page
from micourses.models import QuestionStudentAnswer
from mithreads.models import Thread, ThreadSection, ThreadContent
from mithreads.forms import ThreadSectionForm, ThreadContentForm
from django.contrib.contenttypes.models import ContentType
import re

@dajaxice_register
def send_multiple_choice_question_form(request, form, prefix, seed, identifier):

    dajax = Dajax()

    try:
        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']

        form = MultipleChoiceQuestionForm(form_dict, prefix=prefix)
        question_context=None

        if form.is_valid():
            theanswer = form.cleaned_data.get('answers')
            general_feedback_selector = "#question_%s_feedback" % identifier
            answer_feedback_selector_base = '#feedback_%s-answers' % identifier
            answer_feedback_selector = "%s_%s" % (answer_feedback_selector_base, theanswer.pk)
           
            
            # clear any previous answer feedback
            dajax.assign(general_feedback_selector, 'innerHTML', '')
            for answer_option in theanswer.question.questionansweroption_set.all():
                the_selector = "%s_%s" % (answer_feedback_selector_base, answer_option.pk)
                dajax.assign(the_selector, 'innerHTML', '')
                

            credit=0
            # check if answer is correct
            if(theanswer.correct):
                credit=1
                dajax.assign(answer_feedback_selector, 'innerHTML', '<p class="success" style="margin-top: 0;">Yes, you are correct!</p>')
                dajax.add_css_class('#label_%s-answers_%s' % (identifier, theanswer.pk), 'correct')
            else:
                dajax.assign(answer_feedback_selector, 'innerHTML', '<p class="error" style="margin-top: 0;">No, try again.</p>') 
                dajax.add_css_class('#label_%s-answers_%s' % (identifier, theanswer.pk), 'wrong')

            
            if(theanswer.feedback):
                if not question_context:
                    question_context=theanswer.question.setup_context(seed=seed, identifier=identifier)
                dajax.append(general_feedback_selector, 'innerHTML', '<p>%s</p>' % theanswer.render_feedback(question_context))
        

            # record answer by user
            try:
                if request.user.is_authenticated():
                    if not question_context:
                        question_context=theanswer.question.setup_context(seed=seed, identifier=identifier)
                    QuestionStudentAnswer.objects.create(user=request.user, question=theanswer.question, answer=theanswer.render_answer(question_context), seed=seed, credit=credit)
                    dajax.append(general_feedback_selector, 'innerHTML', '<p><i>Answer recorded for %s.</i></p>' % request.user)
            except Exception as e:
                pass


        else:
            # dajax.remove_css_class('#my_form input', 'error')
            try:
                errorlist=""
                for error in form.errors:
                    errorlist = "%s %s" % (errorlist, error)
                    for error in form.answers.errors:
                        errorlist = "%s %s" % (errorlist, error)
                        
            #     dajax.add_css_class('#id_%s' % error, 'error')
                dajax.alert("something invalid about form: %s" % errorlist)
            except Exception as e:
                dajax.alert("not sure what is wrong: %s" % e )
    except Exception as e:
        dajax.alert("not sure what is wrong 2: %s" % e )

    return dajax.json()



@dajaxice_register
def check_math_write_in(request, answer, question_id, seed, identifier):
    
    dajax = Dajax()

    try: 
        feedback_selector = "#question_%s_feedback" % identifier
        # clear any previous answer feedback
        dajax.assign(feedback_selector, 'innerHTML', '')

        from mitesting.math_objects import parse_and_process, math_object

        the_question = Question.objects.get(id=question_id)

        try:

            question_context = the_question.setup_context(seed=seed, identifier=identifier)
            question_context['identifier'] = identifier

            # render question text to add answer_list to question_context
            the_question.render_text(question_context, identifier='hmm', show_help=False)

            the_correct_answers = question_context.get('answer_list',[])
            
        except Exception as e:
            dajax.alert("Something wrong with solution: %s" % e )

            dajax.append(feedback_selector, 'innerHTML', "<p>Sorry, we messed up.  There is something wrong with the solution for this problem.  You'll get this error no matter what you type...</p>")
            return dajax.json()

        points_achieved=0
        total_points=0

        the_answers={}
        answer_dict = {}
        for  obj in answer:
            answer_dict[obj['name']]=obj['value']
            
        for answer_tuple in the_correct_answers:
            answer_string = answer_tuple[0]

            the_answer= answer_dict['answer_%s_%s' % (answer_string, identifier)]
            

            try:
                the_correct_answer = answer_tuple[1]
                answer_points = answer_tuple[2]
                total_points += answer_points

                answer_feedback_selector = "#answer_%s_%s_feedback" % (answer_string, identifier)

                # get rid of any .methods, so can't call commands like
                # .expand() or .factor()
                the_answer = re.sub('\.[a-zA-Z]+', '', the_answer)
                global_dict = the_question.return_sympy_global_dict()
                the_answer_parsed = parse_and_process(the_answer, 
                                                      global_dict=global_dict)
                
                the_answer_parsed=math_object(the_answer_parsed,
                                              tuple_is_ordered=the_correct_answer.return_if_ordered())

                the_answers[answer_string] = the_answer_parsed.return_expression()
            except Exception as e:
                if the_answer:
                    feedback_message = 'Sorry.  Unable to understand the answer.'
                else:
                    feedback_message = 'No answer.'
                #feedback_message += '<a id="error_show_info_%s">(Show computer error message)</a>' % identifier
                #dajax.alert("%s" % e)
                dajax.assign(answer_feedback_selector, 'innerHTML', feedback_message)

            else:

                #dajax.alert("answer = %s, correct_answer = %s" % (the_answer_parsed,the_correct_answer))
                correctness_of_answer = the_correct_answer.compare_with_expression \
                    (the_answer_parsed.return_expression())
                
                feedback=''
                if correctness_of_answer == 1:
                    points_achieved += answer_points
                    feedback='Yes, $%s$ is correct.' % the_answer_parsed
                    dajax.remove_css_class(answer_feedback_selector, 'error')
                    dajax.add_css_class(answer_feedback_selector, 'success')

                elif correctness_of_answer == -1:
                    feedback="No, $%s$ is not correct.  You are close as your answer is mathematically equivalent to the correct answer, but this question requires you to write your answer in a different form." % the_answer_parsed
                    dajax.remove_css_class(answer_feedback_selector, 'success')
                    dajax.add_css_class(answer_feedback_selector, 'error')
                else:
                    feedback='No, $%s$ is incorrect.  Try again.' % the_answer_parsed
                    dajax.remove_css_class(answer_feedback_selector, 'success')
                    dajax.add_css_class(answer_feedback_selector, 'error')


                dajax.assign(answer_feedback_selector, 'innerHTML', feedback)


        # increment number of attempts
        try:
            number_attempts = int(answer_dict['number_attempts_%s' % identifier])
        except:
            number_attempts=0
        number_attempts+=1
        dajax.assign('#id_number_attempts_%s' % identifier,'value',str(number_attempts))
        
        credit = points_achieved/float(total_points)
        if points_achieved == total_points:
            dajax.append(feedback_selector, 'innerHTML', '<p>Answer is correct.</p>')
        elif points_achieved == 0:
            dajax.append(feedback_selector, 'innerHTML', '<p>Answer is incorrect.</p>')
        else:
            the_feedback = '<p>Answer is %s' % round(credit*100) 
            the_feedback += "% correct</p>"
            dajax.append(feedback_selector, 'innerHTML', the_feedback)

        allow_solution_buttons = answer_dict['asb_%s' % identifier]

        # check if question or subpart has something written in for solution
        solution_exists = False
        if the_question.solution_text:
            solution_exists = True
        else:
            for question_subpart in the_question.questionsubpart_set.all():
                if question_subpart.solution_text:
                    solution_exists = True
                    break
        
        if allow_solution_buttons and \
                the_question.show_solution_button_after_attempts and \
                number_attempts >= the_question.show_solution_button_after_attempts \
                and solution_exists and \
                the_question.user_can_view(request.user, solution=True):

            
            #show_solution_command = "Dajaxice.midocs.show_math_write_in_solution(callback_%s,{ 'seed':'%s', 'question_id': '%s', 'identifier': '%s' });" % ( identifier, seed, question_id, identifier)
            from django.template import Template
            csrftoken=request.COOKIES.get('csrftoken') 
            question_context['csrf_token']=csrftoken
            show_solution_string = '<form action="%s" method="post" target="_blank">{%% csrf_token%%}<input type="hidden" id="id_seed_%s" name="seed" value="%s"><input type="submit" value="Show solution"></form>' % (the_question.get_solution_url(), identifier, seed)
            show_solution_string = Template(show_solution_string).render(question_context)
            dajax.assign("#extra_buttons_%s" % identifier, 'innerHTML', show_solution_string)
        


        # record answer by user
        try:
            if request.user.is_authenticated():
                the_answer_string = "%s" % the_answers
                QuestionStudentAnswer.objects.create(user=request.user, question=the_question, answer=the_answers, seed=seed, credit=credit)
                dajax.append(feedback_selector, 'innerHTML', '<p><i>Answer recorded for %s.</i></p>' % request.user)
        except Exception as e:
            pass
        

    except Exception as e:
        dajax.alert("not sure what is wrong: %s" % e )

    return dajax.json()


@dajaxice_register
def show_math_write_in_solution(request, question_id, seed, identifier):
    
    dajax = Dajax()

    try: 
        the_question = Question.objects.get(id=question_id)

        question_context = the_question.setup_context(seed=seed, identifier=identifier)
        question_context['identifier'] = identifier

        # render question text to add answer_list to question_context
        rendered_solution = the_question.render_text \
            (question_context, identifier='hmm', \
                 show_help=False, solution=True, seed_used=seed)

        rendered_solution = "<h5>Solution</h5><p>%s</p>"  % rendered_solution

        solution_selector = "#question_%s_solution" % identifier
        dajax.assign(solution_selector, 'innerHTML', rendered_solution)

    except Exception as e:
        dajax.alert("not sure what is wrong: %s" % e )

    return dajax.json()

    
@dajaxice_register
def dec_section_level(request, section_code, thread_code):
    dajax = Dajax()
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        if thread_section.level > 1:
            thread_section.level = thread_section.level - 1
            thread_section.save()
            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_section.thread.render_html_edit_string())
    except:
        pass
    return dajax.json()

@dajaxice_register
def inc_section_level(request, section_code, thread_code):
    dajax = Dajax()
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        thread_section.level = thread_section.level + 1
        thread_section.save()
        dajax.assign('#thread_contents', 'innerHTML', \
                         thread_section.thread.render_html_edit_string())
    except:
        pass
    return dajax.json()

@dajaxice_register
def move_section_up(request, section_code, thread_code):
    dajax = Dajax()
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        previous_section = thread_section.find_previous_section()
        if previous_section:
            this_sort_order=thread_section.sort_order
            previous_sort_order=previous_section.sort_order
            # if sort_orders are the same, 
            # redo all sort orders before continuing
            if this_sort_order==previous_sort_order:
                for (i,ts) in enumerate(thread_section.thread.thread_sections.all()):
                    ts.sort_order=i
                    ts.save()
                thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
                previous_section = thread_section.find_previous_section()
                this_sort_order=thread_section.sort_order
                previous_sort_order=previous_section.sort_order

            thread_section.sort_order = previous_sort_order
            previous_section.sort_order = this_sort_order
            thread_section.save()
            previous_section.save()
            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_section.thread.render_html_edit_string())
    except:
        pass
    return dajax.json()

@dajaxice_register
def move_section_down(request, section_code, thread_code):
    dajax = Dajax()
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        next_section = thread_section.find_next_section()
        if next_section:
            this_sort_order=thread_section.sort_order
            next_sort_order=next_section.sort_order
            # if sort_orders are the same, 
            # redo all sort orders before continuing
            if this_sort_order==next_sort_order:
                for (i,ts) in enumerate(thread_section.thread.thread_sections.all()):
                    ts.sort_order=i
                    ts.save()
                thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
                next_section = thread_section.find_next_section()
                this_sort_order=thread_section.sort_order
                next_sort_order=next_section.sort_order
            thread_section.sort_order = next_sort_order
            next_section.sort_order = this_sort_order
            thread_section.save()
            next_section.save()
            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_section.thread.render_html_edit_string())
    except:
        pass
    return dajax.json()

@dajaxice_register
def delete_section(request, section_code, thread_code):
    dajax = Dajax()

    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        delete_prompt = '<h5>Confirm Delete Section</h5><p>Are you sure you want to delete the section: %s?</p>' % thread_section.name
        
        thread_content = thread_section.threadcontent_set.all()
        if thread_content:
            course_set=[]
            delete_prompt += '<p>Deleting will also delete the following from the thread:</p><ul>'
            
            for content in thread_content:
                delete_prompt += '<li>%s</li>' % content.get_title()

                course_thread_content = \
                    content.coursethreadcontent_set.all()
                if course_thread_content:
                    for course_content in course_thread_content:
                        course_name = course_content.course.name
                        if course_name not in course_set:
                            course_set.append(course_name)

            delete_prompt += '</ul>'

            if course_set:
                delete_prompt += '<p>Deleting will also delete content from the following courses:</p><ul>'
            
                for course_name in course_set:
                    delete_prompt += '<li>%s</li>' % course_name
                delete_prompt += '</ul>'


        click_command_base = thread_section.get_click_command_base()
        
        click_command = click_command_base % 'confirm_delete_section'
        delete_prompt += '<p><input type="button" value="Yes" onclick="%s;">' % click_command

        click_command = click_command_base % 'cancel_delete_section'
        delete_prompt += '<input type="button" value="No" onclick="%s;" style="margin-left: 3px;"></p>' % click_command
        dajax.assign('#%s_section_info_box' % section_code, 'innerHTML', \
                         delete_prompt)

        dajax.add_css_class('#%s_section_info_box' % section_code, 'thread_info_box')


    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def cancel_delete_section(request, section_code, thread_code):
    dajax = Dajax()
    
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        dajax.assign('#%s_section_info_box' % section_code, 'innerHTML', '')
        dajax.remove_css_class('#%s_section_info_box' % section_code, 'thread_info_box')

        
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def confirm_delete_section(request, section_code, thread_code):
    dajax = Dajax()
    
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)

        thread_section.delete()

        dajax.assign('#thread_contents', 'innerHTML', \
                         thread_section.thread.render_html_edit_string())
        dajax.remove_css_class('#%s_section_info_box' % section_code, 'thread_info_box')
  
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def edit_section(request, section_code, thread_code):
    dajax = Dajax()
    
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        
        section_form = ThreadSectionForm({'section_name':thread_section.name, 'section_code': thread_section.code})
        
        send_command = "Dajaxice.midocs.confirm_edit_section(Dajax.process,{'section_code': '%s', 'thread_code': '%s', 'form':$('#%s_edit_section_form').serializeArray()})" % (section_code, thread_code, section_code)

        cancel_command = "Dajaxice.midocs.cancel_edit_section(Dajax.process,{'section_code': '%s', 'thread_code': '%s'})" % (section_code, thread_code)
    
        form_html = '<label for="id_section_name">Section name:</label> %s<div class="error" id="%s_section_name_errors"></div><br/><label for="id_section_code">Section code:</label> %s<div class="error" id="%s_section_code_errors"></div>' % (section_form['section_name'], section_code, section_form['section_code'], section_code)

        form_html = '<form action="" method="post" id="%s_edit_section_form" accept-charset="utf-8">%s<input type="button" value="Modify section" onclick="%s;"> <input type="button" value="Cancel" onclick="%s;"></form>' % (section_code,form_html, send_command, cancel_command)
        
        dajax.assign('#thread_section_%s' % section_code, 'innerHTML', \
                         form_html)

    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()


@dajaxice_register
def confirm_edit_section(request, section_code, thread_code, form):
    dajax = Dajax()
    
    try:
        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']
        form = ThreadSectionForm(form_dict)
        
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)

        if form.is_valid():
            new_section_name = form.cleaned_data.get('section_name')
            new_section_code = form.cleaned_data.get('section_code')
            
            thread_section.name = new_section_name
            thread_section.code = new_section_code

            thread_section.save()

            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_section.thread.render_html_edit_string())

        # if form is not valid
        else:
            dajax.assign('#%s_section_name_errors' % section_code,
                         'innerHTML',
                         form['section_name'].errors)
            dajax.assign('#%s_section_code_errors' % section_code,
                         'innerHTML',
                         form['section_code'].errors)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()


@dajaxice_register
def cancel_edit_section(request, section_code, thread_code):
    dajax = Dajax()
    
    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        dajax.assign('#thread_section_%s' % section_code, 'innerHTML', \
                         thread_section.return_html_innerstring(True))

    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()


@dajaxice_register
def insert_section_form_top(request, thread_code):
    dajax = Dajax()

    try:
        section_form = ThreadSectionForm()

        send_command = "Dajaxice.midocs.insert_section_top(Dajax.process,{'thread_code': '%s',  'form':$('#insert_section_form_top_form').serializeArray()})" % ( thread_code)
        cancel_command = "Dajaxice.midocs.cancel_insert_section_top(Dajax.process,{'thread_code': '%s'})" % (thread_code)
    
        form_html = '<label for="id_section_name">Section name:</label> %s<div class="error" id="section_name_errors_top"></div><br/><label for="id_section_code">Section code:</label> %s<div class="error" id="section_code_errors_top"></div>' % (section_form['section_name'], section_form['section_code'])

        form_html = '<form action="" method="post" id="insert_section_form_top_form" accept-charset="utf-8">%s<input type="button" value="Add section" onclick="%s;"> <input type="button" value="Cancel" onclick="%s;"></form>' % (form_html, send_command, cancel_command)
        dajax.assign('#top_section_insert', 'innerHTML', form_html)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def cancel_insert_section_top(request, thread_code):
    dajax = Dajax()
    try:
        thread = Thread.objects.get(code=thread_code)
        dajax.assign('#top_section_insert', 'innerHTML', thread.top_section_insert_html())
    except:
        pass
    return dajax.json()


@dajaxice_register
def insert_section_top(request, thread_code, form):
    dajax = Dajax()

    try:
        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']
        form = ThreadSectionForm(form_dict)
        
        if form.is_valid():
            new_section_name = form.cleaned_data.get('section_name')
            new_section_code = form.cleaned_data.get('section_code')
            
            # add section before first section
            thread = Thread.objects.get(code=thread_code)
            try:
                new_sort_order=thread.thread_sections.all()[0].sort_order-1.0
            except:
                new_sort_order=0
                
            new_section = ThreadSection(name=new_section_name, code=new_section_code,
                                        thread=thread,
                                        sort_order=new_sort_order,
                                        level=1)

            from django.db import IntegrityError
            try:
                new_section.save()
            except IntegrityError as e:
                dajax.assign('#section_code_errors_top',
                              'innerHTML',
                             'Cannot add section. Duplicate code: %s' % (new_section_code))
            else:
                dajax.assign('#thread_contents', 'innerHTML', \
                                 thread.render_html_edit_string())
                
        # if form is not valid
        else:
            dajax.assign('#section_name_errors_top',
                         'innerHTML',
                         form['section_name'].errors)
            dajax.assign('#section_code_errors_top',
                         'innerHTML',
                         form['section_code'].errors)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()



@dajaxice_register
def insert_section_form_below(request, section_code, thread_code):
    dajax = Dajax()

    try:
        section_form = ThreadSectionForm()

        send_command = "Dajaxice.midocs.insert_section_below(Dajax.process,{'section_code': '%s', 'thread_code': '%s',  'form':$('#%s_insert_section_form_below_form').serializeArray()})" % (section_code, thread_code, section_code)
        cancel_command = "Dajaxice.midocs.cancel_insert_section_below(Dajax.process,{'section_code': '%s', 'thread_code': '%s'})" % (section_code, thread_code)
    
        form_html = '<label for="id_section_name">Section name:</label> %s<div class="error" id="%s_section_name_errors"></div><br/><label for="id_section_code">Section code:</label> %s<div class="error" id="%s_section_code_errors"></div>' % (section_form['section_name'], section_code, section_form['section_code'], section_code)

        form_html = '<form action="" method="post" id="%s_insert_section_form_below_form" accept-charset="utf-8">%s<input type="button" value="Add section" onclick="%s;"> <input type="button" value="Cancel" onclick="%s;"></form>' % (section_code,form_html, send_command, cancel_command)
        dajax.assign('#%s_section_insert_below' % section_code, 'innerHTML', \
                         form_html)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()


@dajaxice_register
def cancel_insert_section_below(request, section_code, thread_code):
    dajax = Dajax()

    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        dajax.assign('#%s_section_insert_below' % section_code, 'innerHTML', \
                         thread_section.section_insert_below_html())
    except:
        pass
    return dajax.json()


@dajaxice_register
def insert_section_below(request, section_code, thread_code, form):
    dajax = Dajax()

    try:
        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']
        form = ThreadSectionForm(form_dict)
        
        if form.is_valid():
            new_section_name = form.cleaned_data.get('section_name')
            new_section_code = form.cleaned_data.get('section_code')
            
            # add section after section given by section_code
            thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)

            this_sort_order=thread_section.sort_order
            next_section = thread_section.find_next_section()
            if next_section:
                new_sort_order= (this_sort_order+next_section.sort_order)/2.0
            else:
                new_sort_order=this_sort_order+1.0
                
            new_section = ThreadSection(name=new_section_name, code=new_section_code,
                                  thread=thread_section.thread,
                                  sort_order=new_sort_order,
                                  level=thread_section.level)

            from django.db import IntegrityError
            try:
                new_section.save()
            except IntegrityError as e:
                dajax.assign('#%s_section_code_errors' % section_code,
                              'innerHTML',
                             'Cannot add section. Duplicate code: %s' % (new_section_code))
            else:
                dajax.assign('#thread_contents', 'innerHTML', \
                                 thread_section.thread.render_html_edit_string())
                
        # if form is not valid
        else:
            dajax.assign('#%s_section_name_errors' % section_code,
                         'innerHTML',
                         form['section_name'].errors)
            dajax.assign('#%s_section_code_errors' % section_code,
                         'innerHTML',
                         form['section_code'].errors)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()

@dajaxice_register
def move_content_up(request, threadcontent_id):
    dajax = Dajax()
    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        this_section = thread_content.section
      
        # if previous content in section, switch order
        previous_content = thread_content.find_previous_in_section()
        if previous_content:
            this_sort_order = thread_content.sort_order
            previous_sort_order = previous_content.sort_order

            # if sort_orders are the same, 
            # redo all sort orders before continuing
            if this_sort_order==previous_sort_order:
                for (i,tc) in enumerate(thread_content.section.threadcontent_set.all()):
                    tc.sort_order=i
                    tc.save()
                thread_content = ThreadContent.objects.get(id=threadcontent_id)
                previous_content = thread_content.find_previous_in_section()
                this_sort_order = thread_content.sort_order
                previous_sort_order = previous_content.sort_order
            thread_content.sort_order = previous_sort_order
            previous_content.sort_order = this_sort_order
            thread_content.save()
            previous_content.save()
            
            # rewrite just thread content of section
            dajax.assign('#threadcontent_%s' % this_section.code, \
                             'innerHTML', \
                             this_section.return_content_html_string(True))


        # if content is first in section, move to end of previous section
        else:
            previous_section = thread_content.section.find_previous_section()
            if previous_section:
                other_content =  previous_section.threadcontent_set.reverse()
                if other_content:
                    last_sort_order = other_content[0].sort_order
                    new_sort_order = last_sort_order +1
                else:
                    new_sort_order = 0
                thread_content.section = previous_section
                thread_content.sort_order = new_sort_order
                thread_content.save()

                # rewrite just thread content of section and previous
                dajax.assign('#threadcontent_%s' % this_section.code, \
                                 'innerHTML', \
                                 this_section.return_content_html_string(True))
                dajax.assign('#threadcontent_%s' % previous_section.code, \
                                 'innerHTML', \
                                 previous_section.return_content_html_string(True))
            
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()



@dajaxice_register
def move_content_down(request, threadcontent_id):
    dajax = Dajax()
    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        this_section = thread_content.section

        # if next content in section, switch order
        next_content = thread_content.find_next_in_section()
        if next_content:
            this_sort_order = thread_content.sort_order
            next_sort_order = next_content.sort_order

            # if sort_orders are the same, 
            # redo all sort orders before continuing
            if this_sort_order==next_sort_order:
                for (i,tc) in enumerate(thread_content.section.threadcontent_set.all()):
                    tc.sort_order=i
                    tc.save()
                thread_content = ThreadContent.objects.get(id=threadcontent_id)
                next_content = thread_content.find_next_in_section()
                this_sort_order = thread_content.sort_order
                next_sort_order = next_content.sort_order
            thread_content.sort_order = next_sort_order
            next_content.sort_order = this_sort_order
            thread_content.save()
            next_content.save()
            
            # rewrite just thread content of section
            dajax.assign('#threadcontent_%s' % this_section.code, \
                             'innerHTML', \
                             this_section.return_content_html_string(True))

        # if content is last in section, move to beginning of next section
        else:
            next_section = thread_content.section.find_next_section()
            if next_section:
                other_content=next_section.threadcontent_set.all()
                if other_content:
                    first_sort_order=other_content[0].sort_order
                    new_sort_order = first_sort_order-1
                else:
                    new_sort_order = 0
                thread_content.section = next_section
                thread_content.sort_order = new_sort_order
                thread_content.save()


                # rewrite just thread content of section and next_section
                dajax.assign('#threadcontent_%s' % this_section.code, \
                                 'innerHTML', \
                                 this_section.return_content_html_string(True))
                dajax.assign('#threadcontent_%s' % next_section.code, \
                                 'innerHTML', \
                                 next_section.return_content_html_string(True))
                

            
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
    return dajax.json()


@dajaxice_register
def delete_content(request, threadcontent_id):
    dajax = Dajax()

    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        delete_prompt = '<h5>Confirm Delete</h5><p>Are you sure you want to delete this thread content: %s?</p>' % thread_content.get_title()
    
        course_thread_content = thread_content.coursethreadcontent_set.all()
        if course_thread_content:
            delete_prompt += '<p>Deleting will also delete content from the following courses:</p><ul>'
            
            for content in course_thread_content:
                delete_prompt += '<li>%s</li>' % content.course.name
            delete_prompt += '</ul>'

        click_command_base = thread_content.get_click_command_base()
        
        click_command = click_command_base % 'confirm_delete_content'
        delete_prompt += '<p><input type="button" value="Yes" onclick="%s;">' % click_command

        click_command = click_command_base % 'cancel_delete_content'
        delete_prompt += '<input type="button" value="No" onclick="%s;" style="margin-left: 3px;"></p>' % click_command

        dajax.assign('#%s_content_insert_below_content' % threadcontent_id, \
                         'innerHTML', delete_prompt)
        dajax.add_css_class('#%s_content_insert_below_content' % threadcontent_id, 'thread_info_box')


    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def cancel_delete_content(request, threadcontent_id):
    dajax = Dajax()
    
    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        dajax.assign('#%s_content_insert_below_content' % threadcontent_id, \
                     'innerHTML', thread_content.content_insert_below_content_html()) 
        dajax.remove_css_class('#%s_content_insert_below_content' % threadcontent_id, 'thread_info_box')
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def confirm_delete_content(request, threadcontent_id):
    dajax = Dajax()
    
    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        thread_content.delete()

        dajax.assign('#thread_contents', 'innerHTML', \
                         thread_content.section.thread.render_html_edit_string())
        
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

def return_option_list_for_content_type(content_type_id):
    content_type = ContentType.objects.get(id=content_type_id)
    content_list = content_type.model_class().objects.all()
        
    option_list=[]
    for item in content_list:
        option_list.append("<option value='%s'>%s</option>" % (item.id, unicode(item)))

    return option_list


@dajaxice_register
def insert_content_form_below_section(request, section_code, thread_code):
    dajax = Dajax()

    try:
        content_form = ThreadContentForm(prefix=section_code)

        send_command = "Dajaxice.midocs.insert_content_below_section(Dajax.process,{'section_code': '%s', 'thread_code': '%s',  'form':$('#%s_insert_content_form_below_section_form').serializeArray()})" % (section_code, thread_code, section_code)
        cancel_command = "Dajaxice.midocs.cancel_insert_content_below_section(Dajax.process,{'section_code': '%s', 'thread_code': '%s'})" % (section_code, thread_code)
    
        update_combo_command = "Dajaxice.midocs.update_combo_content_form_below_section(Dajax.process,{'section_code': '%s', 'thread_code': '%s', 'option':this.value})" % (section_code, thread_code)

        # content_type_select_html = str(content_form['content_type'])
        # content_type_select_html = content_type_select_html[:7] + ' onchange="%s"' % update_combo_command + content_type_select_html[7:]

        # find content_type_id for Page
        page_content_type_id = ContentType.objects.get_for_model(Page).id

        # make Page be the default content_type
        temp = re.sub(r'<select','<select onchange="%s"' % update_combo_command, unicode(content_form['content_type']))
        temp = re.sub(r'<option value="" selected="selected">---------</option>\n','',temp)
        content_type_select_html = re.sub(r'<option value="%i">' % page_content_type_id,'<option value="%i" selected="selected">' % page_content_type_id,temp)

        
        option_list = return_option_list_for_content_type(page_content_type_id)
        option_list = ''.join(option_list)
        object_id_select_html = \
            re.sub(r'>\n</select>', '>%s\n</select>' % option_list,\
                       unicode(content_form['object_id']))

        form_html = '<label for="id_%s-content_type">Content type:</label> %s<div class="error" id="%s_content_type_errors"></div><label for="id_%s-object_id">Object:</label> %s<div class="error" id="%s_object_id_errors"></div><label for="id_%s-substitute_title">Substitute title:</label> %s<div class="error" id="%s_substitute_title_errors"></div>' % (section_code, content_type_select_html, section_code, section_code, object_id_select_html, section_code, section_code, content_form['substitute_title'], section_code)

        form_html = '<form action="" method="post" id="%s_insert_content_form_below_section_form" accept-charset="utf-8">%s<input type="button" id="%s_insert_content_form_below_section_form_add" value="Add content" onclick="%s;"> <input type="button" value="Cancel" onclick="%s;"></form>' % (section_code,form_html, section_code, send_command, cancel_command)
        dajax.assign('#%s_content_insert_below_section' % section_code, 'innerHTML', \
                         form_html)
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def update_combo_content_form_below_section(request, section_code, thread_code, option):

    dajax = Dajax()

    try:
        # look up all entries for this content type
        option_list=return_option_list_for_content_type(option)
        dajax.assign('#id_%s-object_id' % section_code, 'innerHTML', \
                         ''.join(option_list))
        #dajax.assign('#%s_insert_content_form_below_section_form_add' % section_code, 'disabled', False)


    except Exception as e:
        dajax.assign('#id_%s-object_id' % section_code, 'innerHTML', \
                         '')
        #dajax.assign('#%s_insert_content_form_below_section_form_add' % section_code, 'disabled', True)
        #dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def cancel_insert_content_below_section(request, section_code, thread_code):
    
    dajax = Dajax()

    try:
        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        dajax.assign('#%s_content_insert_below_section' % section_code,\
                         'innerHTML', \
                         thread_section.content_insert_below_section_html())
    except Exception as e:
        dajax.alert("something wrong: %s" % e)
        
    return dajax.json()

@dajaxice_register
def insert_content_below_section(request, section_code, thread_code, form):
    
    dajax = Dajax()

    try:

        thread_section = ThreadSection.objects.get(code=section_code, thread__code=thread_code)
        
        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']
        form =  ThreadContentForm(form_dict, prefix=section_code)
        if form.is_valid():
            content_type = form.cleaned_data.get('content_type')
            object_id = form.cleaned_data.get('object_id')
            substitute_title = form.cleaned_data.get('substitute_title')

            other_content = thread_section.threadcontent_set.reverse()
            if other_content:
                last_sort_order = other_content[0].sort_order
                sort_order = last_sort_order+1
            else:
                sort_order = 0
                
            thread_content = ThreadContent(section=thread_section,
                                           content_type=content_type,
                                           object_id=object_id,
                                           sort_order=sort_order,
                                           substitute_title=substitute_title)
            thread_content.save()

            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_section.thread.render_html_edit_string())

        # if form is not valid
        else:
            dajax.assign('#%s_content_type_errors' % section_code,
                         'innerHTML',
                         form['content_type'].errors)
            dajax.assign('#%s_object_id_errors' % section_code,
                         'innerHTML',
                         form['object_id'].errors)
            dajax.assign('#%s_substitute_title_errors' % section_code,
                         'innerHTML',
                         form['substitute_title'].errors)

    except Exception as e:
        dajax.alert("something wrong: %s" % e)
        
    return dajax.json()



def return_option_list_for_thread_content(thread_content):
    content_type = ContentType.objects.get(id=thread_content.content_type.id)
    content_list = list(content_type.model_class().objects.all())
    selected_index = content_list.index(thread_content.content_object)
    
    option_list=[]
    for (i,item) in enumerate(content_list):
        if i==selected_index:
            option_list.append("<option value='%s' selected='selected'>%s</option>" % (item.id, unicode(item)))
        else:
            option_list.append("<option value='%s'>%s</option>" % (item.id, unicode(item)))

    return option_list


@dajaxice_register
def edit_content(request, threadcontent_id):
    dajax = Dajax()

    try:

        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        content_form = ThreadContentForm(instance=thread_content, prefix="threadcontent_%s" % threadcontent_id)

        #add_content_form = ThreadContentForm({'content_type': thread_content.content_type, 'object_id': thread_content.object_id, 'substitute_title': thread_content.substitute_title}, prefix="threadcontent_%s" % threadcontent_id)

        send_command = "Dajaxice.midocs.confirm_edit_content(Dajax.process,{'threadcontent_id': '%s', 'form':$('#threadcontent_%s_edit_content_form').serializeArray()})" % (threadcontent_id, threadcontent_id)

        cancel_command = "Dajaxice.midocs.cancel_edit_content(Dajax.process,{'threadcontent_id': '%s'})" % (threadcontent_id)
    
        update_combo_command = "Dajaxice.midocs.update_combo_edit_content(Dajax.process,{'threadcontent_id': '%s', 'option':this.value})" %  (threadcontent_id)

        content_type_select_html = str(content_form['content_type'])
        content_type_select_html = content_type_select_html[:7] + ' onchange="%s"' % update_combo_command + content_type_select_html[7:]


       # form_html = re.sub(r'<select','<select onchange="%s"' % update_combo_command ,form.as_p())

        object_id_select_html = '<select name="threadcontent_%s-object_id" id="id_threadcontent_%s-object_id">' % (threadcontent_id, threadcontent_id)
        
        option_list = return_option_list_for_thread_content(thread_content)
        object_id_select_html = "%s%s</select>" % ( object_id_select_html,\
                                                        ''.join(option_list))
      

        form_html = '<label for="id_threadcontent_%s-content_type">Content type:</label> %s<div class="error" id="threadcontent_%s_content_type_errors"></div><label for="id_threadcontent_%s-object_id">Object:</label> %s<div class="error" id="threadcontent_%s_object_id_errors"></div><label for="id_threadcontent_%s-substitute_title">Substitute title:</label> %s<div class="error" id="threadcontent_%s_substitute_title_errors"></div>' % (threadcontent_id, content_type_select_html, threadcontent_id, threadcontent_id, object_id_select_html, threadcontent_id, threadcontent_id, content_form['substitute_title'], threadcontent_id)

        form_html = '<form action="" method="post" id="threadcontent_%s_edit_content_form" accept-charset="utf-8">%s<input type="button" id="threadcontent_%s_edit_content_form_modify" value="Modify content" onclick="%s;"> <input type="button" value="Cancel" onclick="%s;"></form>' % (threadcontent_id,form_html, threadcontent_id, send_command, cancel_command)

        
        dajax.assign('#thread_content_%s' % threadcontent_id, 'innerHTML', \
                         form_html)
        
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()


@dajaxice_register
def update_combo_edit_content(request, threadcontent_id, option):

    dajax = Dajax()

    try:
        # look up all entries for this content type
        option_list=return_option_list_for_content_type(option)

        dajax.assign('#id_threadcontent_%s-object_id' % threadcontent_id, 'innerHTML', \
                         ''.join(option_list))
        #dajax.assign('#threadcontent_%s_edit_content_form_modify' % threadcontent_id, 'disabled', False)


    except Exception as e:
        dajax.assign('#id_threadcontent_%s-object_id' % threadcontent_id, 'innerHTML', \
                         '')
        #dajax.assign('#threadcontent_%s_edit_content_form_modify' % threadcontent_id, 'disabled', True)
        #dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def confirm_edit_content(request, threadcontent_id, form):
    dajax = Dajax()

    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)

        form_dict={}
        for  obj in form:
            form_dict[obj['name']]=obj['value']
        form = ThreadContentForm(form_dict, prefix="threadcontent_%s" % threadcontent_id)

        if form.is_valid():
            content_type = form.cleaned_data.get('content_type')
            object_id = form.cleaned_data.get('object_id')
            substitute_title = form.cleaned_data.get('substitute_title')
            
            thread_content.content_type=content_type
            thread_content.object_id=object_id
            thread_content.substitute_title =substitute_title
            
            thread_content.save()
            dajax.assign('#thread_contents', 'innerHTML', \
                             thread_content.section.thread.render_html_edit_string())

        # if form is not valid
        else:
            dajax.assign('#threadcontent_%s_content_type_errors' % threadcontent_id,
                         'innerHTML',
                         form['content_type'].errors)
            dajax.assign('#threadcontent_%s_object_id_errors' % threadcontent_id,
                         'innerHTML',
                         form['object_id'].errors)
            dajax.assign('#threadcontent_%s_substitute_title_errors' % threadcontent_id,
                         'innerHTML',
                         form['substitute_title'].errors)
 
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()

@dajaxice_register
def cancel_edit_content(request, threadcontent_id):
    dajax = Dajax()

    try:
        thread_content=ThreadContent.objects.get(id=threadcontent_id)
        dajax.assign('#thread_content_%s' % threadcontent_id, 'innerHTML', \
                         thread_content.return_html_innerstring(True))
    except Exception as e:
        dajax.alert("something wrong: %s" % e)

    return dajax.json()
