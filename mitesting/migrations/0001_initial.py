# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
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
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionSpacing'])

        # Adding model 'QuestionType'
        db.create_table(u'mitesting_questiontype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionType'])

        # Adding model 'QuestionPermission'
        db.create_table(u'mitesting_questionpermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('privacy_level', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('privacy_level_solution', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionPermission'])

        # Adding model 'Question'
        db.create_table(u'mitesting_question', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('question_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionType'])),
            ('question_permission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionPermission'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('question_spacing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionSpacing'], null=True, blank=True)),
            ('css_class', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('question_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('solution_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('hint_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('show_solution_button_after_attempts', self.gf('django.db.models.fields.IntegerField')(default=3)),
        ))
        db.send_create_signal(u'mitesting', ['Question'])

        # Adding M2M table for field allowed_sympy_commands on 'Question'
        m2m_table_name = db.shorten_name(u'mitesting_question_allowed_sympy_commands')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm[u'mitesting.question'], null=False)),
            ('sympycommandset', models.ForeignKey(orm[u'mitesting.sympycommandset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['question_id', 'sympycommandset_id'])

        # Adding M2M table for field keywords on 'Question'
        m2m_table_name = db.shorten_name(u'mitesting_question_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm[u'mitesting.question'], null=False)),
            ('keyword', models.ForeignKey(orm[u'midocs.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['question_id', 'keyword_id'])

        # Adding M2M table for field subjects on 'Question'
        m2m_table_name = db.shorten_name(u'mitesting_question_subjects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm[u'mitesting.question'], null=False)),
            ('subject', models.ForeignKey(orm[u'midocs.subject'], null=False))
        ))
        db.create_unique(m2m_table_name, ['question_id', 'subject_id'])

        # Adding model 'QuestionAuthor'
        db.create_table(u'mitesting_questionauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Author'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['QuestionAuthor'])

        # Adding unique constraint on 'QuestionAuthor', fields ['question', 'author']
        db.create_unique(u'mitesting_questionauthor', ['question_id', 'author_id'])

        # Adding model 'QuestionSubpart'
        db.create_table(u'mitesting_questionsubpart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('question_spacing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.QuestionSpacing'], null=True, blank=True)),
            ('css_class', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
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
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('question_subpart', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
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
            ('template_base_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('record_online_attempts', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'mitesting', ['AssessmentType'])

        # Adding model 'Assessment'
        db.create_table(u'mitesting_assessment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('assessment_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.AssessmentType'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('detailed_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('instructions', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('instructions2', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('time_limit', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('allow_solution_buttons', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('fixed_order', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('nothing_random', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('total_points', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['Assessment'])

        # Adding M2M table for field groups_can_view on 'Assessment'
        m2m_table_name = db.shorten_name(u'mitesting_assessment_groups_can_view')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('assessment', models.ForeignKey(orm[u'mitesting.assessment'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['assessment_id', 'group_id'])

        # Adding M2M table for field groups_can_view_solution on 'Assessment'
        m2m_table_name = db.shorten_name(u'mitesting_assessment_groups_can_view_solution')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('assessment', models.ForeignKey(orm[u'mitesting.assessment'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['assessment_id', 'group_id'])

        # Adding model 'AssessmentBackgroundPage'
        db.create_table(u'mitesting_assessmentbackgroundpage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assessment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Assessment'])),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['midocs.Page'])),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0.0)),
        ))
        db.send_create_signal(u'mitesting', ['AssessmentBackgroundPage'])

        # Adding model 'QuestionSetDetail'
        db.create_table(u'mitesting_questionsetdetail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assessment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Assessment'])),
            ('question_set', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
            ('points', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
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
            ('min_value', self.gf('django.db.models.fields.CharField')(default=u'0', max_length=200)),
            ('max_value', self.gf('django.db.models.fields.CharField')(default=u'10', max_length=200)),
            ('increment', self.gf('django.db.models.fields.CharField')(default=u'1', max_length=200)),
        ))
        db.send_create_signal(u'mitesting', ['RandomNumber'])

        # Adding model 'RandomWord'
        db.create_table(u'mitesting_randomword', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('option_list', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('plural_list', self.gf('django.db.models.fields.CharField')(max_length=400, null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('sympy_parse', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('treat_as_function', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'mitesting', ['RandomWord'])

        # Adding model 'Expression'
        db.create_table(u'mitesting_expression', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('expression', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('required_condition', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('expand', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('doit', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('n_digits', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('round_decimals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('function_inputs', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('use_ln', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('normalize_on_compare', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('split_symbols_on_compare', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('tuple_is_ordered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('collapse_equal_tuple_elements', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('output_no_delimiters', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sort_list', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('randomize_list', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sort_order', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal(u'mitesting', ['Expression'])

        # Adding model 'PlotFunction'
        db.create_table(u'mitesting_plotfunction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('function', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('figure', self.gf('django.db.models.fields.IntegerField')()),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mitesting.Question'])),
            ('linestyle', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('linewidth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('xmin', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('xmax', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('invert', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('condition_to_show', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'mitesting', ['PlotFunction'])

        # Adding model 'SympyCommandSet'
        db.create_table(u'mitesting_sympycommandset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('commands', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'mitesting', ['SympyCommandSet'])


    def backwards(self, orm):
        # Removing unique constraint on 'QuestionSetDetail', fields ['assessment', 'question_set']
        db.delete_unique(u'mitesting_questionsetdetail', ['assessment_id', 'question_set'])

        # Removing unique constraint on 'QuestionReferencePage', fields ['question', 'page', 'question_subpart']
        db.delete_unique(u'mitesting_questionreferencepage', ['question_id', 'page_id', 'question_subpart'])

        # Removing unique constraint on 'QuestionAuthor', fields ['question', 'author']
        db.delete_unique(u'mitesting_questionauthor', ['question_id', 'author_id'])

        # Deleting model 'QuestionSpacing'
        db.delete_table(u'mitesting_questionspacing')

        # Deleting model 'QuestionType'
        db.delete_table(u'mitesting_questiontype')

        # Deleting model 'QuestionPermission'
        db.delete_table(u'mitesting_questionpermission')

        # Deleting model 'Question'
        db.delete_table(u'mitesting_question')

        # Removing M2M table for field allowed_sympy_commands on 'Question'
        db.delete_table(db.shorten_name(u'mitesting_question_allowed_sympy_commands'))

        # Removing M2M table for field keywords on 'Question'
        db.delete_table(db.shorten_name(u'mitesting_question_keywords'))

        # Removing M2M table for field subjects on 'Question'
        db.delete_table(db.shorten_name(u'mitesting_question_subjects'))

        # Deleting model 'QuestionAuthor'
        db.delete_table(u'mitesting_questionauthor')

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
        db.delete_table(db.shorten_name(u'mitesting_assessment_groups_can_view'))

        # Removing M2M table for field groups_can_view_solution on 'Assessment'
        db.delete_table(db.shorten_name(u'mitesting_assessment_groups_can_view_solution'))

        # Deleting model 'AssessmentBackgroundPage'
        db.delete_table(u'mitesting_assessmentbackgroundpage')

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

        # Deleting model 'PlotFunction'
        db.delete_table(u'mitesting_plotfunction')

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
        u'midocs.level': {
            'Meta': {'object_name': 'Level'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0.0'})
        },
        u'mitesting.assessmenttype': {
            'Meta': {'object_name': 'AssessmentType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'privacy_level': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacy_level_solution': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'record_online_attempts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'template_base_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.expression': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'object_name': 'Expression'},
            'collapse_equal_tuple_elements': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doit': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'expand': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expression': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'function_inputs': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'n_digits': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'normalize_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'output_no_delimiters': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'randomize_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'required_condition': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'round_decimals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sort_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'split_symbols_on_compare': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tuple_is_ordered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'use_ln': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'mitesting.plotfunction': {
            'Meta': {'object_name': 'PlotFunction'},
            'condition_to_show': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'figure': ('django.db.models.fields.IntegerField', [], {}),
            'function': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invert': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'linestyle': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'linewidth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'xmax': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'xmin': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
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
        u'mitesting.questionansweroption': {
            'Meta': {'object_name': 'QuestionAnswerOption'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'feedback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"})
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
        u'mitesting.questionsetdetail': {
            'Meta': {'unique_together': "((u'assessment', u'question_set'),)", 'object_name': 'QuestionSetDetail'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        u'mitesting.questionspacing': {
            'Meta': {'ordering': "[u'sort_order', u'name']", 'object_name': 'QuestionSpacing'},
            'css_code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questionsubpart': {
            'Meta': {'ordering': "[u'sort_order', u'id']", 'object_name': 'QuestionSubpart'},
            'css_class': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'hint_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_spacing': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.QuestionSpacing']", 'null': 'True', 'blank': 'True'}),
            'question_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'solution_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'mitesting.questiontype': {
            'Meta': {'object_name': 'QuestionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'mitesting.randomnumber': {
            'Meta': {'object_name': 'RandomNumber'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'increment': ('django.db.models.fields.CharField', [], {'default': "u'1'", 'max_length': '200'}),
            'max_value': ('django.db.models.fields.CharField', [], {'default': "u'10'", 'max_length': '200'}),
            'min_value': ('django.db.models.fields.CharField', [], {'default': "u'0'", 'max_length': '200'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"})
        },
        u'mitesting.randomword': {
            'Meta': {'object_name': 'RandomWord'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'option_list': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'plural_list': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'sympy_parse': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'treat_as_function': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'mitesting.sympycommandset': {
            'Meta': {'object_name': 'SympyCommandSet'},
            'commands': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['mitesting']
