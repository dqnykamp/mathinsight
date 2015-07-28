# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('mitesting', '0002_auto_20150723_2041'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentCategory',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Assessment categories',
            },
        ),
        migrations.CreateModel(
            name='AttendanceDate',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('date', models.DateField()),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('short_name', models.CharField(null=True, max_length=50, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('semester', models.CharField(null=True, max_length=50, blank=True)),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('days_of_week', models.CharField(null=True, max_length=50, blank=True)),
                ('track_attendance', models.BooleanField(default=False)),
                ('adjust_due_date_attendance', models.BooleanField(default=False)),
                ('last_attendance_date', models.DateField(null=True, blank=True)),
                ('attendance_end_of_week', models.CharField(default='F', max_length=2)),
                ('attendance_threshold_percent', models.SmallIntegerField(default=75)),
                ('numbered', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CourseAssessmentCategory',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('number_count_for_grade', models.IntegerField(null=True, blank=True)),
                ('rescale_factor', models.FloatField(default=1.0)),
                ('sort_order', models.FloatField(blank=True)),
                ('assessment_category', models.ForeignKey(to='micourses.AssessmentCategory')),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'verbose_name_plural': 'Course assessment categories',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('section', models.IntegerField(null=True, blank=True)),
                ('group', models.SlugField(null=True, blank=True, max_length=20)),
                ('date_enrolled', models.DateField()),
                ('withdrew', models.BooleanField(default=False)),
                ('role', models.CharField(default='S', max_length=1, choices=[('S', 'Student'), ('I', 'Instructor')])),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'ordering': ['student'],
            },
        ),
        migrations.CreateModel(
            name='CourseSkipDate',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('date', models.DateField()),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseURLs',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseUser',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('userid', models.CharField(null=True, max_length=20, blank=True)),
                ('selected_course_enrollment', models.ForeignKey(null=True, blank=True, to='micourses.CourseEnrollment')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='ManualDueDateAdjustment',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('initial_due_date', models.DateField()),
                ('final_due_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='QuestionStudentAnswer',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('seed', models.CharField(null=True, max_length=150, blank=True)),
                ('question_set', models.SmallIntegerField(null=True, blank=True)),
                ('answer', models.TextField(null=True, blank=True)),
                ('identifier_in_answer', models.CharField(null=True, max_length=50, blank=True)),
                ('credit', models.FloatField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('assessment_seed', models.CharField(null=True, max_length=150, blank=True)),
                ('assessment', models.ForeignKey(null=True, blank=True, to='mitesting.Assessment')),
            ],
            options={
                'get_latest_by': 'datetime',
            },
        ),
        migrations.CreateModel(
            name='StudentAttendance',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('date', models.DateField()),
                ('present', models.FloatField(default=1.0)),
                ('course', models.ForeignKey(to='micourses.Course')),
                ('student', models.ForeignKey(to='micourses.CourseUser')),
            ],
        ),
        migrations.CreateModel(
            name='StudentContentAttempt',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('datetime', models.DateTimeField(blank=True)),
                ('score', models.FloatField(null=True, blank=True)),
                ('seed', models.CharField(null=True, max_length=150, blank=True)),
            ],
            options={
                'get_latest_by': 'datetime',
                'ordering': ['datetime'],
            },
        ),
        migrations.CreateModel(
            name='StudentContentAttemptSolutionView',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('question_set', models.SmallIntegerField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('content_attempt', models.ForeignKey(to='micourses.StudentContentAttempt')),
            ],
        ),
        migrations.CreateModel(
            name='StudentContentCompletion',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('complete', models.BooleanField(default=False)),
                ('skip', models.BooleanField(default=False)),
                ('datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ThreadContent',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('substitute_title', models.CharField(null=True, max_length=200, blank=True)),
                ('instructions', models.TextField(null=True, blank=True)),
                ('assigned_date', models.DateField(null=True, blank=True)),
                ('initial_due_date', models.DateField(null=True, blank=True)),
                ('final_due_date', models.DateField(null=True, blank=True)),
                ('individualize_by_student', models.BooleanField(default=True)),
                ('attempt_aggregation', models.CharField(default='Max', max_length=3, choices=[('Max', 'Maximum'), ('Avg', 'Average'), ('Las', 'Last')])),
                ('optional', models.BooleanField(default=False)),
                ('available_before_assigned', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('assessment_category', models.ForeignKey(null=True, blank=True, to='micourses.AssessmentCategory')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('course', models.ForeignKey(related_name='thread_contents', to='micourses.Course')),
            ],
            options={
                'ordering': ['section', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ThreadSection',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('sort_order', models.FloatField(blank=True)),
                ('course', models.ForeignKey(null=True, related_name='thread_sections', blank=True, to='micourses.Course')),
                ('parent', models.ForeignKey(null=True, related_name='child_sections', blank=True, to='micourses.ThreadSection')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='section',
            field=models.ForeignKey(related_name='thread_contents', to='micourses.ThreadSection'),
        ),
        migrations.AddField(
            model_name='studentcontentcompletion',
            name='content',
            field=models.ForeignKey(to='micourses.ThreadContent'),
        ),
        migrations.AddField(
            model_name='studentcontentcompletion',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='studentcontentattempt',
            name='content',
            field=models.ForeignKey(to='micourses.ThreadContent'),
        ),
        migrations.AddField(
            model_name='studentcontentattempt',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='questionstudentanswer',
            name='course_content_attempt',
            field=models.ForeignKey(null=True, blank=True, to='micourses.StudentContentAttempt'),
        ),
        migrations.AddField(
            model_name='questionstudentanswer',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='questionstudentanswer',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='manualduedateadjustment',
            name='content',
            field=models.ForeignKey(to='micourses.ThreadContent'),
        ),
        migrations.AddField(
            model_name='manualduedateadjustment',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='assessment_categories',
            field=models.ManyToManyField(through='micourses.CourseAssessmentCategory', to='micourses.AssessmentCategory', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='enrolled_students',
            field=models.ManyToManyField(through='micourses.CourseEnrollment', to='micourses.CourseUser', blank=True),
        ),
        migrations.AddField(
            model_name='attendancedate',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AlterUniqueTogether(
            name='studentcontentcompletion',
            unique_together=set([('student', 'content')]),
        ),
        migrations.AlterUniqueTogether(
            name='studentattendance',
            unique_together=set([('course', 'student', 'date')]),
        ),
        migrations.AlterUniqueTogether(
            name='manualduedateadjustment',
            unique_together=set([('content', 'student')]),
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together=set([('course', 'student')]),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('name', 'semester')]),
        ),
    ]
