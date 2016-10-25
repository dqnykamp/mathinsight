# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionansweroption',
            name='sign_flip_partial_credit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='sign_flip_partial_credit_percent',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
