# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0001_initial'),
        ('micourses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expression',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.SlugField()),
                ('expression_type', models.CharField(choices=[('General', (('EX', 'Generic'), ('RN', 'Rand number'), ('FN', 'Function'), ('FE', 'Function name'), ('US', 'Unsplit symbol'), ('CN', 'Required cond'))), ('Random from list', (('RW', 'Rand word'), ('RE', 'Rand expr'), ('RF', 'Rand fun name'))), ('Tuples and sets', (('UT', 'Unordered tuple'), ('ST', 'Sorted tuple'), ('RT', 'Rand order tuple'), ('SE', 'Set'), ('IN', 'Interval'), ('EA', 'Expr w/ alts'))), ('Matrix and vector', (('MX', 'Matrix'), ('VC', 'Vector')))], default='EX', max_length=2)),
                ('expression', models.CharField(max_length=1000)),
                ('evaluate_level', models.IntegerField(choices=[(0, 'None'), (1, 'Partial'), (2, 'Full')], default=2)),
                ('function_inputs', models.CharField(null=True, max_length=50, blank=True)),
                ('random_list_group', models.CharField(null=True, max_length=50, blank=True)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.SlugField(max_length=100)),
                ('answer_code', models.SlugField()),
                ('answer_number', models.IntegerField()),
                ('split_symbols_on_compare', models.BooleanField(default=True)),
                ('answer_type', models.IntegerField(null=True, default=0)),
                ('answer_data', models.TextField(null=True)),
                ('real_variables', models.BooleanField(default=True)),
                ('parse_subscripts', models.BooleanField(default=True)),
                ('default_value', models.CharField(default='_long_underscore_', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('question_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('solution_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('question_spacing', models.CharField(null=True, choices=[('large3spacebelow', 'large3'), ('large2spacebelow', 'large2'), ('largespacebelow', 'large'), ('medlargespacebelow', 'medium large'), ('medspacebelow', 'medium'), ('smallspacebelow', 'small'), ('tinyspacebelow', 'tiny')], max_length=20, blank=True)),
                ('css_class', models.CharField(null=True, max_length=100, blank=True)),
                ('question_text', models.TextField(null=True, blank=True)),
                ('solution_text', models.TextField(null=True, blank=True)),
                ('hint_text', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('customize_user_sympy_commands', models.BooleanField(default=False)),
                ('computer_graded', models.BooleanField(default=False)),
                ('show_solution_button_after_attempts', models.IntegerField(default=0)),
            ],
            options={
                'permissions': (('administer_question', 'Can administer questions'),),
            },
        ),
        migrations.CreateModel(
            name='QuestionAnswerOption',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('answer_type', models.IntegerField(choices=[(0, 'Expression'), (1, 'Multiple Choice'), (2, 'Function'), (3, 'Text')], default=0)),
                ('answer_code', models.SlugField()),
                ('answer', models.CharField(max_length=400)),
                ('percent_correct', models.IntegerField(default=100)),
                ('feedback', models.TextField(null=True, blank=True)),
                ('round_on_compare', models.IntegerField(null=True, blank=True)),
                ('round_absolute', models.BooleanField(default=False)),
                ('round_partial_credit_digits', models.IntegerField(null=True, blank=True)),
                ('round_partial_credit_percent', models.IntegerField(null=True, blank=True)),
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
            name='QuestionAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(blank=True)),
                ('question_subpart', models.CharField(null=True, max_length=1, blank=True)),
                ('page', models.ForeignKey(to='midocs.Page')),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionSubpart',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('question_spacing', models.CharField(null=True, choices=[('large3spacebelow', 'large3'), ('large2spacebelow', 'large2'), ('largespacebelow', 'large'), ('medlargespacebelow', 'medium large'), ('medspacebelow', 'medium'), ('smallspacebelow', 'small'), ('tinyspacebelow', 'tiny')], max_length=20, blank=True)),
                ('css_class', models.CharField(null=True, max_length=100, blank=True)),
                ('sort_order', models.FloatField(blank=True)),
                ('question_text', models.TextField(null=True, blank=True)),
                ('solution_text', models.TextField(null=True, blank=True)),
                ('hint_text', models.TextField(null=True, blank=True)),
                ('question', models.ForeignKey(to='mitesting.Question')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SympyCommandSet',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
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
            field=models.ManyToManyField(to='mitesting.SympyCommandSet', related_name='question_set_user', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='mitesting.QuestionAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='base_question',
            field=models.ForeignKey(null=True, related_name='derived_questions', blank=True, to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='question',
            name='course',
            field=models.ForeignKey(null=True, blank=True, to='micourses.Course'),
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
            field=models.ManyToManyField(to='midocs.Page', through='mitesting.QuestionReferencePage', blank=True),
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
        migrations.CreateModel(
            name='QuestionDatabase',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'question',
                'verbose_name_plural': 'Question database',
            },
            bases=('mitesting.question',),
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
