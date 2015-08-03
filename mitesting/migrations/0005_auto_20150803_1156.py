# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0004_auto_20150729_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionsetdetail',
            name='question_set',
            field=models.SmallIntegerField(db_index=True),
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='time_limit',
        ),
        migrations.RenameField(
            model_name='questionsetdetail',
            old_name='points',
            new_name='weight',
        ),
        migrations.AlterField(
            model_name='questionsetdetail',
            name='weight',
            field=models.FloatField(default=1),
        ),
    ]
