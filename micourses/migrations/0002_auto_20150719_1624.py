# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('micourses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseURLs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='ThreadSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.RenameModel(
            old_name='CourseThreadContent', 
            new_name='ThreadContent'
        ),
        migrations.DeleteModel(
            name='CourseWithAssessmentThreadContent',
        ),
        migrations.DeleteModel(
            name='CourseWithThreadContent',
        ),
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ['sort_order', 'id']},
        ),
        migrations.AlterModelOptions(
            name='threadcontent',
            options={'ordering': ['section', 'sort_order', 'id']},
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='record_scores',
            new_name='available_before_assigned',
        ),
        migrations.AddField(
            model_name='course',
            name='numbered',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='course',
            name='sort_order',
            field=models.FloatField(blank=True, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='object_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='substitute_title',
            field=models.CharField(blank=True, null=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='course',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='description',
            field=models.CharField(blank=True, null=True, max_length=400),
        ),
        migrations.AlterField(
            model_name='course',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='course',
            name='semester',
            field=models.CharField(blank=True, null=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='course',
            name='short_name',
            field=models.CharField(blank=True, null=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='course',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='thread',
            field=models.ForeignKey(blank=True, to='mithreads.Thread', null=True),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='thread_content',
            field=models.ForeignKey(blank=True, to='mithreads.ThreadContent', null=True),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='course',
            field=models.ForeignKey(related_name='thread_contents', to='micourses.Course'),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('name', 'semester')]),
        ),
        migrations.AlterUniqueTogether(
            name='threadcontent',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='threadsection',
            name='course',
            field=models.ForeignKey(blank=True, to='micourses.Course', null=True, related_name='thread_sections'),
        ),
        migrations.AddField(
            model_name='threadsection',
            name='parent',
            field=models.ForeignKey(blank=True, to='micourses.ThreadSection', null=True, related_name='child_sections'),
        ),
        migrations.AddField(
            model_name='courseurls',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.RemoveField(
            model_name='course',
            name='instructor_url',
        ),
        migrations.RemoveField(
            model_name='course',
            name='syllabus_url',
        ),
        migrations.RemoveField(
            model_name='course',
            name='tutoring_url',
        ),
        migrations.RemoveField(
            model_name='threadcontent',
            name='max_number_attempts',
        ),
        migrations.RemoveField(
            model_name='threadcontent',
            name='required_for_grade',
        ),
        migrations.RemoveField(
            model_name='threadcontent',
            name='required_to_pass',
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='section',
            field=models.ForeignKey(to='micourses.ThreadSection', null=True, related_name='thread_contents'),
        ),
        migrations.DeleteModel(
            name='GradeLevel',
        ),
    ]
