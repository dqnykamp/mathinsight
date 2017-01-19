# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0006_course_calculate_course_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='name_section_override',
            field=models.TextField(null=True, blank=True),
        ),
    ]
