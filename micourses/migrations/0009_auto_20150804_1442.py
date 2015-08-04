# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pytz
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0008_auto_20150803_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionattempt',
            name='valid',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='valid',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name='studentcontentrecord',
            name='assigned_adjustment',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='course',
            name='attendance_time_zone',
            field=models.CharField(max_length=50, choices=[(x,x) for x in pytz.common_timezones], default=settings.TIME_ZONE),
        ),
    ]
