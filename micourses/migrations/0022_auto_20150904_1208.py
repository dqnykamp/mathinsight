# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0021_coursewithenrollment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coursewithenrollment',
            options={'verbose_name_plural': 'Courses with enrollment'},
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='group',
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='section',
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
    ]
