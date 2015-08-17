# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0007_auto_20150806_1155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='background_pages',
            field=models.ManyToManyField(through='mitesting.AssessmentBackgroundPage', related_name='old_assessments', to='midocs.Page', blank=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(related_name='old_assessments', to='micourses.Course'),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='groups_can_view',
            field=models.ManyToManyField(related_name='old_assessments_can_view', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='groups_can_view_solution',
            field=models.ManyToManyField(related_name='old_assessments_can_view_solution', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='questions',
            field=models.ManyToManyField(through='mitesting.QuestionAssigned', related_name='old_assessments', to='mitesting.Question', blank=True),
        ),
        migrations.AlterField(
            model_name='assessmentbackgroundpage',
            name='page',
            field=models.ForeignKey(related_name='old_assessment_background_pages', to='midocs.Page'),
        ),
        migrations.AlterField(
            model_name='questionassigned',
            name='question',
            field=models.ForeignKey(related_name='old_questionassigned', to='mitesting.Question'),
        ),
    ]
