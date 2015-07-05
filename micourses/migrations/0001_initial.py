# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mithreads', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Assessment categories',
            },
        ),
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
                ('name', models.CharField(unique=True, max_length=50)),
                ('short_name', models.CharField(max_length=50)),
                ('semester', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=400)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('days_of_week', models.CharField(blank=True, null=True, max_length=50)),
                ('active', models.BooleanField(default=False)),
                ('track_attendance', models.BooleanField(default=False)),
                ('adjust_due_date_attendance', models.BooleanField(default=False)),
                ('last_attendance_date', models.DateField(blank=True, null=True)),
                ('attendance_end_of_week', models.CharField(default='F', max_length=2)),
                ('attendance_threshold_percent', models.SmallIntegerField(default=75)),
                ('syllabus_url', models.URLField(blank=True, null=True)),
                ('instructor_url', models.URLField(blank=True, null=True)),
                ('tutoring_url', models.URLField(blank=True, null=True)),
            ],
            options={
                'ordering': ['start_date', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CourseAssessmentCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('number_count_for_grade', models.IntegerField(blank=True, null=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('section', models.IntegerField(blank=True, null=True)),
                ('group', models.SlugField(max_length=20, null=True, blank=True)),
                ('date_enrolled', models.DateField()),
                ('withdrew', models.BooleanField(default=False)),
                ('role', models.CharField(choices=[('S', 'Student'), ('I', 'Instructor')], max_length=1, default='S')),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'ordering': ['student'],
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
            name='CourseThreadContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('assigned_date', models.DateField(blank=True, null=True)),
                ('initial_due_date', models.DateField(blank=True, null=True)),
                ('final_due_date', models.DateField(blank=True, null=True)),
                ('individualize_by_student', models.BooleanField(default=True)),
                ('required_to_pass', models.BooleanField(default=False)),
                ('max_number_attempts', models.IntegerField(default=1)),
                ('attempt_aggregation', models.CharField(choices=[('Max', 'Maximum'), ('Avg', 'Average'), ('Las', 'Last')], max_length=3, default='Max')),
                ('optional', models.BooleanField(default=False)),
                ('record_scores', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('assessment_category', models.ForeignKey(blank=True, null=True, to='micourses.AssessmentCategory')),
                ('course', models.ForeignKey(to='micourses.Course')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CourseUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('userid', models.CharField(blank=True, null=True, max_length=20)),
                ('selected_course_enrollment', models.ForeignKey(blank=True, null=True, to='micourses.CourseEnrollment')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='GradeLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('grade', models.CharField(unique=True, max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='ManualDueDateAdjustment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('initial_due_date', models.DateField()),
                ('final_due_date', models.DateField()),
                ('content', models.ForeignKey(to='micourses.CourseThreadContent')),
                ('student', models.ForeignKey(to='micourses.CourseUser')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionStudentAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('seed', models.CharField(blank=True, null=True, max_length=150)),
                ('question_set', models.SmallIntegerField(blank=True, null=True)),
                ('answer', models.TextField(blank=True, null=True)),
                ('identifier_in_answer', models.CharField(blank=True, null=True, max_length=50)),
                ('credit', models.FloatField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('assessment_seed', models.CharField(blank=True, null=True, max_length=150)),
                ('assessment', models.ForeignKey(blank=True, null=True, to='mitesting.Assessment')),
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
                ('score', models.FloatField(blank=True, null=True)),
                ('seed', models.CharField(blank=True, null=True, max_length=150)),
                ('content', models.ForeignKey(to='micourses.CourseThreadContent')),
                ('student', models.ForeignKey(to='micourses.CourseUser')),
            ],
            options={
                'get_latest_by': 'datetime',
                'ordering': ['datetime'],
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
                ('content', models.ForeignKey(to='micourses.CourseThreadContent')),
                ('student', models.ForeignKey(to='micourses.CourseUser')),
            ],
        ),
        migrations.AddField(
            model_name='questionstudentanswer',
            name='course_content_attempt',
            field=models.ForeignKey(blank=True, null=True, to='micourses.StudentContentAttempt'),
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
            model_name='coursethreadcontent',
            name='required_for_grade',
            field=models.ForeignKey(blank=True, null=True, to='micourses.GradeLevel'),
        ),
        migrations.AddField(
            model_name='coursethreadcontent',
            name='thread_content',
            field=models.ForeignKey(to='mithreads.ThreadContent'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='assessment_categories',
            field=models.ManyToManyField(blank=True, through='micourses.CourseAssessmentCategory', to='micourses.AssessmentCategory'),
        ),
        migrations.AddField(
            model_name='course',
            name='enrolled_students',
            field=models.ManyToManyField(blank=True, through='micourses.CourseEnrollment', to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='thread',
            field=models.ForeignKey(to='mithreads.Thread'),
        ),
        migrations.AddField(
            model_name='attendancedate',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.CreateModel(
            name='CourseWithAssessmentThreadContent',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Courses with assessment thread content',
            },
            bases=('micourses.course',),
        ),
        migrations.CreateModel(
            name='CourseWithThreadContent',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Courses with thread content',
            },
            bases=('micourses.course',),
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
            name='coursethreadcontent',
            unique_together=set([('thread_content', 'course')]),
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together=set([('course', 'student')]),
        ),
    ]
