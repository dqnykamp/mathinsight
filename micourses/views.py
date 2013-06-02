from micourses.models import Course, Module, ModuleAssessment, StudentAssessmentAttempt, CourseUser
from mitesting.models import Assessment
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
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
        
    # no Google analytics for course
    noanalytics=True

    upcoming_assessments = course.upcoming_assessments(courseuser)


    if courseuser.role == 'S':
        return render_to_response \
            ('micourses/course_student_view.html', 
             {'student': courseuser,
              'course': course,
              'upcoming_assessments': upcoming_assessments,
              'noanalytics': noanalytics,
              },
             context_instance=RequestContext(request))




@login_required
def assessment_attempts_view(request, module_code, assessment_code):
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

    module = get_object_or_404(Module, code=module_code, course=course)
    assessment = get_object_or_404(Assessment, code=assessment_code)
    module_assessment = get_object_or_404(ModuleAssessment, module=module, assessment=assessment)

    assessment_attempts = courseuser.studentassessmentattempt_set.filter(module_assessment=module_assessment)

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/assessment_attempts.html', 
         {'student': courseuser,
          'module': module,
          'module_assessment': module_assessment,
          'assessment_attempts': assessment_attempts,
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

    attendance_dates_form = AttendanceDatesForm()

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
                
                

            attendance_dates_form = AttendanceDatesForm(dates=attendance)

    

    # if POST, then update attendance, assuming date is valid
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


        # valid_day = False
        # if date_form.is_valid():
        #     attendance_date = date_form.cleaned_data['date']
            
        #     # check if date is a class day
        #     for class_day in course.attendancedate_set.all():
        #         if attendance_date == class_day.date:
        #             valid_day = True
        #             break
            
        # else:
        #     attendance_date = None

        # if valid_day:
        #     students_present = request.POST.getlist('students_present')
            
        #     # delete previous attendance data for the day
        #     course.studentattendance_set.filter(date=attendance_date).delete()
        #     for student_id in students_present:
        #         student = CourseUser.objects.get(id=student_id)
        #         course.studentattendance_set.create(student=student, date=attendance_date)
            
        #     if not course.last_attendance_date \
        #             or attendance_date > course.last_attendance_date:
        #         course.last_attendance_date = attendance_date
        #         course.save()

        #     message = "Attendance updated for %s" % \
        #         attendance_date.strftime("%B %d, %Y")

        # else:
        #     message = "Attendance not updated.  " \
        #         + "%s is not a valid course day" % \
        #         request.POST['attendance_date'] 

    # if GET
    else:
        pass
        # # check if student is in GET parameters
        # student_id = request.GET.get('student')
        # try:
        #     student = CourseUser.objects.get(id=student_id)
        #     select_student_form = SelectStudentForm(request.GET)
        # except ObjectDoesNotExist:
        #     student = None
        #     select_student_form = SelectStudentForm()

        
        # if student:
        #     # get list of attendance up to last_attendance_date

        #     last_attendance_date = course.last_attendance_date
        #     if last_attendance_date:
        #         attendance_dates = course.attendancedate_set.filter\
        #             (date__lte = last_attendance_date)
        #         days_attended = student.studentattendance_set.filter \
        #             (course=course).filter(date__lte = last_attendance_date)

        #         for date in attendance_dates:
        #             try:
        #                 attended = days_attended.get(date=date.date)
        #                 present = True
        #             except ObjectDoesNotExist:
        #                 present = False

        #             attendance.append({'date': date.date, 'present': present})
                

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
def adjusted_due_date_calculation_view(request, module_code, assessment_code):
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

    module = get_object_or_404(Module, code=module_code, course=course)
    assessment = get_object_or_404(Assessment, code=assessment_code)
    module_assessment = get_object_or_404(ModuleAssessment, module=module, assessment=assessment)

    initial_due_date = module_assessment.get_initial_due_date(courseuser)
    final_due_date = module_assessment.get_final_due_date(courseuser)
    
    calculation_list = module_assessment.adjusted_due_date_calculation(courseuser)
    if calculation_list:
        adjusted_due_date=calculation_list[-1]['resulting_date']
    else:
        adjusted_due_date= initial_due_date

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/adjusted_due_date_calculation.html', 
         {'course': course,
          'module_assessment': module_assessment,
          'student': courseuser, 
          'calculation_list': calculation_list,
          'adjusted_due_date': adjusted_due_date,
          'initial_due_date': initial_due_date,
          'final_due_date': final_due_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))
