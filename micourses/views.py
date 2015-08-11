
from micourses.models import Course, CourseUser, ThreadSection, ThreadContent, QuestionAttempt, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from mitesting.models import Assessment
from micourses.forms import ContentAttemptForm, thread_content_form_factory
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.template import RequestContext, Context, Template
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.views.generic import DetailView, View, ListView
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.db import IntegrityError, transaction
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.utils import timezone
from micourses.templatetags.course_tags import floatformat_or_dash
from mitesting.render_assessments import render_question_list, render_question
from micourses.utils import format_datetime
import pytz
import reversion


class SelectCourseView(ListView):
    context_object_name = "course_list"
    template_name = 'micourses/select_course.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        self.courseuser = request.user.courseuser
        self.object_list = self.get_queryset()

        # if only one course enrolled, then automatically redirect to course
        self.n_courses = len(self.object_list)

        if self.n_courses == 1:
            return redirect('micourses:coursemain',
                            course_code=self.object_list.first().code)

        context = self.get_context_data()
        return self.render_to_response(context)

    def get_queryset(self):
        return self.courseuser.course_set.filter(active=True)

    def get_context_data(self):
        context = super(ListView,self).get_context_data()
        context["n_courses"]=self.n_courses
        context["cuser"]=self.courseuser
        return context

        
class CourseBaseView(DetailView):
    """
    Requires user to be logged in user enrolled in a course
    before being able to access the post/get methods.
    Adds course, courseuser, and noanalytics to context
    """
    model = Course
    slug_url_kwarg = 'course_code'
    slug_field = 'code'
    instructor_view = False

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.course = self.object
        self.courseuser = request.user.courseuser

        try:
            self.enrollment = self.course.courseenrollment_set.get(
                student=self.courseuser)
        except ObjectDoesNotExist:
            return redirect('micourses:notenrolled', course_code=self.course.code)

        self.current_role=self.get_current_role(course)
        
        if self.instructor_view and not (self.current_role == INSTRUCTOR_ROLE
                                         or self.current_role == DESIGNER_ROLE):
            return redirect('micourses:coursemain', course_code=self.course.code)
            
        self.student = self.get_student()

        # if student isn't the same as course user, obtain students
        # enrollment as well
        if self.student != self.courseuser:
            try:
                self.student_enrollment = self.course.courseenrollment_set.get(
                    student=self.student)
            except ObjectDoesNotExist:
                raise Http404('Student %s not enrolled in course %s' \
                              % (self.student, self.course))
        else:
            self.student_enrollment = self.enrollment

        self.get_additional_objects(request, *args, **kwargs)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_additional_objects(self, request, *args, **kwargs):
        pass

    def get_student(self):
        if self.instructor_view:
            return get_object_or_404(self.course.enrolled_students,
                                     id=self.kwargs['student_id'])
        else:
            return self.courseuser

    def get_context_data(self, **kwargs):
        context = super(CourseBaseView, self).get_context_data(**kwargs)
        
        context['courseuser'] = self.courseuser
        context['course'] = self.course
        context['student'] = self.get_student()
        context['current_role'] = self.current_role
        context['instructor_view'] = self.instructor_view

        # no Google analytics for course
        context['noanalytics']=True

        context.update(self.extra_context())

        return context

    def extra_context(self):
        # for context that derived classes can easily ignore 
        # by declaring own extra_context
        return {}


class CourseView(CourseBaseView):
    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)

        from micourses.utils import find_week_begin_end

        beginning_of_week, end_of_week = find_week_begin_end(self.course)

        context['week_date_parameters'] = \
            "begin_date=%s&end_date=%s" % (beginning_of_week, end_of_week)

        begin_date=beginning_of_week
        end_date=end_of_week+timezone.timedelta(days=7)
        context['begin_date']=begin_date
        context['end_date']=end_date


        context["upcoming_content"] = self.course.course_content_by_adjusted_due \
            (self.courseuser, begin_date=begin_date, \
                 end_date=end_date)

        date_parameters = "begin_date=%s&end_date=%s" % (begin_date,
                                                         end_date)
        context['include_completed_parameters'] = date_parameters

        next_begin_date = end_date + timezone.timedelta(microseconds=1)
        next_end_date = next_begin_date+timezone.timedelta(days=7) \
                        - timezone.timedelta(microseconds=1)
        next_period_parameters = "begin_date=%s&end_date=%s" \
            % (next_begin_date, next_end_date)
        previous_end_date = begin_date - timezone.timedelta(microseconds=1)
        previous_begin_date = previous_end_date-timezone.timedelta(days=7)\
                              + timezone.timedelta(microseconds=1)
        previous_period_parameters = "begin_date=%s&end_date=%s" \
            % (previous_begin_date, previous_end_date)
        previous_period_parameters += "&exclude_completed"
        next_period_parameters += "&exclude_completed"

        context['previous_period_parameters']=previous_period_parameters
        context['next_period_parameters']=next_period_parameters

        context['next_items'] = self.course.next_items(self.courseuser, number=5)

        return context
        

    def get_template_names(self):
        if self.instructor_view:
            return ['micourses/course_instructor_view.html',]
        else:
            return ['micourses/course_student_view.html',]


class ContentRecordView(CourseBaseView):

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, self.content_id))

        try:
            self.content_record = self.thread_content.studentcontentrecord_set\
                                  .get(enrollment=self.student_enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.content_record = self.thread_content.studentcontentrecord_set\
                                  .create(enrollment=self.student_enrollment)


    def get_context_data(self, **kwargs):
        context = super(ContentRecordView, self).get_context_data(**kwargs)

        context['thread_content'] = self.thread_content
        context['content_record'] = self.content_record
        
        return context


    def extra_context(self):
        from micourses.utils import format_datetime
        attempt_list = []
        for (i, attempt) in enumerate(self.content_record.attempts.all()):
            earliest, latest = attempt.return_activity_interval()
            datetime_text = format_datetime(earliest)
            if latest:
                datetime_text += " - " + format_datetime(latest)
            score_text = floatformat_or_dash(attempt.score, 1)
            attempt_dict = {}
            attempt_number = i+1
            attempt_dict['attempt'] = attempt
            attempt_dict['score'] = attempt.score
            attempt_dict['attempt_number']  = attempt_number
            attempt_dict['formatted_attempt_number'] = \
                mark_safe('&nbsp;%i&nbsp;' % attempt_number)
            attempt_dict['datetime'] = \
                mark_safe('&nbsp;%s&nbsp;' % datetime_text)
            attempt_dict['formatted_score'] = \
                mark_safe('&nbsp;%s&nbsp;' % score_text)
            
            # show details if have question_set with credit that isn't None
            question_set_with_credit = False
            if attempt.question_sets.exclude(credit_override=None):
                question_set_with_credit=True
            elif QuestionAttempt.objects.filter(
                    content_attempt_question_set__content_attempt=attempt) \
                    .exclude(credit=None):
                question_set_with_credit=True
            if question_set_with_credit:
                if self.instructor_view:
                    attempt_url = reverse('micourses:contentattemptinstructor', 
                                    kwargs={'course_code': self.course.code,
                                            'content_id': self.object.id,
                                            'attempt_number': attempt_number,
                                            'student_id': self.student.id})
                else:
                    attempt_url = reverse('micourses:contentattempt', 
                                    kwargs={'course_code': self.course.code,
                                            'content_id': self.object.id,
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
                
        return {'adjusted_due': self.thread_content\
                    .adjusted_due(self.student),
                'attempts': attempt_list,
                'score': self.content_record.score,
                }


    def get_template_names(self):
        if self.instructor_view:
            return ['micourses/content_record_instructor.html',]
        else:
            return ['micourses/content_record_student.html',]



class ContentRecordInstructor(ContentRecordView):
    template_name = 'micourses/content_record_instructor.html'
    instructor_view = True


    def extra_course_context(self):
        from micourses.utils import format_datetime
        attempt_list = []
        for (i,attempt) in enumerate(self.assessment_attempts):
            datetime_text = format_datetime(attempt.datetime)
            if attempt.have_datetime_interval():
                datetime_text += " - " \
                    + format_datetime(attempt.get_latest_datetime())
            score_text = floatformat_or_dash(attempt.score, 1)
            attempt_dict = {}
            attempt_number = i+1
            attempt_dict['attempt'] = attempt
            attempt_dict['score'] = attempt.score
            attempt_dict['attempt_number']  = attempt_number
            attempt_dict['formatted_attempt_number'] = \
                mark_safe('&nbsp;%i&nbsp;' % attempt_number)
            attempt_dict['datetime'] = \
                mark_safe('&nbsp;%s&nbsp;' % datetime_text)
            attempt_dict['formatted_score'] = \
                mark_safe('&nbsp;%s&nbsp;' % score_text)
            attempt_dict['direct_link'] = attempt.content.content_object.return_link(direct=True, link_text=" try it",seed=attempt.seed)

            if attempt.questionstudentanswer_set.exists():
                attempt_url = reverse('micourses:assessmentattemptinstructor', 
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
                ({'score': attempt.score, 'content': attempt.content.id,
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
                'datetime': timezone.now()\
                    .strftime('%Y-%m-%d %H:%M'),
                })


        return {'adjusted_due': self.object\
                    .adjusted_due(self.student),
                'attempts': attempt_list,
                'score': self.object.student_score(self.student),
                'new_attempt_form': new_attempt_form,
                }


#class EditContentAttemptView(View):
    

class ContentAttemptView(ContentRecordView):
    
    template_name = 'micourses/content_attempt.html'

    def get_object(self):
        content = super(ContentAttemptView, self).get_object()
        
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
        context['score_overridden'] = self.attempt.score_override is not None

        import random
        rng=random.Random()
        rendered_question_list=render_question_list\
            (self.assessment, rng=rng, seed=self.attempt.seed,
             current_attempt=self.attempt)[0]

        question_list = []
        for qd in rendered_question_list:
            question_dict={'points': qd['points'],
                           'current_credit': qd['question_data']['current_credit'],
                           'current_score': qd['question_data']['current_score'],
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


class AssessmentAttemptInstructor(ContentAttemptView):
    template_name = 'micourses/assessment_attempt_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
    def dispatch(self, request, *args, **kwargs):
        return super(AssessmentAttemptInstructor, self)\
            .dispatch(request, *args, **kwargs) 
    def get_student(self):
        return get_object_or_404(self.course.enrolled_students,
                                 id=self.kwargs['student_id'])


class AssessmentAttemptQuestion(ContentAttemptView):
    
    model = ThreadContent
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
            import random
            rng=random.Random()
            self.question_dict=render_question_list\
                    (self.assessment, rng=rng, seed=self.attempt.seed, 
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
        context['score'] = self. question_dict['question_data']['current_score']
        context['current_credit'] = self.question_dict['question_data']['current_credit']
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

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
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
        try:
            question = self.answer.question
        except ObjectDoesNotExist:
            raise Http404('Question not found.')


        # use aaqav in identifier since coming from
        # assessment attempt question attempt view
        identifier = "aaqav"

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()

        import json
        prefilled_answers = json.loads(self.answer.answer)

        import random
        rng=random.Random()
        question_data = render_question(question, 
                                        rng=rng, seed=self.answer.seed,
                                        question_identifier=identifier,
                                        user=self.request.user, show_help=False,
                                        prefilled_answers=prefilled_answers, 
                                        readonly=True, auto_submit=True, 
                                        record_answers=False,
                                        allow_solution_buttons=False,
                                        auxiliary_data=auxiliary_data)


        context= {'question': question, 
                  'question_data': question_data,
                  '_auxiliary_data_': auxiliary_data,
                  'attempt': self.attempt,
                  'attempt_number': self.attempt_number,
                  'question_number': self.question_number,
                  'answer_dict': answer_dict,
        }
        
        return context

class AssessmentAttemptQuestionAttemptInstructor(AssessmentAttemptQuestionAttempt):
    template_name = 'micourses/assessment_attempt_question_attempt_instructor.html'

    @method_decorator(user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE))
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
        return HttpResponseRedirect(reverse('micourses:selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('micourses:notenrolled'))

    # no Google analytics for course
    noanalytics=True

    # find begining/end of week
    tz = pytz.timezone(course.attendance_time_zone)
    now = tz.normalize(timezone.now().astimezone(tz))
    day_of_week = (now.weekday()+1) % 7
    to_beginning_of_week = timezone.timedelta(
        days=day_of_week, hours=now.hour,
        minutes=now.minute, seconds=now.second, microseconds=now.microsecond
    )
    beginning_of_week = now - to_beginning_of_week
    end_of_week = beginning_of_week + timezone.timedelta(days=7) \
                  - timezone.timedelta(microseconds=1)
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

    content_list = course.course_content_by_adjusted_due\
        (courseuser, exclude_completed=exclude_completed, \
             begin_date=begin_date, end_date=end_date)

    if begin_date and end_date:
        next_begin_date = end_date + timezone.timedelta(1)
        next_end_date = next_begin_date+(end_date-begin_date)
        next_period_parameters = "begin_date=%s&end_date=%s" \
            % (next_begin_date, next_end_date)
        previous_end_date = begin_date - timezone.timedelta(1)
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
        


@login_required
def attendance_display_view(request):
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
def adjusted_due_calculation_view(request, pk):
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

    content = get_object_or_404(ThreadContent, id=pk)

    initial_due = content.get_initial_due(courseuser)
    final_due = content.get_final_due(courseuser)
    
    calculation_list = content.adjusted_due_calculation(courseuser)
    if calculation_list:
        adjusted_due=calculation_list[-1]['resulting_date']
    else:
        adjusted_due= initial_due

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/adjusted_due_calculation.html', 
         {'course': course,
          'content': content,
          'courseuser': courseuser,
          'student': courseuser, 
          'calculation_list': calculation_list,
          'adjusted_due': adjusted_due,
          'initial_due': initial_due,
          'final_due': final_due,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def adjusted_due_calculation_instructor_view(request, student_id, pk):
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

    content = get_object_or_404(ThreadContent, id=pk)

    student = get_object_or_404(course.enrolled_students, id=student_id)

    initial_due = content.get_initial_due(student)
    final_due = content.get_final_due(student)
    
    calculation_list = content.adjusted_due_calculation(student)
    if calculation_list:
        adjusted_due=calculation_list[-1]['resulting_date']
    else:
        adjusted_due= initial_due

    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/adjusted_due_calculation_instructor.html', 
         {'course': course,
          'content': content,
          'courseuser': courseuser,
          'student': student, 
          'calculation_list': calculation_list,
          'adjusted_due': adjusted_due,
          'initial_due': initial_due,
          'final_due': final_due,
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
        return HttpResponseRedirect(reverse('micourses:selectcourse'))
    except ObjectDoesNotExist:
        # courseuser is not in an active course
        # redirect to not enrolled page
        return HttpResponseRedirect(reverse('micourses:notenrolled'))

        
    category_scores=course.student_scores_by_grade_category(courseuser)
    
    # no Google analytics for course
    noanalytics=True

    return render_to_response \
        ('micourses/student_gradebook.html', 
         {'course': course,
          'courseuser': courseuser,
          'student': courseuser, 
          'enrollment': course.courseenrollment_set.get(student=courseuser),
          'category_scores': category_scores,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def instructor_gradebook_view(request):
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

    assessment_categories = course.all_assessments_by_category()
    student_scores = course.all_student_scores_by_grade_category()
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


class EditAssessmentAttempt(CourseBaseView):
    
    model = ThreadContent
    context_object_name = 'content'
    template_name = 'micourses/edit_assessment_attempt.html'
    instructor_view=True

    def get_object(self):
        content = super(EditAssessmentAttempt, self).get_object()
        self.assessment=content.content_object
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
                }


# temporary view while gradebook view is so slow
@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def instructor_list_assessments_view(request):
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



# eventually change this to use generic view
# view to add assessment attempts
@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def add_assessment_attempts_view(request, pk):
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


    content = get_object_or_404(ThreadContent, id=pk)

    assessment=content.content_object
    latest_attempts = content.latest_student_attempts()

    class DateTimeForm(forms.Form):
        datetime = forms.DateTimeField()

    error_message = ""
    status_message = ""

    # if POST, then add assessment attempts, assuming valid date
    if request.method == 'POST':
        datetime_form = DateTimeForm({'datetime': request.POST['new_datetime']})
        valid_day = False
        if datetime_form.is_valid():
            attempt_datetime = datetime_form.cleaned_data['datetime']
            n_added = 0
            n_errors = 0
            with transaction.atomic(), reversion.create_revision():
                for (i,student) in \
                    enumerate(content.course.enrolled_students_ordered()):

                    new_score = request.POST['%i_new' % student.id]

                    if new_score != "":
                        try:
                            content.studentcontentattempt_set.create \
                                (student = student, datetime=attempt_datetime, 
                                 score=new_score)

                            latest_attempts[i]['status'] ="New score saved"
                            latest_attempts[i]['number_attempts'] += 1
                            n_added +=1
                        except ValueError:
                            latest_attempts[i]['error'] = "Enter a number"
                            n_errors +=1

            if(n_added):
                status_message = "%s attempts added." % n_added
            if(n_errors):
                error_message = "%s errors encountered." % n_errors
            if(not n_added and not n_errors):
                error_message = "No attempts added.  Enter at least one score."

            return render(request, 'micourses/edit_assessment_attempt.html',
                          {'latest_attempts': latest_attempts,
                           'assessment': assessment,
                           'content': content,
                           'error_message': error_message,
                           'status_message': status_message,
                       })
            
        else:
            datetime_error = datetime_form['datetime'].errors
            error_message = "Invalid date/time, no attempts added"
            
            for (i,student) in \
                enumerate(content.course.enrolled_students_ordered()):

                new_score = request.POST['%i_new' % student.id]
                latest_attempts[i]['old_value_string'] = 'value=%s' % new_score
                
            return render(request, 'micourses/edit_assessment_attempt.html',
                          {'latest_attempts': latest_attempts,
                           'assessment': assessment,
                           'content': content,
                           'error_message': error_message,
                           'datetime_error': datetime_error,
                    })
            
        
    else:
        return HttpResponseRedirect(reverse('micourses:editassessmentattempt',args=(pk,)))


@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def export_gradebook_view(request):
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


    assessment_categories = course.coursegradecategory_set.all()

    # no Google analytics for course
    noanalytics=True

    
    return render_to_response \
        ('micourses/export_gradebook.html', 
         {'course': course,
          'courseuser': courseuser, 
          'assessment_categories': assessment_categories,
          'noanalytics': noanalytics,
          },
         context_instance=RequestContext(request))


    
@user_passes_test(lambda u: u.is_authenticated() and u.courseuser.get_current_role()==INSTRUCTOR_ROLE)
def gradebook_csv_view(request):
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


    try:
        section = int(request.POST.get('section'))
    except ValueError:
        section = None
    include_total=False
    if request.POST.get("course_total")=="t":
        include_total=True
    if request.POST.get("replace_numbers"):
        replace_numbers=True
    else:
        replace_numbers=False

    included_categories = []
    totaled_categories = []
    assessments_in_category = {}
    assessment_points_in_category = {}

    for cgc in course.coursegradecategory_set.all():
        include_category = request.POST.get('category_%s' % cgc.id, 'e')
        if include_category=="i":
            assessments = course.thread_content\
                        .filter(grade_category=cgc.grade_category)\
                        .filter(thread_content__content_type__model='assessment')
            assessment_list=[]
            assessment_point_list=[]
            i=0
            for assessment in assessments:
                assessment_points = assessment.total_points()
                if not assessment_points:
                    continue
                i=i+1
                if replace_numbers:
                    assessment_list.append(i)
                else:
                    try:
                        name = assessment.content_object.get_short_name()
                    except AttributeError:
                        name = assessment.content_object.get_title()
                    assessment_list.append(name)
                assessment_point_list.append(assessment_points)

            if(assessment_list):
                assessments_in_category[cgc.id] = assessment_list
                assessment_points_in_category[cgc.id] = assessment_point_list
                included_categories.append(cgc)

        elif include_category=="t":
            totaled_categories.append(cgc)
        
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv; charset=iso-8859-1')
    response['Content-Disposition'] = 'attachment; filename="gradebook.csv"'
    
    import csv
    writer = csv.writer(response)
    
    # write first header row with assessment categories
    row=["","",""]
    for cgc in included_categories:
        row.append(cgc.grade_category.name)
        row.extend([""]*(len(assessments_in_category[cgc.id])-1))
        row.append("Total")
    row.extend(["Total"]*len(totaled_categories))
    if include_total:
        row.append("Course")
    writer.writerow(row)
    
        
    row=["Student", "ID", "Section"]
    for cgc in included_categories:
        row.extend(assessments_in_category[cgc.id])
        row.append(cgc.grade_category.name)
    for cgc in totaled_categories:
        row.append(cgc.grade_category.name)
    if include_total:
        row.append("Total")
    writer.writerow(row)

    for student in course.enrolled_students_ordered(section=section):
        student_section = course.courseenrollment_set.get(student=student).section
        row=[str(student), student.userid, student_section]
        for cgc in included_categories:
            cgc_assessments=course.student_scores_for_grade_category(student, cgc)
            for cgc_assessment in cgc_assessments:
                score = cgc_assessment['student_score']
                if score is None:
                    score=0
                row.append(round(score*10)/10.0)
            row.append(round(course.student_score_for_grade_category \
                             (cgc.grade_category, student)*10)/10.0)
        for cgc in totaled_categories:
            row.append(round(course.student_score_for_grade_category \
                             (cgc.grade_category, student)*10)/10.0)
        if include_total:
            row.append(round(course.total_student_score(student)*10)/10.0)

        writer.writerow(row)
            
    comments=[]

    row=["Possible points","",""]
    for cgc in included_categories:
        row.extend(assessment_points_in_category[cgc.id])
        row.append(course.points_for_grade_category \
                   (cgc.grade_category))
        number_assessments = len(assessment_points_in_category[cgc.id])
        score_comment=""
        if cgc.number_count_for_grade and \
           cgc.number_count_for_grade < number_assessments:
            score_comment = "the top %s scores out of %s" % \
                            (cgc.number_count_for_grade,
                             number_assessments)
        if cgc.rescale_factor != 1.0:
            if score_comment:
                score_comment += ", "
            score_comment += "rescaled by %s%%" % \
                             (round(cgc.rescale_factor*1000)/10)
        if score_comment:
            score_comment = "Total %s is %s" % (cgc.grade_category.name,
                                                score_comment)
            comments.append(score_comment)
    for cgc in totaled_categories:
        row.append(course.points_for_grade_category \
                   (cgc.grade_category))
    if include_total:
        row.append(course.total_points())
        score_comment = "Course total is "
        first=True
        for cgc in course.coursegradecategory_set.all():
            if (course.points_for_grade_category \
                (cgc.grade_category)):
                if not first:
                    score_comment += " + "
                else:
                    first=False
                score_comment += "Total %s" %cgc.grade_category.name
        comments.append(score_comment)
    writer.writerow(row)
    
    if(comments):
        writer.writerow([])
        for score_comment in comments:
            writer.writerow([score_comment])

    return response


class ThreadView(DetailView):
    model=Course
    slug_field='code'
    slug_url_kwarg ='course_code'
    template_name = 'micourses/thread_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.user = request.user
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)

        noanalytics=False
        if settings.SITE_ID==2:
            noanalytics=True
        context['noanalytics'] = noanalytics

        courseuser = None
        include_edit_link = False

        # record if user is logged in and is designer
        if self.user.is_authenticated():
            courseuser = self.user.courseuser
            try:
                enrollment = self.object.courseenrollment_set.get(
                    student=courseuser)
            except ObjectDoesNotExist:
                pass
            else:
                if enrollment.role==DESIGNER_ROLE:
                    include_edit_link = True

        context['student'] = courseuser
        context['include_edit_link'] = include_edit_link
        if self.object.numbered:
            context['ltag'] = "ol"
        else:
            context['ltag'] = "ul"

        return context


class ThreadEditView(DetailView):
    model=Course
    slug_field='code'
    slug_url_kwarg ='course_code'
    template_name = 'micourses/thread_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(self.object) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return redirect('mithreads:thread', course_code=self.object.code)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        context = super(ThreadEditView, self).get_context_data(**kwargs)

        # no Google analytics for edit
        context['noanalytics'] = False

        if self.object.numbered:
            context['ltag'] = "ol"
        else:
            context['ltag'] = "ul"

        return context


class RecordContentCompletion(View):

    def post(self, request, *args, **kwargs):

        try:
            student = CourseUser.objects.get(id=request.POST['student_id'])
            content = ThreadContent.objects.get(id=request.POST['content_id'])
            complete = int(request.POST['complete'])

        except (KeyError, ObjectDoesNotExist, ValueError):
            return JsonResponse({})


        with transaction.atomic(), reversion.create_revision():
            # if content complete record exists, modify record
            try:
                scc=student.studentcontentcompletion_set.get(content=content)
                scc.complete=complete
                scc.save()

             # if content complete record exists, add record
            except ObjectDoesNotExist:
                student.studentcontentcompletion_set.create \
                    (content=content, complete=complete)


            # if marking as complete, create attempt record if one doesn't exist
            if complete:
                if not student.studentcontentattempt_set.filter(content=content)\
                        .exists():
                    student.studentcontentattempt_set.create(content=content)

        
        return JsonResponse({'student_id': student.id,
                             'content_id': content.id,
                             'complete': complete,
                             })

class EditSectionView(View):
    """
    Perform one of the following changes to a ThreadSection
    depending on value of POST parameter action:
    - dec_level: decrement the level of the section
    - inc_level: increment the level of the section
    - move_up: move section up
    - move_down: move section down
    - delete: delete section
    - edit: change section name
    - insert: insert new section (below current if exists, else at top)

    # must be designer of course
    
    """

    def post(self, request, *args, **kwargs):

        try:
            action = request.POST['action']
        except KeyError:
            return JsonResponse({})


        try:
            section_id = int(request.POST.get('section_id'))
        except ValueError:
            section_id = None


        # if no section id, then action must be insert
        # and the thread must be specified
        if section_id is None:
            if action == 'insert':
                try:
                    course = Course.objects.get(id=request.POST['course_id'])
                except (KeyError, ObjectDoesNotExist):
                    return JsonResponse({})
                thread_section=None
            else:
                return JsonResponse({})
        else:
            try:
                thread_section = ThreadSection.objects.get(id=section_id)
            except ObjectDoesNotExist:
                return JsonResponse({})
            course = thread_section.get_course()

        
        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})

      
        rerender_thread=True
        new_section_html={}
        rerender_sections=[]
        replace_section_html={}

        if course.numbered:
            ltag = "ol"
        else:
            ltag = "ul"

        # decrement level of section
        if action=='dec_level':
            if thread_section.course is None:
                parent = thread_section.parent
                next_sibling = parent.find_next_sibling()

                if next_sibling:
                    if parent.sort_order==next_sibling.sort_order:
                        course.reset_thread_section_sort_order()
                        parent.refresh_from_db()
                        next_sibling.refresh_from_db()

                    thread_section.sort_order = \
                        (parent.sort_order+next_sibling.sort_order)/2

                else:
                    thread_section.sort_order = parent.sort_order+1

                if parent.course:
                    if parent.course != course:
                        return JsonResponse({})

                    thread_section.parent = None
                    thread_section.course = course

                else:
                    thread_section.parent = parent.parent
                    

                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()


        # increment level of section
        elif action=='inc_level':
            previous_sibling = thread_section.find_previous_sibling()
            
            if previous_sibling:
                last_child = previous_sibling.child_sections.last()
                thread_section.parent = previous_sibling
                thread_section.course = None
                if last_child:
                    thread_section.sort_order = last_child.sort_order+1
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()

        # move section up
        elif action=="move_up":

            previous_sibling = thread_section.find_previous_sibling()
            if previous_sibling:
                if previous_sibling.sort_order == thread_section.sort_order:
                    course.reset_thread_section_sort_order()
                    previous_sibling.refresh_from_db()
                    thread_section.refresh_from_db()
                sort_order = thread_section.sort_order
                thread_section.sort_order = previous_sibling.sort_order
                previous_sibling.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()
                    previous_sibling.save()

            elif not thread_section.course:
                previous_parent_sibling = \
                    thread_section.parent.find_previous_sibling()
            
                if previous_parent_sibling:
                    last_child = previous_parent_sibling.child_sections.last()
                    if last_child:
                        thread_section.sort_order = last_child.sort_order+1
                    thread_section.parent = previous_parent_sibling
                    with transaction.atomic(), reversion.create_revision():
                        thread_section.save()


        # move section down
        elif action=="move_down":

            next_sibling = thread_section.find_next_sibling()
            if next_sibling:
                if next_sibling.sort_order == thread_section.sort_order:
                    course.reset_thread_section_sort_order()
                    next_sibling.refresh_from_db()
                    thread_section.refresh_from_db()
                sort_order = thread_section.sort_order
                thread_section.sort_order = next_sibling.sort_order
                next_sibling.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_section.save()
                    next_sibling.save()

            elif not thread_section.course:
                next_parent_sibling = \
                    thread_section.parent.find_next_sibling()
            
                if next_parent_sibling:
                    first_child = next_parent_sibling.child_sections.first()
                    if first_child:
                        thread_section.sort_order = first_child.sort_order-1
                    thread_section.parent = next_parent_sibling
                    with transaction.atomic(), reversion.create_revision():
                        thread_section.save()

        # delete section
        elif action=="delete":
            # rerender next and prevous siblings as commands may have changed
            sibling=thread_section.find_next_sibling()
            if sibling:
                rerender_sections.append(sibling)
            sibling=thread_section.find_previous_sibling()
            if sibling:
                rerender_sections.append(sibling)

            thread_section.mark_deleted()
            rerender_thread=False
            
        # edit section name
        elif action=="edit":
            thread_section.name = request.POST['section_name']
            with transaction.atomic(), reversion.create_revision():
                thread_section.save();
            rerender_thread=False

        # insert section
        elif action=="insert":
            new_section_name = request.POST['section_name']
            
            if thread_section:
                # add section as first child of current section
                try:
                    new_sort_order = thread_section.child_sections.first()\
                                                                .sort_order-1
                except AttributeError:
                    new_sort_order=0

                with transaction.atomic(), reversion.create_revision():
                    new_section = ThreadSection.objects.create(
                        name=new_section_name, 
                        parent=thread_section,
                        sort_order=new_sort_order)

                prepend_section = "child_sections_%s" % thread_section.id

            else:
                # add section as first in course
                try:
                    new_sort_order = course.thread_sections.first().sort_order-1
                except AttributeError:
                    new_sort_order = 0
                    
                with transaction.atomic(), reversion.create_revision():
                    new_section = ThreadSection.objects.create(
                        name=new_section_name, 
                        course=course,
                        sort_order=new_sort_order)
                    
                prepend_section = "child_sections_top"

            # rerender next siblings as commands may have changed
            sibling=new_section.find_next_sibling()
            if sibling:
                rerender_sections.append(sibling)
            
            template = Template("{% load course_tags %}<li id='thread_section_{{section.id}}'>{% thread_section_edit section %}</li>")
            context = Context({'section': new_section, 'ltag': ltag})

            new_section_html[prepend_section] = template.render(context)


            course.reset_thread_section_sort_order()
            rerender_thread = False

        
        for section in rerender_sections:
            template = Template("{% load course_tags %}{% thread_section_edit section %}")
            context = Context({'section': section, 'ltag': ltag})

            replace_section_html[section.id] = template.render(context)
            
            
        if rerender_thread:

            # must reset thread section sort order if changed sections
            # because thread_content ordering depends on thread_sections
            # as a single group being sorted correctly
            course.reset_thread_section_sort_order()

            # generate html for entire thread
            from django.template.loader import render_to_string

            thread_html = render_to_string(
                template_name='micourses/thread_edit_sub.html',
                context = {'course': course, 'ltag': ltag }
            )
        else:
            thread_html = None

        return JsonResponse({'action': action,
                             'section_id': section_id,
                             'course_id': course.id,
                             'thread_html': thread_html,
                             'new_section_html': new_section_html,
                             'replace_section_html': replace_section_html,
                             })

class EditContentView(View):
    """
    Perform one of the following changes to a ThreadContent
    depending on value of POST parameter action:
    - move_up: move content up
    - move_down: move content down
    - delete: delete content
    - edit: edit content attributes
    - insert: insert new content at end of section

    Must be designer of course

    """


    def post(self, request, *args, **kwargs):

        try:
            action = request.POST['action']
            the_id = request.POST['id']
        except KeyError:
            return JsonResponse({})

        form_html=""

        # if action is insert, then the_id must be a valid section_id
        if action=='insert':
            try:
                thread_section = ThreadSection.objects.get(id=the_id)
            except (KeyError, ValueError, ObjectDoesNotExist):
                return JsonResponse({})

            course = thread_section.get_course()
            thread_content=None

        # else, the_id must be a valid content_id
        else:
            try:
                thread_content = ThreadContent.objects.get(id=the_id)
            except (KeyError, ValueError, ObjectDoesNotExist):
                return JsonResponse({})

            course = thread_content.course
            thread_section=thread_content.section

        
        # must be designer of course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})


        rerender_sections = []

        # move content up
        if action=="move_up":
            previous_in_section = thread_content.find_previous(in_section=True)
            if previous_in_section:
                if previous_in_section.sort_order == thread_content.sort_order:
                    thread_section.reset_thread_content_sort_order()
                    previous_in_section.refresh_from_db()
                    thread_content.refresh_from_db()
                sort_order = thread_content.sort_order
                thread_content.sort_order = previous_in_section.sort_order
                previous_in_section.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()
                    previous_in_section.save()

                rerender_sections = [thread_section,]

            else:
                # if thread_content is first in section, then move up to
                # end of previous section

                previous_section = thread_section.find_previous()
                try:
                    thread_content.sort_order = previous_section\
                                  .thread_contents.last().sort_order+1
                except AttributeError:
                    thread_content.sort_order = 0
                thread_content.section = previous_section
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()

                rerender_sections = [thread_section, previous_section]

        # move content down
        if action=="move_down":
            next_in_section = thread_content.find_next(in_section=True)
            if next_in_section:
                if next_in_section.sort_order == thread_content.sort_order:
                    thread_section.reset_thread_content_sort_order()
                    next_in_section.refresh_from_db()
                    thread_content.refresh_from_db()
                sort_order = thread_content.sort_order
                thread_content.sort_order = next_in_section.sort_order
                next_in_section.sort_order = sort_order
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()
                    next_in_section.save()

                rerender_sections = [thread_section,]

            else:
                # if thread_content is last in section, then move down to
                # beginning of next section

                next_section = thread_section.find_next()
                try:
                    thread_content.sort_order = next_section\
                                  .thread_contents.first().sort_order-1
                except AttributeError:
                    thread_content.sort_order = 0
                thread_content.section = next_section
                with transaction.atomic(), reversion.create_revision():
                    thread_content.save()

                rerender_sections = [thread_section, next_section]
        
        # delete content
        elif action=="delete":
            thread_content.mark_deleted()
            rerender_sections = [thread_section,]


        # edit content
        elif action=="edit":
            try:
                content_type = ContentType.objects.get(id=request.POST['content_type'])
                
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({});

            form_identifier = "edit_%s" % the_id

            update_options_command="update_content_options('%s', this.value)"% \
                form_identifier

            form = thread_content_form_factory(
                the_content_type=content_type,
                update_options_command=update_options_command
            )
            form = form(request.POST, instance=thread_content,
                        auto_id="content_form_%s_%%s" % form_identifier,
                    )
            if form.is_valid():
                with transaction.atomic(), reversion.create_revision():
                    form.save()
                rerender_sections = [thread_section,]
            else:
                form_html = form.as_p()


        # insert content
        elif action=="insert":
            try:
                content_type = ContentType.objects.get(id=request.POST['content_type'])
                
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({});

            form_identifier = "insert_%s" % the_id

            update_options_command="update_content_options('%s', this.value)"% \
                form_identifier

            try:
                new_sort_order = thread_section.thread_contents.last()\
                                                              .sort_order+1
            except AttributeError:
                new_sort_order = 0

            initial={'section': thread_section, 
                     'course': thread_section.get_course(),
                     'sort_order': new_sort_order}

            form = thread_content_form_factory(
                the_content_type=content_type,
                update_options_command=update_options_command
            )
            form = form(request.POST,
                        auto_id="content_form_%s_%%s" % form_identifier,
                    )
            if form.is_valid():
                with transaction.atomic(), reversion.create_revision():
                    new_thread_content=form.save(commit=False)
                    new_thread_content.section=thread_section
                    new_thread_content.sort_order = new_sort_order
                    new_thread_content.save()

                rerender_sections = [thread_section,]
            else:
                form_html = form.as_p()



        section_contents={}
        for section in rerender_sections:
            # generate html for thread_content of section
            from django.template.loader import render_to_string

            content_html = render_to_string(
                template_name='micourses/thread_content_edit_container.html',
                context = {'thread_section': section }
            )
            
            section_contents[section.id] = content_html

        return JsonResponse({'section_contents': section_contents,
                             'action': action,
                             'id': the_id,
                             'form_html': form_html,
                             })


class ReturnContentForm(View):
   def post(self, request, *args, **kwargs):

        try:
            form_type = request.POST['form_type']
            the_id = request.POST['id']
        except KeyError:
            return JsonResponse({})

        instance = None
        thread_content=None
        thread_section=None

        # If form type is "edit", then the_id must be 
        # a valid thread_content id.
        # Populate form with instance of that thread_content
        if form_type=="edit":
            try:
                thread_content = ThreadContent.objects.get(id=the_id)
            except (KeyError,ObjectDoesNotExist):
                return JsonResponse({})

            instance = thread_content
            the_content_type = thread_content.content_type

        # If form type is "insert", then the_id must be
        # a valid thread_section id.
        # Create blank form 
        elif form_type=="insert":
            try:
                thread_section = ThreadSection.objects.get(id=the_id)
            except ObjectDoesNotExist:
                return JsonResponse({})
            the_content_type = None


        # else invalid form_type
        else:
            return JsonResponse({})


        # must be designer of course
        if thread_content:
            course=thread_content.course
        else:
            course=thread_section.get_course()
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role(course) 
            if role==DESIGNER_ROLE:
                is_designer=True

        if not is_designer:
            return JsonResponse({})


        form_identifier = "%s_%s" % (form_type, the_id)

        update_options_command="update_content_options('%s', this.value)" % \
            form_identifier

        form = thread_content_form_factory(
            the_content_type=the_content_type,
            update_options_command=update_options_command
        )
        form = form(instance=instance, 
                    auto_id="content_form_%s_%%s" % form_identifier,
        )

        form_html = form.as_p()

        return JsonResponse({'form_type': form_type,
                             'id': the_id,
                             'form_html': form_html})



class ReturnContentOptions(View):

    def post(self, request, *args, **kwargs):
        
        # must be designer of some course
        is_designer = False
        if request.user.is_authenticated():
            courseuser = request.user.courseuser
            role = courseuser.get_current_role() 
            if role==DESIGNER_ROLE:
                is_designer=True
        if not is_designer:
            return JsonResponse({})

        try:
            form_id = request.POST['form_id']
            this_content_type = ContentType.objects.get(id=request.POST['option'])
        except (KeyError,ObjectDoesNotExist):
            return JsonResponse({})

        content_options = '<option selected="selected" value="">---------</option>\n'
        for item in this_content_type.model_class().objects.all():
            content_options += "<option value='%s'>%s</option>\n" \
                                    % (item.id, item)

        return JsonResponse({'form_id': form_id, 
                             'content_options': content_options})

