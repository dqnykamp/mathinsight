# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'QuestionSpacing'
        db.create_table(u'mitesting_questionspacing', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('css_code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionSpacing'])

        # Adding model 'QuestionType'
        db.create_table(u'mitesting_questiontype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('privacy_level', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('privacy_level_solution', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionType'])

        # Adding model 'Question'
        db.create_table(u'mitesting_question', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('question_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionType'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('question_spacing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionSpacing'], null=True, blank=True)),
            ('css_class', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('question_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('solution_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('hint_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('allow_expand', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Video'], null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['Question'])

        # Adding M2M table for field allowed_sympy_commands on 'Question'
        db.create_table(u'mitesting_question_allowed_sympy_commands', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm[u'mitesting.question'], null=False)),
            ('sympycommandset', models.ForeignKey(orm[u'mitesting.sympycommandset'], null=False))
        ))
        db.create_unique(u'mitesting_question_allowed_sympy_commands', ['question_id', 'sympycommandset_id'])

        # Adding model 'QuestionSubpart'
        db.create_table(u'mitesting_questionsubpart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('question_spacing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionSpacing'], null=True, blank=True)),
            ('css_class', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('question_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('solution_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('hint_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionSubpart'])

        # Adding model 'QuestionReferencePage'
        db.create_table(u'mitesting_questionreferencepage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('sort_order', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('question_subpart', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionReferencePage'])

        # Adding unique constraint on 'QuestionReferencePage', fields ['question', 'page', 'question_subpart']
        db.create_unique(u'mitesting_questionreferencepage', ['question_id', 'page_id', 'question_subpart'])

        # Adding model 'QuestionAnswerOption'
        db.create_table(u'mitesting_questionansweroption', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('correct', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('feedback', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionAnswerOption'])

        # Adding model 'AssessmentType'
        db.create_table(u'mitesting_assessmenttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('privacy_level', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('privacy_level_solution', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['AssessmentType'])

        # Adding model 'Assessment'
        db.create_table(u'mitesting_assessment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('assessment_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.AssessmentType'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('fixed_order', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('instructions', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('time_limit', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['Assessment'])

        # Adding M2M table for field groups_can_view on 'Assessment'
        db.create_table(u'mitesting_assessment_groups_can_view', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('assessment', models.ForeignKey(orm[u'mitesting.assessment'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(u'mitesting_assessment_groups_can_view', ['assessment_id', 'group_id'])

        # Adding M2M table for field groups_can_view_solution on 'Assessment'
        db.create_table(u'mitesting_assessment_groups_can_view_solution', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('assessment', models.ForeignKey(orm[u'mitesting.assessment'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(u'mitesting_assessment_groups_can_view_solution', ['assessment_id', 'group_id'])

        # Adding model 'QuestionSetDetail'
        db.create_table(u'mitesting_questionsetdetail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assessment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Assessment'])),
            ('question_set', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
            ('points', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionSetDetail'])

        # Adding unique constraint on 'QuestionSetDetail', fields ['assessment', 'question_set']
        db.create_unique(u'mitesting_questionsetdetail', ['assessment_id', 'question_set'])

        # Adding model 'QuestionAssigned'
        db.create_table(u'mitesting_questionassigned', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assessment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Assessment'])),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('question_set', self.gf('django.db.models.fields.SmallIntegerField')(blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionAssigned'])

        # Adding model 'RandomNumber'
        db.create_table(u'mitesting_randomnumber', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('min_value', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('max_value', self.gf('django.db.models.fields.FloatField')(default=10)),
            ('increment', self.gf('django.db.models.fields.FloatField')(default=1)),
        ))
        db.send_create_signal(u'mitesting', ['RandomNumber'])

        # Adding unique constraint on 'RandomNumber', fields ['name', 'question']
        db.create_unique(u'mitesting_randomnumber', ['name', 'question_id'])

        # Adding model 'RandomWord'
        db.create_table(u'mitesting_randomword', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('option_list', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('plural_list', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('sympy_parse', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'mitesting', ['RandomWord'])

        # Adding unique constraint on 'RandomWord', fields ['name', 'question']
        db.create_unique(u'mitesting_randomword', ['name', 'question_id'])

        # Adding model 'Expression'
        db.create_table(u'mitesting_expression', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('expression', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('required_condition', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('expand', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('n_digits', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('round_decimals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('function_inputs', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('figure', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('linestyle', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('linewidth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('xmin', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('xmax', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('use_ln', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['Expression'])

        # Adding unique constraint on 'Expression', fields ['name', 'question']
        db.create_unique(u'mitesting_expression', ['name', 'question_id'])

        # Adding model 'SympyCommandSet'
        db.create_table(u'mitesting_sympycommandset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('commands', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'mitesting', ['SympyCommandSet'])


    def backwards(self, orm):
        # Removing unique constraint on 'Expression', fields ['name', 'question']
        db.delete_unique(u'mitesting_expression', ['name', 'question_id'])

        # Removing unique constraint on 'RandomWord', fields ['name', 'question']
        db.delete_unique(u'mitesting_randomword', ['name', 'question_id'])

        # Removing unique constraint on 'RandomNumber', fields ['name', 'question']
        db.delete_unique(u'mitesting_randomnumber', ['name', 'question_id'])

        # Removing unique constraint on 'QuestionSetDetail', fields ['assessment', 'question_set']
        db.delete_unique(u'mitesting_questionsetdetail', ['assessment_id', 'question_set'])

        # Removing unique constraint on 'QuestionReferencePage', fields ['question', 'page', 'question_subpart']
        db.delete_unique(u'mitesting_questionreferencepage', ['question_id', 'page_id', 'question_subpart'])

        # Deleting model 'QuestionSpacing'
        db.delete_table(u'mitesting_questionspacing')

        # Deleting model 'QuestionType'
        db.delete_table(u'mitesting_questiontype')

        # Deleting model 'Question'
        db.delete_table(u'mitesting_question')

        # Removing M2M table for field allowed_sympy_commands on 'Question'
        db.delete_table('mitesting_question_allowed_sympy_commands')

        # Deleting model 'QuestionSubpart'
        db.delete_table(u'mitesting_questionsubpart')

        # Deleting model 'QuestionReferencePage'
        db.delete_table(u'mitesting_questionreferencepage')

        # Deleting model 'QuestionAnswerOption'
        db.delete_table(u'mitesting_questionansweroption')

        # Deleting model 'AssessmentType'
        db.delete_table(u'mitesting_assessmenttype')

        # Deleting model 'Assessment'
        db.delete_table(u'mitesting_assessment')

        # Removing M2M table for field groups_can_view on 'Assessment'
        db.delete_table('mitesting_assessment_groups_can_view')

        # Removing M2M table for field groups_can_view_solution on 'Assessment'
        db.delete_table('mitesting_assessment_groups_can_view_solution')

        # Deleting model 'QuestionSetDetail'
        db.delete_table(u'mitesting_questionsetdetail')

        # Deleting model 'QuestionAssigned'
        db.delete_table(u'mitesting_questionassigned')

        # Deleting model 'RandomNumber'
        db.delete_table(u'mitesting_randomnumber')

        # Deleting model 'RandomWord'
        db.delete_table(u'mitesting_randomword')

        # Deleting model 'Expression'
        db.delete_table(u'mitesting_expression')

        # Deleting model 'SympyCommandSet'
        db.delete_table(u'mitesting_sympycommandset')


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
            'Meta': {'ordering': "['code']", 'object_name': 'Applet'},
            'additional_credits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'applet_file': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_file2': ('django.db.models.fields.files.FileField', [], {'max_length': '150', 'blank': 'True'}),
            'applet_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.AppletType']"}),
            'author_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Author']", 'through': u"orm['midocs.AppletAuthor']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'default_inline_caption': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
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
            'template_dir': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'template_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'worksheet': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'midocs.pageauthor': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('page', 'author'),)", 'object_name': 'PageAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'midocs.pagerelationship': {
            'Meta': {'ordering': "['relationship_type', 'sort_order', 'id']", 'unique_together': "(('origin', 'related', 'relationship_type'),)", 'object_name': 'PageRelationship'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relationships'", 'to': u"orm['midocs.Page']"}),
            'related': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverse_relationships'", 'to': u"orm['midocs.Page']"}),
            'relationship_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.RelationshipType']"}),
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'midocs.pagesimilar': {
            'Meta': {'ordering': "['-score', 'id']", 'unique_together': "(('origin', 'similar'),)", 'object_name': 'PageSimilar'},
            'background_page': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'similar'", 'to': u"orm['midocs.Page']"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'similar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reverse_similar'", 'to': u"orm['midocs.Page']"})
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
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']"})
        },
        u'midocs.videoparameter': {
            'Meta': {'unique_together': "(('video', 'parameter'),)", 'object_name': 'VideoParameter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.VideoTypeParameter']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
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
        u'mitesting.assessment': {
            'Meta': {'object_name': 'Assessment'},
            'assessment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.AssessmentType']"}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'fixed_order': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups_can_view': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'assessments_can_view'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'groups_can_view_solution': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'assessments_can_view_solution'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mitesting.Question']", 'through': u"orm['mitesting.QuestionAssigned']", 'symmetrical': 'False'}),
            'time_limit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.assessmenttype': {
            'Meta': {'object_name': 'AssessmentType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'privacy_level': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacy_level_solution': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mitesting.expression': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('name', 'question'),)", 'object_name': 'Expression'},
            'expand': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expression': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'figure': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'function_inputs': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linestyle': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'linewidth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'n_digits': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'required_condition': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'round_decimals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'use_ln': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'xmax': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'xmin': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mitesting.question': {
            'Meta': {'object_name': 'Question'},
            'allow_expand': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allowed_sympy_commands': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['mitesting.SympyCommandSet']", 'null': 'True', 'blank': 'True'}),
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'question_spacing': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionSpacing']", 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionType']"}),
            'reference_pages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Page']", 'through': u"orm['mitesting.QuestionReferencePage']", 'symmetrical': 'False'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Video']", 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.questionansweroption': {
            'Meta': {'object_name': 'QuestionAnswerOption'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'feedback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"})
        },
        u'mitesting.questionassigned': {
            'Meta': {'ordering': "['question_set', 'id']", 'object_name': 'QuestionAssigned'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'blank': 'True'})
        },
        u'mitesting.questionreferencepage': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(('question', 'page', 'question_subpart'),)", 'object_name': 'QuestionReferencePage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['midocs.Page']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_subpart': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mitesting.questionsetdetail': {
            'Meta': {'unique_together': "(('assessment', 'question_set'),)", 'object_name': 'QuestionSetDetail'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        u'mitesting.questionspacing': {
            'Meta': {'ordering': "['name']", 'object_name': 'QuestionSpacing'},
            'css_code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'mitesting.questionsubpart': {
            'Meta': {'ordering': "['sort_order', 'id']", 'object_name': 'QuestionSubpart'},
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_spacing': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionSpacing']", 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mitesting.questiontype': {
            'Meta': {'object_name': 'QuestionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'privacy_level': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacy_level_solution': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'mitesting.randomnumber': {
            'Meta': {'unique_together': "(('name', 'question'),)", 'object_name': 'RandomNumber'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'increment': ('django.db.models.fields.FloatField', [], {'default': '1'}),
            'max_value': ('django.db.models.fields.FloatField', [], {'default': '10'}),
            'min_value': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"})
        },
        u'mitesting.randomword': {
            'Meta': {'unique_together': "(('name', 'question'),)", 'object_name': 'RandomWord'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'option_list': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'plural_list': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'sympy_parse': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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

    complete_apps = ['mitesting']