# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(db_index=True, unique=True, max_length=100)),
                ('description', models.CharField(max_length=400)),
                ('sort_order', models.FloatField(default=0)),
                ('numbered', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ThreadContent',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('sort_order', models.FloatField(default=0)),
                ('substitute_title', models.CharField(null=True, blank=True, max_length=200)),
                ('content_type', models.ForeignKey(default=19, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='ThreadSection',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('code', models.SlugField()),
                ('sort_order', models.FloatField(default=0)),
                ('level', models.IntegerField(default=1)),
                ('thread', models.ForeignKey(related_name='thread_sections', to='mithreads.Thread')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='section',
            field=models.ForeignKey(to='mithreads.ThreadSection'),
        ),
        migrations.AlterUniqueTogether(
            name='threadsection',
            unique_together=set([('code', 'thread')]),
        ),
    ]
