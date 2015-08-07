# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0006_auto_20150802_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionresponse',
            name='question_attempt',
            field=models.ForeignKey(related_name='responses', to='micourses.QuestionAttempt', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='contentattemptquestionset',
            unique_together=set([('content_attempt', 'question_set'), ('content_attempt', 'question_number')]),
        ),
    ]
