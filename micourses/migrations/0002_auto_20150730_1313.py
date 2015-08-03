# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentcontentattempt',
            name='score',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='studentcontentcompletion',
            name='score',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='record_scores',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentcontentattempt',
            name='valid',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.RemoveField(
            model_name='studentcontentattempt',
            name='datetime',
        ),
        migrations.RenameField(
            model_name='studentcontentattempt',
            old_name='datetime_added',
            new_name='datetime',
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='assigned_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='final_due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='initial_due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='assigned_date',
            new_name='assigned',
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='final_due_date',
            new_name='final_due',
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='initial_due_date',
            new_name='initial_due',
        ),
    ]
