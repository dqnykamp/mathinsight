# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0002_auto_20150719_1624'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='thread',
        ),
        migrations.RemoveField(
            model_name='threadcontent',
            name='thread_content',
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='object_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='threadcontent',
            name='section',
            field=models.ForeignKey(to='micourses.ThreadSection', related_name='thread_contents'),
        ),
    ]
