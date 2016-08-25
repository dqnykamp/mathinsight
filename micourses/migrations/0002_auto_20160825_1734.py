# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('micourses', '0001_initial'),
        ('midocs', '0002_auto_20160825_1734'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('mitesting', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='questionattempt',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='questionassigned',
            name='assessment',
            field=models.ForeignKey(to='micourses.Assessment'),
        ),
        migrations.AddField(
            model_name='questionassigned',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='courseuser',
            name='selected_course_enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, to='micourses.CourseEnrollment'),
        ),
        migrations.AddField(
            model_name='courseuser',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='courseurl',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='courseskipdate',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='coursegradecategory',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='coursegradecategory',
            name='grade_category',
            field=models.ForeignKey(to='micourses.GradeCategory'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='student',
            field=models.ForeignKey(to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='course',
            name='enrolled_students',
            field=models.ManyToManyField(to='micourses.CourseUser', through='micourses.CourseEnrollment', blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='grade_categories',
            field=models.ManyToManyField(to='micourses.GradeCategory', through='micourses.CourseGradeCategory', blank=True),
        ),
        migrations.AddField(
            model_name='contentrecord',
            name='content',
            field=models.ForeignKey(to='micourses.ThreadContent'),
        ),
        migrations.AddField(
            model_name='contentrecord',
            name='enrollment',
            field=models.ForeignKey(null=True, to='micourses.CourseEnrollment'),
        ),
        migrations.AddField(
            model_name='contentattemptquestionset',
            name='content_attempt',
            field=models.ForeignKey(related_name='question_sets', to='micourses.ContentAttempt'),
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='base_attempt',
            field=models.ForeignKey(null=True, related_name='derived_attempts', to='micourses.ContentAttempt'),
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='record',
            field=models.ForeignKey(related_name='attempts', to='micourses.ContentRecord'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='courseuser',
            field=models.ForeignKey(null=True, to='micourses.CourseUser'),
        ),
        migrations.AddField(
            model_name='attendancedate',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='assessmentbackgroundpage',
            name='assessment',
            field=models.ForeignKey(to='micourses.Assessment'),
        ),
        migrations.AddField(
            model_name='assessmentbackgroundpage',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='assessment_type',
            field=models.ForeignKey(to='micourses.AssessmentType'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='background_pages',
            field=models.ManyToManyField(to='midocs.Page', through='micourses.AssessmentBackgroundPage', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='course',
            field=models.ForeignKey(to='micourses.Course'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view',
            field=models.ManyToManyField(to='auth.Group', related_name='assessments_can_view', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view_solution',
            field=models.ManyToManyField(to='auth.Group', related_name='assessments_can_view_solution', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='questions',
            field=models.ManyToManyField(to='mitesting.Question', through='micourses.QuestionAssigned', blank=True),
        ),
        migrations.CreateModel(
            name='CourseWithEnrollment',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Courses with enrollment',
            },
            bases=('micourses.course',),
        ),
        migrations.AlterUniqueTogether(
            name='studentattendance',
            unique_together=set([('enrollment', 'date')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionsetdetail',
            unique_together=set([('assessment', 'question_set')]),
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together=set([('course', 'student')]),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('name', 'semester')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentrecord',
            unique_together=set([('enrollment', 'content')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentattemptquestionset',
            unique_together=set([('content_attempt', 'question_number'), ('content_attempt', 'question_set')]),
        ),
        migrations.AlterUniqueTogether(
            name='assessment',
            unique_together=set([('course', 'code'), ('course', 'name')]),
        ),
    ]
