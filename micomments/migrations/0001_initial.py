# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_comments', '0002_update_user_email_field_length'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='MiComment',
            fields=[
                ('comment_ptr', models.OneToOneField(auto_created=True, parent_link=True, primary_key=True, to='django_comments.Comment', serialize=False)),
                ('credit_eligible', models.BooleanField(default=False)),
                ('credit', models.BooleanField(default=False)),
                ('credit_group', models.ForeignKey(null=True, blank=True, to='auth.Group')),
            ],
            options={
                'abstract': False,
            },
            bases=('django_comments.comment',),
        ),
    ]
