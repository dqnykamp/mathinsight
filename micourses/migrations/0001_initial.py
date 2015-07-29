# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mitesting', '0002_auto_20150723_2041'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('date', models.DateField()),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('short_name', models.CharField(blank=True, max_length=50, null=True)),
                ('description', models.CharField(blank=True, max_length=400, null=True)),
                ('semester', models.CharField(blank=True, max_length=50, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('days_of_week', models.CharField(blank=True, max_length=50, null=True)),
                ('track_attendance', models.BooleanField(default=False)),
                ('adjust_due_date_attendance', models.BooleanField(default=False)),
                ('last_attendance_date', models.DateField(blank=True, null=True)),
                ('attendance_end_of_week', models.CharField(max_length=2, default='F')),
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
            name='CourseEnrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('section', models.IntegerField(blank=True, null=True)),
                ('group', models.SlugField(blank=True, max_length=20, null=True)),
                ('date_enrolled', models.DateField()),
                ('withdrew', models.BooleanField(default=False)),
                ('role', models.CharField(max_length=1, default='S', choices=[('S', 'Student'), ('I', 'Instructor')])),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'ordering': ['student'],
            },
        ),
        migrations.CreateModel(
            name='CourseGradeCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('number_count_for_grade', models.IntegerField(blank=True, null=True)),
                ('rescale_factor', models.FloatField(default=1.0)),
                ('sort_order', models.FloatField(blank=True)),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
                'verbose_name_plural': 'Course grade categories',
            },
        ),
        migrations.CreateModel(
            name='CourseSkipDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('date', models.DateField()),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseURLs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('userid', models.CharField(blank=True, max_length=20, null=True)),
                ('selected_course_enrollment', models.ForeignKey(blank=True, null=True, to='micourses.CourseEnrollment')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='GradeCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Grade categories',
            },
        ),
        migrations.CreateModel(
            name='ManualDueDateAdjustment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('initial_due_date', models.DateField()),
                ('final_due_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='QuestionStudentAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('seed', models.CharField(max_length=150)),
                ('question_set', models.SmallIntegerField()),
                ('answer', models.TextField()),
                ('identifier_in_answer', models.CharField(max_length=50)),
                ('credit', models.FloatField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'get_latest_by': 'datetime',
            },
        ),
        migrations.CreateModel(
            name='StudentAttendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('date', models.DateField()),
                ('present', models.FloatField(default=1.0)),
                ('course', models.ForeignKey(to='micourses.Course')),
                ('student', models.ForeignKey(to='micourses.CourseUser')),
            ],
        ),
        migrations.CreateModel(
            name='StudentContentAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('datetime', models.DateTimeField(blank=True)),
                ('score_override', models.FloatField(blank=True, null=True)),
                ('score', models.FloatField()),
                ('seed', models.CharField(blank=True, max_length=150, null=True)),
            ],
            options={
                'ordering': ['datetime'],
                'get_latest_by': 'datetime',
            },
        ),
        migrations.CreateModel(
            name='StudentContentAttemptSolutionView',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('question_set', models.SmallIntegerField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('content_attempt', models.ForeignKey(to='micourses.StudentContentAttempt')),
            ],
        ),
        migrations.CreateModel(
            name='StudentContentCompletion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('complete', models.BooleanField(default=False)),
                ('skip', models.BooleanField(default=False)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('score', models.FloatField()),
                ('score_override', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ThreadContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('object_id', models.PositiveIntegerField()),
                ('substitute_title', models.CharField(blank=True, max_length=200, null=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('assigned_date', models.DateField(blank=True, null=True)),
                ('initial_due_date', models.DateField(blank=True, null=True)),
                ('final_due_date', models.DateField(blank=True, null=True)),
                ('individualize_by_student', models.BooleanField(default=True)),
                ('attempt_aggregation', models.CharField(max_length=3, default='Max', choices=[('Max', 'Maximum'), ('Avg', 'Average'), ('Las', 'Last')])),
                ('optional', models.BooleanField(default=False)),
                ('available_before_assigned', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('course', models.ForeignKey(related_name='thread_contents', to='micourses.Course')),
                ('grade_category', models.ForeignKey(blank=True, null=True, to='micourses.GradeCategory')),
            ],
            options={
                'ordering': ['section', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ThreadSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('sort_order', models.FloatField(blank=True)),
                ('course', models.ForeignKey(blank=True, related_name='thread_sections', null=True, to='micourses.Course')),
                ('parent', models.ForeignKey(blank=True, related_name='child_sections', null=True, to='micourses.ThreadSection')),
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
            field=models.ForeignKey(to='micourses.StudentContentAttempt'),
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
            model_name='coursegradecategory',
            name='grade_category',
            field=models.ForeignKey(to='micourses.GradeCategory'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='enrolled_students',
            field=models.ManyToManyField(blank=True, through='micourses.CourseEnrollment', to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='grade_categories',
            field=models.ManyToManyField(blank=True, through='micourses.CourseGradeCategory', to='micourses.GradeCategory'),
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
