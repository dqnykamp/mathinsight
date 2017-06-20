# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0007_assessment_name_section_override'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='skip_assessment_overview',
            field=models.BooleanField(default=False),
        ),
    ]
