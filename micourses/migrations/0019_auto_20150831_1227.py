# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0018_auto_20150828_1838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='changelog',
            name='field_name',
        ),
        migrations.AlterField(
            model_name='changelog',
            name='new_value',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='changelog',
            name='old_value',
            field=models.TextField(blank=True, null=True),
        ),
    ]
