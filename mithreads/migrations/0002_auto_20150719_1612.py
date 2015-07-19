# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mithreads', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='threadcontent',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='threadcontent_original', default=19),
        ),
    ]
