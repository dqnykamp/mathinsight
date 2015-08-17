# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import re
import micourses.utils
import django.core.validators


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
    ]
