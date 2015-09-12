# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from sympy import sympify

def migrate_round_partial_credit(apps, schema_editor):
    QuestionAnswerOption = apps.get_model('mitesting', 'QuestionAnswerOption')
    for answer_option in QuestionAnswerOption.objects.all():
        if answer_option.round_partial_credit:
            answer_option.round_partial_credit_digits=0
            answer_option.round_partial_credit_percent=0
            try:
                rnd=sympify(answer_option.round_partial_credit)
                if isinstance(rnd, tuple):
                    answer_option.round_partial_credit_digits = int(rnd[0])
                else:
                    answer_option.round_partial_credit_digits = int(rnd)
                if answer_option.round_partial_credit_digits > 0:
                    answer_option.round_partial_credit_percent=int(rnd[1])
            except (TypeError, IndexError, ValueError):
                pass
            answer_option.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0010_auto_20150819_2205'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='questiondatabase',
            options={'verbose_name': 'question', 'verbose_name_plural': 'Question database'},
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='round_partial_credit_digits',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='questionansweroption',
            name='round_partial_credit_percent',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='expression',
            name='expression_type',
            field=models.CharField(choices=[('General', (('EX', 'Generic'), ('RN', 'Rand number'), ('FN', 'Function'), ('FE', 'Function name'), ('US', 'Unsplit symbol'), ('CN', 'Required cond'))), ('Random from list', (('RW', 'Rand word'), ('RE', 'Rand expr'), ('RF', 'Rand fun name'))), ('Tuples and sets', (('UT', 'Unordered tuple'), ('ST', 'Sorted tuple'), ('RT', 'Rand order tuple'), ('SE', 'Set'), ('IN', 'Interval'), ('EA', 'Expr w/ alts'))), ('Matrix and vector', (('MX', 'Matrix'), ('VC', 'Vector')))], default='EX', max_length=2),
        ),
        migrations.RunPython(migrate_round_partial_credit),
        migrations.RemoveField(
            model_name='questionansweroption',
            name='round_partial_credit',
        ),        
    ]
