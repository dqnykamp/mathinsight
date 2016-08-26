# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def copy_detailed_description_to_thread_content(apps, schema_editor):

    Assessment = apps.get_model('micourses', 'Assessment')
    ThreadContent = apps.get_model('micourses', 'ThreadContent')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    assessment_ct = ContentType.objects.get_for_model(Assessment)

    for assessment in Assessment.objects.all():
        for tc in ThreadContent.objects.filter(object_id=assessment.id, 
                                               content_type=assessment_ct):

            tc.detailed_description = assessment.detailed_description
            tc.save()

def copy_detailed_description_to_assessment(apps, schema_editor):

    Assessment = apps.get_model('micourses', 'Assessment')
    ThreadContent = apps.get_model('micourses', 'ThreadContent')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    assessment_ct = ContentType.objects.get_for_model(Assessment)

    for assessment in Assessment.objects.all():
        for tc in ThreadContent.objects.filter(object_id=assessment.id, 
                                               content_type=assessment_ct):
            
            if tc.detailed_description:
                assessment.detailed_description = tc.detailed_description
                assessment.save()
                break


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0003_auto_20160624_1336'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assessment',
            old_name='instructions',
            new_name='front_matter',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='instructions2',
            new_name='front_matter2',
        ),
        migrations.RenameField(
            model_name='threadcontent',
            old_name='instructions',
            new_name='detailed_description',
        ),
        migrations.RunPython(copy_detailed_description_to_thread_content,
                        reverse_code=copy_detailed_description_to_assessment),
        migrations.RemoveField(
            model_name='assessment',
            name='detailed_description',
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='time_limit',
            field=models.DurationField(null=True, verbose_name='time limit (hh:mm:ss)', blank=True),
        ),
    ]
