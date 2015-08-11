# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0009_auto_20150804_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionattempt',
            name='random_outcomes',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='content_attempt',
            field=models.ForeignKey(related_name='question_attempts', to='micourses.ContentAttempt', null=True),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='question_set',
            field=models.SmallIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='content_attempt',
            field=models.ForeignKey(to='micourses.ContentAttempt', null=True),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='question',
            field=models.ForeignKey(to='mitesting.Question', null=True),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='question_set',
            field=models.SmallIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='seed',
            field=models.CharField(null=True, max_length=150),
        ),
        migrations.RenameField(
            model_name='course',
            old_name='adjust_due_date_attendance',
            new_name='adjust_due_attendance',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='identifier_in_response',
        ),
    ]
