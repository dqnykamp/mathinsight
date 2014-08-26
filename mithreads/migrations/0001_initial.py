# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Thread'
        db.create_table(u'mithreads_thread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('numbered', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'mithreads', ['Thread'])

        # Adding model 'ThreadSection'
        db.create_table(u'mithreads_threadsection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'thread_sections', to=orm['mithreads.Thread'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('level', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'mithreads', ['ThreadSection'])

        # Adding unique constraint on 'ThreadSection', fields ['code', 'thread']
        db.create_unique(u'mithreads_threadsection', ['code', 'thread_id'])

        # Adding model 'ThreadContent'
        db.create_table(u'mithreads_threadcontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('section', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mithreads.ThreadSection'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(default=19, to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('substitute_title', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'mithreads', ['ThreadContent'])


    def backwards(self, orm):
        # Removing unique constraint on 'ThreadSection', fields ['code', 'thread']
        db.delete_unique(u'mithreads_threadsection', ['code', 'thread_id'])

        # Deleting model 'Thread'
        db.delete_table(u'mithreads_thread')

        # Deleting model 'ThreadSection'
        db.delete_table(u'mithreads_threadsection')

        # Deleting model 'ThreadContent'
        db.delete_table(u'mithreads_threadcontent')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'mithreads.thread': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'object_name': 'Thread'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'numbered': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mithreads.threadcontent': {
            'Meta': {'ordering': "[u'sort_order']", 'object_name': 'ThreadContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'default': '19', 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mithreads.ThreadSection']"}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'substitute_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'mithreads.threadsection': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'unique_together': "((u'code', u'thread'),)", 'object_name': 'ThreadSection'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'thread_sections'", 'to': u"orm['mithreads.Thread']"})
        }
    }

    complete_apps = ['mithreads']