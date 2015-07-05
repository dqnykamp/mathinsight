# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True, max_length=200)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=30)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('detailed_description', models.TextField(blank=True, null=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('instructions2', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('time_limit', models.CharField(blank=True, null=True, max_length=20)),
                ('allow_solution_buttons', models.BooleanField(default=True)),
                ('fixed_order', models.BooleanField(default=False)),
                ('nothing_random', models.BooleanField(default=False)),
                ('total_points', models.FloatField(blank=True, null=True)),
            ],
            options={
                'permissions': (('administer_assessment', 'Can administer assessments'),),
            },
        ),
        migrations.CreateModel(
            name='AssessmentBackgroundPage',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('assessment', models.ForeignKey(to='mitesting.Assessment')),
                ('page', models.ForeignKey(to='midocs.Page')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('assessment_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('solution_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('template_base_name', models.CharField(blank=True, null=True, max_length=50)),
                ('record_online_attempts', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Expression',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.SlugField()),
                ('expression_type', models.CharField(max_length=2, choices=[('General', (('EX', 'Generic'), ('RN', 'Rand number'), ('FN', 'Function'), ('FE', 'Function name'), ('CN', 'Required cond'))), ('Random from list', (('RW', 'Rand word'), ('RE', 'Rand expr'), ('RF', 'Rand fun name'))), ('Tuples and sets', (('UT', 'Unordered tuple'), ('ST', 'Sorted tuple'), ('RT', 'Rand order tuple'), ('SE', 'Set'), ('IN', 'Interval'), ('EA', 'Expr w/ alts'))), ('Matrix and vector', (('MX', 'Matrix'), ('VC', 'Vector')))], default='EX')),
                ('expression', models.CharField(max_length=1000)),
                ('evaluate_level', models.IntegerField(choices=[(0, 'None'), (1, 'Partial'), (2, 'Full')], default=2)),
                ('function_inputs', models.CharField(blank=True, null=True, max_length=50)),
                ('random_list_group', models.CharField(blank=True, null=True, max_length=50)),
                ('real_variables', models.BooleanField(default=True)),
                ('parse_subscripts', models.BooleanField(default=False)),
                ('post_user_response', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['post_user_response', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ExpressionFromAnswer',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.SlugField(max_length=100)),
                ('answer_code', models.SlugField()),
                ('answer_number', models.IntegerField()),
                ('split_symbols_on_compare', models.BooleanField(default=True)),
                ('answer_type', models.IntegerField(null=True, default=0)),
                ('answer_data', models.TextField(null=True)),
                ('real_variables', models.BooleanField(default=True)),
                ('parse_subscripts', models.BooleanField(default=True)),
                ('default_value', models.CharField(max_length=20, default='_long_underscore_')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('question_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('solution_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('description', models.CharField(blank=True, null=True, max_length=400)),
                ('question_spacing', models.CharField(blank=True, null=True, choices=[('large3spacebelow', 'large3'), ('large2spacebelow', 'large2'), ('largespacebelow', 'large'), ('medlargespacebelow', 'medium large'), ('medspacebelow', 'medium'), ('smallspacebelow', 'small'), ('tinyspacebelow', 'tiny')], max_length=20)),
                ('css_class', models.CharField(blank=True, null=True, max_length=100)),
                ('question_text', models.TextField(blank=True, null=True)),
                ('solution_text', models.TextField(blank=True, null=True)),
                ('hint_text', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('customize_user_sympy_commands', models.BooleanField(default=False)),
                ('computer_graded', models.BooleanField(default=False)),
                ('show_solution_button_after_attempts', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionAnswerOption',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('answer_type', models.IntegerField(choices=[(0, 'Expression'), (1, 'Multiple Choice'), (2, 'Function')], default=0)),
                ('answer_code', models.SlugField()),
                ('answer', models.CharField(max_length=400)),
                ('percent_correct', models.IntegerField(default=100)),
                ('feedback', models.TextField(blank=True, null=True)),
                ('round_on_compare', models.IntegerField(blank=True, null=True)),
                ('round_absolute', models.BooleanField(default=False)),
                ('round_partial_credit', models.CharField(blank=True, null=True, max_length=10)),
                ('normalize_on_compare', models.BooleanField(default=False)),
                ('split_symbols_on_compare', models.BooleanField(default=True)),
                ('match_partial_on_compare', models.BooleanField(default=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionAssigned',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('question_set', models.SmallIntegerField(blank=True)),
                ('assessment', models.ForeignKey(to='mitesting.Assessment')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'verbose_name_plural': 'Questions assigned',
                'ordering': ['question_set', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionAuthor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('author', models.ForeignKey(to='midocs.Author')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionReferencePage',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('sort_order', models.FloatField(blank=True)),
                ('question_subpart', models.CharField(blank=True, null=True, max_length=1)),
                ('page', models.ForeignKey(to='midocs.Page')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionSetDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('question_set', models.SmallIntegerField(db_index=True, default=0)),
                ('points', models.FloatField(default=0)),
                ('group', models.CharField(blank=True, null=True, max_length=50)),
                ('assessment', models.ForeignKey(to='mitesting.Assessment')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionSubpart',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('question_spacing', models.CharField(blank=True, null=True, choices=[('large3spacebelow', 'large3'), ('large2spacebelow', 'large2'), ('largespacebelow', 'large'), ('medlargespacebelow', 'medium large'), ('medspacebelow', 'medium'), ('smallspacebelow', 'small'), ('tinyspacebelow', 'tiny')], max_length=20)),
                ('css_class', models.CharField(blank=True, null=True, max_length=100)),
                ('sort_order', models.FloatField(blank=True)),
                ('question_text', models.TextField(blank=True, null=True)),
                ('solution_text', models.TextField(blank=True, null=True)),
                ('hint_text', models.TextField(blank=True, null=True)),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SympyCommandSet',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('commands', models.TextField()),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='allowed_sympy_commands',
            field=models.ManyToManyField(to='mitesting.SympyCommandSet', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='allowed_user_sympy_commands',
            field=models.ManyToManyField(related_name='question_set_user', to='mitesting.SympyCommandSet', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', blank=True, through='mitesting.QuestionAuthor'),
        ),
        migrations.AddField(
            model_name='question',
            name='keywords',
            field=models.ManyToManyField(to='midocs.Keyword', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.ForeignKey(to='mitesting.QuestionType'),
        ),
        migrations.AddField(
            model_name='question',
            name='reference_pages',
            field=models.ManyToManyField(to='midocs.Page', blank=True, through='mitesting.QuestionReferencePage'),
        ),
        migrations.AddField(
            model_name='question',
            name='subjects',
            field=models.ManyToManyField(to='midocs.Subject', blank=True),
        ),
        migrations.AddField(
            model_name='expressionfromanswer',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='expression',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='assessment_type',
            field=models.ForeignKey(to='mitesting.AssessmentType'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='background_pages',
            field=models.ManyToManyField(to='midocs.Page', blank=True, through='mitesting.AssessmentBackgroundPage'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view',
            field=models.ManyToManyField(related_name='assessments_can_view', to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='groups_can_view_solution',
            field=models.ManyToManyField(related_name='assessments_can_view_solution', to='auth.Group', blank=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='questions',
            field=models.ManyToManyField(to='mitesting.Question', blank=True, through='mitesting.QuestionAssigned'),
        ),
        migrations.AlterUniqueTogether(
            name='questionsetdetail',
            unique_together=set([('assessment', 'question_set')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionreferencepage',
            unique_together=set([('question', 'page', 'question_subpart')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionauthor',
            unique_together=set([('question', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='expressionfromanswer',
            unique_together=set([('name', 'question', 'answer_number')]),
        ),
    ]
