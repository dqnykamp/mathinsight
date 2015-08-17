# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations




class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0008_auto_20150811_2300'),
        ('midocs', '0002_auto_20150718_2203'),
        ('auth', '0006_require_contenttypes_0002'),
        ('micourses', '0012_auto_20150811_1326'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.SlugField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=30, blank=True, null=True)),
                ('description', models.CharField(max_length=400, blank=True, null=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('instructions', models.TextField(null=True, blank=True)),
                ('instructions2', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('allow_solution_buttons', models.BooleanField(default=True)),
                ('fixed_order', models.BooleanField(default=False)),
                ('single_version', models.BooleanField(default=False)),
                ('resample_question_sets', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['code'],
                'permissions': (('administer_assessment', 'Can administer assessments'),),
            },
        ),
        migrations.CreateModel(
            name='AssessmentBackgroundPage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('sort_order', models.FloatField(blank=True)),
                ('assessment', models.ForeignKey(to='micourses.Assessment')),
                ('page', models.ForeignKey(to='midocs.Page')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('assessment_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('solution_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('template_base_name', models.CharField(max_length=50, blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionAssigned',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('question_set', models.SmallIntegerField(blank=True)),
                ('assessment', models.ForeignKey(to='micourses.Assessment')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['question_set', 'id'],
                'verbose_name_plural': 'Questions assigned',
            },
        ),
        migrations.CreateModel(
            name='QuestionSetDetail',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('question_set', models.SmallIntegerField(db_index=True)),
                ('weight', models.FloatField(default=1)),
                ('group', models.CharField(max_length=50, blank=True, default='')),
                ('assessment', models.ForeignKey(to='micourses.Assessment')),
            ],
        ),
        migrations.AddField(
            model_name='assessment',
            name='assessment_type',
            field=models.ForeignKey(to='micourses.AssessmentType'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='background_pages',
            field=models.ManyToManyField(through='micourses.AssessmentBackgroundPage', to='midocs.Page', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view',
            field=models.ManyToManyField(related_name='assessments_can_view', to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view_solution',
            field=models.ManyToManyField(related_name='assessments_can_view_solution', to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='questions',
            field=models.ManyToManyField(through='micourses.QuestionAssigned', to='mitesting.Question', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='questionsetdetail',
            unique_together=set([('assessment', 'question_set')]),
        ),
        migrations.AlterUniqueTogether(
            name='assessment',
            unique_together=set([('course', 'name'), ('course', 'code')]),
        ),
    ]
