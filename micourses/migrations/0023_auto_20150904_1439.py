# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def copy_grade_categories(apps, schema_editor):

    Course = apps.get_model('micourses', 'Course')
    ThreadContent = apps.get_model('micourses', 'ThreadContent')
    
    for course in Course.objects.all():
        for course_grade_category in course.coursegradecategory_set.all():
            course.thread_contents.filter(
                old_grade_category=course_grade_category.grade_category) \
                .update(grade_category=course_grade_category)


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0022_auto_20150904_1208'),
    ]

    operations = [
        migrations.RenameField(
            model_name='threadcontent',
            old_name='grade_category',
            new_name='old_grade_category',
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='grade_category',
            field=models.ForeignKey(to='micourses.CourseGradeCategory', blank=True, null=True),
        ),
        migrations.RunPython(copy_grade_categories),
        migrations.RemoveField(
            model_name='threadcontent',
            name='old_grade_category',
        ),
        

    ]
