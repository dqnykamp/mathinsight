# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def copy_assessments(apps, schema_editor):
    AssessmentType = apps.get_model('micourses', 'AssessmentType')
    OldAssessmentType = apps.get_model('mitesting', 'AssessmentType')
    
    for oat in OldAssessmentType.objects.all():
        AssessmentType.objects.create(
            code=oat.code, name=oat.name,
            assessment_privacy=oat.assessment_privacy,
            solution_privacy=oat.solution_privacy,
            template_base_name=oat.template_base_name)

    Assessment = apps.get_model('micourses', 'Assessment')
    OldAssessment = apps.get_model('mitesting', 'Assessment')

    ContentType = apps.get_model('contenttypes', 'ContentType')
    assessment_ct = ContentType.objects.get_for_model(Assessment)
    old_assessment_ct = ContentType.objects.get_for_model(OldAssessment)
    
    for oa in OldAssessment.objects.all():
        na = Assessment()
        na.code=oa.code
        na.name=oa.name
        na.short_name=oa.short_name
        na.assessment_type = AssessmentType.objects.get(code=oa.assessment_type.code)
        na.course=oa.course
        na.description=oa.description
        na.detailed_description=oa.detailed_description
        na.instructions=oa.instructions
        na.instructions2=oa.instructions2
        na.notes=oa.notes
        na.allow_solution_buttons=oa.allow_solution_buttons
        na.fixed_order=oa.fixed_order
        na.single_version=oa.single_version
        na.resample_question_sets=oa.resample_question_sets
        na.save()

        ThreadContent = apps.get_model('micourses', 'ThreadContent')
    
        for tc in list(ThreadContent.objects.filter(object_id=oa.id, 
                                               content_type=old_assessment_ct)):
            tc.object_id=na.id
            tc.content_type=assessment_ct
            tc.save()

        for oqa in oa.questionassigned_set.all():
            na.questionassigned_set.create(question=oqa.question,
                                           question_set=oqa.question_set)

        for ogcv in oa.groups_can_view.all():
            na.groups_can_view.add(ogcv)
        for ogcv in oa.groups_can_view_solution.all():
            na.groups_can_view_solution.add(ogcv)

        for oabp in oa.assessmentbackgroundpage_set.all():
            na.assessmentbackgroundpage_set.create(page=oabp.page, 
                                                   sort_order=oabp.sort_order)

        for oqsd in oa.questionsetdetail_set.all():
            na.questionsetdetail_set.create(question_set=oqsd.question_set,
                                             weight=oqsd.weight, group=oqsd.group)


class Migration(migrations.Migration):

    dependencies = [
        ('micourses', '0013_auto_20150811_2300'),
    ]

    operations = [
        migrations.RunPython(copy_assessments),
    ]
