
from micourses.models import Course, CourseUser, ThreadContent, QuestionAttempt, QuestionResponse, Assessment, STUDENT_ROLE, INSTRUCTOR_ROLE, DESIGNER_ROLE
from micourses.forms import ContentAttemptForm, ScoreForm, CreditForm, AttemptScoresForm
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template import RequestContext, Context, Template
from django.core.exceptions import ObjectDoesNotExist
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
from micourses.templatetags.course_tags import floatformat_or_dash, floatformat
from micourses.utils import format_datetime
import pytz
import reversion


class SelectCourseView(ListView):
    context_object_name = "course_list"
    template_name = 'micourses/select_course.html'
    not_enrolled=False

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
        return self.courseuser.course_set.all()

    def get_context_data(self):
        context = super(ListView,self).get_context_data()
        context["n_courses"]=self.n_courses
        context["cuser"]=self.courseuser
        context['not_enrolled'] = self.not_enrolled
        if self.not_enrolled:
            try:
                 context['not_enrolled_course'] = \
                    Course.objects.get(code=self.kwargs['course_code'])
            except:
                pass
        return context

        
class NotLoggedin(Exception):
    pass
class NotEnrolled(Exception):
    pass
class NotInstructor(Exception):
    pass

class CourseBaseMixin(SingleObjectMixin):
    """
    Modifieds get_object to do the following:
    - raises NotLogged in if user not logged in (should be logged in)
    - raises NotEnrolled if user not enrolled in course
    - raises NotInstructor if instruct view and user isn't instructor
    - adds course, courseuser, and enrollment data
    - updates courseusers' selected course and session's last course viewed

    Adds course, courseuser, and noanalytics to context
    """
    model = Course
    slug_url_kwarg = 'course_code'
    slug_field = 'code'
    instructor_view = False


    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated():
            raise NotLoggedIn

        self.course = super(CourseBaseMixin,self).get_object(queryset)
    
        self.courseuser = self.request.user.courseuser

        try:
            self.enrollment = self.course.courseenrollment_set.get(
                student=self.courseuser)
        except ObjectDoesNotExist:
            raise NotEnrolled

        # make sure this course is saved as selected course enrollment
        if self.enrollment != self.courseuser.selected_course_enrollment:
            self.courseuser.selected_course_enrollment = self.enrollment
            self.courseuser.save()

        # also update session with last course viewed
        self.request.session['last_course_viewed'] = self.course.id


        self.current_role=self.enrollment.role
        
        if self.instructor_view and not (self.current_role == INSTRUCTOR_ROLE
                                         or self.current_role == DESIGNER_ROLE):
            raise NotInstructor

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

        from micourses.utils import find_week_begin_end
        self.beginning_of_week, self.end_of_week = find_week_begin_end(
            self.course)
        
        self.datetime_format = '%Y-%m-%d %H:%M:%S.%f%z'

        return self.course

    def get_student(self):
        if self.instructor_view:
            return get_object_or_404(self.course.enrolled_students,
                                     id=self.kwargs['student_id'])
        else:
            return self.courseuser

    def get_context_data(self, **kwargs):
        context = super(CourseBaseMixin, self).get_context_data(**kwargs)
        
        context['courseuser'] = self.courseuser
        context['course'] = self.course
        context['student'] = self.student
        context['current_role'] = self.current_role
        context['instructor_role'] = self.current_role==INSTRUCTOR_ROLE \
                                     or self.current_role==DESIGNER_ROLE
        context['enrollment'] = self.enrollment
        context['student_enrollment'] = self.student_enrollment

        context['week_date_parameters'] = "begin_date=%s&end_date=%s" % \
                        (self.beginning_of_week.strftime(self.datetime_format), 
                         self.end_of_week.strftime(self.datetime_format))

        # no Google analytics for course
        context['noanalytics']=True

        context.update(self.extra_context())

        return context

    def extra_context(self):
        # for context that derived classes can easily ignore 
        # by declaring own extra_context
        return {}



class CourseBaseView(CourseBaseMixin, TemplateResponseMixin, View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)

        self.get_additional_objects(request, *args, **kwargs)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_additional_objects(self, request, *args, **kwargs):
        pass


class CourseView(CourseBaseView):
    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)

        if self.courseuser.courseenrollment_set.filter(
                withdrew=False,course__active=True).exclude(course=self.course)\
                                               .exists():
            context['multiple_courses']=True
        else:
            context['multiple_courses']=False


        begin_date=self.beginning_of_week
        end_date=self.end_of_week
        context['begin_date']=begin_date
        context['end_date']=end_date


        context["upcoming_content"] = self.course.content_by_date \
            (enrollment=self.enrollment, begin_date=begin_date, \
                 end_date=end_date)

        this_week_parameters = "begin_date=%s&end_date=%s" %\
                               (begin_date.strftime(self.datetime_format),
                                end_date.strftime(self.datetime_format))

        this_week_parameters += "&exclude_completed"
        context['this_week_parameters'] = this_week_parameters
        

        context['next_items'] = self.course.next_items(self.courseuser, number=5)

        context['message'] = self.request.GET.get("message","")

        return context
        

    def get_template_names(self):
        # base template on current role
        if self.current_role == INSTRUCTOR_ROLE \
           or self.current_role == DESIGNER_ROLE:
            return ['micourses/course_instructor_view.html',]
        else:
            return ['micourses/course_student_view.html',]


class CourseContentRecordView(CourseBaseView):
    instructor_view = True
    template_name="micourses/course_content_record.html"

    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))

        try:
            self.course_content_record = self.thread_content.contentrecord_set\
                                  .get(enrollment=None)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.course_content_record =\
                        self.thread_content.contentrecord_set\
                                  .create(enrollment=None)

    
    def get_context_data(self, **kwargs):
        context = super(CourseContentRecordView, self).get_context_data(**kwargs)

        context['thread_content'] = self.thread_content
        context['course_content_record'] = self.course_content_record
        cca_dicts=[]
        for cca in self.course_content_record.attempts.all():
            question_numbers=[]
            for qs in cca.question_sets.all():
                try:
                    qa = qs.question_attempts.latest()
                except ObjectDoesNotExist:
                    continue
                question_numbers.append(str(qa.question.id))
            question_numbers = ", ".join(question_numbers)
            cca_dicts.append({'cca': cca, 
                              'question_numbers': question_numbers})
        context['course_content_attempts'] = cca_dicts

        return context


class EditCourseContentAttempts(CourseBaseMixin, View):
    instructor_view=True
    
    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))

        try:
            self.course_content_record = self.thread_content.contentrecord_set\
                                  .get(enrollment=None)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.course_content_record =\
                        self.thread_content.contentrecord_set\
                                  .create(enrollment=None)


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        self.get_additional_objects(request, *args, **kwargs)

        try:
            action = request.POST['action']
        except KeyError:
            return JsonResponse({}) 

        coursewide_attempts_selected = request.POST.getlist("cca_ids")

        from micourses.models import ContentAttempt
        
        if action=="delete":
            valid=False
        elif action=="undelete":
            valid=True
        else:
            return JsonResponse({})
            
        ids_changed=[]

        for cca_id in coursewide_attempts_selected:
            try:
                cca = ContentAttempt.objects.get(id=cca_id)
            except ContentAttempt.DoesNotExist:
                continue

            if cca.record.content != self.thread_content:
                continue

            cca.valid=valid
            cca.save(cuser=self.courseuser)
            ids_changed.append(cca_id)

        return JsonResponse({'ids_changed': ids_changed,
                             'action': action})


class ContentRecordView(CourseBaseView):

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))

        try:
            self.content_record = self.thread_content.contentrecord_set\
                                  .get(enrollment=self.student_enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.content_record = self.thread_content.contentrecord_set\
                                  .create(enrollment=self.student_enrollment)
                
        # if instructor view, also find coursewide record
        if self.instructor_view:
            try:
                self.course_content_record = self.thread_content\
                                .contentrecord_set.get(enrollment=None)
            except ObjectDoesNotExist:
                with transaction.atomic(), reversion.create_revision():
                    self.course_content_record =\
                            self.thread_content.contentrecord_set\
                                      .create(enrollment=None)

        # look for message in get parameters
        self.message = request.GET.get("message","")


    def get_context_data(self, **kwargs):
        context = super(ContentRecordView, self).get_context_data(**kwargs)

        context['thread_content'] = self.thread_content
        context['content_record'] = self.content_record
        
        return context


    def extra_context(self):
        from micourses.utils import format_datetime
        current_tz = timezone.get_current_timezone()
        attempt_list = []
        if self.instructor_view:
            attempts = self.content_record.attempts\
                       .order_by('-valid', 'attempt_created')
        else:
            attempts = self.content_record.attempts.filter(valid=True)

        n_invalid_attempts=0
        for (i, attempt) in enumerate(attempts):
            earliest, latest = attempt.return_activity_interval()
            datetime_text = format_datetime(
                current_tz.normalize(earliest.astimezone(current_tz)))
            if latest:
                datetime_text += " - " + format_datetime(
                    current_tz.normalize(latest.astimezone(current_tz)))
            score_text = floatformat_or_dash(attempt.score, 1)
            attempt_dict = {}
            attempt_dict["valid"] = attempt.valid
            if attempt.valid:
                attempt_number = str(i+1)
            else:
                n_invalid_attempts +=1
                attempt_number = "x%s" % n_invalid_attempts
            attempt_dict['attempt'] = attempt
            attempt_dict['version'] = attempt.version
            attempt_dict['score'] = attempt.score
            attempt_dict['score_text'] = score_text
            attempt_dict['score_overridden'] = \
                                    attempt.score_override is not None
            attempt_dict['attempt_number']  = attempt_number
            attempt_dict['formatted_attempt_number'] = \
                mark_safe('&nbsp;%s&nbsp;' % attempt_number)
            attempt_dict['datetime'] = \
                mark_safe('&nbsp;%s&nbsp;' % datetime_text)
            attempt_dict['formatted_score'] = \
                mark_safe('&nbsp;%s&nbsp;' % score_text)


            # show details if have question_set with credit that isn't None
            show_details = False
            if attempt.question_sets.exclude(credit_override=None):
                # found question set whose credit was overriden manually
                show_details=True
            elif QuestionAttempt.objects.filter(
                    content_attempt_question_set__content_attempt=attempt) \
                    .exclude(credit=None).exists():
                # found question set with question attempts with credit set
                show_details=True
            # for instructor view, show details if any responses
            if not show_details and self.instructor_view:
                if QuestionResponse.objects.filter(
                    question_attempt__content_attempt_question_set__content_attempt=attempt).exists():
                    show_details=True
            if show_details:
                if self.instructor_view:
                    attempt_url = reverse(
                        'micourses:content_attempt_instructor', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
                                'attempt_number': attempt_number,
                                'student_id': self.student.id})
                    attempt_dict['formatted_attempt_number'] = mark_safe \
                    ('<a href="%s" id="attempt_%s_link">%s (details)</a><br/><a href="%s?latest_attempts" id="attempt_%s_link2">(with latest attempts)</a>' % \
                         (attempt_url, attempt_number,
                          attempt_dict['formatted_attempt_number'],
                          attempt_url, 
                          attempt_dict['formatted_attempt_number']))
                    
                else:
                    attempt_url = reverse(
                        'micourses:content_attempt', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
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

            if self.instructor_view:
                attempt_dict['version_url'] = attempt.return_url()
                score_or_zero = attempt.score
                if score_or_zero is None:
                    score_or_zero = 0
                attempt_dict["score_form"] = ScoreForm({'score': score_or_zero},
                        auto_id="edit_attempt_%s_score_form_%%s" % attempt.id)
            attempt_list.append(attempt_dict)

        score_overridden = self.content_record.score_override is not None
        score=self.content_record.score
        score_text = floatformat_or_dash(score, 1)
        if score is None:
            score_or_zero = 0
        else:
            score_or_zero = score
        score_form = ScoreForm({'score': score_or_zero},
                               auto_id="edit_attempt_record_score_form_%s")

        if self.instructor_view:
            # find coursewide attempts that aren't used already by student
            new_course_attempts=self.course_content_record.attempts.exclude(
                derived_attempts__in=self.content_record.attempts.all())\
                .filter(valid=True)
            new_course_attempts_form = AttemptScoresForm(
                attempts=new_course_attempts, auto_id="coursewide_%s")
            new_course_attempt_list=[]
            for (i,field) in enumerate(new_course_attempts_form):
                new_course_attempt_list.append({
                    'field': field,
                    'attempt': new_course_attempts[i],
                    })
        else:
            new_course_attempt_list=None

        return {'adjusted_due': self.thread_content\
                    .get_adjusted_due(self.content_record),
                'attempts': attempt_list,
                'score': score,
                'score_text': score_text,
                'score_overridden': score_overridden,
                'score_form': score_form,
                'new_course_attempt_list': new_course_attempt_list,
                'message': self.message,
                }


    def get_template_names(self):
        if self.instructor_view:
            return ['micourses/content_record_instructor.html',]
        else:
            return ['micourses/content_record_student.html',]


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Called when adding course wide attempts.
        """
        if not self.instructor_view:
            return self.get(request, *args, **kwargs)

        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)

        self.get_additional_objects(request, *args, **kwargs)

        new_course_attempts=self.course_content_record.attempts.exclude(
            derived_attempts__in=self.content_record.attempts.all())\
                                                    .filter(valid=True)
        new_course_attempts_form = AttemptScoresForm(
            request.POST,
            attempts=new_course_attempts, auto_id="coursewide_%s")

        if new_course_attempts_form.is_valid():
            n_added=0
            for attempt in new_course_attempts:
                new_score = new_course_attempts_form.cleaned_data.get(
                    'score_%s' % attempt.id)
                if new_score is not None:
                    new_attempt = attempt.create_derived_attempt(
                        content_record = self.content_record,
                        score=new_score)
                    n_added+=1
            from django.utils.encoding import escape_uri_path
            if n_added==1:
                message = "%s attempt added." % n_added
            else:
                message = "%s attempts added." % n_added

            url = reverse('micourses:content_record_instructor',
                          kwargs={'course_code': self.course.code,
                                  'content_id': self.thread_content.id,
                                  'student_id': self.student.id})
            url += "?message=%s" % escape_uri_path(message)
            return redirect(url) 
        
        else:
            context = self.get_context_data(object=self.object)

            new_course_attempt_list=[]
            for (i,field) in enumerate(new_course_attempts_form):
                new_course_attempt_list.append({
                    'field': field,
                    'attempt': new_course_attempts[i],
                    })
            context['new_course_attempt_list']= new_course_attempt_list
            return self.render_to_response(context)


class ChangeScore(CourseBaseMixin, View):
    instructor_view=True
    
    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))

        try:
            self.content_record = self.thread_content.contentrecord_set\
                                  .get(enrollment=self.student_enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.content_record = self.thread_content.contentrecord_set\
                                  .create(enrollment=self.student_enrollment)


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        self.get_additional_objects(request, *args, **kwargs)

        try:
            action = request.POST['action']
            record_type = request.POST['record_type']
        except KeyError:
            return JsonResponse({}) 

        score_type = request.POST.get('score_type', 'score')

        if record_type=="content_record":
        
            # have not implemented credit so far
            if score_type == 'credit':
                return JsonResponse({})

            success=False
            score_form = ScoreForm(request.POST,
                                   auto_id="edit_attempt_record_score_form_%s")

            if action=="change":
                if score_form.is_valid():
                    score = score_form.cleaned_data['score']
                    self.content_record.score_override=score
                    self.content_record.save(cuser=self.courseuser)
                    success=True

            elif action=="delete":
                self.content_record.score_override=None
                self.content_record.save(cuser=self.courseuser)
                success=True
                score_form = ScoreForm({'score': self.content_record.score },
                                   auto_id="edit_attempt_record_score_form_%s")


            score=self.content_record.score
            score_text = floatformat_or_dash(score, 1)

            return JsonResponse({'action': action,
                                 'id': 'record', 'score': score, 
                                 'form': score_form.as_p(),
                                 'success': success, 'score_text': score_text })

        
        elif record_type=='content_attempt':
            try:
                attempt_id = request.POST['attempt_id']
                content_attempt=self.content_record.attempts.get(id=attempt_id)
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({})
            
            success=False
            score_text=None

            if score_type == 'credit':
                score_form = CreditForm(request.POST,
                        auto_id="edit_attempt_%s_credit_form_%%s" % attempt_id)

            else:
                score_form = ScoreForm(request.POST,
                        auto_id="edit_attempt_%s_score_form_%%s" % attempt_id)

            if action=="change":
                if score_form.is_valid():
                    if score_type=='credit':
                        credit = score_form.cleaned_data['percent']/100
                        points = self.thread_content.points
                        if points is None:
                            score=None
                        else:
                            score = points*credit
                    else:
                        score = score_form.cleaned_data['score']
                    content_attempt.score_override=score
                    content_attempt.save(cuser=self.courseuser)
                    success=True


            elif action=="delete":
                content_attempt.score_override=None
                content_attempt.save(cuser=self.courseuser)
                success=True
                if score_type=='credit':
                    score_form = CreditForm(
                        {'percent': content_attempt.get_percent_credit() },
                        auto_id="edit_attempt_%s_credit_form_%%s" % attempt_id)
                else:
                    score_form = ScoreForm({'score': content_attempt.score },
                        auto_id="edit_attempt_%s_score_form_%%s" % attempt_id)
                
            score=content_attempt.score
            score_text = floatformat_or_dash(score, 1)
            percent_credit=content_attempt.get_percent_credit()
            percent_credit_text=floatformat_or_dash(percent_credit,1)
            record_score=self.content_record.score
            record_score_text=floatformat_or_dash(record_score, 1)
            
            return JsonResponse({'action': action,
                                 'id': attempt_id, 
                                 'num': "attempt",
                                 'score_type': score_type,
                                 'form': score_form.as_p(),
                                 'success': success, 
                                 'score': score, 'score_text': score_text,
                                 'percent_credit': percent_credit,
                                 'percent_credit_text': percent_credit_text,
                                 'record_score': record_score,
                                 'record_score_text': record_score_text })
            

        elif record_type=='question_set':
            try:
                attempt_id = request.POST['attempt_id']
                content_attempt=self.content_record.attempts.get(id=attempt_id)
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({})
            
            try:
                question_number = request.POST['question_number']
                ca_question_set=content_attempt.question_sets.get(
                    question_number=question_number)
            except (KeyError, ObjectDoesNotExist):
                return JsonResponse({})

            success=False
            score_text=None

            if score_type == 'credit':
                score_form = CreditForm(request.POST,
                    auto_id="edit_question_%s_credit_form_%%s" % question_number)
            else:
                score_form = ScoreForm(request.POST,
                    auto_id="edit_question_%s_score_form_%%s" % question_number)

            points = ca_question_set.get_points()


            if action=="change":
                if score_form.is_valid():
                    if score_type=='credit':
                        credit = score_form.cleaned_data['percent']/100
                    else:
                        score = score_form.cleaned_data['score']
                        credit=score/points

                    ca_question_set.credit_override=credit
                    ca_question_set.save(cuser=self.courseuser)
                    success=True


            elif action=="delete":
                ca_question_set.credit_override=None
                ca_question_set.save(cuser=self.courseuser)
                success=True
                credit = ca_question_set.get_credit()
                if credit is None:
                    credit=0
                score = points*credit
                if score_type=='credit':
                    score_form = CreditForm(
                        {'percent': credit*100 },
                        auto_id="edit_question_%s_credit_form_%%s" % \
                        question_number)
                else:
                    score_form = ScoreForm({'score': score },
                        auto_id="edit_question_%s_score_form_%%s" % \
                                           question_number)
                
            credit = ca_question_set.get_credit()
            if credit is None:
                credit=0
            score = points*credit
            score_text = floatformat_or_dash(score, 1)
                        
            percent_credit = credit*100
            percent_credit_text=floatformat_or_dash(percent_credit,1)

            attempt_score=content_attempt.score
            attempt_percent_credit=content_attempt.get_percent_credit()
            attempt_score_text=floatformat_or_dash(attempt_score, 1)
            attempt_percent_credit_text=floatformat_or_dash(
                attempt_percent_credit,1)

            return JsonResponse({'action': action,
                                 'id': attempt_id, 
                                 'num': question_number,
                                 'form': score_form.as_p(),
                                 'success': success, 
                                 'score_type': score_type,
                                 'score': score, 'score_text': score_text,
                                 'percent_credit': percent_credit,
                                 'percent_credit_text': percent_credit_text,
                                 'attempt_score': attempt_score,
                                 'attempt_score_text': attempt_score_text,
                                 'attempt_percent_credit': 
                                 attempt_percent_credit,
                                 'attempt_percent_credit_text':
                                 attempt_percent_credit_text})
  
    

class ContentAttemptView(ContentRecordView):
    
    def get_additional_objects(self, request, *args, **kwargs):
        super(ContentAttemptView,self).get_additional_objects(
            request, *args, **kwargs)

        self.attempt_number = self.kwargs['attempt_number']
        
        # if attempt_number begins with an x, it is an invalid attempt number
        if self.attempt_number[0]=="x":
            if not self.instructor_view:
                raise Http404('Content attempt %s not found.' \
                              % self.attempt_number)
            self.content_attempt_valid = False
            attempt_number_int = self.attempt_number[1:]
        else:
            self.content_attempt_valid = True
            attempt_number_int = self.attempt_number
            
        # don't pad attempt number with a zero
        if attempt_number_int[0]=='0':
            raise Http404('Content attempt %s not found.' \
                              % self.attempt_number)

        try:
            attempt_number_int = int(attempt_number_int)
        except ValueError:
            raise Http404('Content attempt %s not found.' \
                          % self.attempt_number)
            
        if self.content_attempt_valid:
            attempts = self.content_record.attempts.filter(valid=True)
        else:
            attempts = self.content_record.attempts.filter(valid=False)

        try:
            self.content_attempt = attempts[attempt_number_int-1]
        except IndexError:
            raise Http404('Content attempt %s not found.' \
                              % self.attempt_number)

        # if content object isn't an assessment, then return 404
        assessment_content_type = ContentType.objects.get(app_label="micourses",
                                                          model='assessment')
        if self.thread_content.content_type != assessment_content_type:
            raise Http404("No assessment found") 

        self.assessment = self.thread_content.content_object

        self.show_latest_question_attempts = "latest_attempts" in request.GET


    def get_context_data(self, **kwargs):
        context = super(ContentAttemptView, self).get_context_data(**kwargs)

        context['content_attempt'] = self.content_attempt
        context['attempt_number'] = self.attempt_number
        context['content_attempt_valid'] = self.content_attempt_valid

        return context


    def extra_context(self):
        from micourses.utils import format_datetime
        current_tz = timezone.get_current_timezone()
        
        context={}
        context['score_overridden'] = self.content_attempt.score_override is not None

        earliest, latest = self.content_attempt.return_activity_interval()
        datetime_text = format_datetime(
            current_tz.normalize(earliest.astimezone(current_tz)))
        if latest:
            datetime_text += " - " + format_datetime(
                current_tz.normalize(latest.astimezone(current_tz)))

        context['datetime'] = mark_safe('&nbsp;%s&nbsp;' % datetime_text)

        context['version'] = self.content_attempt.version
        
        if self.instructor_view:
            context['version_url'] = self.content_attempt.return_url()


        from micourses.render_assessments import get_question_list_from_attempt
        question_list = get_question_list_from_attempt(
            self.assessment, self.content_attempt)

        context['show_latest_question_attempts']= \
                    self.show_latest_question_attempts

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()
        context['_auxiliary_data_'] = auxiliary_data
        
        for q_dict in question_list:
            ca_question_set=q_dict['ca_question_set']
            question_number =ca_question_set.question_number
            q_dict['question_number'] = question_number

            credit =  ca_question_set.get_credit()
            if credit is None:
                credit=0
            score = credit*q_dict.get('points',0)
            percent_credit = credit*100
            q_dict['percent_credit'] = percent_credit
            q_dict['percent_credit_text'] = floatformat_or_dash(
                percent_credit,1)
            q_dict['score'] = score
            q_dict['score_text'] = floatformat_or_dash(score, 1)
            q_dict['credit_overridden'] = \
                                ca_question_set.credit_override is not None


            if self.instructor_view:
                q_dict['show_details'] = \
                    ca_question_set.question_attempts.exclude(credit=None)\
                                                     .exists()
                if not q_dict['show_details']:
                    q_dict['show_details'] = QuestionResponse.objects.filter(
                        question_attempt__content_attempt_question_set=ca_question_set).exists()
                               
            else:
                q_dict['show_details'] = \
                    ca_question_set.question_attempts.exclude(credit=None)\
                                                .exclude(valid=False).exists()
            
            if q_dict['show_details']:
                if self.instructor_view:
                    q_dict['attempt_url'] = reverse(
                        'micourses:question_attempts_instructor', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
                                'attempt_number': self.attempt_number,
                                'student_id': self.student.id,
                                'question_number': ca_question_set\
                                .question_number})

                    if self.show_latest_question_attempts:
                        from .utils import get_latest_question_data
                        q_dict['latest_question_data'] = \
                            get_latest_question_data(
                                ca_question_set=ca_question_set,
                                auxiliary_data=auxiliary_data)
                    

                else:
                    q_dict['attempt_url'] = reverse(
                        'micourses:question_attempts', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
                                'attempt_number': self.attempt_number,
                                'question_number': ca_question_set\
                                .question_number})

            if self.instructor_view:
                q_dict['direct_link'] =  self.content_attempt.return_url(
                    question_number=ca_question_set.question_number)
                q_dict["score_form"] = ScoreForm({'score': score},
                    auto_id="edit_question_%s_score_form_%%s" % question_number)
                q_dict["credit_form"] = CreditForm({'percent': percent_credit},
                    auto_id="edit_question_%s_credit_form_%%s" % question_number)


        if self.instructor_view:
            score=self.content_attempt.score
            score_text = floatformat_or_dash(score, 1)
            if score is None:
                score_or_zero=0
            else:
                score_or_zero=score
            score_form = ScoreForm({'score': score_or_zero},
                                   auto_id="edit_attempt_%s_score_form_%%s" %\
                                   self.content_attempt.id)

            percent_credit = self.content_attempt.get_percent_credit()
            percent_credit_text = floatformat_or_dash(percent_credit,1)
            percent_credit_or_zero = percent_credit
            if percent_credit_or_zero is None:
                percent_credit_or_zero = 0
            credit_form = CreditForm({'percent': percent_credit_or_zero},
                                    auto_id="edit_attempt_%s_credit_form_%%s" %\
                                    self.content_attempt.id)

            context['score']=score
            context['score_text']=score_text
            context['score_form'] = score_form
            context['percent_credit'] = percent_credit
            context['percent_credit_text'] = percent_credit_text
            context['credit_form'] = credit_form

        context['question_list'] =question_list

        return context


    def get_template_names(self):
        if self.instructor_view:
            if self.show_latest_question_attempts:
                return ['micourses/content_attempt_instructor_with_latest_attempts.html',]
            else:
                return ['micourses/content_attempt_instructor.html',]
                
        else:
            return ['micourses/content_attempt_student.html',]


class QuestionAttemptsView(ContentAttemptView):

    def get_additional_objects(self, request, *args, **kwargs):
        super(QuestionAttemptsView,self).get_additional_objects(
            request, *args, **kwargs)

        # don't pad question_number with zeros
        self.question_number = self.kwargs['question_number']
        if self.question_number[0]=='0':
            raise Http404('Question %s not found.' % self.question_number)

        self.question_number = int(self.question_number)

        try:
            self.ca_question_set = self.content_attempt.question_sets.get(
                question_number = self.question_number)
        except ObjectDoesNotExist:
            raise Http404('Question number %s not found.' \
                              % self.question_number)

        self.question_set_points = self.ca_question_set.get_points()
        

    def get_context_data(self, **kwargs):
        context = super(QuestionAttemptsView, self).get_context_data(**kwargs)

        context['question_number'] = self.question_number
        context['ca_question_set'] = self.ca_question_set

        return context

    def extra_context(self):
        from micourses.utils import format_datetime
        current_tz = timezone.get_current_timezone()

        context={}


        context['credit_overridden'] = \
                        self.ca_question_set.credit_override is not None

        earliest, latest = self.ca_question_set.return_activity_interval()
        datetime_text = format_datetime(
            current_tz.normalize(earliest.astimezone(current_tz)))
        if latest:
            datetime_text += " - " + format_datetime(
                current_tz.normalize(latest.astimezone(current_tz)))

        context['datetime'] = mark_safe('&nbsp;%s&nbsp;' % datetime_text)

        question_attempt_list = []

        if self.instructor_view:
            question_attempts = self.ca_question_set.question_attempts\
                       .order_by('-valid', 'attempt_began')
        else:
            question_attempts = self.ca_question_set.question_attempts\
                                                    .filter(valid=True)
        
        valid_response_number = 0
        invalid_response_number=0
        for (i,question_attempt) in enumerate(question_attempts):
            attempt_dict = {'question_attempt': question_attempt,
                            'version_number': i+1,}

            if self.instructor_view:
                responses = question_attempt.responses\
                       .order_by('-valid', 'response_submitted')
            else:
                responses = question_attempt.responses.filter(valid=True)
            
            response_list = []

            attempt_valid = question_attempt.valid

            for response in responses:

                response_valid = attempt_valid and response.valid

                if response_valid:
                    valid_response_number +=1
                    response_number = str(valid_response_number)
                else:
                    invalid_response_number +=1
                    response_number = "x%s" % invalid_response_number


                response_dict = {'submitted': response.response_submitted,
                                 'valid': response_valid,
                                 'response_number': response_number}

                percent_credit = response.credit*100
                if self.question_set_points:
                    score = response.credit * self.question_set_points
                else:
                    score = 0
                score_text = floatformat_or_dash(score,1)
                
                response_dict['percent_credit']=percent_credit
                response_dict['score']=score
                response_dict['score_text']=score_text


                if self.instructor_view:
                    response_dict['response_url'] = reverse(
                        'micourses:question_response_instructor', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
                                'attempt_number': self.attempt_number,
                                'student_id': self.student.id,
                                'question_number': self.question_number,
                                'response_number': response_number
                            })

                else:
                    response_dict['response_url'] = reverse(
                        'micourses:question_response', 
                        kwargs={'course_code': self.course.code,
                                'content_id': self.thread_content.id,
                                'attempt_number': self.attempt_number,
                                'question_number': self.question_number,
                                'response_number': response_number
                            })

                response_list.append(response_dict)

            attempt_dict['responses'] = response_list
            question_attempt_list.append(attempt_dict)

        context['question_attempt_list'] = question_attempt_list

        context['multiple_question_attempts'] = len(question_attempt_list)>1

        credit = self.ca_question_set.get_credit()

        if credit is None:
            percent_credit = None
            score = None
        else:
            percent_credit = credit*100
            if self.question_set_points:
                score = self.question_set_points*credit
            else:
                score = 0

        score_text = floatformat_or_dash(score,1)

        context['points'] = self.question_set_points
        context['score'] = score
        context['score_text'] = score_text
        context['percent_credit'] = percent_credit
        
        if self.instructor_view:
            context["score_form"] = ScoreForm({'score': score},
                auto_id="edit_question_%s_score_form_%%s" % \
                                              self.question_number)
            context["credit_form"] = CreditForm({'percent': percent_credit},
                auto_id="edit_question_%s_credit_form_%%s" % \
                                                self.question_number)

        return context

    def get_template_names(self):
        if self.instructor_view:
            return ['micourses/question_attempts_instructor.html',]
        else:
            return ['micourses/question_attempts_student.html',]


class QuestionResponseView(QuestionAttemptsView):
    

    def get_additional_objects(self, request, *args, **kwargs):
        super(QuestionResponseView,self).get_additional_objects(
            request, *args, **kwargs)

        self.response_number = self.kwargs['response_number']
        
        # if response_number begins with an x, it is an invalid response number
        if self.response_number[0]=="x":
            if not self.instructor_view:
                raise Http404('Response %s not found.' \
                              % self.response_number)
            self.response_valid = False
            response_number_int = self.response_number[1:]
        else:
            self.response_valid = True
            response_number_int = self.response_number
            
        # don't pad response_number with a zero
        if response_number_int[0]=='0':
            raise Http404('Response %s not found.' \
                              % self.response_number)

        try:
            response_number_int = int(response_number_int)
        except ValueError:
            raise Http404('Response %s not found.' \
                          % self.response_number)

        if self.response_valid:
            responses = QuestionResponse.objects.filter(
                question_attempt__content_attempt_question_set =\
                self.ca_question_set,
                question_attempt__valid = True, valid=True)

        else:
            responses = QuestionResponse.objects.filter(
                question_attempt__content_attempt_question_set =\
                self.ca_question_set)\
                    .exclude(question_attempt__valid = True, valid=True)
        try:
            self.response = responses[response_number_int-1]
        except IndexError:
            raise Http404('Response %s not found.' \
                              % self.response_number)
            

    def extra_context(self):
        
        context = {'submitted': self.response.response_submitted,
                   'valid': self.response_valid,
                          }
        try:
            context['score'] = self.response.credit*\
                                     self.question_set_points
        except TypeError:
            context['score'] = 0
        context['points'] = self.question_set_points
        context['percent_credit'] = self.response.credit*100
        context['response_number'] = self.response_number

        question = self.response.question_attempt.question

        # use qrv in identifier since coming from
        # question response view
        identifier = "qrv"

        from midocs.functions import return_new_auxiliary_data
        auxiliary_data =  return_new_auxiliary_data()

        question_dict = {
            'question': question,
            'question_set': self.ca_question_set.question_set,
            'seed': self.response.question_attempt.seed,
            'question_attempt':self.response.question_attempt,
            'response': self.response
        }



        import random
        rng=random.Random()
        from mitesting.render_questions import render_question
        question_data = render_question(
            question_dict, rng=rng, question_identifier=identifier,
            user=self.request.user, assessment=self.assessment,
            show_help=False, readonly=True, auto_submit=True, 
            record_response=False,
            allow_solution_buttons=self.thread_content.allow_solution_buttons_in_gradebook,
            auxiliary_data=auxiliary_data)

        context['question']=question
        context['question_data']= question_data
        context['_auxiliary_data_']= auxiliary_data
        context['attempt_number']=self.attempt_number
        context['question_number']= self.question_number
        context['STATIC_URL'] = settings.STATIC_URL
        
        return context


    def get_template_names(self):
        if self.instructor_view:
            return ['micourses/question_response_instructor.html',]
        else:
            return ['micourses/question_response_student.html',]


class ContentListView(CourseBaseView):
    template_name='micourses/content_list.html'

    def get_context_data(self, **kwargs):
        context = super(ContentListView, self).get_context_data(**kwargs)


        exclude_completed='exclude_completed' in self.request.GET
        #exclude_past_due='exclude_past_due' in self.request.GET
        by_assigned='by_assigned' in self.request.GET


        try:
            begin_date = timezone.datetime.strptime(self.request.GET.get('begin_date'),self.datetime_format)
        except TypeError:
            begin_date = None
        try:
            end_date = timezone.datetime.strptime(self.request.GET.get('end_date'),self.datetime_format)
        except TypeError:
            end_date = None

        context['begin_date'] = begin_date
        context['end_date'] = end_date
        context['by_assigned'] = by_assigned
        context['content_list'] = self.course.content_by_date\
            (enrollment=self.enrollment, exclude_completed=exclude_completed, 
             begin_date=begin_date, end_date=end_date,
             by_assigned=by_assigned)

        if begin_date and end_date:
            next_begin_date = end_date + timezone.timedelta(microseconds=1)
            next_end_date = next_begin_date+timezone.timedelta(days=7) \
                            - timezone.timedelta(microseconds=1)
            next_period_parameters = "begin_date=%s&end_date=%s" \
                % (next_begin_date.strftime(self.datetime_format),
                   next_end_date.strftime(self.datetime_format))
            previous_end_date = begin_date - timezone.timedelta(microseconds=1)
            previous_begin_date = previous_end_date-timezone.timedelta(days=7)\
                                  + timezone.timedelta(microseconds=1)
            previous_period_parameters = "begin_date=%s&end_date=%s" \
                % (previous_begin_date.strftime(self.datetime_format),
                   previous_end_date.strftime(self.datetime_format))
            if exclude_completed:
                previous_period_parameters += "&exclude_completed"
                next_period_parameters += "&exclude_completed"
            if by_assigned:
                previous_period_parameters += "&by_assigned"
                next_period_parameters += "&by_assigned"
        else:
            previous_period_parameters=None
            next_period_parameters=None

        all_dates_parameters = ""
        if exclude_completed:
            all_dates_parameters = "exclude_completed"
        if by_assigned:
            if all_dates_parameters:
                all_dates_parameters += "&by_assigned"
            else:
                all_dates_parameters = "by_assigned"

        date_parameters=""
        if begin_date:
            date_parameters += "begin_date=%s" % begin_date.strftime(self.datetime_format)
        if end_date:
            if date_parameters:
                date_parameters += "&"
            date_parameters += "end_date=%s" % end_date.strftime(self.datetime_format)

        exclude_completed_parameters="exclude_completed"
        if date_parameters:
            exclude_completed_parameters += "&" + date_parameters
        if by_assigned:
            exclude_completed_parameters += "&by_assigned"

        include_completed_parameters=date_parameters
        if by_assigned:
            if include_completed_parameters:
                include_completed_parameters += "&by_assigned"
            else:
                include_completed_parmaeters = "by_assigned"


        by_assigned_parameters="by_assigned"
        if date_parameters:
            by_assigned_parameters += "&" + date_parameters
        if exclude_completed:
            by_assigned_parameters += "&exclude_completed"

        by_due_parameters = date_parameters
        if exclude_completed:
            if by_due_parameters:
                by_due_parameters += "&exclude_completed"
            else:
                by_due_parameters = "exclude_completed"

        context['exclude_completed']=exclude_completed

        context['previous_period_parameters']=previous_period_parameters
        context['next_period_parameters']=next_period_parameters
        context['exclude_completed_parameters']=exclude_completed_parameters
        context['include_completed_parameters']=include_completed_parameters
        context['all_dates_parameters']=all_dates_parameters
        context['by_assigned_parameters']=by_assigned_parameters
        context['by_due_parameters']=by_due_parameters

        return context


class StudentGradebook(CourseBaseView):
    template_name = "micourses/student_gradebook.html"
    def get_context_data(self, **kwargs):
        context = super(StudentGradebook, self).get_context_data(**kwargs)

        context['category_scores']=self.course.student_scores_by_grade_category(self.courseuser)
    
        return context


class InstructorGradebook(CourseBaseView):
    template_name = "micourses/instructor_gradebook.html"
    def get_context_data(self, **kwargs):
        context = super(InstructorGradebook, self).get_context_data(**kwargs)
        context['assessment_categories'] = self.course.all_assessments_by_category()
        context['student_scores'] = self.course.student_scores_by_grade_category()
        context['total_points'] = self.course.total_points()

        return context

class OpenCloseAttempt(CourseBaseMixin, View):
    instructor_view=True
    
    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))



    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        self.get_additional_objects(request, *args, **kwargs)

        try:
            action = request.POST['action']
        except KeyError:
            return JsonResponse({}) 

        try:
            enrollment_id= int(request.POST['enrollment_id'])
        except (KeyError, ValueError):
            return JsonResponse({})

        try:
            student_record = self.thread_content.contentrecord_set\
                            .get(enrollment__id=enrollment_id)
        except ObjectDoesNotExist:
            return JsonResponse({})

        if action == "open":
            from .utils import ensure_open_assessment_attempt
            ensure_open_assessment_attempt(student_record)

        elif action == "close":
            from .utils import close_latest_assessment_attempt
            close_latest_assessment_attempt(student_record)
            
        from .utils import get_open_attempt_info
        info_dict = get_open_attempt_info(student_record)
        open_attempt = info_dict['open_attempt']
        latest_attempt_info_text = info_dict['latest_attempt_info_text']

        return JsonResponse({
            'enrollment_id': enrollment_id,
            'score': floatformat_or_dash(student_record.score,1),
            'open_attempt': open_attempt,
            'latest_attempt_info_text': latest_attempt_info_text,
            'action': action})


class EditCourseContentAttemptScores(CourseBaseView):

    template_name = 'micourses/edit_course_content_attempt_scores.html'
    instructor_view=True

    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_additional_objects(self, request, *args, **kwargs):
        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))

        try:
            self.course_content_record = self.thread_content.contentrecord_set\
                                  .get(enrollment=None)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                self.course_content_record =\
                        self.thread_content.contentrecord_set\
                                  .create(enrollment=None)




    def get_context_data(self, **kwargs):
        context = super(EditCourseContentAttemptScores, self).get_context_data(**kwargs)

        context['thread_content']=self.thread_content

        ccas = self.course_content_record.attempts.filter(valid=True)
        context['ccas'] = ccas

        enrollment_list = []

        record_dict = {
            record.enrollment.id: record for \
            record in self.thread_content.contentrecord_set.filter(enrollment__role=STUDENT_ROLE)\
            .select_related('enrollment', 'latest_attempt')
        }

        ces =  self.course.courseenrollment_set.filter(role=STUDENT_ROLE).select_related('student__user')


        from .utils import get_open_attempt_info

        for (i,ce) in enumerate(ces):
            content_record = record_dict.get(ce.id)
            if not content_record:
                with transaction.atomic(), reversion.create_revision():
                    content_record = self.thread_content.contentrecord_set\
                                                        .create(enrollment=ce)

            if i < len(ces)-1:
                next_enrollment_id = ces[i+1].id
            else:
                next_enrollment_id = 'null'

            info_dict = get_open_attempt_info(content_record)
            open_attempt = info_dict['open_attempt']
            latest_attempt_info_text = info_dict['latest_attempt_info_text']

            enrollment_list.append({
                'enrollment': ce,
                'content_record': content_record,
                'attempts': [],
                'next_enrollment_id': next_enrollment_id,
                'open_attempt': open_attempt,
                'latest_attempt_info_text': latest_attempt_info_text,
            })


        from micourses.models import ContentAttempt

        skipdate_dict = {sd.date: sd.id for sd in self.course.courseskipdate_set.all() }


        for cca in ccas:
            attempts = ContentAttempt.objects.filter(
                record__content=self.thread_content,
                record__enrollment__role=STUDENT_ROLE,
                base_attempt=cca, valid=True).select_related('record')

            attempt_dict = { attempt.record.id: attempt for attempt in attempts}

            
            # for each enrollment, find the associated attempt if exists
            for enrollment_dict in enrollment_list:
                content_record = enrollment_dict['content_record']
                try:
                    attempt = attempt_dict[content_record.id]
                    score = attempt.score
                    if score is None:
                        score=""
                except KeyError:
                    attempt = None
                    score = ""

                try:
                    past_due = self.thread_content.get_adjusted_due(
                        content_record, skipdate_dict=skipdate_dict) \
                        < cca.attempt_began
                except TypeError:
                    past_due = False
                
                enrollment_dict['attempts'].append({
                    'base_attempt': cca,
                    'attempt': attempt,
                    'score': floatformat(score,1),
                    'past_due': past_due,
                })
                
                

        context['enrollment_list'] = enrollment_list

        context['message'] = self.request.GET.get('message')

        return context


    def post_open_close_attempts(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)

        self.get_additional_objects(request, *args, **kwargs)

        open_attempt_action = request.POST.get('open_attempt_action')

        message = ""

        if open_attempt_action == "open":
            from .utils import ensure_open_assessment_attempt_all_students
            result = ensure_open_assessment_attempt_all_students(
                self.thread_content)
            if result['n_created']:
                message = 'Opened attempt for %s students' % result['n_created']
            elif not result['n_students']:
                message = 'No students enrolled'
            elif not result['assessment_available']:
                message = 'Assessment is not available'
            else:
                message = 'No new attempts opened'
        elif open_attempt_action == "close":
            from .utils import close_latest_assessment_attempt_all_students
            close_latest_assessment_attempt_all_students(self.thread_content)
            message="Closed attempts for all students"
        

        return HttpResponseRedirect(reverse(
            'micourses:edit_course_content_attempt_scores',
            kwargs={'course_code': self.course.code,
                    'content_id': self.thread_content.id})
                                    +'?message=' + message)


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Called when edit course wide attempts (as AJAX)
        or when click button to open/close attempts (as standard POST request)
        """

        # if have open_attempt_action, then is request to open/close attempts
        if request.POST.get('open_attempt_action'):
            return self.post_open_close_attempts(request, *args, **kwargs)


        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        self.get_additional_objects(request, *args, **kwargs)

        try:
            enrollment_id = request.POST['enrollment_id']
            base_attempt_id = request.POST['base_attempt_id']
            enrollment = self.course.courseenrollment_set.get(
                id = enrollment_id)
            base_attempt = self.course_content_record.attempts.get(
                id=base_attempt_id)

        except (KeyError, ObjectDoesNotExist):
            return JsonResponse({})

        try:
            value = request.POST['value']
            if value=="":
                value=None
            else:
                value=float(value)
        except (KeyError,ValueError):
            return JsonResponse({
                'enrollment_id': enrollment_id,
                'base_attempt_id': base_attempt_id,
                'error_message': "Enter a number",
            })
            
        
        try:
            content_record = self.thread_content.contentrecord_set\
                                                .get(enrollment=enrollment)
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                content_record = self.thread_content.contentrecord_set\
                                                .create(enrollment=enrollment)
                
        try:
            attempt = content_record.attempts.get(
                base_attempt=base_attempt, valid=True)
            attempt.score_override=value
            attempt.save()
        except ObjectDoesNotExist:
            with transaction.atomic(), reversion.create_revision():
                attempt = base_attempt.create_derived_attempt(
                    content_record = content_record, score=value)



        content_record.refresh_from_db()

        return JsonResponse({
            'enrollment_id': enrollment_id,
            'base_attempt_id': base_attempt_id,
            'error_message': "",
            'score': floatformat(attempt.score,1),
            'overall_score': floatformat_or_dash(content_record.score,1),
        })




class LatestContentAttemptsCSV(CourseBaseMixin, View):
    instructor_view=True
    
    # no student for this view
    def get_student(self):
        return self.courseuser


    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except NotEnrolled:
            return redirect('micourses:notenrolled', 
                            course_code=self.course.code)
        except NotInstructor:
            return redirect('micourses:coursemain', 
                            course_code=self.course.code)

        try:
            self.thread_content = self.course.thread_contents.get(
                id=kwargs["content_id"])
        except ObjectDoesNotExist:
            raise Http404("Thread content not found with course %s and id=%s"\
                          % (self.course, kwargs["content_id"]))


        content_records = self.thread_content.contentrecord_set.filter(enrollment__role=STUDENT_ROLE)

        # Create the HttpResponse object with the appropriate CSV header.
        hresponse = HttpResponse(content_type='text/csv; charset=utf-8')
        hresponse['Content-Disposition'] = 'attachment; filename="gradebook.csv"'

        import csv, json 
        writer = csv.writer(hresponse)

        student_names = []
        question_rows = []
        fields_per_question = []
        
        for cr in content_records:
            try:
                ca = cr.attempts.filter(valid=True).latest()
            except ObjectDoesNotExist:
                continue


            student_names.append(cr.enrollment.student.get_full_name())
            
            
            for (i,qs) in enumerate(ca.question_sets.all()):
                try:
                    qr = question_rows[i]
                except IndexError:
                    question_rows.append([])
                    qr = question_rows[i]
                try:
                    fpq = fields_per_question[i]
                except IndexError:
                    fields_per_question.append(0)
                    fpq = 0

                try:
                    responses = json.loads(qs.question_attempts.filter(valid=True).latest().responses.filter(valid=True).latest().response)
                except ObjectDoesNotExist:
                    qr.append([])
                    continue

                num_fields = len(responses)
                if num_fields > fpq:
                    fields_per_question[i] = num_fields

                resplist = []
                for r in responses:
                    resplist.append(r['response'])
                qr.append(resplist)

                print(question_rows)   
                print(fields_per_question)

        n_questions = len(fields_per_question)
        print(fields_per_question)
        print(n_questions)
        print(question_rows[0])
        for (i,sn) in enumerate(student_names):
            row = [sn,]
            for j in range(n_questions):
                print(i,j)
                try:
                    qr= question_rows[j][i]
                except IndexError:
                    qr = []
                print(qr)
                row.extend(qr)
                fpq = fields_per_question[j]
                if len(qr) < fpq:
                    row.extend(['']*(fpq-len(qr)))
            print(row)
            writer.writerow(row)
        
        return hresponse


    

class ExportGradebook(CourseBaseView):
    instructor_view=True
    template_name = 'micourses/export_gradebook.html'

    # no student for this view
    def get_student(self):
        return self.courseuser

    def get_context_data(self, **kwargs):
        context = super(ExportGradebook, self).get_context_data(**kwargs)

        context['assessment_categories'] = \
                                self.course.coursegradecategory_set.all()
        
        return context


class GradebookCSV(CourseBaseMixin, View):
    instructor_view=True
    
    # no student for this view
    def get_student(self):
        return self.courseuser


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

        section = request.POST.get('section')

        include_total=False
        if request.POST.get("course_total")=="t":
            include_total=True
        if request.POST.get("replace_numbers"):
            replace_numbers=True
        else:
            replace_numbers=False

        included_categories = []
        totaled_categories = []
        assessment_names_in_category = {}
        assessment_points_in_category = {}
        
        grade_categories = self.course.all_assessments_by_category()

        grade_category_dicts = {}
        
        for cgc_dict in grade_categories:
            cgc = cgc_dict['cgc']
            grade_category_dicts[cgc.id] = cgc_dict

            include_category = request.POST.get('category_%s' % cgc.id, 'e')
            if include_category=="i":
                assessments = cgc_dict['assessments']

                assessment_name_list=[]
                assessment_point_list=[]
                i=0
                for assessment in assessments:
                    assessment_points = assessment['points']
                    if not assessment_points:
                        continue
                    i=i+1
                    if replace_numbers:
                        assessment_name_list.append(i)
                    else:
                        try:
                            name = assessment['assessment'].get_short_name()
                        except AttributeError:
                            name = assessment['assessment'].get_title()
                        assessment_name_list.append(name)
                    assessment_point_list.append(assessment_points)

                if(assessment_name_list):
                    assessment_names_in_category[cgc.id] = assessment_name_list
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
        row=["","","",""]
        for cgc in included_categories:
            row.append(cgc.grade_category.name)
            row.extend([""]*(len(assessment_names_in_category[cgc.id])-1))
            row.append("Total")
        row.extend(["Total"]*len(totaled_categories))
        if include_total:
            row.append("Course")
        writer.writerow(row)


        row=["Student", "ID", "Section", "Group"]
        for cgc in included_categories:
            row.extend(assessment_names_in_category[cgc.id])
            row.append(cgc.grade_category.name)
        for cgc in totaled_categories:
            row.append(cgc.grade_category.name)
        if include_total:
            row.append("Total")
        writer.writerow(row)

        student_scores = self.course.student_scores_by_grade_category(
            section=section)

        # if no student scores, 
        # then test to see if section is an integer and 
        # query with a zero-padded string
        if not student_scores:
            try:
                section_int = int(section)
            except ValueError:
                pass
            else:
                # if it is an integer, try a padded section
                section_padded = '0'+ str(section)
                student_scores = self.course.student_scores_by_grade_category(
                    section=section_padded)

        for score_dict in student_scores:
            ce = score_dict['enrollment']
            student_section = ce.section
            student = ce.student
            row=[str(student), student.userid, student_section, ce.group]
            for student_category in score_dict['categories']:
                if student_category['cgc'] not in included_categories:
                    continue
                for assessment_results in student_category['scores']:
                    score = assessment_results['score']
                    if score is None:
                        score=0
                    row.append(round(score*10)/10.0)
                row.append(round(student_category['student_score']*10)/10.0)

            for student_category in score_dict['categories']:
                if student_category['cgc'] not in totaled_categories:
                    continue

                row.append(round(student_category['student_score']*10)/10.0)

            if include_total:
                row.append(round(score_dict['total_score']*10)/10.0)

            writer.writerow(row)

        comments=[]

        row=["Possible points","","",""]
        for cgc in included_categories:
            cgc_dict = grade_category_dicts[cgc.id]
            row.extend(assessment_points_in_category[cgc.id])
            row.append(cgc_dict['points'])
            number_assessments = len(assessment_points_in_category[cgc.id])
            score_comment=cgc_dict['score_comment_long']
            if score_comment:
                score_comment = "Total %s is %s" % (cgc.grade_category.name,
                                                    score_comment)
                comments.append(score_comment)
        for cgc in totaled_categories:
            row.append( grade_category_dicts[cgc.id]['points'])
        if include_total:
            row.append(self.course.total_points())
            score_comment = "Course total is "
            first=True
            for cgc in self.course.coursegradecategory_set.all():
                if (self.course.points_for_grade_category \
                    (cgc)):
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



class RecordContentCompletion(CourseBaseMixin, View):

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        try:

            thread_content = self.course.thread_contents.get(
                id=request.POST["content_id"])
            complete = int(request.POST['complete'])
        except (KeyError, ObjectDoesNotExist, ValueError):
            return JsonResponse({})

        with transaction.atomic(), reversion.create_revision():
            try:
                content_record = thread_content.contentrecord_set\
                                    .get(enrollment=self.student_enrollment)
            except ObjectDoesNotExist:
                content_record = thread_content.contentrecord_set\
                                  .create(enrollment=self.student_enrollment,
                                          complete=complete)
            else:
                content_record.complete=complete
                content_record.save()

        
        return JsonResponse({'content_id': thread_content.id,
                             'complete': complete,
                             })

    
class ImportClassRosterView(CourseBaseView):
    instructor_view=True
    template_name="micourses/import_class_roster.html"
    
    
    # no student for this view
    def get_student(self):
        return self.courseuser


    def get_additional_objects(self, request, *args, **kwargs):
        from .forms import ImportClassRosterForm
        if request.method == "POST":
            self.form = ImportClassRosterForm(request.POST, request.FILES)
        else:
            self.form = ImportClassRosterForm()
    
    def get_context_data(self, **kwargs):
        context = super(ImportClassRosterView, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context

    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Called when edit course wide attempts (as AJAX)
        or when click button to open/close attempts (as standard POST request)
        """

        try:
            self.object = self.get_object()
        except (NotEnrolled, NotInstructor):
            return JsonResponse({})

        self.get_additional_objects(request, *args, **kwargs)

        if self.form.is_valid():

            from .utils import import_class_roster
            csvfile = request.FILES['file'].read().decode("utf-8").splitlines()
            import_class_roster(csvfile, self.course)

            return HttpResponseRedirect(reverse(
                'micourses:coursemain',
                kwargs={'course_code': self.course.code})
            +'?message=class roster imported')
        else:
            return self.render_to_response(self.get_context_data())
        
