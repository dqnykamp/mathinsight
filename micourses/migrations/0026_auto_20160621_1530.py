# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0025_auto_20150912_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessmenttype',
            name='require_secured_browser',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='browser_exam_keys',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
