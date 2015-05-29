# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ExpressionFromAnswer.parse_subscripts'
        db.add_column(u'mitesting_expressionfromanswer', 'parse_subscripts',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Expression.parse_subscripts'
        db.add_column(u'mitesting_expression', 'parse_subscripts',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ExpressionFromAnswer.parse_subscripts'
        db.delete_column(u'mitesting_expressionfromanswer', 'parse_subscripts')

        # Deleting field 'Expression.parse_subscripts'
        db.delete_column(u'mitesting_expression', 'parse_subscripts')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'in_pages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'embedded_applets'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['midocs.Page']"}),
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
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'function_input_variable': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
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
        u'midocs.keyword': {
            'Meta': {'ordering': "[u'code']", 'object_name': 'Keyword'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'Meta': {'ordering': "[u'code', u'page_type']", 'unique_together': "((u'code', u'page_type'),)", 'object_name': 'Page'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.PageAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '200'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'javascript': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'notation_systems': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.NotationSystem']", 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'objectives': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Objective']", 'null': 'True', 'blank': 'True'}),
            'page_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.PageType']"}),
            'publish_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'blank': 'True'}),
            'related_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'pages_related_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageRelationship']", 'to': u"orm['midocs.Page']"}),
            'related_videos': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'related_pages'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['midocs.Video']"}),
            'similar_pages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'pages_similar_from'", 'symmetrical': 'False', 'through': u"orm['midocs.PageSimilar']", 'to': u"orm['midocs.Page']"}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'midocs.pageauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'page', u'author'),)", 'object_name': 'PageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
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
        u'midocs.pagetype': {
            'Meta': {'object_name': 'PageType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'in_pages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'embedded_videos'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['midocs.Page']"}),
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
        u'mitesting.assessment': {
            'Meta': {'object_name': 'Assessment'},
            'allow_solution_buttons': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'assessment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.AssessmentType']"}),
            'background_pages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Page']", 'through': u"orm['mitesting.AssessmentBackgroundPage']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'fixed_order': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups_can_view': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'assessments_can_view'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'groups_can_view_solution': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'assessments_can_view_solution'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'instructions2': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'nothing_random': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mitesting.Question']", 'through': u"orm['mitesting.QuestionAssigned']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'time_limit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mitesting.assessmentbackgroundpage': {
            'Meta': {'ordering': "[u'sort_order']", 'object_name': 'AssessmentBackgroundPage'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        u'mitesting.assessmenttype': {
            'Meta': {'object_name': 'AssessmentType'},
            'assessment_privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'record_online_attempts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'solution_privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'template_base_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.expression': {
            'Meta': {'ordering': "[u'post_user_response', u'sort_order', u'id']", 'object_name': 'Expression'},
            'evaluate_level': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'expression': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'expression_type': ('django.db.models.fields.CharField', [], {'default': "u'EX'", 'max_length': '2'}),
            'function_inputs': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'parse_subscripts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_user_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'random_list_group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'real_variables': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        u'mitesting.expressionfromanswer': {
            'Meta': {'unique_together': "((u'name', u'question', u'answer_number'),)", 'object_name': 'ExpressionFromAnswer'},
            'answer_code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'answer_data': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'answer_number': ('django.db.models.fields.IntegerField', [], {}),
            'answer_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'default': "u'_long_underscore_'", 'max_length': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '100'}),
            'parse_subscripts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'real_variables': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'split_symbols_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'mitesting.question': {
            'Meta': {'object_name': 'Question'},
            'allowed_sympy_commands': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mitesting.SympyCommandSet']", 'null': 'True', 'blank': 'True'}),
            'allowed_user_sympy_commands': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'question_set_user'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['mitesting.SympyCommandSet']"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['mitesting.QuestionAuthor']", 'symmetrical': 'False'}),
            'computer_graded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'customize_user_sympy_commands': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Keyword']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'question_spacing': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionType']"}),
            'reference_pages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Page']", 'through': u"orm['mitesting.QuestionReferencePage']", 'symmetrical': 'False'}),
            'show_solution_button_after_attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'solution_privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'subjects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['midocs.Subject']", 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.questionansweroption': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'object_name': 'QuestionAnswerOption'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'answer_code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'answer_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'feedback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match_partial_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'normalize_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'percent_correct': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'round_absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'round_on_compare': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'round_partial_credit': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'split_symbols_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'mitesting.questionassigned': {
            'Meta': {'ordering': "[u'question_set', u'id']", 'object_name': 'QuestionAssigned'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'blank': 'True'})
        },
        u'mitesting.questionauthor': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'question', u'author'),)", 'object_name': 'QuestionAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        u'mitesting.questionreferencepage': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'question', u'page', u'question_subpart'),)", 'object_name': 'QuestionReferencePage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_subpart': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        u'mitesting.questionsetdetail': {
            'Meta': {'unique_together': "((u'assessment', u'question_set'),)", 'object_name': 'QuestionSetDetail'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        u'mitesting.questionsubpart': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'object_name': 'QuestionSubpart'},
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_spacing': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        u'mitesting.questiontype': {
            'Meta': {'object_name': 'QuestionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'mitesting.sympycommandset': {
            'Meta': {'object_name': 'SympyCommandSet'},
            'commands': ('django.db.models.fields.TextField', [], {}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['mitesting']