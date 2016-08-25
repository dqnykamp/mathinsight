# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import midocs.storage
import midocs.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Applet',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('default_inline_caption', models.TextField(null=True, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('applet_file', models.FileField(storage=midocs.storage.OverwriteStorage(), verbose_name='file', upload_to=midocs.models.applet_path, max_length=150, blank=True)),
                ('applet_file2', models.FileField(storage=midocs.storage.OverwriteStorage(), verbose_name='file2 (for double)', upload_to=midocs.models.applet_2_path, max_length=150, blank=True)),
                ('encoded_content', models.TextField(null=True, blank=True)),
                ('notation_specific', models.BooleanField(default=False)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('javascript', models.TextField(null=True, blank=True)),
                ('child_applet_percent_width', models.IntegerField(default=50)),
                ('child_applet_parameters', models.CharField(null=True, max_length=400, blank=True)),
                ('overwrite_thumbnail', models.SmallIntegerField(choices=[(0, "don't overwrite"), (1, 'from image 1'), (2, 'from image 2')], default=1)),
                ('thumbnail', models.ImageField(upload_to=midocs.models.applet_thumbnail_path, storage=midocs.storage.OverwriteStorage(), blank=True, null=True, height_field='thumbnail_height', max_length=150, width_field='thumbnail_width')),
                ('thumbnail_width', models.IntegerField(null=True, blank=True)),
                ('thumbnail_height', models.IntegerField(null=True, blank=True)),
                ('image', models.ImageField(upload_to=midocs.models.applet_image_path, storage=midocs.storage.OverwriteStorage(), blank=True, null=True, height_field='image_height', max_length=150, width_field='image_width')),
                ('image_width', models.IntegerField(null=True, blank=True)),
                ('image_height', models.IntegerField(null=True, blank=True)),
                ('image2', models.ImageField(upload_to=midocs.models.applet_2_image_path, storage=midocs.storage.OverwriteStorage(), blank=True, null=True, height_field='image2_height', max_length=150, width_field='image2_width')),
                ('image2_width', models.IntegerField(null=True, blank=True)),
                ('image2_height', models.IntegerField(null=True, blank=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('iframe', models.BooleanField(default=False)),
                ('additional_credits', models.TextField(null=True, blank=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(db_index=True, blank=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='AppletAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('copyright_only', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AppletChildObjectLink',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('object_name', models.CharField(max_length=100)),
                ('child_object_name', models.CharField(max_length=100)),
                ('applet_to_child_link', models.BooleanField(default=True)),
                ('child_to_applet_link', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppletFeature',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=20)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='AppletNotationSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('applet_file', models.FileField(verbose_name='file', upload_to=midocs.models.applet_notation_path, storage=midocs.storage.OverwriteStorage(), blank=True)),
                ('applet_file2', models.FileField(verbose_name='file2 (for double)', upload_to=midocs.models.applet_2_notation_path, storage=midocs.storage.OverwriteStorage(), blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppletObject',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('change_from_javascript', models.BooleanField(default=True)),
                ('capture_changes', models.BooleanField(default=False)),
                ('state_variable', models.BooleanField(default=False)),
                ('related_objects', models.CharField(null=True, max_length=200, blank=True)),
                ('name_for_changes', models.CharField(null=True, max_length=100, blank=True)),
                ('category_for_capture', models.CharField(null=True, max_length=100, blank=True)),
                ('function_input_variable', models.CharField(null=True, max_length=1, blank=True)),
                ('default_value', models.CharField(null=True, max_length=50, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppletObjectType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('object_type', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='AppletParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('value', models.CharField(max_length=1000, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppletText',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('default_position', models.CharField(null=True, choices=[('top', 'top'), ('bottom', 'bottom')], max_length=6, blank=True)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AppletType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
                ('help_text', models.TextField()),
                ('error_string', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='AppletTypeParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('parameter_name', models.CharField(db_index=True, max_length=50)),
                ('default_value', models.CharField(null=True, max_length=1000, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True)),
                ('first_name', models.CharField(db_index=True, max_length=50)),
                ('middle_name', models.CharField(null=True, max_length=50, blank=True)),
                ('last_name', models.CharField(db_index=True, max_length=50)),
                ('title', models.CharField(null=True, max_length=200, blank=True)),
                ('institution', models.CharField(null=True, max_length=200, blank=True)),
                ('web_address', models.URLField(null=True, blank=True)),
                ('email_address', models.EmailField(null=True, max_length=254, blank=True)),
                ('display_email', models.BooleanField(default=False)),
                ('mi_contributor', models.SmallIntegerField(db_index=True, default=0)),
                ('contribution_summary', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['last_name', 'first_name', 'middle_name'],
            },
        ),
        migrations.CreateModel(
            name='AuxiliaryFile',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField()),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('auxiliary_file', models.FileField(storage=midocs.storage.OverwriteStorage(), verbose_name='file', upload_to=midocs.models.auxiliary_path, max_length=150, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AuxiliaryFileType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
                ('description', models.CharField(max_length=400)),
                ('heading', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='CopyrightType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(null=True, blank=True)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='EquationTag',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField()),
                ('tag', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ExternalLink',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('external_url', models.URLField()),
                ('link_text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('imagefile', models.ImageField(upload_to=midocs.models.image_path, blank=True, null=True, db_index=True, height_field='height', storage=midocs.storage.OverwriteStorage(), width_field='width')),
                ('height', models.IntegerField(null=True, blank=True)),
                ('width', models.IntegerField(null=True, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('notation_specific', models.BooleanField(default=False)),
                ('thumbnail', models.ImageField(upload_to=midocs.models.image_thumbnail_path, storage=midocs.storage.OverwriteStorage(), blank=True, null=True, height_field='thumbnail_height', max_length=150, width_field='thumbnail_width')),
                ('thumbnail_width', models.IntegerField(null=True, blank=True)),
                ('thumbnail_height', models.IntegerField(null=True, blank=True)),
                ('original_file', models.FileField(upload_to=midocs.models.image_source_path, null=True, max_length=150, blank=True, storage=midocs.storage.OverwriteStorage())),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(null=True, blank=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(db_index=True, blank=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='ImageAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('copyright_only', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ImageNotationSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('imagefile', models.ImageField(upload_to=midocs.models.image_notation_path, db_index=True, height_field='height', blank=True, width_field='width')),
                ('height', models.IntegerField(null=True, blank=True)),
                ('width', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='IndexEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('indexed_phrase', models.CharField(db_index=True, max_length=100)),
                ('indexed_subphrase', models.CharField(null=True, db_index=True, max_length=100, blank=True)),
                ('page_anchor', models.CharField(null=True, max_length=100, blank=True)),
            ],
            options={
                'ordering': ['indexed_phrase', 'indexed_subphrase'],
                'verbose_name_plural': 'Index entries',
            },
        ),
        migrations.CreateModel(
            name='IndexType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='NewsAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('copyright_only', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=400)),
                ('content', models.TextField()),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(blank=True)),
            ],
            options={
                'ordering': ['-date_created'],
            },
        ),
        migrations.CreateModel(
            name='NotationSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(max_length=400, blank=True)),
                ('configfile', models.CharField(unique=True, max_length=20)),
                ('detailed_description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(db_index=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(null=True, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('header', models.TextField(null=True, blank=True)),
                ('javascript', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['code', 'page_type'],
            },
        ),
        migrations.CreateModel(
            name='PageAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('copyright_only', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageCitation',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField()),
                ('footnote_text', models.TextField(null=True, blank=True)),
                ('reference_number', models.SmallIntegerField()),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='PageNavigation',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('navigation_phrase', models.CharField(max_length=100)),
                ('page_anchor', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='PageNavigationSub',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('navigation_subphrase', models.CharField(max_length=100)),
                ('page_anchor', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='PageRelationship',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['relationship_type', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageSimilar',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('score', models.SmallIntegerField()),
                ('background_page', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-score', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField()),
                ('title', models.CharField(null=True, max_length=400, blank=True)),
                ('booktitle', models.CharField(null=True, max_length=400, blank=True)),
                ('journal', models.CharField(null=True, max_length=200, blank=True)),
                ('year', models.IntegerField(null=True, blank=True)),
                ('volume', models.IntegerField(null=True, blank=True)),
                ('number', models.IntegerField(null=True, blank=True)),
                ('pages', models.CharField(null=True, max_length=20, blank=True)),
                ('publisher', models.CharField(null=True, max_length=100, blank=True)),
                ('address', models.CharField(null=True, max_length=100, blank=True)),
                ('published_web_address', models.URLField(null=True, blank=True)),
                ('preprint_web_address', models.URLField(null=True, blank=True)),
                ('notes', models.CharField(null=True, max_length=100, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReferenceAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ReferenceEditor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ReferenceType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('default_inline_caption', models.TextField(null=True, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('transcript', models.TextField(null=True, blank=True)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('thumbnail', models.ImageField(upload_to=midocs.models.video_thumbnail_path, storage=midocs.storage.OverwriteStorage(), blank=True, null=True, height_field='thumbnail_height', max_length=150, width_field='thumbnail_width')),
                ('thumbnail_width', models.IntegerField(null=True, blank=True)),
                ('thumbnail_height', models.IntegerField(null=True, blank=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(null=True, blank=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(db_index=True, blank=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='VideoAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('copyright_only', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='VideoParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('value', models.CharField(max_length=1000, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='VideoQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='VideoType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.CharField(db_index=True, unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='VideoTypeParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('parameter_name', models.CharField(db_index=True, max_length=50)),
                ('default_value', models.CharField(null=True, max_length=1000, blank=True)),
                ('video_type', models.ForeignKey(related_name='valid_parameters', to='midocs.VideoType')),
            ],
        ),
    ]
