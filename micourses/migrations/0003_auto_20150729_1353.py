# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0002_auto_20150728_1708'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AssessmentCategory',
            new_name='GradeCategory',
        ),
        migrations.RenameField(
            model_name='courseassessmentcategory',
            old_name='assessment_category',
            new_name='grade_category',
        ),
        migrations.AlterModelOptions(
            name='gradecategory',
            options={'verbose_name_plural': 'Grade categories'},
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='assessment_category',
            new_name='grade_category',
        ),
        migrations.RenameField(
            model_name='course',
            old_name='assessment_categories',
            new_name='grade_categories',
        ),
        migrations.AlterModelOptions(
            name='courseassessmentcategory',
            options={'verbose_name_plural': 'Course grade categories', 'ordering': ['sort_order', 'id']},
        ),
        migrations.AlterField(
            model_name='courseassessmentcategory',
            name='course',
            field=models.ForeignKey(related_name='coursegradecategory_set', to='micourses.Course'),
        ),
    ]
