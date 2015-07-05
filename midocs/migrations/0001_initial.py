# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import midocs.models
import midocs.storage


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Applet',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('default_inline_caption', models.TextField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('detailed_description', models.TextField(blank=True, null=True)),
                ('applet_file', models.FileField(blank=True, max_length=150, verbose_name='file', storage=midocs.storage.OverwriteStorage(), upload_to=midocs.models.applet_path)),
                ('applet_file2', models.FileField(blank=True, max_length=150, verbose_name='file2 (for double)', storage=midocs.storage.OverwriteStorage(), upload_to=midocs.models.applet_2_path)),
                ('encoded_content', models.TextField(blank=True, null=True)),
                ('notation_specific', models.BooleanField(default=False)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('javascript', models.TextField(blank=True, null=True)),
                ('child_applet_percent_width', models.IntegerField(default=50)),
                ('child_applet_parameters', models.CharField(blank=True, null=True, max_length=400)),
                ('overwrite_thumbnail', models.SmallIntegerField(choices=[(0, "don't overwrite"), (1, 'from image 1'), (2, 'from image 2')], default=1)),
                ('thumbnail', models.ImageField(max_length=150, null=True, storage=midocs.storage.OverwriteStorage(), height_field='thumbnail_height', width_field='thumbnail_width', blank=True, upload_to=midocs.models.applet_thumbnail_path)),
                ('thumbnail_width', models.IntegerField(blank=True, null=True)),
                ('thumbnail_height', models.IntegerField(blank=True, null=True)),
                ('image', models.ImageField(max_length=150, null=True, storage=midocs.storage.OverwriteStorage(), height_field='image_height', width_field='image_width', blank=True, upload_to=midocs.models.applet_image_path)),
                ('image_width', models.IntegerField(blank=True, null=True)),
                ('image_height', models.IntegerField(blank=True, null=True)),
                ('image2', models.ImageField(max_length=150, null=True, storage=midocs.storage.OverwriteStorage(), height_field='image2_height', width_field='image2_width', blank=True, upload_to=midocs.models.applet_2_image_path)),
                ('image2_width', models.IntegerField(blank=True, null=True)),
                ('image2_height', models.IntegerField(blank=True, null=True)),
                ('author_copyright', models.BooleanField(default=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('iframe', models.BooleanField(default=False)),
                ('additional_credits', models.TextField(blank=True, null=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(blank=True, db_index=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='AppletAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AppletChildObjectLink',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('object_name', models.CharField(max_length=100)),
                ('child_object_name', models.CharField(max_length=100)),
                ('applet_to_child_link', models.BooleanField(default=True)),
                ('child_to_applet_link', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='AppletFeature',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=20, db_index=True)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='AppletNotationSystem',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('applet_file', models.FileField(blank=True, verbose_name='file', storage=midocs.storage.OverwriteStorage(), upload_to=midocs.models.applet_notation_path)),
                ('applet_file2', models.FileField(blank=True, verbose_name='file2 (for double)', storage=midocs.storage.OverwriteStorage(), upload_to=midocs.models.applet_2_notation_path)),
            ],
        ),
        migrations.CreateModel(
            name='AppletObject',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('change_from_javascript', models.BooleanField(default=True)),
                ('capture_changes', models.BooleanField(default=False)),
                ('state_variable', models.BooleanField(default=False)),
                ('related_objects', models.CharField(blank=True, null=True, max_length=200)),
                ('name_for_changes', models.CharField(blank=True, null=True, max_length=100)),
                ('category_for_capture', models.CharField(blank=True, null=True, max_length=100)),
                ('function_input_variable', models.CharField(blank=True, null=True, max_length=1)),
                ('default_value', models.CharField(blank=True, null=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='AppletObjectType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('object_type', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='AppletParameter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('value', models.CharField(blank=True, max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='AppletText',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('default_position', models.CharField(blank=True, null=True, choices=[('top', 'top'), ('bottom', 'bottom')], max_length=6)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AppletType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=20, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
                ('help_text', models.TextField()),
                ('error_string', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='AppletTypeParameter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('parameter_name', models.CharField(max_length=50, db_index=True)),
                ('default_value', models.CharField(blank=True, null=True, max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True)),
                ('first_name', models.CharField(max_length=50, db_index=True)),
                ('middle_name', models.CharField(blank=True, null=True, max_length=50)),
                ('last_name', models.CharField(max_length=50, db_index=True)),
                ('title', models.CharField(blank=True, null=True, max_length=200)),
                ('institution', models.CharField(blank=True, null=True, max_length=200)),
                ('web_address', models.URLField(blank=True, null=True)),
                ('email_address', models.EmailField(blank=True, null=True, max_length=254)),
                ('display_email', models.BooleanField(default=False)),
                ('mi_contributor', models.SmallIntegerField(db_index=True, default=0)),
                ('contribution_summary', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['last_name', 'first_name', 'middle_name'],
            },
        ),
        migrations.CreateModel(
            name='AuxiliaryFile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True)),
                ('description', models.CharField(max_length=400)),
                ('auxiliary_file', models.FileField(blank=True, max_length=150, verbose_name='file', storage=midocs.storage.OverwriteStorage(), upload_to=midocs.models.auxiliary_path)),
            ],
        ),
        migrations.CreateModel(
            name='AuxiliaryFileType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
                ('description', models.CharField(max_length=400)),
                ('heading', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='EquationTag',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField()),
                ('tag', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ExternalLink',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('external_url', models.URLField()),
                ('link_text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('imagefile', models.ImageField(null=True, db_index=True, storage=midocs.storage.OverwriteStorage(), height_field='height', width_field='width', blank=True, upload_to=midocs.models.image_path)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('detailed_description', models.TextField(blank=True, null=True)),
                ('notation_specific', models.BooleanField(default=False)),
                ('thumbnail', models.ImageField(max_length=150, null=True, storage=midocs.storage.OverwriteStorage(), height_field='thumbnail_height', width_field='thumbnail_width', blank=True, upload_to=midocs.models.image_thumbnail_path)),
                ('thumbnail_width', models.IntegerField(blank=True, null=True)),
                ('thumbnail_height', models.IntegerField(blank=True, null=True)),
                ('original_file', models.FileField(blank=True, null=True, storage=midocs.storage.OverwriteStorage(), max_length=150, upload_to=midocs.models.image_source_path)),
                ('author_copyright', models.BooleanField(default=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(blank=True, null=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(blank=True, db_index=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='ImageAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ImageNotationSystem',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('imagefile', models.ImageField(height_field='height', blank=True, width_field='width', db_index=True, upload_to=midocs.models.image_notation_path)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=20, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='IndexEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('indexed_phrase', models.CharField(max_length=100, db_index=True)),
                ('indexed_subphrase', models.CharField(blank=True, null=True, db_index=True, max_length=100)),
                ('page_anchor', models.CharField(blank=True, null=True, max_length=100)),
            ],
            options={
                'verbose_name_plural': 'Index entries',
                'ordering': ['indexed_phrase', 'indexed_subphrase'],
            },
        ),
        migrations.CreateModel(
            name='IndexType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True, max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='NewsAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(blank=True, max_length=400)),
                ('configfile', models.CharField(unique=True, max_length=20)),
                ('detailed_description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('text', models.TextField(blank=True, null=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(blank=True, db_index=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('author_copyright', models.BooleanField(default=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(blank=True, null=True)),
                ('detailed_description', models.TextField(blank=True, null=True)),
                ('header', models.TextField(blank=True, null=True)),
                ('javascript', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['code', 'page_type'],
            },
        ),
        migrations.CreateModel(
            name='PageAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageCitation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField()),
                ('footnote_text', models.TextField(blank=True, null=True)),
                ('reference_number', models.SmallIntegerField()),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='PageNavigation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['relationship_type', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageSimilar',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField()),
                ('title', models.CharField(blank=True, null=True, max_length=400)),
                ('booktitle', models.CharField(blank=True, null=True, max_length=400)),
                ('journal', models.CharField(blank=True, null=True, max_length=200)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('volume', models.IntegerField(blank=True, null=True)),
                ('number', models.IntegerField(blank=True, null=True)),
                ('pages', models.CharField(blank=True, null=True, max_length=20)),
                ('publisher', models.CharField(blank=True, null=True, max_length=100)),
                ('address', models.CharField(blank=True, null=True, max_length=100)),
                ('published_web_address', models.URLField(blank=True, null=True)),
                ('preprint_web_address', models.URLField(blank=True, null=True)),
                ('notes', models.CharField(blank=True, null=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ReferenceAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ReferenceEditor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ReferenceType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=20, db_index=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=50, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('code', models.SlugField(unique=True, max_length=100)),
                ('default_inline_caption', models.TextField(blank=True, null=True)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('detailed_description', models.TextField(blank=True, null=True)),
                ('transcript', models.TextField(blank=True, null=True)),
                ('highlight', models.BooleanField(db_index=True, default=False)),
                ('thumbnail', models.ImageField(max_length=150, null=True, storage=midocs.storage.OverwriteStorage(), height_field='thumbnail_height', width_field='thumbnail_width', blank=True, upload_to=midocs.models.video_thumbnail_path)),
                ('thumbnail_width', models.IntegerField(blank=True, null=True)),
                ('thumbnail_height', models.IntegerField(blank=True, null=True)),
                ('author_copyright', models.BooleanField(default=True)),
                ('hidden', models.BooleanField(db_index=True, default=False)),
                ('additional_credits', models.TextField(blank=True, null=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField(blank=True, db_index=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='VideoAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='VideoParameter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('value', models.CharField(blank=True, max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='VideoQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='VideoType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=20, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='VideoTypeParameter',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('parameter_name', models.CharField(max_length=50, db_index=True)),
                ('default_value', models.CharField(blank=True, null=True, max_length=1000)),
                ('video_type', models.ForeignKey(related_name='valid_parameters', to='midocs.VideoType')),
            ],
        ),
    ]
