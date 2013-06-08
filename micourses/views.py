from micourses.models import Course, CourseUser, CourseThreadContent
from mitesting.models import Assessment
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, Context
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import Http404
from django.contrib.auth.decorators import permission_required
from django import forms
import datetime


@login_required
def course_main_view(request):
    courseuser = request.user.courseuser

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
    
    if courseuser.role == 'S':
        return render_to_response \
            ('micourses/course_student_view.html', 
             {'student': courseuser,
              'course': course,
              'upcoming_assessments': upcoming_assessments,
              'next_items': next_items,
              'multiple_courses': multiple_courses,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))


@login_required
def assessment_attempts_view(request, id):
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
    adjusted_due_date = content.adjusted_due_date(courseuser)

    assessment_attempts = courseuser.studentcontentattempt_set\
            .filter(content=content)

    score = content.student_score(courseuser)

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/assessment_attempts.html', 
         {'student': courseuser, 'course': course,
          'content': content,
          'score': score,
          'assessment_attempts': assessment_attempts,
          'adjusted_due_date': adjusted_due_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@login_required
def assessment_attempt_questions_view(request, id, attempt_number):
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

    assessment_attempts = courseuser.studentcontentattempt_set\
        .filter(content=content)

    # don't pad attempt_number with zeros
    if attempt_number[0]=='0':
        raise  Http404('Assessment attempt %s not found.' % attempt_number)

    try:
        attempt = assessment_attempts[int(attempt_number)-1]
    except IndexError:
        raise Http404('Assessment attempt %s not found.' % attempt_number)


    assessment=content.thread_content.content_object
    # must be an assessment 
    if not isinstance(assessment,Assessment):
        raise Http404('Thread content %s is not an assessment' % assessment)

    if attempt.score is not None and attempt.score != attempt.get_score():
        score_overridden = True
    else:
        score_overridden = False
  
    rendered_question_list=assessment.render_question_list\
        (attempt.seed, current_attempt=attempt)

    question_list = []
    for qd in rendered_question_list:
        question_dict={'points': qd['points'],
                       'current_credit': qd['current_credit'],
                       'current_score': qd['current_score'],
                       }

        question_dict['answers_available'] = attempt.questionstudentanswer_set\
            .filter(question_set=qd['question_set']).exists()

        question_list.append(question_dict)

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/assessment_attempt_questions.html', 
         {'student': courseuser, 'course': course,
          'content': content,
          'attempt': attempt,
          'attempt_number': attempt_number,
          'question_list': question_list,
          'score_overridden': score_overridden,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@login_required
def assessment_attempt_question_detail_view(request, id, attempt_number, 
                                            question_number):
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

    assessment=content.thread_content.content_object
    # must be an assessment 
    if not isinstance(assessment,Assessment):
        raise Http404('Thread content %s is not an assessment' % assessment)

    assessment_attempts = courseuser.studentcontentattempt_set\
        .filter(content=content)

    # don't pad attempt_number with zeros
    if attempt_number[0]=='0':
        raise  Http404('Assessment attempt %s not found.' % attempt_number)

    try:
        attempt = assessment_attempts[int(attempt_number)-1]
    except IndexError:
        raise Http404('Assessment attempt %s not found.' % attempt_number)


    # don't pad question_number with zeros
    if question_number[0]=='0':
        raise  Http404('Question %s not found.' % question_number)

    question_number = int(question_number)

    try:
        question_dict = assessment.render_question_list\
            (attempt.seed, current_attempt=attempt)[question_number-1]
    except IndexError:
        raise  Http404('Question %s not found.' % question_number)

    question_set = question_dict['question_set']

    answers=attempt.questionstudentanswer_set.filter\
        (question_set=question_set)

    if not answers:
        raise Http404('Question %s not found.' % question_number)

    answer_list=[]
    for answer in answers:
        answer_dict = {'datetime': answer.datetime, }
        answer_dict['score'] = answer.credit*question_dict['points']
        answer_dict['credit_percent'] = int(answer.credit*100)
        answer_list.append(answer_dict)




    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/assessment_attempt_question_detail.html', 
         {'student': courseuser, 'course': course, 
          'content': content,
          'attempt': attempt,
          'attempt_number': attempt_number,
          'answers': answer_list,
          'points': question_dict['points'],
          'score': question_dict['current_score'],
          'current_credit': question_dict['current_credit'],
          'question_number': question_number,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


def assessment_attempt_question_attempt_view(request, id, attempt_number, 
                                             question_number, 
                                             question_attempt_number):
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

    assessment=content.thread_content.content_object
    # must be an assessment 
    if not isinstance(assessment,Assessment):
        raise Http404('Thread content %s is not an assessment' % assessment)

    assessment_attempts = courseuser.studentcontentattempt_set\
        .filter(content=content)

    # don't pad attempt_number with zeros
    if attempt_number[0]=='0':
        raise  Http404('Assessment attempt %s not found.' % attempt_number)

    try:
        attempt = assessment_attempts[int(attempt_number)-1]
    except IndexError:
        raise Http404('Assessment attempt %s not found.' % attempt_number)


    # don't pad question_number with zeros
    if question_number[0]=='0':
        raise  Http404('Question %s not found.' % question_number)

    question_number = int(question_number)

    try:
        question_dict = assessment.render_question_list\
            (attempt.seed, current_attempt=attempt)[question_number-1]
    except IndexError:
        raise  Http404('Question %s not found.' % question_number)

    question_set = question_dict['question_set']

    # don't pad question_attempt_number with zeros
    if question_attempt_number[0]=='0':
        raise  Http404('Question attempt %s not found.'\
                           % question_attempt_number)

    try:
        answer = attempt.questionstudentanswer_set.filter\
            (question_set=question_set)[int(question_attempt_number)-1]
    except IndexError:
        raise Http404('Question attempt %s not found.' \
                          % question_attempt_number)

    answer_dict = {'datetime': answer.datetime, 'answer': answer.answer  }
    answer_dict['score'] = answer.credit*question_dict['points']
    answer_dict['points'] = question_dict['points']
    answer_dict['credit_percent'] = int(answer.credit*100)
    answer_dict['attempt_number'] = question_attempt_number

    # determine if user has permission to view assessment, given privacy level
    if not assessment.user_can_view(request.user, solution=False):
        path = request.build_absolute_uri()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path)


    # construct question
    question = answer.question

    # use aaqav in identifier since coming from
    # assessment attempt question attempt view
    identifier = "aaqav"
    question_context = question.setup_context(identifier=identifier,
                                              seed=answer.seed, 
                                              allow_solution_buttons=False)

    # if there was an error, question_context is a string 
    # so just make rendered question text be that string
    if not isinstance(question_context, Context):
        rendered_question = question_context
        geogebra_oninit_commands=""
    else:
        pre_answers = {'identifier': answer.identifier_in_answer }
        import json
        pre_answers.update(json.loads(answer.answer))
        rendered_question = question.render_question\
            (question_context, identifier=identifier,user=request.user,\
                 show_help=False, pre_answers=pre_answers, readonly=True, \
                 precheck=True)

        geogebra_oninit_commands=question_context.get('geogebra_oninit_commands')

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/assessment_attempt_question_attempt.html', 
         {'question': question, 'rendered_question': rendered_question,
          'geogebra_oninit_commands': geogebra_oninit_commands,
          'student': courseuser, 'course': course,
          'content': content,
          'attempt': attempt,
          'attempt_number': attempt_number,
          'question': question,
          'question_number': question_number,
          'answer_dict': answer_dict,
          'rendered_question': rendered_question,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


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

    
    if courseuser.role == 'S':
        return render_to_response \
            ('micourses/upcoming_assessments.html', 
             {'student': courseuser,
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
    except ObjectDoesNotExist:
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
            
            attendance=[]
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
             student.studentattendance_set.filter(course=course)\
                 .filter(date__lte = last_attendance_date).delete()
             for (date, present) in attendance_dates_form.date_attendance():
                 if present:
                     student.studentattendance_set.create\
                         (course=course, date=date)
             message = "Updated attendance of %s." % student

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
