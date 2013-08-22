# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'StudentAttendance.present'
        db.add_column(u'micourses_studentattendance', 'present',
                      self.gf('django.db.models.fields.FloatField')(default=1.0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'StudentAttendance.present'
        db.delete_column(u'micourses_studentattendance', 'present')


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
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'micourses.assessmentcategory': {
            'Meta': {'object_name': 'AssessmentCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'micourses.attendancedate': {
            'Meta': {'ordering': "['date']", 'object_name': 'AttendanceDate'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'micourses.course': {
            'Meta': {'ordering': "['start_date', 'id']", 'object_name': 'Course'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adjust_due_date_attendance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'assessment_categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['micourses.AssessmentCategory']", 'through': u"orm['micourses.CourseAssessmentCategory']", 'symmetrical': 'False'}),
            'attendance_end_of_week': ('django.db.models.fields.CharField', [], {'default': "'F'", 'max_length': '2'}),
            'attendance_threshold_percent': ('django.db.models.fields.SmallIntegerField', [], {'default': '75'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'days_of_week': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'enrolled_students': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['micourses.CourseUser']", 'through': u"orm['micourses.CourseEnrollment']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_attendance_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'semester': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mithreads.Thread']"}),
            'track_attendance': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'micourses.courseassessmentcategory': {
            'Meta': {'object_name': 'CourseAssessmentCategory'},
            'assessment_category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.AssessmentCategory']"}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_count_for_grade': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0.0'})
        },
        u'micourses.courseenrollment': {
            'Meta': {'unique_together': "(('course', 'student'),)", 'object_name': 'CourseEnrollment'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            'date_enrolled': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseUser']"}),
            'withdrew': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'micourses.courseskipdate': {
            'Meta': {'object_name': 'CourseSkipDate'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'micourses.coursethreadcontent': {
            'Meta': {'ordering': "['sort_order', 'id']", 'unique_together': "(['course', 'thread_content'],)", 'object_name': 'CourseThreadContent'},
            'assessment_category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.AssessmentCategory']", 'null': 'True', 'blank': 'True'}),
            'attempt_aggregation': ('django.db.models.fields.CharField', [], {'default': "'Max'", 'max_length': '3'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            'final_due_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'individualize_by_student': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'initial_due_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'max_number_attempts': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'optional': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'required_for_grade': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.GradeLevel']", 'null': 'True', 'blank': 'True'}),
            'required_to_pass': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'thread_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mithreads.ThreadContent']"})
        },
        u'micourses.courseuser': {
            'Meta': {'object_name': 'CourseUser'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'}),
            'selected_course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'micourses.gradelevel': {
            'Meta': {'object_name': 'GradeLevel'},
            'grade': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'micourses.manualduedateadjustment': {
            'Meta': {'unique_together': "(('content', 'student'),)", 'object_name': 'ManualDueDateAdjustment'},
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseThreadContent']"}),
            'final_due_date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_due_date': ('django.db.models.fields.DateField', [], {}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseUser']"})
        },
        u'micourses.questionstudentanswer': {
            'Meta': {'object_name': 'QuestionStudentAnswer'},
            'answer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']", 'null': 'True', 'blank': 'True'}),
            'assessment_seed': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'course_content_attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.StudentContentAttempt']", 'null': 'True', 'blank': 'True'}),
            'credit': ('django.db.models.fields.FloatField', [], {}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier_in_answer': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'seed': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'micourses.studentattendance': {
            'Meta': {'object_name': 'StudentAttendance'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.Course']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'present': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseUser']"})
        },
        u'micourses.studentcontentattempt': {
            'Meta': {'ordering': "['datetime']", 'object_name': 'StudentContentAttempt'},
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseThreadContent']"}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'seed': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseUser']"})
        },
        u'micourses.studentcontentcompletion': {
            'Meta': {'unique_together': "(['student', 'content'],)", 'object_name': 'StudentContentCompletion'},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseThreadContent']"}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'skip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['micourses.CourseUser']"})
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
            'allow_solution_buttons': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'assessment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.AssessmentType']"}),
            'background_pages': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['midocs.Page']", 'through': u"orm['mitesting.AssessmentBackgroundPage']", 'symmetrical': 'False'}),
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'detailed_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'fixed_order': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups_can_view': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'assessments_can_view'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'groups_can_view_solution': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'assessments_can_view_solution'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'hand_graded_component': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'instructions2': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'nothing_random': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mitesting.Question']", 'through': u"orm['mitesting.QuestionAssigned']", 'symmetrical': 'False'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'time_limit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'mitesting.assessmentbackgroundpage': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'AssessmentBackgroundPage'},
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
            'privacy_level_solution': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
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
        u'mitesting.questionassigned': {
            'Meta': {'ordering': "['question_set', 'id']", 'object_name': 'QuestionAssigned'},
            'assessment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Assessment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mitesting.Question']"}),
            'question_set': ('django.db.models.fields.SmallIntegerField', [], {'blank': 'True'})
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
            'sort_order': ('django.db.models.fields.FloatField', [], {'default': '0'})
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

    complete_apps = ['micourses']