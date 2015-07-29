# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionstudentanswer',
            name='assessment',
        ),
        migrations.RemoveField(
            model_name='questionstudentanswer',
            name='assessment_seed',
        ),
        migrations.RenameField(
            model_name='studentcontentattempt',
            old_name='score',
            new_name='score_override',
        ),
        migrations.AddField(
            model_name='studentcontentattempt',
            name='score',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='questionstudentanswer',
            name='answer',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='questionstudentanswer',
            name='course_content_attempt',
            field=models.ForeignKey(to='micourses.StudentContentAttempt'),
        ),
        migrations.AlterField(
            model_name='questionstudentanswer',
            name='identifier_in_answer',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='questionstudentanswer',
            name='question_set',
            field=models.SmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='questionstudentanswer',
            name='seed',
            field=models.CharField(max_length=150),
        ),
        migrations.AddField(
            model_name='studentcontentcompletion',
            name='score',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='studentcontentcompletion',
            name='score_override',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
