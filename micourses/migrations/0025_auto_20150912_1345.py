# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0024_auto_20150905_1942'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollment',
            name='role',
            field=models.CharField(choices=[('A', 'Auditor'), ('S', 'Student'), ('I', 'Instructor'), ('D', 'Designer')], default='S', max_length=1),
        ),
    ]
