# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0020_auto_20150903_1640'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseWithEnrollment',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Courses with enrollmentt',
                'proxy': True,
            },
            bases=('micourses.course',),
        ),
    ]
