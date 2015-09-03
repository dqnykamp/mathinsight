# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0019_auto_20150831_1227'),
    ]

    operations = [
        migrations.RenameModel(
            old_name = 'CourseURLs',
            new_name = 'CourseURL'
        ),
        migrations.AddField(
            model_name = 'courseurl',
            name='sort_order',
            field=models.FloatField(blank=True),
        ),
        migrations.AlterModelOptions(
            name='courseurl',
            options={'ordering': ['sort_order']},
        ),
        migrations.AlterField(
            model_name='changelog',
            name='action',
            field=models.CharField(max_length=20, choices=[('change score', 'change score'), ('change date', 'change date'), ('change', 'change'), ('delete', 'delete'), ('create', 'create')]),
        ),
        migrations.AlterField(
            model_name='studentattendance',
            name='present',
            field=models.SmallIntegerField(default=1),
        ),
    ]
