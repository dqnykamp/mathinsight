# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0001_initial'),
        ('mitesting', '0002_auto_20150723_2041'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(null=True, blank=True, to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='question',
            name='base_question',
            field=models.ForeignKey(null=True, related_name='derived_questions', blank=True, to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='question',
            name='course',
            field=models.ForeignKey(null=True, blank=True, to='micourses.Course'),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='code',
            field=models.SlugField(max_length=200),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='assessment',
            unique_together=set([('course', 'code'), ('course', 'name')]),
        ),
    ]
