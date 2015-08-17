# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0007_auto_20150806_1155'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('micourses', '0011_auto_20150810_1534'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.CharField(max_length=20, choices=[('change score', 'change score'), ('change date', 'change date'), ('delete', 'delete'), ('create', 'create')])),
                ('field_name', models.CharField(max_length=50, null=True, blank=True)),
                ('old_value', models.CharField(max_length=100, null=True, blank=True)),
                ('new_value', models.CharField(max_length=100, null=True, blank=True)),
                ('time', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('courseuser', models.ForeignKey(to='micourses.CourseUser', null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='role',
            field=models.CharField(max_length=1, choices=[('S', 'Student'), ('I', 'Instructor'), ('R', 'Designer')], default='S'),
        ),
    ]
