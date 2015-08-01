 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0004_auto_20150729_2133'),
        ('micourses', '0002_auto_20150730_1313'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StudentContentCompletion',
            new_name='StudentContentRecord',
        ),
        migrations.RenameModel(
            old_name='StudentContentAttempt',
            new_name='ContentAttempt',
        ),
        migrations.RenameModel(
            old_name='StudentContentAttemptSolutionView',
            new_name='QuestionAttempt',
        ),
        migrations.RenameModel(
            old_name='QuestionStudentAnswer',
            new_name='QuestionResponse',
        ),
        migrations.RemoveField(
            model_name='questionresponse',
            name='user',
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='record',
            field=models.ForeignKey(to='micourses.StudentContentRecord', blank=True, related_name='attempts', null=True),
        ),
        migrations.AlterModelOptions(
            name='questionattempt',
            options={'get_latest_by': 'datetime', 'ordering': ['datetime']},
        ),
        migrations.AlterModelOptions(
            name='questionresponse',
            options={'get_latest_by': 'datetime', 'ordering': ['datetime']},
        ),
        migrations.RenameField(
            model_name='questionresponse',
            old_name='course_content_attempt',
            new_name='content_attempt',
        ),
        migrations.RenameField(
            model_name='questionresponse',
            old_name='identifier_in_answer',
            new_name='identifier_in_response',
        ),
        migrations.RenameField(
            model_name='questionresponse',
            old_name='answer',
            new_name='response',
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='question',
            field=models.ForeignKey(to='mitesting.Question', null=True),
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='seed',
            field=models.CharField(max_length=150, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='questionattempt',
            name='solution_viewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='question_attempt',
            field=models.ForeignKey(related_name='answers', to='micourses.QuestionAttempt', null=True),
        ),
        migrations.AddField(
            model_name='studentattendance',
            name='enrollment',
            field=models.ForeignKey(to='micourses.CourseEnrollment', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='enrollment',
            field=models.ForeignKey(to='micourses.CourseEnrollment', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='final_due_adjustment',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='initial_due_adjustment',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='threadsection',
            name='deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='contentattempt',
            name='invalid',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='course',
            name='active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='content_attempt',
            field=models.ForeignKey(related_name='question_attempts', to='micourses.ContentAttempt'),
        ),

    ]
