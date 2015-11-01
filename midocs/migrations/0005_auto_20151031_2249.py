# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0004_video_slides'),
    ]

    operations = [
        migrations.AddField(
            model_name='auxiliaryfile',
            name='detailed_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='auxiliaryfile',
            name='code',
            field=models.SlugField(),
        ),
        migrations.AlterField(
            model_name='auxiliaryfile',
            name='description',
            field=models.CharField(max_length=400, blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='auxiliaryfile',
            unique_together=set([('code', 'file_type')]),
        ),
    ]
