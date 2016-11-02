# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0002_auto_20161024_1946'),
    ]

    operations = [
        migrations.RenameField(
            model_name='questionansweroption',
            old_name='sign_flip_partial_credit',
            new_name='sign_error_partial_credit',
        ),
        migrations.RenameField(
            model_name='questionansweroption',
            old_name='sign_flip_partial_credit_percent',
            new_name='sign_error_partial_credit_percent',
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='constant_term_error_partial_credit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='constant_term_error_partial_credit_percent',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='constant_factor_error_partial_credit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='constant_factor_error_partial_credit_percent',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
