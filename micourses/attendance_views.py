
from micourses.models import Course, CourseUser, ThreadContent, QuestionAttempt, QuestionResponse, Assessment, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE, ABSENT, PRESENT, EXCUSED

from micourses.views import CourseBaseView, CourseBaseMixin

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
from micourses.attendance_forms import DateForm, attendance_dates_form_factory, select_student_form_factory
import pytz
import reversion



class UpdateAttendance(CourseBaseView):
    instructor_view = True
    template_name = 'micourses/update_attendance.html'

    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_context_data(self, **kwargs):
        context = super(UpdateAttendance, self).get_context_data(**kwargs)

        # get next_attendance date
        context['next_attendance_date'] = self.course.find_next_attendance_date()
            
        context['enrollment_list'] = self.course.courseenrollment_set.filter(role=STUDENT_ROLE,withdrew=False).order_by('group', 'student__user__last_name', 'student__user__first_name')

        message = self.request.GET.get("message")
        if message:
            context['message'] = message

        context['PRESENT'] = PRESENT
        context['ABSENT'] = ABSENT
        context['EXCUSED'] = EXCUSED
        
        return context


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)


        # update attendance, assuming date is valid
        date_form = DateForm({'date':  request.POST['attendance_date']})
        valid_day = False

        if date_form.is_valid():
            attendance_date = date_form.cleaned_data['date']

            # check if date is a class day
            for class_day in self.course.attendancedate_set.all():
                if attendance_date == class_day.date:
                    valid_day = True
                    break
            
        else:
            attendance_date = None

        if valid_day:
            with transaction.atomic(), reversion.create_revision():

                for ce in self.course.courseenrollment_set.filter(withdrew=False):
                    present=request.POST.get('student_%s' % ce.id, ABSENT)
                    try:
                        present = int(present)
                    except ValueError:
                        present = ABSENT

                    sa, created = ce.studentattendance_set.get_or_create(
                        date=attendance_date,
                        defaults = {'present': present})
                    # don't override an excused absence with an absence
                    if not created and \
                       not (sa.present == EXCUSED and present==ABSENT):
                        sa.present = present
                        sa.save()

                if not self.course.last_attendance_date \
                        or attendance_date > self.course.last_attendance_date:
                    self.course.last_attendance_date = attendance_date
                    self.course.save()


            message = "Attendance updated for %s" % \
                      attendance_date.strftime("%B %d, %Y")

            from django.utils.encoding import escape_uri_path
            url = reverse('micourses:update_attendance',
                          kwargs={'course_code': self.course.code})
            url += "?message=%s" % escape_uri_path(message)
            return redirect(url) 


        else:
            context = self.get_context_data(object=self.object)

            context['message'] = "Attendance not updated.  " \
                + "%s is not a valid course day" % \
                (request.POST['attendance_date'])

            return self.render_to_response(context)





class UpdateIndividualAttendance(CourseBaseView):
    instructor_view = True
    template_name = 'micourses/update_individual_attendance.html'


    # return student, unless no_student has been set
    def get_student(self):

        student_id=None
        if self.request.method=="GET":
            student_id = self.request.GET.get('student')
        elif self.request.method=="POST":
            student_id = self.request.POST.get('student')

        student=None
        self.no_student=True

        if student_id:
            try:
                student=self.course.enrolled_students.get(id=student_id)
                self.no_student=False
            except ObjectDoesNotExist:
                student=None

        if not student:
            return self.courseuser
        else:
            return student


    def get_forms(self, data=None):
        """
        Get select student and attendance dates forms.
        
        If data is None, then population attendance dates form
        with the initial values from student attendance database.
        Otherwise, population attendance dates form with data.
        
        """


        if self.no_student:
            self.select_student_form = select_student_form_factory\
                                       (self.course)()
            self.attendance_dates_form = None
            return


        self.select_student_form = select_student_form_factory\
                                       (self.course)({'student': self.student})

        attendance = self.get_attendance()

        the_form = attendance_dates_form_factory(
            course=self.course, student=self.student)

        self.attendance_dates_form = the_form(data, dates=attendance,
                                              label_suffix="")



    def get_attendance(self):
        # get list of attendance up to last_attendance_date

        attendance=[]
        if self.last_attendance_date:
            date_enrolled = self.student.courseenrollment_set.get(
                course=self.course).date_enrolled
            attendance_dates = self.course.attendancedate_set\
                .filter(date__lte = self.last_attendance_date)\
                .filter(date__gte = date_enrolled)
            days_attended = self.student_enrollment.studentattendance_set\
                    .filter(date__lte = self.last_attendance_date)\
                    .filter(date__gte = date_enrolled)
            
            for date in attendance_dates:
                try:
                    attended = days_attended.get(date=date.date)
                    present = int(attended.present)
                except ObjectDoesNotExist:
                    present = ABSENT

                attendance.append({'date': date.date, 'present': present})

        return attendance


    def get_context_data(self, **kwargs):
        context = super(UpdateIndividualAttendance, self)\
            .get_context_data(**kwargs)

        context['select_student_form'] = self.select_student_form
        
        context['attendance_dates_form'] = self.attendance_dates_form
        context['next_attendance_date'] = self.course\
                                              .find_next_attendance_date()

        context['future_excused_absences'] = \
                self.student_enrollment.studentattendance_set.filter(
                    date__gt=self.last_attendance_date,
                    present=EXCUSED)


        if self.no_student:
            context['student'] = None

        message = self.request.GET.get("message")
        if message:
            context['message'] = message

        return context


    # called for a get
    def get_additional_objects(self, request, *args, **kwargs):

        self.last_attendance_date = self.course.last_attendance_date

        # get forms with data from database
        self.get_forms()
        

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)

        
        # possible actions: update, add_excused, delete_excused
        action = request.POST.get("action")

        self.last_attendance_date = self.course.last_attendance_date

        message = ""

        if action=="add_excused":
            date_form = DateForm({'date':  request.POST['attendance_date']})
            valid_day = False
            if date_form.is_valid():
                attendance_date = date_form.cleaned_data['date']

                # check if date is a class day
                for class_day in self.course.attendancedate_set.all():
                    if attendance_date == class_day.date:
                        valid_day = True
                        break
            else:
                attendance_date = None

            if valid_day:
                with transaction.atomic(), reversion.create_revision():
                    sa, created = self.student_enrollment.studentattendance_set\
                        .get_or_create(
                        date=attendance_date, defaults = {'present': EXCUSED})

                    if not created:
                        sa.present=EXCUSED
                        sa.save()

                message = "Added excused absence for %s on %s." % \
                          (self.student, attendance_date.strftime("%B %d, %Y"))

                from django.utils.encoding import escape_uri_path
                url = reverse('micourses:update_individual_attendance',
                              kwargs={'course_code': self.course.code})
                url += "?student=%s&message=%s" % \
                       (self.student.id, escape_uri_path(message))
                return redirect(url) 

            else:
                
                message = "Excused absence not added.  " \
                          + "%s is not a valid course day" % \
                          (request.POST['attendance_date'])
            
                # get attendance forms with data from database
                self.get_forms()


        elif action=="delete_excused":
            
            excused_to_delete = request.POST.getlist("excused_date")

            n_deleted=0
            deleted_date=None
            for excused_id in excused_to_delete:
                try:
                    excused=self.student_enrollment.studentattendance_set.get(
                        id=excused_id, present=EXCUSED)
                except ObjectDoesNotExist:
                    pass
                else:
                    deleted_date = excused.date
                    with transaction.atomic(), reversion.create_revision():
                        excused.delete()
                    n_deleted +=1

            if n_deleted == 1:
                message = "Deleted 1 excused absence for %s: %s." % \
                          (self.student, deleted_date.strftime("%B %d, %Y"))
            else:
                message = "Deleted %s excused absences for %s." % \
                          (n_deleted, self.student)

            from django.utils.encoding import escape_uri_path
            url = reverse('micourses:update_individual_attendance',
                          kwargs={'course_code': self.course.code})
            url += "?student=%s&message=%s" % \
                   (self.student.id, escape_uri_path(message))
            return redirect(url) 



        elif action=="update":
            # get attendance forms populated with POST data
            self.get_forms(request.POST)

            if not self.last_attendance_date:
                message = "Last attendance date for course not set.  Cannot update attendance."
            elif self.attendance_dates_form.is_valid():
                with transaction.atomic(), reversion.create_revision():
                    self.student_enrollment.studentattendance_set\
                        .filter(date__lte = self.last_attendance_date).delete()
                for (date, present) in \
                    self.attendance_dates_form.date_attendance():
                    if present:
                        self.student_enrollment.studentattendance_set\
                                        .create(date=date, present=present)

                message = "Updated attendance of %s." % self.student

                from django.utils.encoding import escape_uri_path
                url = reverse('micourses:update_individual_attendance',
                              kwargs={'course_code': self.course.code})
                url += "?student=%s&message=%s" % \
                       (self.student.id, escape_uri_path(message))
                return redirect(url) 
                 
        
        context = self.get_context_data(object=self.object)

        context['message'] = message

        return self.render_to_response(context)



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
            days_attended = self.enrollment.studentattendance_set \
                .filter(date__lte = last_attendance_date)\
                .filter(date__gte = date_enrolled)

            number_days=0
            number_present=0
            for date in attendance_dates:
                number_days += 1
                try:
                    attended = days_attended.get(date=date.date)
                    present = attended.present_as_word()

                    if attended.present==EXCUSED:
                        number_days -= 1
                    elif attended.present==PRESENT:
                        number_present += 1


                except ObjectDoesNotExist:
                    present = 'Absent'

                try:
                    percent = 100.0*number_present/float(number_days)
                except ZeroDivisionError:
                    percent = 0

                attendance.append({'date': date.date, 'present': present, \
                                   'percent': percent })

            final_percent = percent

        context['attendance']=attendance
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
