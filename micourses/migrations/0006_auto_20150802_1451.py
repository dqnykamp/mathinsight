# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0005_auto_20150801_2006'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='manualduedateadjustment',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='manualduedateadjustment',
            name='content',
        ),
        migrations.RemoveField(
            model_name='manualduedateadjustment',
            name='student',
        ),
        migrations.RemoveField(
            model_name='contentattempt',
            name='content',
        ),
        migrations.RemoveField(
            model_name='contentattempt',
            name='student',
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
            model_name='contentattempt',
            name='record',
            field=models.ForeignKey(related_name='attempts', to='micourses.StudentContentRecord'),
        ),
        migrations.AlterField(
            model_name='questionresponse',
            name='question_attempt',
            field=models.ForeignKey(related_name='answers', to='micourses.QuestionAttempt'),
        ),
        migrations.AlterField(
            model_name='studentattendance',
            name='enrollment',
            field=models.ForeignKey(to='micourses.CourseEnrollment'),
        ),
        migrations.AlterField(
            model_name='studentcontentrecord',
            name='enrollment',
            field=models.ForeignKey(to='micourses.CourseEnrollment'),
        ),
        migrations.AlterUniqueTogether(
            name='studentattendance',
            unique_together=set([('enrollment', 'date')]),
        ),
        migrations.AlterUniqueTogether(
            name='studentcontentrecord',
            unique_together=set([('enrollment', 'content')]),
        ),
        migrations.DeleteModel(
            name='ManualDueDateAdjustment',
        ),
        migrations.RemoveField(
            model_name='studentattendance',
            name='course',
        ),
        migrations.RemoveField(
            model_name='studentattendance',
            name='student',
        ),
        migrations.RemoveField(
            model_name='studentcontentrecord',
            name='student',
        ),
    ]
