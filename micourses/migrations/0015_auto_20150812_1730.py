# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import timezone
import django.db.models.deletion

def adjust_datetimes_to_right_timezone(apps, schema_editor):
    # Apparently, dates are convert to datetimes assuming UTC
    # Adjust so new datatime is correct date assuming current time zone

    CourseEnrollment = apps.get_model('micourses', 'CourseEnrollment')
    for ce in CourseEnrollment.objects.all():
        ce.date_enrolled = timezone.make_aware(
            timezone.make_naive(ce.date_enrolled,
                                timezone=ce.date_enrolled.tzinfo))
        ce.save()

class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0014_auto_20150812_0044'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StudentContentRecord',
            new_name='ContentRecord',
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='base_attempt',
            field=models.ForeignKey(related_name='derived_attempts', null=True, to='micourses.ContentAttempt'),
        ),
        migrations.AlterField(
            model_name='contentrecord',
            name='enrollment',
            field=models.ForeignKey(to='micourses.CourseEnrollment', null=True),
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='version_string',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='n_of_object',
            field=models.SmallIntegerField(default=1),
        ),
        migrations.RenameField(
            model_name='changelog',
            old_name='time',
            new_name='datetime',
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='role',
            field=models.CharField(max_length=1, default='S', choices=[('S', 'Student'), ('I', 'Instructor'), ('D', 'Designer')]),
        ),
        migrations.AlterModelOptions(
            name='questionresponse',
            options={'get_latest_by': 'response_submitted', 'ordering': ['question_attempt', 'response_submitted']},
        ),
        migrations.AlterModelOptions(
            name='assessment',
            options={'ordering': ['code']},
        ),
        migrations.AlterField(
            model_name='courseuser',
            name='selected_course_enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='micourses.CourseEnrollment', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='date_enrolled',
            field=models.DateTimeField(blank=True),
        ),
        migrations.RunPython(adjust_datetimes_to_right_timezone),
    ]
