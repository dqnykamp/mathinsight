# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import midocs.models


def create_and_assign_copyrights(apps, schema_editor):
    CopyrightType = apps.get_model('midocs', 'CopyrightType')
    Page = apps.get_model('midocs', 'Page')
    Image = apps.get_model('midocs', 'Image')
    Applet = apps.get_model('midocs', 'Applet')
    Video = apps.get_model('midocs', 'Video')

    sa=CopyrightType.objects.create(
	name = "Creative Commons Attribution-Noncommercial-ShareAlike 4.0 License",
        url = "http://creativecommons.org/licenses/by-nc-sa/4.0/",
        default=True
    )
    CopyrightType.objects.create(
	name = "Creative Commons Attribution-Noncommercial 4.0 License",
        url = "http://creativecommons.org/licenses/by-nc/4.0/"
    )

    Page.objects.filter(author_copyright=True).update(copyright_type=sa)
    Page.objects.filter(author_copyright=False).update(copyright_type=None)
    Image.objects.filter(author_copyright=True).update(copyright_type=sa)
    Image.objects.filter(author_copyright=False).update(copyright_type=None)
    Applet.objects.filter(author_copyright=True).update(copyright_type=sa)
    Applet.objects.filter(author_copyright=False).update(copyright_type=None)
    Video.objects.filter(author_copyright=True).update(copyright_type=sa)
    Video.objects.filter(author_copyright=False).update(copyright_type=None)



class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0002_auto_20150718_2203'),
    ]

    operations = [
        migrations.CreateModel(
            name='CopyrightType',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(blank=True, null=True)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='appletauthor',
            name='copyright_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='imageauthor',
            name='copyright_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='newsauthor',
            name='copyright_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pageauthor',
            name='copyright_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='videoauthor',
            name='copyright_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='applet',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, null=True, to='midocs.CopyrightType', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, null=True, to='midocs.CopyrightType', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, null=True, to='midocs.CopyrightType', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, null=True, to='midocs.CopyrightType', blank=True),
        ),

        migrations.RunPython(create_and_assign_copyrights),

        migrations.RemoveField(
            model_name='page',
            name='author_copyright'),
        migrations.RemoveField(
            model_name='image',
            name='author_copyright'),
        migrations.RemoveField(
            model_name='applet',
            name='author_copyright'),
        migrations.RemoveField(
            model_name='video',
            name='author_copyright'),
    ]
