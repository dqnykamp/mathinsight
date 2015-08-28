# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0016_auto_20150827_1137'),
    ]

    operations = [
        migrations.AddField(
            model_name='threadcontent',
            name='comment',
            field=models.CharField(default='', max_length=100, blank=True),
        ),
    ]
