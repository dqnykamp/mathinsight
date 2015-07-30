# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0003_auto_20150728_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.CreateModel(
            name='QuestionDatabase',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Question database',
            },
            bases=('mitesting.question',),
        ),
        migrations.RemoveField(
            model_name='assessmenttype',
            name='record_online_attempts',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='nothing_random',
            new_name='single_version',
        ),
        migrations.AddField(
            model_name='assessment',
            name='resample_question_sets',
            field=models.BooleanField(default=False),
        ),
     ]
