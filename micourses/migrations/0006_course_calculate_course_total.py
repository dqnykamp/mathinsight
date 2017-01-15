# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0005_threadcontent_allow_solution_buttons_in_gradebook'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='calculate_course_total',
            field=models.BooleanField(default=True),
        ),
    ]
