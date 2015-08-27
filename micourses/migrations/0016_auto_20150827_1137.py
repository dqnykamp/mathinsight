# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0015_auto_20150812_1730'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionattempt',
            name='content_attempt',
        ),
        migrations.RemoveField(
            model_name='questionattempt',
            name='question_set',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='content_attempt',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='question',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='question_set',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='seed',
        ),
        migrations.AlterField(
            model_name='contentattemptquestionset',
            name='question_number',
            field=models.SmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='content_attempt_question_set',
            field=models.ForeignKey(related_name='question_attempts', to='micourses.ContentAttemptQuestionSet'),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='question_attempt',
            field=models.ForeignKey(related_name='responses', to='micourses.QuestionAttempt'),
        ),
    ]
