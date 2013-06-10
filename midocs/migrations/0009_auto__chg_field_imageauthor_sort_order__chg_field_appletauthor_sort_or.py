# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'ImageAuthor.sort_order'
        db.alter_column(u'midocs_imageauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'AppletAuthor.sort_order'
        db.alter_column(u'midocs_appletauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'ReferenceEditor.sort_order'
        db.alter_column(u'midocs_referenceeditor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'PageAuthor.sort_order'
        db.alter_column(u'midocs_pageauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'NewsAuthor.sort_order'
        db.alter_column(u'midocs_newsauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'VideoAuthor.sort_order'
        db.alter_column(u'midocs_videoauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'PageRelationship.sort_order'
        db.alter_column(u'midocs_pagerelationship', 'sort_order', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'ReferenceAuthor.sort_order'
        db.alter_column(u'midocs_referenceauthor', 'sort_order', self.gf('django.db.models.fields.FloatField')())

    def backwards(self, orm):

        # Changing field 'ImageAuthor.sort_order'
        db.alter_column(u'midocs_imageauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'AppletAuthor.sort_order'
        db.alter_column(u'midocs_appletauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'ReferenceEditor.sort_order'
        db.alter_column(u'midocs_referenceeditor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'PageAuthor.sort_order'
        db.alter_column(u'midocs_pageauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'NewsAuthor.sort_order'
        db.alter_column(u'midocs_newsauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'VideoAuthor.sort_order'
        db.alter_column(u'midocs_videoauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'PageRelationship.sort_order'
        db.alter_column(u'midocs_pagerelationship', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'ReferenceAuthor.sort_order'
        db.alter_column(u'midocs_referenceauthor', 'sort_order', self.gf('django.db.models.fields.SmallIntegerField')())

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.applet': {
            'Meta': {'ordering': "['code']", 'object_name': 'Applet'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'applet_file': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_file2': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_objects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AppletObjectType']", 'null': 'True', 'through': u"orm['midocs.AppletObject']", 'blank': 'True'}),
            'applet_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletType']"}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.AppletAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'default_inline_caption': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'encoded_content': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AppletFeature']", 'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
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
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('applet', 'author'),)", 'object_name': 'AppletAuthor'},
            'applet': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Applet']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.appletfeature': {
            'Meta': {'object_name': 'AppletFeature'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.appletnotationsystem': {
            'Meta': {'unique_together': "(('applet', 'notation_system'),)", 'object_name': 'AppletNotationSystem'},
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
            'change_from_javascript': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletObjectType']"}),
            'related_objects': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'midocs.appletobjecttype': {
            'Meta': {'object_name': 'AppletObjectType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'midocs.appletparameter': {
            'Meta': {'unique_together': "(('applet', 'parameter'),)", 'object_name': 'AppletParameter'},
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
            'Meta': {'unique_together': "(('applet_type', 'parameter_name'),)", 'object_name': 'AppletTypeParameter'},
            'applet_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'valid_parameters'", 'to': u"orm['midocs.AppletType']"}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        },
        u'midocs.author': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'Author'},
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
            'Meta': {'ordering': "['code']", 'object_name': 'Image'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ImageAuthor']", 'symmetrical': 'False'}),
            'auxiliary_files': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.AuxiliaryFile']", 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
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
            'width': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        },
        u'midocs.imageauthor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('image', 'author'),)", 'object_name': 'ImageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Image']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.imagenotationsystem': {
            'Meta': {'unique_together': "(('image', 'notation_system'),)", 'object_name': 'ImageNotationSystem'},
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
            'Meta': {'ordering': "['indexed_phrase', 'indexed_subphrase']", 'object_name': 'IndexEntry'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index_type': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'entries'", 'to': u"orm['midocs.IndexType']"}),
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
            'Meta': {'ordering': "['code']", 'object_name': 'Keyword'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.level': {
            'Meta': {'object_name': 'Level'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'midocs.newsauthor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('newsitem', 'author'),)", 'object_name': 'NewsAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsitem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.NewsItem']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.newsitem': {
            'Meta': {'ordering': "['-date_created']", 'object_name': 'NewsItem'},
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
            'Meta': {'ordering': "['code']", 'object_name': 'Page'},
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
            'level': ('django.db.models.fields.related.ForeignKey', [], {'default': "'i'", 'to': u"orm['midocs.Level']"}),
            'notation_systems': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.NotationSystem']", 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'objectives': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Objective']", 'null': 'True', 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'related_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'pages_related_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageRelationship']", 'to': u"orm['midocs.Page']"}),
            'similar_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'pages_similar_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageSimilar']", 'to': u"orm['midocs.Page']"}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'worksheet': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'midocs.pageauthor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('page', 'author'),)", 'object_name': 'PageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.pagecitation': {
            'Meta': {'ordering': "['id']", 'unique_together': "(('page', 'code'),)", 'object_name': 'PageCitation'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'footnote_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Reference']", 'null': 'True', 'blank': 'True'}),
            'reference_number': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'midocs.pagenavigation': {
            'Meta': {'ordering': "['id']", 'unique_together': "(('page', 'navigation_phrase'),)", 'object_name': 'PageNavigation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'navigation_phrase': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'page_anchor': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.pagenavigationsub': {
            'Meta': {'ordering': "['id']", 'unique_together': "(('navigation', 'navigation_subphrase'),)", 'object_name': 'PageNavigationSub'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'navigation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.PageNavigation']"}),
            'navigation_subphrase': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'page_anchor': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'midocs.pagerelationship': {
            'Meta': {'ordering': "['relationship_type', 'sort_order', 'id']", 'unique_together': "(('origin', 'related', 'relationship_type'),)", 'object_name': 'PageRelationship'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relationships'", 'to': u"orm['midocs.Page']"}),
            'related': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverse_relationships'", 'to': u"orm['midocs.Page']"}),
            'relationship_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.RelationshipType']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.pagesimilar': {
            'Meta': {'ordering': "['-score', 'id']", 'unique_together': "(('origin', 'similar'),)", 'object_name': 'PageSimilar'},
            'background_page': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'similar'", 'to': u"orm['midocs.Page']"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'similar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverse_similar'", 'to': u"orm['midocs.Page']"})
        },
        u'midocs.reference': {
            'Meta': {'object_name': 'Reference'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'references_authored'", 'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ReferenceAuthor']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'booktitle': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'editors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'references_edited'", 'to': u"orm['midocs.Author']", 'through': u"orm['midocs.ReferenceEditor']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
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
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('reference', 'author'),)", 'object_name': 'ReferenceAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Reference']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'midocs.referenceeditor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('reference', 'editor'),)", 'object_name': 'ReferenceEditor'},
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
            'Meta': {'ordering': "['code']", 'object_name': 'Video'},
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
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('video', 'author'),)", 'object_name': 'VideoAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videoparameter': {
            'Meta': {'unique_together': "(('video', 'parameter'),)", 'object_name': 'VideoParameter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.VideoTypeParameter']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videoquestion': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('video', 'question'),)", 'object_name': 'VideoQuestion'},
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
            'Meta': {'unique_together': "(('video_type', 'parameter_name'),)", 'object_name': 'VideoTypeParameter'},
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'video_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'valid_parameters'", 'to': u"orm['midocs.VideoType']"})
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
            'show_solution_button_after_attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.questionauthor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('question', 'author'),)", 'object_name': 'QuestionAuthor'},
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
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('question', 'page', 'question_subpart'),)", 'object_name': 'QuestionReferencePage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_subpart': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questionspacing': {
            'Meta': {'ordering': "['sort_order', 'name']", 'object_name': 'QuestionSpacing'},
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
        },
        u'mithreads.thread': {
            'Meta': {'ordering': "['sort_order', 'id']", 'object_name': 'Thread'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'numbered': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mithreads.threadcontent': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'ThreadContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'default': '19', 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mithreads.ThreadSection']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'substitute_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mithreads.threadsection': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('code', 'thread'),)", 'object_name': 'ThreadSection'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'thread_sections'", 'to': u"orm['mithreads.Thread']"})
        }
    }

    complete_apps = ['midocs']