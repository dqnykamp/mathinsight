# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0007_auto_20150806_1155'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('micourses', '0011_auto_20150810_1534'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.CharField(max_length=20, choices=[('change score', 'change score'), ('change date', 'change date'), ('delete', 'delete'), ('create', 'create')])),
                ('field_name', models.CharField(max_length=50, null=True, blank=True)),
                ('old_value', models.CharField(max_length=100, null=True, blank=True)),
                ('new_value', models.CharField(max_length=100, null=True, blank=True)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('courseuser', models.ForeignKey(to='micourses.CourseUser', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseContentAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('begin_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('seed', models.CharField(max_length=150)),
                ('content', models.ForeignKey(to='micourses.ThreadContent')),
            ],
            options={
                'get_latest_by': 'begin_time',
                'ordering': ['begin_time'],
            },
        ),
        migrations.CreateModel(
            name='CourseContentAttemptQuestionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('question_number', models.SmallIntegerField()),
                ('question_set', models.SmallIntegerField()),
                ('content_attempt', models.ForeignKey(to='micourses.CourseContentAttempt', related_name='question_sets')),
            ],
            options={
                'ordering': ['question_number'],
            },
        ),
        migrations.CreateModel(
            name='CourseQuestionAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('seed', models.CharField(max_length=150)),
                ('random_outcomes', models.TextField()),
                ('content_attempt_question_set', models.ForeignKey(to='micourses.CourseContentAttemptQuestionSet', related_name='question_attempts')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='role',
            field=models.CharField(max_length=1, default='S', choices=[('S', 'Student'), ('I', 'Instructor'), ('R', 'Designer')]),
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='derived_from',
            field=models.ForeignKey(to='micourses.CourseContentAttempt', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='coursecontentattemptquestionset',
            unique_together=set([('content_attempt', 'question_number'), ('content_attempt', 'question_set')]),
        ),
    ]
