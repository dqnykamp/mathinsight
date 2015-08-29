# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0017_threadcontent_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contentattempt',
            old_name='version_string',
            new_name='version',
        ),
    ]
