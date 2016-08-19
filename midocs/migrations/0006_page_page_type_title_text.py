# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0005_auto_20151031_2249'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='page_type_title_text',
            field=models.CharField(max_length=200, default=''),
        ),
    ]
