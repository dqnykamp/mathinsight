# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0003_auto_20150801_0114'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contentattempt',
            options={'ordering': ['attempt_began'], 'get_latest_by': 'attempt_began'},
        ),
        migrations.AlterModelOptions(
            name='questionattempt',
            options={'ordering': ['attempt_began'], 'get_latest_by': 'attempt_began'},
        ),
        migrations.AlterModelOptions(
            name='questionresponse',
            options={'ordering': ['response_submitted'], 'get_latest_by': 'response_submitted'},
        ),
        migrations.RenameField(
            model_name='contentattempt',
            old_name='datetime',
            new_name='attempt_began',
        ),
        migrations.RenameField(
            model_name='questionattempt',
            old_name='datetime',
            new_name='solution_viewed',
        ),
        migrations.RenameField(
            model_name='questionresponse',
            old_name='datetime',
            new_name='response_submitted',
        ),
        migrations.RenameField(
            model_name='studentcontentrecord',
            old_name='datetime',
            new_name='last_modified',
        ),
        migrations.AlterField(
            model_name='contentattempt',
            name='attempt_began',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='solution_viewed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='attempt_began',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='response_submitted',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, blank=True),
        ),
        migrations.AlterField(
            model_name='studentcontentrecord',
            name='last_modified',
            field=models.DateTimeField(blank=True),
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='content_attempt_question_set',
            field=models.ForeignKey(related_name='question_attempts', to='micourses.ContentAttemptQuestionSet', null=True),
        ),
    ]
