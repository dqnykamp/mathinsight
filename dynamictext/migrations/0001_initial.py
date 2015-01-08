# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DynamicText'
        db.create_table(u'dynamictext_dynamictext', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contained_in_content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('contained_in_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('nodelisttext', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'dynamictext', ['DynamicText'])

        # Adding unique constraint on 'DynamicText', fields ['contained_in_content_type', 'contained_in_object_id', 'number']
        db.create_unique(u'dynamictext_dynamictext', ['contained_in_content_type_id', 'contained_in_object_id', 'number'])


    def backwards(self, orm):
        # Removing unique constraint on 'DynamicText', fields ['contained_in_content_type', 'contained_in_object_id', 'number']
        db.delete_unique(u'dynamictext_dynamictext', ['contained_in_content_type_id', 'contained_in_object_id', 'number'])

        # Deleting model 'DynamicText'
        db.delete_table(u'dynamictext_dynamictext')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dynamictext.dynamictext': {
            'Meta': {'unique_together': "((u'contained_in_content_type', u'contained_in_object_id', u'number'),)", 'object_name': 'DynamicText'},
            'contained_in_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'contained_in_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nodelisttext': ('django.db.models.fields.TextField', [], {}),
            'number': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['dynamictext']