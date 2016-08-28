# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0004_auto_20160826_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='threadcontent',
            name='allow_solution_buttons_in_gradebook',
            field=models.BooleanField(default=True),
        ),
    ]
