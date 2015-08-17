# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0008_auto_20150811_2300'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='assessment',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='assessment_type',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='background_pages',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='course',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='groups_can_view',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='groups_can_view_solution',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='assessmentbackgroundpage',
            name='assessment',
        ),
        migrations.RemoveField(
            model_name='assessmentbackgroundpage',
            name='page',
        ),
        migrations.RemoveField(
            model_name='questionassigned',
            name='assessment',
        ),
        migrations.RemoveField(
            model_name='questionassigned',
            name='question',
        ),
        migrations.AlterUniqueTogether(
            name='questionsetdetail',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='questionsetdetail',
            name='assessment',
        ),
        migrations.DeleteModel(
            name='Assessment',
        ),
        migrations.DeleteModel(
            name='AssessmentBackgroundPage',
        ),
        migrations.DeleteModel(
            name='AssessmentType',
        ),
        migrations.DeleteModel(
            name='QuestionAssigned',
        ),
        migrations.DeleteModel(
            name='QuestionSetDetail',
        ),
    ]
