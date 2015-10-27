# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0003_auto_20151026_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='slides',
            field=models.ForeignKey(to='midocs.Page', blank=True, null=True),
        ),
    ]
