# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicText',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('contained_in_object_id', models.PositiveIntegerField()),
                ('number', models.IntegerField()),
                ('nodelisttext', models.TextField()),
                ('contained_in_content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dynamictext',
            unique_together=set([('contained_in_content_type', 'contained_in_object_id', 'number')]),
        ),
    ]
