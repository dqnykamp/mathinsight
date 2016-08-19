# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.core.exceptions import ObjectDoesNotExist


def copy_allow_solutions_buttons(apps, schema_editor):

    Assessment = apps.get_model('micourses', 'Assessment')
    ThreadContent = apps.get_model('micourses', 'ThreadContent')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    assessment_ct = ContentType.objects.get_for_model(Assessment)

    for assessment in Assessment.objects.all():
        for tc in ThreadContent.objects.filter(object_id=assessment.id, 
                                               content_type=assessment_ct):

            tc.allow_solution_buttons = assessment.allow_solution_buttons
            tc.save()


def copy_attempt_began_to_attempt_created(apps, schema_editor):

    ContentAttempt = apps.get_model('micourses', 'ContentAttempt')
    
    for attempt in ContentAttempt.objects.all():
        if attempt.attempt_began:
            attempt.attempt_created=attempt.attempt_began
        else:
            attempt.attempt_created = django.utils.timezone.now()
        attempt.save()

def update_latest_attempt(apps, schema_editor):

    ContentRecord = apps.get_model('micourses', 'ContentRecord')

    for record in ContentRecord.objects.all():
        try:
            record.latest_attempt = record.attempts.latest()
            record.save()
        except ObjectDoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0002_auto_20160825_1734'),
    ]

    operations = [
        migrations.RenameField(
            model_name='threadcontent',
            old_name='attempt_aggregation',
            new_name='assessment_attempt_aggregation',
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='browser_exam_keys',
            field=models.CharField(max_length=400, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='question_attempt_aggregation',
            field=models.CharField(max_length=3, choices=[('Sam', 'Same as Assessment'), ('Max', 'Maximum'), ('Avg', 'Average'), ('Las', 'Last')], default='Sam'),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='require_secured_browser',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='restrict_to_ip_address',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='show_response_correctness',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='allow_solution_buttons',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='access_only_open_attempts',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_allow_solutions_buttons),
        migrations.RemoveField(
            model_name='assessment',
            name='allow_solution_buttons',
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='closed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='time_end_override',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='time_limit',
            field=models.DurationField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='contentattempt',
            name='attempt_began',
            field=models.DateTimeField(null=True, default=django.utils.timezone.now, blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='handwritten',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name='contentattempt',
            options={'get_latest_by': 'attempt_created', 'ordering': ['attempt_created']},
        ),
        migrations.AddField(
            model_name='contentattempt',
            name='attempt_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(copy_attempt_began_to_attempt_created,
                             reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contentattempt',
            name='attempt_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='contentrecord',
            name='latest_attempt',
            field=models.ForeignKey(blank=True, to='micourses.ContentAttempt', null=True),
        ),
        migrations.RunPython(update_latest_attempt,
                             reverse_code=migrations.RunPython.noop),
    ]
