from micourses.models import Course, CourseUser, CourseThreadContent
from mitesting.models import Assessment
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
        course = Course.objects.get(code=course_code)
        courseuser.selected_course = course
        courseuser.save()
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

    upcoming_assessments = course.upcoming_assessments(courseuser, 
                                                       days_future=14)

    next_items = course.next_items(courseuser, number=5)
    
    if courseuser.role == 'I':
        return render_to_response \
            ('micourses/course_instructor_view.html', 
             {'student': courseuser,
              'courseuser': courseuser,
              'course': course,
              'upcoming_assessments': upcoming_assessments,
              'next_items': next_items,
              'multiple_courses': multiple_courses,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))
    else:
        return render_to_response \
            ('micourses/course_student_view.html', 
             {'student': courseuser,
              'courseuser': courseuser,
              'course': course,
              'upcoming_assessments': upcoming_assessments,
              'next_items': next_items,
              'multiple_courses': multiple_courses,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))


class AssessmentAttempted(CourseUserAuthenticationMixin,DetailView):
    
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

        rendered_question_list=self.assessment.render_question_list\
            (self.attempt.seed, current_attempt=self.attempt)

        question_list = []
        for qd in rendered_question_list:
            question_dict={'points': qd['points'],
                           'current_credit': qd['current_credit'],
                           'current_score': qd['current_score'],
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
            self.question_dict = self.assessment.render_question_list\
                (self.attempt.seed, current_attempt=self.attempt)\
                [self.question_number-1]
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
            answer_dict['score'] = answer.credit*self.question_dict['points']
            answer_dict['credit_percent'] = int(answer.credit*100)
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
        answer_dict['score'] = self.answer.credit*self.question_dict['points']
        answer_dict['points'] = self.question_dict['points']
        answer_dict['credit_percent'] = int(self.answer.credit*100)
        answer_dict['attempt_number'] = self.question_attempt_number
        


        # construct question
        question = self.answer.question

        # use aaqav in identifier since coming from
        # assessment attempt question attempt view
        identifier = "aaqav"
        question_context = question.setup_context(identifier=identifier,
                                                  seed=self.answer.seed, 
                                                  allow_solution_buttons=False)

        # if there was an error, question_context is a string 
        # so just make rendered question text be that string
        if not isinstance(question_context, Context):
            rendered_question = question_context
            geogebra_oninit_commands=""
        else:
            pre_answers = {'identifier': self.answer.identifier_in_answer }
            import json
            pre_answers.update(json.loads(self.answer.answer))
            rendered_question = question.render_question\
                (question_context, identifier=identifier,\
                     user=self.request.user,\
                     show_help=False, pre_answers=pre_answers, readonly=True, \
                     precheck=True)

            geogebra_oninit_commands=question_context\
                .get('geogebra_oninit_commands')

            context= {'question': question, 
                      'rendered_question': rendered_question,
                      'geogebra_oninit_commands': geogebra_oninit_commands,
                      'attempt': self.attempt,
                      'attempt_number': self.attempt_number,
                      'question_number': self.question_number,
                      'answer_dict': answer_dict,
                      'rendered_question': rendered_question,
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
def upcoming_assessments_view(request):
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

    upcoming_assessments = course.upcoming_assessments(courseuser)

    
    return render_to_response \
        ('micourses/upcoming_assessments.html', 
         {'student': courseuser,
          'courseuser': courseuser,
          'course': course,
          'upcoming_assessments': upcoming_assessments,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))



@permission_required("micourse.update_attendance")
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
            students_present = request.POST.getlist('students_present')
            
            # delete previous attendance data for the day
            course.studentattendance_set.filter(date=attendance_date).delete()
            for student_id in students_present:
                student = CourseUser.objects.get(id=student_id)
                course.studentattendance_set.create(student=student, date=attendance_date)
            
            if not course.last_attendance_date \
                    or attendance_date > course.last_attendance_date:
                course.last_attendance_date = attendance_date
                course.save()

            message = "Attendance updated for %s" % \
                attendance_date.strftime("%B %d, %Y")

        else:
            message = "Attendance not updated.  " \
                + "%s is not a valid course day" % \
                request.POST['attendance_date'] 

            
    else:
        message = None


    # get next_attendance date
    next_attendance_date = course.find_next_attendance_date()
            

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/update_attendance.html', 
         {'course': course,
          'message': message,
          'next_attendance_date': next_attendance_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@permission_required("micourse.update_attendance")
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
        student = forms.ModelChoiceField(queryset=course.enrolled_students.all())           
    

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
            (queryset=course.enrolled_students.all(), \
                 widget=forms.HiddenInput,\
                 initial=thestudent)
        
        def __init__(self, *args, **kwargs):
            try:
                dates = kwargs.pop('dates')
            except:
                dates =[]
            super(AttendanceDatesForm, self).__init__(*args, **kwargs)

            for i, attendance_date in enumerate(dates):
                self.fields['date_%s' % i] = forms.BooleanField\
                    (label=attendance_date['date'],\
                         initial=attendance_date['present'],\
                         required=False)
                
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
                    present = True
                except ObjectDoesNotExist:
                    present = False

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
                             (course=course, date=date)
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

    last_attendance_date = course.last_attendance_day_previous_week()
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
                present = 'Y'
                number_present += 1
            except ObjectDoesNotExist:
                present = 'N'
                
            percent = 100.0*number_present/float(number_days)
            
            attendance.append({'date': date.date, 'present': present, \
                                   'percent': percent })
    


    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/attendance_display.html', 
         {'course': course,
          'student': courseuser, 
          'attendance': attendance,
          'date_enrolled': date_enrolled,
          'noanalytics': noanalytics,
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
    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/instructor_gradebook.html', 
         {'course': course,
          'courseuser': courseuser, 
          'assessment_categories': assessment_categories,
          'student_scores': student_scores,
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

