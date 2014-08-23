from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from micourses.models import Course, CourseUser, CourseThreadContent
from mitesting.models import Assessment
from midocs.models import Applet
from micourses.forms import StudentContentAttemptForm
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.template import RequestContext, Context
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.views.generic import DetailView
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils import formats
from django.utils.safestring import mark_safe
from django import forms
import datetime
from micourses.templatetags.course_tags import floatformat_or_dash
from mitesting.render_assessments import render_question_list, render_question

def format_datetime(value):
    return "%s, %s" % (formats.date_format(value), formats.time_format(value))

class CourseUserAuthenticationMixin(object):
    """
    Requires user to be logged in user enrolled in a course
    before being able to access the post/get methods.
    Adds course, courseuser, and noanalytics to context
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):

        try:
            self.courseuser = request.user.courseuser
        # if courseuser does not exist, redirect to not enrolled page
        except ObjectDoesNotExist:
            return redirect('mic-notenrolled')
        try:
            self.course = self.courseuser.return_selected_course()
        except MultipleObjectsReturned:
            # courseuser is in multple active courses and hasn't selected one
            # redirect to select course page
            return redirect('mic-selectcourse')
        except ObjectDoesNotExist:
            # courseuser is not in an active course
            # redirect to not enrolled page
            return redirect('mic-notenrolled')

        return super(CourseUserAuthenticationMixin, self)\
            .dispatch(request, *args, **kwargs) 

    def get_student(self):
        return self.courseuser

    def get_context_data(self, **kwargs):
        context = super(CourseUserAuthenticationMixin, self)\
            .get_context_data(**kwargs)
        
        context['courseuser'] = self.courseuser
        context['course'] = self.course
        context['student'] = self.get_student()


        # find begining/end of week
        today= datetime.date.today()
        day_of_week = (today.weekday()+1) % 7
        to_beginning_of_week = datetime.timedelta(days=day_of_week)
        beginning_of_week = today - to_beginning_of_week
        end_of_week = beginning_of_week + datetime.timedelta(13)
        context['week_date_parameters'] = "begin_date=%s&end_date=%s" \
            % (beginning_of_week, end_of_week)
        
        # no Google analytics for course
        context['noanalytics']=True
        
        context.update(self.extra_course_context())

        return context

    def extra_course_context(self):
        return {}


@login_required
def course_main_view(request):

    try:
        courseuser = request.user.courseuser
    # if courseuser does not exist, redirect to not enrolled page
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('mic-notenrolled'))
        
    # if POST, then set selected_course
    if request.method == 'POST':
        course_code = request.POST['course']
        selected_enrollment = courseuser.courseenrollment_set\
                                        .get(course__code=course_code)
        courseuser.selected_course_enrollment = selected_enrollment
        courseuser.save()
        course=selected_enrollment.course
    # else get selected_course from database
    else:
        try:
            course = courseuser.return_selected_course()
        except MultipleObjectsReturned:
            # courseuser is in multple active courses and hasn't selected one
            # redirect to select course page
            return HttpResponseRedirect(reverse('mic-selectcourse'))
        except ObjectDoesNotExist:
            # courseuser is not in an active course
            # redirect to not enrolled page
            return HttpResponseRedirect(reverse('mic-notenrolled'))

    if courseuser.course_set.count() > 1:
        multiple_courses = True
    else:
        multiple_courses = False

    # no Google analytics for course
    noanalytics=True

    # find begining/end of week
    today= datetime.date.today()
    day_of_week = (today.weekday()+1) % 7
    to_beginning_of_week = datetime.timedelta(days=day_of_week)
    beginning_of_week = today - to_beginning_of_week
    end_of_week = beginning_of_week + datetime.timedelta(6)
    week_date_parameters = "begin_date=%s&end_date=%s" \
        % (beginning_of_week, end_of_week)

    begin_date = beginning_of_week
    end_date = begin_date + datetime.timedelta(13)


    upcoming_content = course.course_content_by_adjusted_due_date \
        (courseuser, begin_date=begin_date, \
             end_date=end_date)
    
    date_parameters = "begin_date=%s&end_date=%s" % (begin_date,
                                                     end_date)

    next_begin_date = end_date + datetime.timedelta(1)
    next_end_date = next_begin_date+datetime.timedelta(6)
    next_period_parameters = "begin_date=%s&end_date=%s" \
        % (next_begin_date, next_end_date)
    previous_end_date = begin_date - datetime.timedelta(1)
    previous_begin_date = previous_end_date-datetime.timedelta(6)
    previous_period_parameters = "begin_date=%s&end_date=%s" \
        % (previous_begin_date, previous_end_date)
    previous_period_parameters += "&exclude_completed"
    next_period_parameters += "&exclude_completed"

    next_items = course.next_items(courseuser, number=5)
    
    if courseuser.get_current_role() == 'I':
        return render_to_response \
            ('micourses/course_instructor_view.html', 
             {'student': courseuser,
              'courseuser': courseuser,
              'course': course,
              'upcoming_content': upcoming_content,
              'next_items': next_items,
              'multiple_courses': multiple_courses,
              'week_date_parameters': week_date_parameters,
              'begin_date': begin_date,
              'end_date': end_date,
              'previous_period_parameters': previous_period_parameters,
              'next_period_parameters': next_period_parameters,
              'include_completed_parameters': date_parameters,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))
    else:
        return render_to_response \
            ('micourses/course_student_view.html', 
             {'student': courseuser,
              'courseuser': courseuser,
              'course': course,
              'upcoming_content': upcoming_content,
              'next_items': next_items,
              'multiple_courses': multiple_courses,
              'week_date_parameters': week_date_parameters,
              'begin_date': begin_date,
              'end_date': end_date,
              'previous_period_parameters': previous_period_parameters,
              'next_period_parameters': next_period_parameters,
              'include_completed_parameters': date_parameters,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))


class AssessmentAttempted(CourseUserAuthenticationMixin,DetailView):
    """
    should be: AssessmentAttemptList
    """
    model = CourseThreadContent
    context_object_name = 'content'
    template_name = 'micourses/assessment_attempted.html'

    def get_object(self):
        content = super(AssessmentAttempted, self).get_object()
        self.student = self.get_student()
        self.assessment=content.thread_content.content_object
        self.assessment_attempts = self.student.studentcontentattempt_set\
            .filter(content=content)
        return content

    def extra_course_context(self):
        attempt_list = []
        for (i,attempt) in enumerate(self.assessment_attempts):
            datetime_text = format_datetime(attempt.datetime)
            if attempt.have_datetime_interval():
                datetime_text += " - " \
                    + format_datetime(attempt.get_latest_datetime())
            score_text = floatformat_or_dash(attempt.get_score(), 1)
            attempt_dict = {}
            attempt_number = i+1
            attempt_dict['attempt'] = attempt
            attempt_dict['score'] = attempt.get_score()
            attempt_dict['attempt_number']  = attempt_number
            attempt_dict['formatted_attempt_number'] = \
                mark_safe('&nbsp;%i&nbsp;' % attempt_number)
            attempt_dict['datetime'] = \
                mark_safe('&nbsp;%s&nbsp;' % datetime_text)
            attempt_dict['formatted_score'] = \
                mark_safe('&nbsp;%s&nbsp;' % score_text)
            if attempt.questionstudentanswer_set.exists():
                attempt_url = reverse('mic-assessmentattempt', 
                                      kwargs={'pk': self.object.id,
                                              'attempt_number': attempt_number})
                attempt_dict['formatted_attempt_number'] = mark_safe \
                ('<a href="%s">%s</a>' % \
                     (attempt_url, attempt_dict['formatted_attempt_number']))
                attempt_dict['datetime'] = \
                    mark_safe('<a href="%s">%s</a>' % \
                                  (attempt_url, attempt_dict['datetime']))
                attempt_dict['formatted_score'] = mark_safe\
                    ('<a href="%s">%s</a>' \
                         % (attempt_url, attempt_dict['formatted_score']))

            attempt_list.append(attempt_dict)
                
        return {'adjusted_due_date': self.object\
                    .adjusted_due_date(self.student),
                'attempts': attempt_list,
                'score': self.object.student_score(self.student),
                }


class AssessmentAttemptedInstructor(AssessmentAttempted):
    """
    should be: AssessmentAttemptListInstructor
    """

    template_name = 'micourses/assessment_attempted_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I'))
    def dispatch(self, request, *args, **kwargs):
        return super(AssessmentAttemptedInstructor, self)\
            .dispatch(request, *args, **kwargs) 
    
    def get_student(self):
        return get_object_or_404(self.course.enrolled_students,
                                 id=self.kwargs['student_id'])
    def extra_course_context(self):
        attempt_list = []
        for (i,attempt) in enumerate(self.assessment_attempts):
            datetime_text = format_datetime(attempt.datetime)
            if attempt.have_datetime_interval():
                datetime_text += " - " \
                    + format_datetime(attempt.get_latest_datetime())
            score_text = floatformat_or_dash(attempt.get_score(), 1)
            attempt_dict = {}
            attempt_number = i+1
            attempt_dict['attempt'] = attempt
            attempt_dict['score'] = attempt.get_score()
            attempt_dict['attempt_number']  = attempt_number
            attempt_dict['formatted_attempt_number'] = \
                mark_safe('&nbsp;%i&nbsp;' % attempt_number)
            attempt_dict['datetime'] = \
                mark_safe('&nbsp;%s&nbsp;' % datetime_text)
            attempt_dict['formatted_score'] = \
                mark_safe('&nbsp;%s&nbsp;' % score_text)
            attempt_dict['direct_link'] = attempt.content.thread_content.content_object.return_link(direct=True, link_text=" try it",seed=attempt.seed)

            if attempt.questionstudentanswer_set.exists():
                attempt_url = reverse('mic-assessmentattemptinstructor', 
                                      kwargs={'pk': self.object.id,
                                              'attempt_number': attempt_number,
                                              'student_id': self.student.id})
                attempt_dict['formatted_attempt_number'] = mark_safe \
                ('<a href="%s">%s</a>' % \
                     (attempt_url, attempt_dict['formatted_attempt_number']))
                attempt_dict['datetime'] = \
                    mark_safe('<a href="%s">%s</a>' % \
                                  (attempt_url, attempt_dict['datetime']))
                attempt_dict['formatted_score'] = mark_safe\
                    ('<a href="%s">%s</a>' \
                         % (attempt_url, attempt_dict['formatted_score']))

            edit_attempt_form = StudentContentAttemptForm\
                ({'score': attempt.get_score(), 'content': attempt.content.id,
                  'student': attempt.student.id, 'seed': attempt.seed, 
                  'datetime': attempt.datetime })
            edit_content_command = "Dajaxice.midocs.edit_student_content_attempt(Dajax.process,{'form':$('#edit_student_content_attempt_%i_form').serializeArray(), attempt_id: %i, attempt_number: %i })" % (attempt_number, attempt.id, attempt_number)
            toggle_command = 'toggleEditForm(%i)' % attempt_number

            score_or_edit = '<span id="edit_attempt_%i_score" hidden><form id="edit_student_content_attempt_%i_form"><span id ="edit_student_content_attempt_%i_form_inner" >%s</span><div id="edit_attempt_%i_errors" class="error"></div><input type="button" value="Change" onclick="%s"><input type="button" value="Cancel" onclick="%s"></form></span><span id="attempt_%i_score"><span id="attempt_%i_score_inner">%s</span><input type="button" value="Edit" onclick="%s"></span>' \
                % (attempt_number, attempt_number, attempt_number, \
                       edit_attempt_form.as_p(), attempt_number, \
                       edit_content_command, toggle_command, attempt_number,\
                       attempt_number,\
                       attempt_dict['formatted_score'], toggle_command)
            attempt_dict['score_or_edit'] = mark_safe(score_or_edit)

            attempt_list.append(attempt_dict)
                
        new_attempt_form = StudentContentAttemptForm({
                'content': self.object.id,
                'student': self.student.id,
                'datetime': datetime.datetime.now()\
                    .strftime('%Y-%m-%d %H:%M'),
                })


        return {'adjusted_due_date': self.object\
                    .adjusted_due_date(self.student),
                'attempts': attempt_list,
                'score': self.object.student_score(self.student),
                'new_attempt_form': new_attempt_form,
                }


class AssessmentAttempt(AssessmentAttempted):
    
    template_name = 'micourses/assessment_attempt.html'

    def get_object(self):
        content = super(AssessmentAttempt, self).get_object()
        
        # don't pad attempt_number with zeros
        self.attempt_number = self.kwargs['attempt_number']
        if self.attempt_number[0]=='0':
            raise  Http404('Assessment attempt %s not found.' \
                               % self.attempt_number)

        try:
            self.attempt = self.assessment_attempts[int(self.attempt_number)-1]
        except IndexError:
            raise Http404('Assessment attempt %s not found.' \
                              % self.attempt_number)
        
        return content

    def extra_course_context(self):
        
        context={}
        context['attempt'] = self.attempt
        context['attempt_number'] = self.attempt_number
        context['score_overridden'] = self.attempt.score_overridden()


        rendered_question_list=render_question_list\
            (self.assessment, self.attempt.seed,
             current_attempt=self.attempt)[0]

        question_list = []
        for qd in rendered_question_list:
            question_dict={'points': qd['points'],
                           'current_credit': qd['current_credit'],
                           'current_score': qd['current_score'],
                           'direct_link':\
                               mark_safe('<a href="%s?seed=%s" class="assessment">try it</a>' \
                                             % (qd['question'].get_absolute_url(), qd['seed']))
                           }
            
            question_dict['answers_available'] = \
                self.attempt.questionstudentanswer_set \
                .filter(question_set=qd['question_set']).exists()
            
            question_list.append(question_dict)

        context['question_list'] =question_list

        return context


class AssessmentAttemptInstructor(AssessmentAttempt):
    template_name = 'micourses/assessment_attempt_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I'))
    def dispatch(self, request, *args, **kwargs):
        return super(AssessmentAttemptInstructor, self)\
            .dispatch(request, *args, **kwargs) 
    
    def get_student(self):
        return get_object_or_404(self.course.enrolled_students,
                                 id=self.kwargs['student_id'])


class AssessmentAttemptQuestion(AssessmentAttempt):
    
    model = CourseThreadContent
    context_object_name = 'content'
    template_name = 'micourses/assessment_attempt_question.html'

    def get_object(self):
        content = super(AssessmentAttemptQuestion, self).get_object()
        
        # don't pad question_number with zeros
        self.question_number = self.kwargs['question_number']
        if self.question_number[0]=='0':
            raise  Http404('Question %s not found.' % self.question_number)

        self.question_number = int(self.question_number)

        try:
            self.question_dict=render_question_list\
                    (self.assessment, self.attempt.seed, 
                     current_attempt=self.attempt)[0][self.question_number-1]
        except IndexError:
            raise  Http404('Question %s not found.' % self.question_number)

        question_set = self.question_dict['question_set']

        self.answers=self.attempt.questionstudentanswer_set.filter\
            (question_set=question_set)
        
        if not self.answers:
            raise Http404('Question %s not found.' % self.question_number)

        return content

    def extra_course_context(self):
        
        context={}
        context['attempt'] = self.attempt
        context['attempt_number'] = self.attempt_number
        context['points'] = self.question_dict['points']
        context['score'] = self. question_dict['current_score']
        context['current_credit'] = self.question_dict['current_credit']
        context['question_number'] = self.question_number

        answer_list=[]
        for answer in self.answers:
            answer_dict = {'datetime': answer.datetime, }
            try:
                answer_dict['score'] = answer.credit*self.question_dict['points']
            except TypeError:
                answer_dict['score'] = 0
            answer_dict['credit_percent'] = int(round(answer.credit*100))
            answer_list.append(answer_dict)
        context['answers'] = answer_list

        return context


class AssessmentAttemptQuestionInstructor(AssessmentAttemptQuestion):
    template_name = 'micourses/assessment_attempt_question_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I'))
    def dispatch(self, request, *args, **kwargs):
        return super(AssessmentAttemptQuestionInstructor, self)\
            .dispatch(request, *args, **kwargs) 
    
    def get_student(self):
        return get_object_or_404(self.course.enrolled_students,
                                 id=self.kwargs['student_id'])


class AssessmentAttemptQuestionAttempt(AssessmentAttemptQuestion):
    
    template_name = 'micourses/assessment_attempt_question_attempt.html'


    def get_object(self):
        content = super(AssessmentAttemptQuestionAttempt, self).get_object()
        

        # don't pad question_attempt_number with zeros
        self.question_attempt_number = self.kwargs['question_attempt_number']
        if self.question_attempt_number[0]=='0':
            raise  Http404('Question attempt %s not found.'\
                               % self.question_attempt_number)

        try:
            self.answer = self.answers[int(self.question_attempt_number)-1]

        except IndexError:
            raise Http404('Question attempt %s not found.' \
                              % self.question_attempt_number)

        return content


    def render_to_response(self, *args, **kwargs):
        # determine if user has permission to view assessment,
        # given privacy level
        if not self.assessment.user_can_view(self.request.user, solution=False):
            path = self.request.build_absolute_uri()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path)
        else:
            return super(AssessmentAttemptQuestionAttempt, self)\
                .render_to_response(*args, **kwargs)
        

    def extra_course_context(self):
        
        answer_dict = {'datetime': self.answer.datetime,
                       'answer': self.answer.answer  }
        try:
            answer_dict['score'] = self.answer.credit*self.question_dict['points']
        except TypeError:
            answer_dict['score'] = 0
        answer_dict['points'] = self.question_dict['points']
        answer_dict['credit_percent'] = int(round(self.answer.credit*100))
        answer_dict['attempt_number'] = self.question_attempt_number
        


        # construct question
        question = self.answer.question

        # use aaqav in identifier since coming from
        # assessment attempt question attempt view
        identifier = "aaqav"

        applet_data = Applet.return_initial_applet_data()

        import json
        prefilled_answers = json.loads(self.answer.answer)

        question_data = render_question(question, seed=self.answer.seed,
                                        question_identifier=identifier,
                                        user=self.request.user, show_help=False,
                                        prefilled_answers=prefilled_answers, 
                                        readonly=True, auto_submit=True, 
                                        record_answers=False,
                                        allow_solution_buttons=False,
                                        applet_data=applet_data)


        context= {'question': question, 
                  'question_data': question_data,
                  'applet_data': applet_data,
                  'attempt': self.attempt,
                  'attempt_number': self.attempt_number,
                  'question_number': self.question_number,
                  'answer_dict': answer_dict,
        }
        
        return context

class AssessmentAttemptQuestionAttemptInstructor(AssessmentAttemptQuestionAttempt):
    template_name = 'micourses/assessment_attempt_question_attempt_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I'))
    def dispatch(self, request, *args, **kwargs):
        return super(AssessmentAttemptQuestionAttemptInstructor, self)\
            .dispatch(request, *args, **kwargs) 
    
    def get_student(self):
        return get_object_or_404(self.course.enrolled_students,
                                 id=self.kwargs['student_id'])


@login_required
def content_list_view(request):
    courseuser = request.user.courseuser

    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    # no Google analytics for course
    noanalytics=True

    # find begining/end of week
    today= datetime.date.today()
    day_of_week = (today.weekday()+1) % 7
    to_beginning_of_week = datetime.timedelta(days=day_of_week)
    beginning_of_week = today - to_beginning_of_week
    end_of_week = beginning_of_week + datetime.timedelta(6)
    week_date_parameters = "begin_date=%s&end_date=%s" \
        % (beginning_of_week, end_of_week)


    exclude_completed='exclude_completed' in request.GET
    exclude_past_due='exclude_past_due' in request.GET
    try:
        begin_date = datetime.datetime.strptime(request.GET.get('begin_date'),"%Y-%m-%d").date()
    except:
        begin_date = None
    try:
        end_date = datetime.datetime.strptime(request.GET.get('end_date'),"%Y-%m-%d").date()
    except:
        end_date = None

    content_list = course.course_content_by_adjusted_due_date\
        (courseuser, exclude_completed=exclude_completed, \
             begin_date=begin_date, end_date=end_date)

    if begin_date and end_date:
        next_begin_date = end_date + datetime.timedelta(1)
        next_end_date = next_begin_date+(end_date-begin_date)
        next_period_parameters = "begin_date=%s&end_date=%s" \
            % (next_begin_date, next_end_date)
        previous_end_date = begin_date - datetime.timedelta(1)
        previous_begin_date = previous_end_date+(begin_date-end_date)
        previous_period_parameters = "begin_date=%s&end_date=%s" \
            % (previous_begin_date, previous_end_date)
        if exclude_completed:
            previous_period_parameters += "&exclude_completed"
            next_period_parameters += "&exclude_completed"
    else:
        previous_period_parameters=None
        next_period_parameters=None

    all_dates_parameters = ""
    if exclude_completed:
        all_dates_parameters = "exclude_completed"

    date_parameters=""
    if begin_date:
        date_parameters += "begin_date=%s" % begin_date
    if end_date:
        if date_parameters:
            date_parameters += "&"
        date_parameters += "end_date=%s" % end_date

    exclude_completed_parameters="exclude_completed"
    if date_parameters:
        exclude_completed_parameters += "&" + date_parameters
    
    return render_to_response \
        ('micourses/content_list.html', 
         {'student': courseuser,
          'courseuser': courseuser,
          'course': course,
          'content_list': content_list,
          'exclude_completed': exclude_completed,
          'week_date_parameters': week_date_parameters,
          'begin_date': begin_date, 'end_date': end_date,
          'previous_period_parameters': previous_period_parameters,
          'next_period_parameters': next_period_parameters,
          'exclude_completed_parameters': exclude_completed_parameters,
          'include_completed_parameters': date_parameters,
          'all_dates_parameters': all_dates_parameters,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))



@permission_required("micourses.update_attendance")
def update_attendance_view(request):
    
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    class DateForm(forms.Form):
        date = forms.DateField()


    # if POST, then update attendance, assuming date is valid
    if request.method == 'POST':
        date_form = DateForm({'date':  request.POST['attendance_date']})
        valid_day = False
        if date_form.is_valid():
            attendance_date = date_form.cleaned_data['date']
            
            # check if date is a class day
            for class_day in course.attendancedate_set.all():
                if attendance_date == class_day.date:
                    valid_day = True
                    break
            
        else:
            attendance_date = None

        if valid_day:
            # delete previous attendance data for the day
            course.studentattendance_set.filter(date=attendance_date).delete()
            
            for student in course.enrolled_students.all():
                present=request.POST.get('student_%s' % student.id, 0)
                try:
                    present = float(present)
                except ValueError:
                    present = 0.0
                course.studentattendance_set.create(student=student, 
                                                    date=attendance_date,
                                                    present=present)

            
            if not course.last_attendance_date \
                    or attendance_date > course.last_attendance_date:
                course.last_attendance_date = attendance_date
                course.save()

            message = "Attendance updated for %s" % \
                attendance_date.strftime("%B %d, %Y")

        else:
            message = "Attendance not updated.  " \
                + "%s is not a valid course day: %s" % \
                (request.POST['attendance_date'], attendance_date)

            
    else:
        message = None


    # get next_attendance date
    next_attendance_date = course.find_next_attendance_date()
            

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/update_attendance.html', 
         {'course': course,
          'courseuser': courseuser,
          'message': message,
          'next_attendance_date': next_attendance_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@permission_required("micourses.update_attendance")
def update_individual_attendance_view(request):
    
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    message=''

    class SelectStudentForm(forms.Form):
        student = forms.ModelChoiceField(queryset=course.enrolled_students_ordered())           
    

    # get student from request
    student_id = request.REQUEST.get('student')
    try:
        student = CourseUser.objects.get(id=student_id)
        select_student_form = SelectStudentForm(request.REQUEST)
    except (ObjectDoesNotExist, ValueError):
        student = None
        select_student_form = SelectStudentForm()

    thestudent=student
    class AttendanceDatesForm(forms.Form):
        student = forms.ModelChoiceField\
            (queryset=course.enrolled_students_ordered(), \
                 widget=forms.HiddenInput,\
                 initial=thestudent)
        
        def __init__(self, *args, **kwargs):
            try:
                dates = kwargs.pop('dates')
            except:
                dates =[]
            super(AttendanceDatesForm, self).__init__(*args, **kwargs)

            for i, attendance_date in enumerate(dates):
                self.fields['date_%s' % i] = forms.ChoiceField\
                    (label=attendance_date['date'],\
                         initial=attendance_date['present'],\
                         choices=((1,1),(0.5,0.5),(0,0),(-1,-1)),\
                         widget=forms.RadioSelect,
                     )
                
        def date_attendance(self):
            for name, value in self.cleaned_data.items():
                if name.startswith('date_'):
                    yield (self.fields[name].label, value)



    if student:
        # get list of attendance up to last_attendance_date

        attendance=[]
        last_attendance_date = course.last_attendance_date
        if last_attendance_date:
            date_enrolled = student.courseenrollment_set.get(course=course)\
                .date_enrolled
            attendance_dates = course.attendancedate_set\
                .filter(date__lte = last_attendance_date)\
                .filter(date__gte = date_enrolled)
            days_attended = student.studentattendance_set.filter \
                (course=course).filter(date__lte = last_attendance_date)\
                .filter(date__gte = date_enrolled)
            
            for date in attendance_dates:
                try:
                    attended = days_attended.get(date=date.date)

                    # for integer values, present must be integer
                    # so that radio button shows initial value
                    if attended.present==1 or attended.present==0 or attended.present==-1:
                        present=int(round(attended.present))
                    else:
                        present = attended.present
                except ObjectDoesNotExist:
                    present = 0

                attendance.append({'date': date.date, 'present': present})

    
                
    

    # if POST, then update attendance, assuming data is valid
    if request.method == 'POST':

         attendance_dates_form = AttendanceDatesForm(request.POST or None, dates=attendance)

         if attendance_dates_form.is_valid():
             if last_attendance_date:
                 student.studentattendance_set.filter(course=course)\
                     .filter(date__lte = last_attendance_date).delete()
                 for (date, present) in attendance_dates_form.date_attendance():
                     if present:
                         student.studentattendance_set.create\
                             (course=course, date=date, present=present)
                 message = "Updated attendance of %s." % student
             else:
                 message = "Last attendance date for course not set.  Cannot update attendance."

    # if get
    else:
        if student:
            attendance_dates_form = AttendanceDatesForm(dates=attendance)
        else:            
            attendance_dates_form = AttendanceDatesForm()


    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/update_individual_attendance.html', 
         {'course': course,
          'courseuser': courseuser,
          'select_student_form': select_student_form,
          'student': student,
          'attendance_dates_form': attendance_dates_form,
          'message': message,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@login_required
def attendance_display_view(request):
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    attendance = []
    date_enrolled = courseuser.courseenrollment_set.get(course=course)\
        .date_enrolled

    percent = 0

    last_attendance_date = course.last_attendance_date
    if last_attendance_date:

        attendance_dates = course.attendancedate_set\
            .filter(date__lte = last_attendance_date)\
            .filter(date__gte = date_enrolled)
        days_attended = courseuser.studentattendance_set.filter(course=course)\
            .filter(date__lte = last_attendance_date)\
            .filter(date__gte = date_enrolled)

        number_days=0
        number_present=0
        for date in attendance_dates:
            number_days += 1
            try:
                attended = days_attended.get(date=date.date)
                if attended.present==1:
                    present = 'Y'
                elif attended.present==0:
                    present = 'N'
                elif attended.present==-1:
                    present = 'E'
                elif attended.present==0.5:
                    present = mark_safe('&frac12;')
                else:
                    present = '%.0f%%' % (attended.present*100)

                if attended.present==-1:
                    number_days -= 1
                else:
                    number_present += attended.present
                    
                    
            except ObjectDoesNotExist:
                present = 'N'
                
            try:
                percent = 100.0*number_present/float(number_days)
            except ZeroDivisionError:
                percent = 0

            attendance.append({'date': date.date, 'present': present, \
                                   'percent': percent })
    
        final_percent = percent

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/attendance_display.html', 
         {'course': course,
          'courseuser': courseuser,
          'student': courseuser, 
          'attendance': attendance,
          'date_enrolled': date_enrolled,
          'noanalytics': noanalytics,
          'last_attendance_date': last_attendance_date,
          'final_attendance_percent': percent,
          },
         context_instance=RequestContext(request))


@login_required
def adjusted_due_date_calculation_view(request, id):
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    content = get_object_or_404(CourseThreadContent, id=id)

    initial_due_date = content.get_initial_due_date(courseuser)
    final_due_date = content.get_final_due_date(courseuser)
    
    calculation_list = content.adjusted_due_date_calculation(courseuser)
    if calculation_list:
        adjusted_due_date=calculation_list[-1]['resulting_date']
    else:
        adjusted_due_date= initial_due_date

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/adjusted_due_date_calculation.html', 
         {'course': course,
          'content': content,
          'courseuser': courseuser,
          'student': courseuser, 
          'calculation_list': calculation_list,
          'adjusted_due_date': adjusted_due_date,
          'initial_due_date': initial_due_date,
          'final_due_date': final_due_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@login_required
def student_gradebook_view(request):
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

        
    category_scores=course.student_scores_by_assessment_category(courseuser)
    
    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/student_gradebook.html', 
         {'course': course,
          'courseuser': courseuser,
          'student': courseuser, 
          'category_scores': category_scores,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I')
def instructor_gradebook_view(request):
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))

    assessment_categories = course.all_assessments_by_category()
    student_scores = course.all_student_scores_by_assessment_category()
    total_points = course.total_points()

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/instructor_gradebook.html', 
         {'course': course,
          'courseuser': courseuser, 
          'assessment_categories': assessment_categories,
          'student_scores': student_scores,
          'total_points': total_points,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


class EditAssessmentAttempt(CourseUserAuthenticationMixin,DetailView):
    
    model = CourseThreadContent
    context_object_name = 'content'
    template_name = 'micourses/edit_assessment_attempt.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I'))
    def dispatch(self, request, *args, **kwargs):
        return super(EditAssessmentAttempt, self)\
            .dispatch(request, *args, **kwargs) 

    def get_object(self):
        content = super(EditAssessmentAttempt, self).get_object()
        self.assessment=content.thread_content.content_object
        self.latest_attempts = content.latest_student_attempts()
        return content

    def extra_course_context(self):
        latest_attempts_present=False
        for attempt in self.latest_attempts:
            if attempt['attempt']:
                latest_attempts_present = True
                break
        return {'latest_attempts': self.latest_attempts,
                'assessment': self.assessment,
                'latest_attempts_present': latest_attempts_present,
                'default_datetime': datetime.datetime.now()\
                    .strftime('%Y-%m-%d %H:%M')
                }


# temporary view while gradebook view is so slow
# and while don't have a way to have asseessment that don't contribute
# to course score show up in gradebook
@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()=='I')
def instructor_list_assessments_view(request):
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('mic-selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('mic-notenrolled'))


    assessments_with_points = course.all_assessments_with_points()

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/instructor_list_assessments.html', 
         {'course': course,
          'courseuser': courseuser, 
          'assessments': assessments_with_points,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

