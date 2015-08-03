# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import timezone

def adjust_datetimes_to_right_timezone(apps, schema_editor):
    # Apparently, datetimes were made timezone aware assuming UTC
    # Adjust so it is made aware assuming current time zone
    # Also, set created to last_modified for StudentContentRecord
    # and set assign/due times to be beginning/end of day of current time zone

    StudentContentRecord = apps.get_model('micourses', 'StudentContentRecord')
    for scr in StudentContentRecord.objects.all():
        if scr.last_modified:
            scr.last_modified = timezone.make_aware(
                timezone.make_naive(scr.last_modified,
                                    timezone=scr.last_modified.tzinfo))
            scr.created = scr.last_modified
        else:
            print("no last modified for: %s" % scr)
        scr.save()
        

    ContentAttempt = apps.get_model('micourses', 'ContentAttempt')
    for ca in ContentAttempt.objects.all():
        ca.attempt_began = timezone.make_aware(
            timezone.make_naive(ca.attempt_began, 
                                timezone=ca.attempt_began.tzinfo))
        ca.save()

    QuestionAttempt = apps.get_model('micourses', 'QuestionAttempt')
    for qa in QuestionAttempt.objects.all():
        qa.solution_viewed = timezone.make_aware(
            timezone.make_naive(qa.solution_viewed, 
                                timezone=qa.solution_viewed.tzinfo))
        qa.save()

    QuestionResponse = apps.get_model('micourses', 'QuestionResponse')
    for qr in QuestionResponse.objects.all():
        qr.response_submitted = timezone.make_aware(
            timezone.make_naive(qr.response_submitted, 
                                timezone=qr.response_submitted.tzinfo))
        qr.save()

    ThreadContent = apps.get_model('micourses', 'ThreadContent')
    dt_endofday=timezone.timedelta(hours=23, minutes=59, seconds=59)
    for tc in ThreadContent.objects.all():
        changed=False
        if tc.assigned is not None:
            changed=True
            tc.assigned=timezone.make_aware(
                timezone.make_naive(tc.assigned,
                                    timezone=tc.assigned.tzinfo))
        if tc.initial_due is not None:
            changed=True
            tc.initial_due=timezone.make_aware(
                timezone.make_naive(tc.initial_due,
                                    timezone=tc.initial_due.tzinfo))
            tc.initial_due += dt_endofday
        if tc.final_due is not None:
            changed=True
            tc.final_due=timezone.make_aware(
                timezone.make_naive(tc.final_due,
                                    timezone=tc.final_due.tzinfo))
            tc.final_due += dt_endofday
        if changed:
            tc.save()


            
def base_attendance_on_enrollment(apps, schema_editor):
    # replace student/course with the enrollment into the course
    # if student isn't enrolled in the course, then delete record

    StudentAttendance = apps.get_model("micourses", "StudentAttendance")
    CourseEnrollment = apps.get_model("micourses", "CourseEnrollment")
    
    for sa in StudentAttendance.objects.all():
        try:
            ce = CourseEnrollment.objects.get(student=sa.student, 
                                              course=sa.course)
        except CourseEnrollment.DoesNotExist():
            ce = None

        if ce:
            sa.enrollment = ce
            sa.save()
        else:
            sa.delete()


def move_due_date_adjustments_to_content_record(apps, schema_editor):
    # for the new datimes, set them to end of day of current timezone
    import datetime
    time_endofday=datetime.time(hour=23, minute=59, second=59)

    ManualDueDateAdjustment = apps.get_model('micourses', 
                                             'ManualDueDateAdjustment')
    StudentContentRecord = apps.get_model('micourses', 'StudentContentRecord')

    for mdd in ManualDueDateAdjustment.objects.all():
        try:
            scr = StudentContentRecord.objects.get(student=mdd.student,
                                                   content=mdd.content)
        except StudentContentRecord.DoesNotExist:
            scr =StudentContentRecord(student=mdd.student, content=mdd.content,
                                      last_modified=timezone.now())

        scr.initial_due_adjustment = timezone.make_aware(
            timezone.datetime.combine(mdd.initial_due_date, time_endofday))
        scr.final_due_adjustment =  timezone.make_aware(
            timezone.datetime.combine(mdd.final_due_date, time_endofday))

        scr.save()

    
def base_record_on_enrollment(apps, schema_editor):

    StudentContentRecord = apps.get_model('micourses', 'StudentContentRecord')
    CourseEnrollment = apps.get_model("micourses", "CourseEnrollment")

    for scr in StudentContentRecord.objects.all():
        try:
            ce = CourseEnrollment.objects.get(student=scr.student, 
                                              course=scr.content.course)
        except CourseEnrollment.DoesNotExist:
            ce = None

        if ce:
            scr.enrollment = ce
            scr.save()
        else:
            scr.delete()


def base_attempt_on_record(apps, schema_editor):
    StudentContentRecord = apps.get_model('micourses', 'StudentContentRecord')
    ContentAttempt = apps.get_model("micourses", "ContentAttempt")
    CourseEnrollment = apps.get_model("micourses", "CourseEnrollment")

    # if content record doesn't exist but student is enrolled,
    # create content record
    for ca in ContentAttempt.objects.all():
        
        try:
            scr = StudentContentRecord.objects.get(student=ca.student,
                                                  content=ca.content)
        except StudentContentRecord.DoesNotExist:
            scr = None

        if not scr:
            try:
                ce = CourseEnrollment.objects.get(student=ca.student,
                                                  course=ca.content.course)
            except CourseEnrollment.DoesNotExist:
                ce = None

            # if found enrollment, create record
            if ce:
                scr = StudentContentRecord(student=ca.student,
                                           content=ca.content, 
                                           enrollment=ce)
            # else delete
            else:
                ca.delete()

        if scr:
            if scr.created:
                scr.created = min(scr.created, ca.attempt_began)
            else:
                scr.created = ca.attempt_began
            if not scr.last_modified:
                scr.last_modified = ca.attempt_began
            scr.save()

            ca.record=scr
            ca.save()


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0004_auto_20150801_2222'),
    ]

    operations = [
        migrations.RunPython(adjust_datetimes_to_right_timezone),
        migrations.RunPython(base_attendance_on_enrollment),
        migrations.RunPython(move_due_date_adjustments_to_content_record),
        migrations.RunPython(base_record_on_enrollment),
        migrations.RunPython(base_attempt_on_record),
    ]
