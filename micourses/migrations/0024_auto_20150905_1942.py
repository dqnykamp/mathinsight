# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0023_auto_20150904_1439'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='courseuser',
            options={'ordering': ['user__last_name', 'user__first_name', 'user__username']},
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='comment',
            field=models.CharField(max_length=200, default='', blank=True),
        ),
    ]
