# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0003_page_page_type_title_text'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appletobject',
            options={'ordering': ['sort_order', 'id']},
        ),
        migrations.AddField(
            model_name='appletobject',
            name='sort_order',
            field=models.FloatField(default=0, blank=True),
            preserve_default=False,
        ),
    ]
