
from micourses.models import Course, CourseUser, ThreadContent, QuestionAttempt, QuestionResponse, Assessment, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from micourses.views import CourseBaseView

from micourses.forms import ContentAttemptForm, ScoreForm, CreditForm, AttemptScoresForm
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext, Context, Template
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.views.generic import DetailView, View, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import TemplateResponseMixin
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.db import IntegrityError, transaction
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.utils import timezone
from micourses.templatetags.course_tags import floatformat_or_dash
from micourses.utils import format_datetime
import pytz
import reversion

@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def update_attendance_view(request):
    
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('micourses:selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('micourses:notenrolled'))

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
            with transaction.atomic(), reversion.create_revision():

                for student in course.enrolled_students_ordered():
                    present=request.POST.get('student_%s' % student.id, 0)
                    try:
                        present = float(present)
                    except ValueError:
                        present = 0.0

                    sa, created = course.studentattendance_set.get_or_create(
                        student=student, date=attendance_date,
                        defaults = {'present': present})
                    if not created and sa.present != -1:
                        sa.present = present
                        sa.save()

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
            
    enrollment_list = course.courseenrollment_set.filter(role=STUDENT_ROLE,withdrew=False).order_by('group', 'student__user__last_name', 'student__user__first_name')

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/update_attendance.html', 
         {'course': course,
          'courseuser': courseuser,
          'enrollment_list': enrollment_list,
          'message': message,
          'next_attendance_date': next_attendance_date,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def update_individual_attendance_view(request):
    
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('micourses:selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('micourses:notenrolled'))

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
                    (label=str(attendance_date['date']),\
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

         attendance_dates_form = AttendanceDatesForm(request.POST or None, dates=attendance, label_suffix="")

         if attendance_dates_form.is_valid():
             if last_attendance_date:
                 student.studentattendance_set.filter(course=course)\
                     .filter(date__lte = last_attendance_date).delete()
                 for (date, present) in attendance_dates_form.date_attendance():
                     if present:
                         with transaction.atomic(), reversion.create_revision():
                             student.studentattendance_set.create\
                                 (course=course, date=date, present=present)
                 message = "Updated attendance of %s." % student
             else:
                 message = "Last attendance date for course not set.  Cannot update attendance."

    # if get
    else:
        if student:
            attendance_dates_form = AttendanceDatesForm(dates=attendance, label_suffix="")
        else:            
            attendance_dates_form = AttendanceDatesForm()


    # get next_attendance date
    next_attendance_date = course.find_next_attendance_date()

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/update_individual_attendance.html', 
         {'course': course,
          'courseuser': courseuser,
          'select_student_form': select_student_form,
          'student': student,
          'attendance_dates_form': attendance_dates_form,
          'next_attendance_date': next_attendance_date,
          'message': message,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))



@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def add_excused_absence_view(request):
    
    courseuser = request.user.courseuser
    
    try:
        course = courseuser.return_selected_course()
    except MultipleObjectsReturned:
        # courseuser is in multple active courses and hasn't selected one
        # redirect to select course page
        return HttpResponseRedirect(reverse('micourses:selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('micourses:notenrolled'))


    if request.method == "GET":
        return HttpResponseRedirect(reverse('micourses:updateindividualattendance') + '?' + request.GET.urlencode())

    class SelectStudentForm(forms.Form):
        student = forms.ModelChoiceField(queryset=course.enrolled_students_ordered())           
    # get student from request
    student_id = request.POST.get('student')
    try:
        student = CourseUser.objects.get(id=student_id)
        select_student_form = SelectStudentForm(request.POST)
    except (ObjectDoesNotExist, ValueError):
        return HttpResponseRedirect(reverse('micourses:updateindividualattendance'))


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
                    (label=str(attendance_date['date']),\
                         initial=attendance_date['present'],\
                         choices=((1,1),(0.5,0.5),(0,0),(-1,-1)),\
                         widget=forms.RadioSelect,
                     )
                
        def date_attendance(self):
            for name, value in self.cleaned_data.items():
                if name.startswith('date_'):
                    yield (self.fields[name].label, value)





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
            with transaction.atomic(), reversion.create_revision():
                sa, created = student.studentattendance_set.get_or_create(
                    course=course, date=attendance_date, defaults = {'present': -1})

                if not created:
                    sa.present=-1
                    sa.save()

                message = "Added excused absence for %s on %s." % \
                          (student, attendance_date.strftime("%B %d, %Y"))

        else:

            message = "Excused absence not added.  " \
                + "%s is not a valid course day: %s" % \
                (request.POST['attendance_date'], attendance_date)

    # no Google analytics for course
    noanalytics=True

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


    attendance_dates_form = AttendanceDatesForm(dates=attendance, label_suffix="")


    return render_to_response \
        ('micourses/update_individual_attendance.html', 
         {'course': course,
          'courseuser': courseuser,
          'select_student_form': select_student_form,
          'student': student,
          'attendance_dates_form': attendance_dates_form,
          'next_attendance_date': attendance_date,
          'message': message,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))
        



class AttendanceDisplay(CourseBaseView):
    template_name='micourses/attendance_display.html'

    def get_context_data(self, **kwargs):
        context = super(AttendanceDisplay, self).get_context_data(**kwargs)

        attendance = []
        date_enrolled = self.enrollment.date_enrolled

        percent = 0

        last_attendance_date = self.course.last_attendance_date
        if last_attendance_date:

            attendance_dates = self.course.attendancedate_set\
                .filter(date__lte = last_attendance_date)\
                .filter(date__gte = date_enrolled)
            days_attended = self.courseuser.studentattendance_set.filter(course=self.course)\
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

        context['attendance']=attendance,
        context['date_enrolled']= date_enrolled
        context['last_attendance_date']=last_attendance_date
        context['final_attendance_percent'] =percent

        return context


class AdjustedDueCalculation(CourseBaseView):
    template_name='micourses/adjusted_due_calculation.html'

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))



    def get_context_data(self, **kwargs):
        context = super(AdjustedDueCalculation, self).get_context_data(**kwargs)

        context['thread_content'] = self.thread_content
        
        initial_due = self.thread_content.get_initial_due(self.student)
        final_due = self.thread_content.get_final_due(self.student)
    
        calculation_list = self.thread_content.adjusted_due_calculation(
            self.student)
        if calculation_list:
            adjusted_due=calculation_list[-1]['resulting_date']
        else:
            adjusted_due= initial_due

            
        context['calculation_list']=calculation_list
        context['adjusted_due'] = adjusted_due
        context['initial_due']=initial_due
        context['final_due']=final_due

        return context
