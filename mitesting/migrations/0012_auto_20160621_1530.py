# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0011_auto_20150912_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionansweroption',
            name='answer_type',
            field=models.IntegerField(default=0, choices=[(0, 'Expression'), (1, 'Multiple Choice'), (2, 'Function'), (3, 'Text')]),
        ),
    ]
