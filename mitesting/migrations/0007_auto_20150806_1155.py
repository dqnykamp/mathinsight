# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def group_none_blank_string(apps, schema_editor):
    QuestionSetDetail = apps.get_model('mitesting', 'QuestionSetDetail')
    QuestionSetDetail.objects.filter(group=None).update(group="")


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0006_auto_20150804_1218'),
    ]

    operations = [
        migrations.RunPython(group_none_blank_string),
        migrations.AlterField(
            model_name='questionsetdetail',
            name='group',
            field=models.CharField(default='', blank=True, max_length=50),
        ),
    ]
