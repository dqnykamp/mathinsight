# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NotationSystem'
        db.create_table(u'midocs_notationsystem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('configfile', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('detailed_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['NotationSystem'])

        # Adding model 'EquationTag'
        db.create_table(u'midocs_equationtag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'midocs', ['EquationTag'])

        # Adding model 'Author'
        db.create_table(u'midocs_author', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('institution', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('web_address', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('email_address', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('display_email', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mi_contributor', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
            ('contribution_summary', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Author'])

        # Adding model 'Level'
        db.create_table(u'midocs_level', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'midocs', ['Level'])

        # Adding model 'Objective'
        db.create_table(u'midocs_objective', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['Objective'])

        # Adding model 'Subject'
        db.create_table(u'midocs_subject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal(u'midocs', ['Subject'])

        # Adding model 'Keyword'
        db.create_table(u'midocs_keyword', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal(u'midocs', ['Keyword'])

        # Adding model 'RelationshipType'
        db.create_table(u'midocs_relationshiptype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['RelationshipType'])

        # Adding model 'AuxiliaryFileType'
        db.create_table(u'midocs_auxiliaryfiletype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('heading', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'midocs', ['AuxiliaryFileType'])

        # Adding model 'AuxiliaryFile'
        db.create_table(u'midocs_auxiliaryfile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('file_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.AuxiliaryFileType'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('auxiliary_file', self.gf('django.db.models.fields.files.FileField')(max_length=150, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['AuxiliaryFile'])

        # Adding model 'Page'
        db.create_table(u'midocs_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('level', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['midocs.Level'])),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(db_index=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('highlight', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('worksheet', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('author_copyright', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('additional_credits', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Page'])

        # Adding M2M table for field objectives on 'Page'
        m2m_table_name = db.shorten_name(u'midocs_page_objectives')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False)),
            ('objective', models.ForeignKey(orm[u'midocs.objective'], null=False))
        ))
        db.create_unique(m2m_table_name, ['page_id', 'objective_id'])

        # Adding M2M table for field subjects on 'Page'
        m2m_table_name = db.shorten_name(u'midocs_page_subjects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False)),
            ('subject', models.ForeignKey(orm[u'midocs.subject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['page_id', 'subject_id'])

        # Adding M2M table for field keywords on 'Page'
        m2m_table_name = db.shorten_name(u'midocs_page_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False)),
            ('keyword', models.ForeignKey(orm[u'midocs.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['page_id', 'keyword_id'])

        # Adding M2M table for field notation_systems on 'Page'
        m2m_table_name = db.shorten_name(u'midocs_page_notation_systems')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False)),
            ('notationsystem', models.ForeignKey(orm[u'midocs.notationsystem'], null=False))
        ))
        db.create_unique(m2m_table_name, ['page_id', 'notationsystem_id'])

        # Adding model 'PageAuthor'
        db.create_table(u'midocs_pageauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['PageAuthor'])

        # Adding unique constraint on 'PageAuthor', fields ['page', 'author']
        db.create_unique(u'midocs_pageauthor', ['page_id', 'author_id'])

        # Adding model 'PageRelationship'
        db.create_table(u'midocs_pagerelationship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'relationships', to=orm['midocs.Page'])),
            ('related', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'reverse_relationships', to=orm['midocs.Page'])),
            ('relationship_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.RelationshipType'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['PageRelationship'])

        # Adding unique constraint on 'PageRelationship', fields ['origin', 'related', 'relationship_type']
        db.create_unique(u'midocs_pagerelationship', ['origin_id', 'related_id', 'relationship_type_id'])

        # Adding model 'PageSimilar'
        db.create_table(u'midocs_pagesimilar', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'similar', to=orm['midocs.Page'])),
            ('similar', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'reverse_similar', to=orm['midocs.Page'])),
            ('score', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('background_page', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'midocs', ['PageSimilar'])

        # Adding unique constraint on 'PageSimilar', fields ['origin', 'similar']
        db.create_unique(u'midocs_pagesimilar', ['origin_id', 'similar_id'])

        # Adding model 'PageNavigation'
        db.create_table(u'midocs_pagenavigation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('navigation_phrase', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('page_anchor', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'midocs', ['PageNavigation'])

        # Adding unique constraint on 'PageNavigation', fields ['page', 'navigation_phrase']
        db.create_unique(u'midocs_pagenavigation', ['page_id', 'navigation_phrase'])

        # Adding model 'PageNavigationSub'
        db.create_table(u'midocs_pagenavigationsub', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('navigation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.PageNavigation'])),
            ('navigation_subphrase', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('page_anchor', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'midocs', ['PageNavigationSub'])

        # Adding unique constraint on 'PageNavigationSub', fields ['navigation', 'navigation_subphrase']
        db.create_unique(u'midocs_pagenavigationsub', ['navigation_id', 'navigation_subphrase'])

        # Adding model 'IndexType'
        db.create_table(u'midocs_indextype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['IndexType'])

        # Adding model 'IndexEntry'
        db.create_table(u'midocs_indexentry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('index_type', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name=u'entries', to=orm['midocs.IndexType'])),
            ('indexed_phrase', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('indexed_subphrase', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=100, null=True, blank=True)),
            ('page_anchor', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['IndexEntry'])

        # Adding model 'ImageType'
        db.create_table(u'midocs_imagetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['ImageType'])

        # Adding model 'Image'
        db.create_table(u'midocs_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('imagefile', self.gf('django.db.models.fields.files.ImageField')(max_length=100, db_index=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('detailed_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('notation_specific', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=150, null=True, blank=True)),
            ('thumbnail_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('thumbnail_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('original_file', self.gf('django.db.models.fields.files.FileField')(max_length=150, null=True, blank=True)),
            ('original_file_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.ImageType'], null=True, blank=True)),
            ('author_copyright', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('additional_credits', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(db_index=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Image'])

        # Adding M2M table for field in_pages on 'Image'
        m2m_table_name = db.shorten_name(u'midocs_image_in_pages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm[u'midocs.image'], null=False)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False))
        ))
        db.create_unique(m2m_table_name, ['image_id', 'page_id'])

        # Adding M2M table for field subjects on 'Image'
        m2m_table_name = db.shorten_name(u'midocs_image_subjects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm[u'midocs.image'], null=False)),
            ('subject', models.ForeignKey(orm[u'midocs.subject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['image_id', 'subject_id'])

        # Adding M2M table for field keywords on 'Image'
        m2m_table_name = db.shorten_name(u'midocs_image_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm[u'midocs.image'], null=False)),
            ('keyword', models.ForeignKey(orm[u'midocs.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['image_id', 'keyword_id'])

        # Adding M2M table for field auxiliary_files on 'Image'
        m2m_table_name = db.shorten_name(u'midocs_image_auxiliary_files')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('image', models.ForeignKey(orm[u'midocs.image'], null=False)),
            ('auxiliaryfile', models.ForeignKey(orm[u'midocs.auxiliaryfile'], null=False))
        ))
        db.create_unique(m2m_table_name, ['image_id', 'auxiliaryfile_id'])

        # Adding model 'ImageAuthor'
        db.create_table(u'midocs_imageauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Image'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['ImageAuthor'])

        # Adding unique constraint on 'ImageAuthor', fields ['image', 'author']
        db.create_unique(u'midocs_imageauthor', ['image_id', 'author_id'])

        # Adding model 'ImageNotationSystem'
        db.create_table(u'midocs_imagenotationsystem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Image'])),
            ('notation_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.NotationSystem'])),
            ('imagefile', self.gf('django.db.models.fields.files.ImageField')(db_index=True, max_length=100, blank=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['ImageNotationSystem'])

        # Adding unique constraint on 'ImageNotationSystem', fields ['image', 'notation_system']
        db.create_unique(u'midocs_imagenotationsystem', ['image_id', 'notation_system_id'])

        # Adding model 'AppletType'
        db.create_table(u'midocs_applettype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('help_text', self.gf('django.db.models.fields.TextField')()),
            ('error_string', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'midocs', ['AppletType'])

        # Adding model 'AppletTypeParameter'
        db.create_table(u'midocs_applettypeparameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'valid_parameters', to=orm['midocs.AppletType'])),
            ('parameter_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['AppletTypeParameter'])

        # Adding unique constraint on 'AppletTypeParameter', fields ['applet_type', 'parameter_name']
        db.create_unique(u'midocs_applettypeparameter', ['applet_type_id', 'parameter_name'])

        # Adding model 'AppletFeature'
        db.create_table(u'midocs_appletfeature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['AppletFeature'])

        # Adding model 'AppletObjectType'
        db.create_table(u'midocs_appletobjecttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_type', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'midocs', ['AppletObjectType'])

        # Adding model 'Applet'
        db.create_table(u'midocs_applet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('applet_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.AppletType'])),
            ('default_inline_caption', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('detailed_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('applet_file', self.gf('django.db.models.fields.files.FileField')(max_length=150, blank=True)),
            ('applet_file2', self.gf('django.db.models.fields.files.FileField')(max_length=150, blank=True)),
            ('encoded_content', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('notation_specific', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('highlight', self.gf('django.db.models.fields.BooleanField')(db_index=True)),
            ('javascript', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('child_applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'], null=True, blank=True)),
            ('child_applet_percent_width', self.gf('django.db.models.fields.IntegerField')(default=50)),
            ('child_applet_parameters', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=150, null=True, blank=True)),
            ('thumbnail_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('thumbnail_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=150, null=True, blank=True)),
            ('image_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image2', self.gf('django.db.models.fields.files.ImageField')(max_length=150, null=True, blank=True)),
            ('image2_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image2_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('author_copyright', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(db_index=True)),
            ('additional_credits', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(db_index=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Applet'])

        # Adding M2M table for field in_pages on 'Applet'
        m2m_table_name = db.shorten_name(u'midocs_applet_in_pages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('applet', models.ForeignKey(orm[u'midocs.applet'], null=False)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False))
        ))
        db.create_unique(m2m_table_name, ['applet_id', 'page_id'])

        # Adding M2M table for field subjects on 'Applet'
        m2m_table_name = db.shorten_name(u'midocs_applet_subjects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('applet', models.ForeignKey(orm[u'midocs.applet'], null=False)),
            ('subject', models.ForeignKey(orm[u'midocs.subject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['applet_id', 'subject_id'])

        # Adding M2M table for field keywords on 'Applet'
        m2m_table_name = db.shorten_name(u'midocs_applet_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('applet', models.ForeignKey(orm[u'midocs.applet'], null=False)),
            ('keyword', models.ForeignKey(orm[u'midocs.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['applet_id', 'keyword_id'])

        # Adding M2M table for field features on 'Applet'
        m2m_table_name = db.shorten_name(u'midocs_applet_features')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('applet', models.ForeignKey(orm[u'midocs.applet'], null=False)),
            ('appletfeature', models.ForeignKey(orm[u'midocs.appletfeature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['applet_id', 'appletfeature_id'])

        # Adding model 'AppletParameter'
        db.create_table(u'midocs_appletparameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'])),
            ('parameter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.AppletTypeParameter'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['AppletParameter'])

        # Adding unique constraint on 'AppletParameter', fields ['applet', 'parameter']
        db.create_unique(u'midocs_appletparameter', ['applet_id', 'parameter_id'])

        # Adding model 'AppletObject'
        db.create_table(u'midocs_appletobject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'])),
            ('object_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.AppletObjectType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('change_from_javascript', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('capture_changes', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('state_variable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('related_objects', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('name_for_changes', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('category_for_capture', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['AppletObject'])

        # Adding model 'AppletChildObjectLink'
        db.create_table(u'midocs_appletchildobjectlink', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'])),
            ('object_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('child_object_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('applet_to_child_link', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('child_to_applet_link', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'midocs', ['AppletChildObjectLink'])

        # Adding model 'AppletAuthor'
        db.create_table(u'midocs_appletauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['AppletAuthor'])

        # Adding unique constraint on 'AppletAuthor', fields ['applet', 'author']
        db.create_unique(u'midocs_appletauthor', ['applet_id', 'author_id'])

        # Adding model 'AppletNotationSystem'
        db.create_table(u'midocs_appletnotationsystem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'])),
            ('notation_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.NotationSystem'])),
            ('applet_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('applet_file2', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['AppletNotationSystem'])

        # Adding unique constraint on 'AppletNotationSystem', fields ['applet', 'notation_system']
        db.create_unique(u'midocs_appletnotationsystem', ['applet_id', 'notation_system_id'])

        # Adding model 'VideoType'
        db.create_table(u'midocs_videotype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
        ))
        db.send_create_signal(u'midocs', ['VideoType'])

        # Adding model 'VideoTypeParameter'
        db.create_table(u'midocs_videotypeparameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'valid_parameters', to=orm['midocs.VideoType'])),
            ('parameter_name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['VideoTypeParameter'])

        # Adding unique constraint on 'VideoTypeParameter', fields ['video_type', 'parameter_name']
        db.create_unique(u'midocs_videotypeparameter', ['video_type_id', 'parameter_name'])

        # Adding model 'Video'
        db.create_table(u'midocs_video', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('video_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.VideoType'])),
            ('default_inline_caption', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('detailed_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('transcript', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('associated_applet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Applet'], null=True, blank=True)),
            ('highlight', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=150, null=True, blank=True)),
            ('thumbnail_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('thumbnail_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('author_copyright', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('additional_credits', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(db_index=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Video'])

        # Adding M2M table for field in_pages on 'Video'
        m2m_table_name = db.shorten_name(u'midocs_video_in_pages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('video', models.ForeignKey(orm[u'midocs.video'], null=False)),
            ('page', models.ForeignKey(orm[u'midocs.page'], null=False))
        ))
        db.create_unique(m2m_table_name, ['video_id', 'page_id'])

        # Adding M2M table for field subjects on 'Video'
        m2m_table_name = db.shorten_name(u'midocs_video_subjects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('video', models.ForeignKey(orm[u'midocs.video'], null=False)),
            ('subject', models.ForeignKey(orm[u'midocs.subject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['video_id', 'subject_id'])

        # Adding M2M table for field keywords on 'Video'
        m2m_table_name = db.shorten_name(u'midocs_video_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('video', models.ForeignKey(orm[u'midocs.video'], null=False)),
            ('keyword', models.ForeignKey(orm[u'midocs.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['video_id', 'keyword_id'])

        # Adding model 'VideoParameter'
        db.create_table(u'midocs_videoparameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Video'])),
            ('parameter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.VideoTypeParameter'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['VideoParameter'])

        # Adding unique constraint on 'VideoParameter', fields ['video', 'parameter']
        db.create_unique(u'midocs_videoparameter', ['video_id', 'parameter_id'])

        # Adding model 'VideoQuestion'
        db.create_table(u'midocs_videoquestion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Video'])),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['VideoQuestion'])

        # Adding unique constraint on 'VideoQuestion', fields ['video', 'question']
        db.create_unique(u'midocs_videoquestion', ['video_id', 'question_id'])

        # Adding model 'VideoAuthor'
        db.create_table(u'midocs_videoauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Video'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['VideoAuthor'])

        # Adding unique constraint on 'VideoAuthor', fields ['video', 'author']
        db.create_unique(u'midocs_videoauthor', ['video_id', 'author_id'])

        # Adding model 'NewsItem'
        db.create_table(u'midocs_newsitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(blank=True)),
        ))
        db.send_create_signal(u'midocs', ['NewsItem'])

        # Adding model 'NewsAuthor'
        db.create_table(u'midocs_newsauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('newsitem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.NewsItem'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['NewsAuthor'])

        # Adding unique constraint on 'NewsAuthor', fields ['newsitem', 'author']
        db.create_unique(u'midocs_newsauthor', ['newsitem_id', 'author_id'])

        # Adding model 'ExternalLink'
        db.create_table(u'midocs_externallink', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('external_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('in_page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'], null=True, blank=True)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'midocs', ['ExternalLink'])

        # Adding model 'ReferenceType'
        db.create_table(u'midocs_referencetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'midocs', ['ReferenceType'])

        # Adding model 'Reference'
        db.create_table(u'midocs_reference', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('reference_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.ReferenceType'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('booktitle', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('journal', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('volume', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('published_web_address', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('preprint_web_address', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'midocs', ['Reference'])

        # Adding model 'ReferenceAuthor'
        db.create_table(u'midocs_referenceauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Reference'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['ReferenceAuthor'])

        # Adding unique constraint on 'ReferenceAuthor', fields ['reference', 'author']
        db.create_unique(u'midocs_referenceauthor', ['reference_id', 'author_id'])

        # Adding model 'ReferenceEditor'
        db.create_table(u'midocs_referenceeditor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Reference'])),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'midocs', ['ReferenceEditor'])

        # Adding unique constraint on 'ReferenceEditor', fields ['reference', 'editor']
        db.create_unique(u'midocs_referenceeditor', ['reference_id', 'editor_id'])

        # Adding model 'PageCitation'
        db.create_table(u'midocs_pagecitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Reference'], null=True, blank=True)),
            ('footnote_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('reference_number', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'midocs', ['PageCitation'])

        # Adding unique constraint on 'PageCitation', fields ['page', 'code']
        db.create_unique(u'midocs_pagecitation', ['page_id', 'code'])


    def backwards(self, orm):
        # Removing unique constraint on 'PageCitation', fields ['page', 'code']
        db.delete_unique(u'midocs_pagecitation', ['page_id', 'code'])

        # Removing unique constraint on 'ReferenceEditor', fields ['reference', 'editor']
        db.delete_unique(u'midocs_referenceeditor', ['reference_id', 'editor_id'])

        # Removing unique constraint on 'ReferenceAuthor', fields ['reference', 'author']
        db.delete_unique(u'midocs_referenceauthor', ['reference_id', 'author_id'])

        # Removing unique constraint on 'NewsAuthor', fields ['newsitem', 'author']
        db.delete_unique(u'midocs_newsauthor', ['newsitem_id', 'author_id'])

        # Removing unique constraint on 'VideoAuthor', fields ['video', 'author']
        db.delete_unique(u'midocs_videoauthor', ['video_id', 'author_id'])

        # Removing unique constraint on 'VideoQuestion', fields ['video', 'question']
        db.delete_unique(u'midocs_videoquestion', ['video_id', 'question_id'])

        # Removing unique constraint on 'VideoParameter', fields ['video', 'parameter']
        db.delete_unique(u'midocs_videoparameter', ['video_id', 'parameter_id'])

        # Removing unique constraint on 'VideoTypeParameter', fields ['video_type', 'parameter_name']
        db.delete_unique(u'midocs_videotypeparameter', ['video_type_id', 'parameter_name'])

        # Removing unique constraint on 'AppletNotationSystem', fields ['applet', 'notation_system']
        db.delete_unique(u'midocs_appletnotationsystem', ['applet_id', 'notation_system_id'])

        # Removing unique constraint on 'AppletAuthor', fields ['applet', 'author']
        db.delete_unique(u'midocs_appletauthor', ['applet_id', 'author_id'])

        # Removing unique constraint on 'AppletParameter', fields ['applet', 'parameter']
        db.delete_unique(u'midocs_appletparameter', ['applet_id', 'parameter_id'])

        # Removing unique constraint on 'AppletTypeParameter', fields ['applet_type', 'parameter_name']
        db.delete_unique(u'midocs_applettypeparameter', ['applet_type_id', 'parameter_name'])

        # Removing unique constraint on 'ImageNotationSystem', fields ['image', 'notation_system']
        db.delete_unique(u'midocs_imagenotationsystem', ['image_id', 'notation_system_id'])

        # Removing unique constraint on 'ImageAuthor', fields ['image', 'author']
        db.delete_unique(u'midocs_imageauthor', ['image_id', 'author_id'])

        # Removing unique constraint on 'PageNavigationSub', fields ['navigation', 'navigation_subphrase']
        db.delete_unique(u'midocs_pagenavigationsub', ['navigation_id', 'navigation_subphrase'])

        # Removing unique constraint on 'PageNavigation', fields ['page', 'navigation_phrase']
        db.delete_unique(u'midocs_pagenavigation', ['page_id', 'navigation_phrase'])

        # Removing unique constraint on 'PageSimilar', fields ['origin', 'similar']
        db.delete_unique(u'midocs_pagesimilar', ['origin_id', 'similar_id'])

        # Removing unique constraint on 'PageRelationship', fields ['origin', 'related', 'relationship_type']
        db.delete_unique(u'midocs_pagerelationship', ['origin_id', 'related_id', 'relationship_type_id'])

        # Removing unique constraint on 'PageAuthor', fields ['page', 'author']
        db.delete_unique(u'midocs_pageauthor', ['page_id', 'author_id'])

        # Deleting model 'NotationSystem'
        db.delete_table(u'midocs_notationsystem')

        # Deleting model 'EquationTag'
        db.delete_table(u'midocs_equationtag')

        # Deleting model 'Author'
        db.delete_table(u'midocs_author')

        # Deleting model 'Level'
        db.delete_table(u'midocs_level')

        # Deleting model 'Objective'
        db.delete_table(u'midocs_objective')

        # Deleting model 'Subject'
        db.delete_table(u'midocs_subject')

        # Deleting model 'Keyword'
        db.delete_table(u'midocs_keyword')

        # Deleting model 'RelationshipType'
        db.delete_table(u'midocs_relationshiptype')

        # Deleting model 'AuxiliaryFileType'
        db.delete_table(u'midocs_auxiliaryfiletype')

        # Deleting model 'AuxiliaryFile'
        db.delete_table(u'midocs_auxiliaryfile')

        # Deleting model 'Page'
        db.delete_table(u'midocs_page')

        # Removing M2M table for field objectives on 'Page'
        db.delete_table(db.shorten_name(u'midocs_page_objectives'))

        # Removing M2M table for field subjects on 'Page'
        db.delete_table(db.shorten_name(u'midocs_page_subjects'))

        # Removing M2M table for field keywords on 'Page'
        db.delete_table(db.shorten_name(u'midocs_page_keywords'))

        # Removing M2M table for field notation_systems on 'Page'
        db.delete_table(db.shorten_name(u'midocs_page_notation_systems'))

        # Deleting model 'PageAuthor'
        db.delete_table(u'midocs_pageauthor')

        # Deleting model 'PageRelationship'
        db.delete_table(u'midocs_pagerelationship')

        # Deleting model 'PageSimilar'
        db.delete_table(u'midocs_pagesimilar')

        # Deleting model 'PageNavigation'
        db.delete_table(u'midocs_pagenavigation')

        # Deleting model 'PageNavigationSub'
        db.delete_table(u'midocs_pagenavigationsub')

        # Deleting model 'IndexType'
        db.delete_table(u'midocs_indextype')

        # Deleting model 'IndexEntry'
        db.delete_table(u'midocs_indexentry')

        # Deleting model 'ImageType'
        db.delete_table(u'midocs_imagetype')

        # Deleting model 'Image'
        db.delete_table(u'midocs_image')

        # Removing M2M table for field in_pages on 'Image'
        db.delete_table(db.shorten_name(u'midocs_image_in_pages'))

        # Removing M2M table for field subjects on 'Image'
        db.delete_table(db.shorten_name(u'midocs_image_subjects'))

        # Removing M2M table for field keywords on 'Image'
        db.delete_table(db.shorten_name(u'midocs_image_keywords'))

        # Removing M2M table for field auxiliary_files on 'Image'
        db.delete_table(db.shorten_name(u'midocs_image_auxiliary_files'))

        # Deleting model 'ImageAuthor'
        db.delete_table(u'midocs_imageauthor')

        # Deleting model 'ImageNotationSystem'
        db.delete_table(u'midocs_imagenotationsystem')

        # Deleting model 'AppletType'
        db.delete_table(u'midocs_applettype')

        # Deleting model 'AppletTypeParameter'
        db.delete_table(u'midocs_applettypeparameter')

        # Deleting model 'AppletFeature'
        db.delete_table(u'midocs_appletfeature')

        # Deleting model 'AppletObjectType'
        db.delete_table(u'midocs_appletobjecttype')

        # Deleting model 'Applet'
        db.delete_table(u'midocs_applet')

        # Removing M2M table for field in_pages on 'Applet'
        db.delete_table(db.shorten_name(u'midocs_applet_in_pages'))

        # Removing M2M table for field subjects on 'Applet'
        db.delete_table(db.shorten_name(u'midocs_applet_subjects'))

        # Removing M2M table for field keywords on 'Applet'
        db.delete_table(db.shorten_name(u'midocs_applet_keywords'))

        # Removing M2M table for field features on 'Applet'
        db.delete_table(db.shorten_name(u'midocs_applet_features'))

        # Deleting model 'AppletParameter'
        db.delete_table(u'midocs_appletparameter')

        # Deleting model 'AppletObject'
        db.delete_table(u'midocs_appletobject')

        # Deleting model 'AppletChildObjectLink'
        db.delete_table(u'midocs_appletchildobjectlink')

        # Deleting model 'AppletAuthor'
        db.delete_table(u'midocs_appletauthor')

        # Deleting model 'AppletNotationSystem'
        db.delete_table(u'midocs_appletnotationsystem')

        # Deleting model 'VideoType'
        db.delete_table(u'midocs_videotype')

        # Deleting model 'VideoTypeParameter'
        db.delete_table(u'midocs_videotypeparameter')

        # Deleting model 'Video'
        db.delete_table(u'midocs_video')

        # Removing M2M table for field in_pages on 'Video'
        db.delete_table(db.shorten_name(u'midocs_video_in_pages'))

        # Removing M2M table for field subjects on 'Video'
        db.delete_table(db.shorten_name(u'midocs_video_subjects'))

        # Removing M2M table for field keywords on 'Video'
        db.delete_table(db.shorten_name(u'midocs_video_keywords'))

        # Deleting model 'VideoParameter'
        db.delete_table(u'midocs_videoparameter')

        # Deleting model 'VideoQuestion'
        db.delete_table(u'midocs_videoquestion')

        # Deleting model 'VideoAuthor'
        db.delete_table(u'midocs_videoauthor')

        # Deleting model 'NewsItem'
        db.delete_table(u'midocs_newsitem')

        # Deleting model 'NewsAuthor'
        db.delete_table(u'midocs_newsauthor')

        # Deleting model 'ExternalLink'
        db.delete_table(u'midocs_externallink')

        # Deleting model 'ReferenceType'
        db.delete_table(u'midocs_referencetype')

        # Deleting model 'Reference'
        db.delete_table(u'midocs_reference')

        # Deleting model 'ReferenceAuthor'
        db.delete_table(u'midocs_referenceauthor')

        # Deleting model 'ReferenceEditor'
        db.delete_table(u'midocs_referenceeditor')

        # Deleting model 'PageCitation'
        db.delete_table(u'midocs_pagecitation')


    models = {
        u'midocs.applet': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Applet'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'applet_file': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_file2': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_objects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AppletObjectType']", 'null': 'True', 'through': u"orm['midocs.AppletObject']", 'blank': 'True'}),
            'applet_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletType']"}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.AppletAuthor']", 'symmetrical': 'False'}),
            'child_applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']", 'null': 'True', 'blank': 'True'}),
            'child_applet_parameters': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'child_applet_percent_width': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'default_inline_caption': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'encoded_content': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AppletFeature']", 'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'db_index': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'image2': ('django.db.models.fields.files.ImageField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'image2_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'image2_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'image_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'image_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'in_pages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Page']", 'null': 'True', 'blank': 'True'}),
            'javascript': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'notation_specific': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notation_systems': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.NotationSystem']", 'through': u"orm['midocs.AppletNotationSystem']", 'symmetrical': 'False'}),
            'parameters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AppletTypeParameter']", 'null': 'True', 'through': u"orm['midocs.AppletParameter']", 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'midocs.appletauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'applet', u'author'),)", 'object_name': 'AppletAuthor'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.appletchildobjectlink': {
            'Meta': {'object_name': 'AppletChildObjectLink'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            'applet_to_child_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'child_object_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'child_to_applet_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.appletfeature': {
            'Meta': {'object_name': 'AppletFeature'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.appletnotationsystem': {
            'Meta': {'unique_together': "((u'applet', u'notation_system'),)", 'object_name': 'AppletNotationSystem'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            'applet_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'applet_file2': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notation_system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.NotationSystem']"})
        },
        u'midocs.appletobject': {
            'Meta': {'object_name': 'AppletObject'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            'capture_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'category_for_capture': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'change_from_javascript': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_for_changes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletObjectType']"}),
            'related_objects': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'state_variable': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'midocs.appletobjecttype': {
            'Meta': {'object_name': 'AppletObjectType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'midocs.appletparameter': {
            'Meta': {'unique_together': "((u'applet', u'parameter'),)", 'object_name': 'AppletParameter'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletTypeParameter']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        u'midocs.applettype': {
            'Meta': {'object_name': 'AppletType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'error_string': ('django.db.models.fields.TextField', [], {}),
            'help_text': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.applettypeparameter': {
            'Meta': {'unique_together': "((u'applet_type', u'parameter_name'),)", 'object_name': 'AppletTypeParameter'},
            'applet_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'valid_parameters'", 'to': u"orm['midocs.AppletType']"}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        u'midocs.author': {
            'Meta': {'ordering': "[u'last_name', u'first_name', u'middle_name']", 'object_name': 'Author'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'contribution_summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_address': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'mi_contributor': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'web_address': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'midocs.auxiliaryfile': {
            'Meta': {'object_name': 'AuxiliaryFile'},
            'auxiliary_file': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'file_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AuxiliaryFileType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.auxiliaryfiletype': {
            'Meta': {'object_name': 'AuxiliaryFileType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.equationtag': {
            'Meta': {'object_name': 'EquationTag'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'midocs.externallink': {
            'Meta': {'object_name': 'ExternalLink'},
            'external_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']", 'null': 'True', 'blank': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'midocs.image': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Image'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ImageAuthor']", 'symmetrical': 'False'}),
            'auxiliary_files': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AuxiliaryFile']", 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imagefile': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'db_index': 'True'}),
            'in_pages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Page']", 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'notation_specific': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notation_systems': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.NotationSystem']", 'through': u"orm['midocs.ImageNotationSystem']", 'symmetrical': 'False'}),
            'original_file': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'original_file_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.ImageType']", 'null': 'True', 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        u'midocs.imageauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'image', u'author'),)", 'object_name': 'ImageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Image']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.imagenotationsystem': {
            'Meta': {'unique_together': "((u'image', u'notation_system'),)", 'object_name': 'ImageNotationSystem'},
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Image']"}),
            'imagefile': ('django.db.models.fields.files.ImageField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'notation_system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.NotationSystem']"}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'midocs.imagetype': {
            'Meta': {'object_name': 'ImageType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.indexentry': {
            'Meta': {'ordering': "[u'indexed_phrase', u'indexed_subphrase']", 'object_name': 'IndexEntry'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index_type': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "u'entries'", 'to': u"orm['midocs.IndexType']"}),
            'indexed_phrase': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'indexed_subphrase': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'page_anchor': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'midocs.indextype': {
            'Meta': {'object_name': 'IndexType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.keyword': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Keyword'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.level': {
            'Meta': {'object_name': 'Level'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.newsauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'newsitem', u'author'),)", 'object_name': 'NewsAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsitem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.NewsItem']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.newsitem': {
            'Meta': {'ordering': "[u'-date_created']", 'object_name': 'NewsItem'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.NewsAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'midocs.notationsystem': {
            'Meta': {'object_name': 'NotationSystem'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'configfile': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'midocs.objective': {
            'Meta': {'object_name': 'Objective'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.page': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Page'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.PageAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['midocs.Level']"}),
            'notation_systems': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.NotationSystem']", 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'objectives': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Objective']", 'null': 'True', 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'related_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'pages_related_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageRelationship']", 'to': u"orm['midocs.Page']"}),
            'similar_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'pages_similar_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageSimilar']", 'to': u"orm['midocs.Page']"}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'worksheet': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'midocs.pageauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'page', u'author'),)", 'object_name': 'PageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.pagecitation': {
            'Meta': {'ordering': "[u'id']", 'unique_together': "((u'page', u'code'),)", 'object_name': 'PageCitation'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'footnote_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Reference']", 'null': 'True', 'blank': 'True'}),
            'reference_number': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'midocs.pagenavigation': {
            'Meta': {'ordering': "[u'id']", 'unique_together': "((u'page', u'navigation_phrase'),)", 'object_name': 'PageNavigation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'navigation_phrase': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'page_anchor': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.pagenavigationsub': {
            'Meta': {'ordering': "[u'id']", 'unique_together': "((u'navigation', u'navigation_subphrase'),)", 'object_name': 'PageNavigationSub'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'navigation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.PageNavigation']"}),
            'navigation_subphrase': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'page_anchor': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.pagerelationship': {
            'Meta': {'ordering': "[u'relationship_type', u'sort_order', u'id']", 'unique_together': "((u'origin', u'related', u'relationship_type'),)", 'object_name': 'PageRelationship'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'relationships'", 'to': u"orm['midocs.Page']"}),
            'related': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'reverse_relationships'", 'to': u"orm['midocs.Page']"}),
            'relationship_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.RelationshipType']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.pagesimilar': {
            'Meta': {'ordering': "[u'-score', u'id']", 'unique_together': "((u'origin', u'similar'),)", 'object_name': 'PageSimilar'},
            'background_page': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'similar'", 'to': u"orm['midocs.Page']"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'similar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'reverse_similar'", 'to': u"orm['midocs.Page']"})
        },
        u'midocs.reference': {
            'Meta': {'object_name': 'Reference'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'references_authored'", 'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ReferenceAuthor']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'booktitle': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'editors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'references_edited'", 'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ReferenceEditor']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'journal': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'preprint_web_address': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'published_web_address': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reference_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.ReferenceType']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'volume': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'midocs.referenceauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'reference', u'author'),)", 'object_name': 'ReferenceAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Reference']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.referenceeditor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'reference', u'editor'),)", 'object_name': 'ReferenceEditor'},
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Reference']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.referencetype': {
            'Meta': {'object_name': 'ReferenceType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.relationshiptype': {
            'Meta': {'object_name': 'RelationshipType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.subject': {
            'Meta': {'object_name': 'Subject'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.video': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Video'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'associated_applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']", 'null': 'True', 'blank': 'True'}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.VideoAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'default_inline_caption': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_pages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Page']", 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'parameters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.VideoTypeParameter']", 'null': 'True', 'through': u"orm['midocs.VideoParameter']", 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mitesting.Question']", 'null': 'True', 'through': u"orm['midocs.VideoQuestion']", 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'transcript': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'video_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.VideoType']"})
        },
        u'midocs.videoauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'video', u'author'),)", 'object_name': 'VideoAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videoparameter': {
            'Meta': {'unique_together': "((u'video', u'parameter'),)", 'object_name': 'VideoParameter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.VideoTypeParameter']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videoquestion': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'video', u'question'),)", 'object_name': 'VideoQuestion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videotype': {
            'Meta': {'object_name': 'VideoType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.videotypeparameter': {
            'Meta': {'unique_together': "((u'video_type', u'parameter_name'),)", 'object_name': 'VideoTypeParameter'},
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'video_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'valid_parameters'", 'to': u"orm['midocs.VideoType']"})
        },
        u'mitesting.question': {
            'Meta': {'object_name': 'Question'},
            'allowed_sympy_commands': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mitesting.SympyCommandSet']", 'null': 'True', 'blank': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['mitesting.QuestionAuthor']", 'symmetrical': 'False'}),
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_permission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionPermission']"}),
            'question_spacing': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionSpacing']", 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionType']"}),
            'reference_pages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Page']", 'through': u"orm['mitesting.QuestionReferencePage']", 'symmetrical': 'False'}),
            'show_solution_button_after_attempts': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.questionauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'question', u'author'),)", 'object_name': 'QuestionAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questionpermission': {
            'Meta': {'object_name': 'QuestionPermission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'privacy_level': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacy_level_solution': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mitesting.questionreferencepage': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'question', u'page', u'question_subpart'),)", 'object_name': 'QuestionReferencePage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_subpart': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questionspacing': {
            'Meta': {'ordering': "[u'sort_order', u'name']", 'object_name': 'QuestionSpacing'},
            'css_code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questiontype': {
            'Meta': {'object_name': 'QuestionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'mitesting.sympycommandset': {
            'Meta': {'object_name': 'SympyCommandSet'},
            'commands': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['midocs']