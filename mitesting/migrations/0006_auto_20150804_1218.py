# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.exceptions import ObjectDoesNotExist

# based on function from models.py
def question_sets(assessment):
    question_set_dicts= assessment.questionassigned_set.order_by('question_set').values('question_set').distinct()
    question_sets = []
    for question_set_dict in question_set_dicts:
        question_sets.append(question_set_dict['question_set'])
    return question_sets

# based on function from models.py
def get_total_points(assessment):
    if assessment.total_points is None:
        total_points=0
        for question_set in question_sets(assessment):
            the_points = points_of_question_set(assessment,question_set)
            if the_points:
                total_points += the_points
        return total_points
    else:
        return assessment.total_points

# based on function from models.py
def points_of_question_set(assessment, question_set):
    try:
        question_detail=assessment.questionsetdetail_set.get(
            question_set=question_set)
        return question_detail.weight
    except ObjectDoesNotExist:
        return None

def points_to_thread_content(apps, schema_editor):
    # calculate points for each assessment and save to thread content

     Assessment = apps.get_model('mitesting', 'Assessment')
     ThreadContent = apps.get_model('micourses', 'ThreadContent')
     ContentType = apps.get_model('contenttypes', 'ContentType')
     assessment_content_type = ContentType.objects.get_for_model(Assessment)

     for assessment in Assessment.objects.all():
         points = get_total_points(assessment)
         for tc in ThreadContent.objects.filter(
                 content_type= assessment_content_type, 
                 object_id = assessment.id):
             tc.points = points
             tc.save()
    


class Migration(migrations.Migration):

    dependencies = [
        ('mitesting', '0005_auto_20150803_1156'),
        ('micourses', '0008_auto_20150803_1725'),
    ]

    operations = [
        migrations.RunPython(points_to_thread_content),
        migrations.RemoveField(
            model_name='assessment',
            name='total_points',
        ),
        
    ]
