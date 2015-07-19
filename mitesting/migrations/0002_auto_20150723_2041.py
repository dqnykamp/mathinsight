# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assessment',
            options={'permissions': (('administer_assessment', 'Can administer assessments'),), 'ordering': ['code']},
        ),
        migrations.AlterField(
            model_name='assessment',
            name='short_name',
            field=models.CharField(null=True, blank=True, max_length=30),
        ),
    ]
