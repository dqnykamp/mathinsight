# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0007_auto_20150803_1526'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentattempt',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='contentattemptquestionset',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='questionattempt',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='studentcontentrecord',
            name='deleted',
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='credit',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='points',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='question_attempt',
            field=models.ForeignKey(related_name='responses', to='micourses.QuestionAttempt'),
        ),
    ]
