# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0009_auto_20150812_0155'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'permissions': (('administer_question', 'Can administer questions'),)},
        ),
    ]
