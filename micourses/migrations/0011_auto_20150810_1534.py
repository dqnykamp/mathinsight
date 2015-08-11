# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0010_auto_20150808_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentattemptquestionset',
            name='credit_override',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='questionattempt',
            name='credit',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
