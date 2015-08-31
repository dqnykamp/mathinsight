from django import template
from django.template.base import (Node, NodeList, Template, Context, Library, Variable, TemplateSyntaxError, VariableDoesNotExist)
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import floatformat
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings

register=Library()

@register.inclusion_tag('micourses/threads/thread_section.html', takes_context=True)
def thread_section(context, section):
    return {'thread_section': section, 
            'id': section.id,
            'student': context.get('student'),
            'enrollment': context.get('enrollment'),
            'ltag': context['ltag'],
    }

@register.inclusion_tag('micourses/threads/thread_section_edit.html',
                        takes_context=True)
def thread_section_edit(context, section):

    move_left=True
    move_right=True
    move_up=True
    move_down=True

    if section.course:
        move_left = False
    
    siblings = section.return_siblings()
    sections_of_grandparent = None

    if section == siblings.first():
        move_right = False

    if section == siblings.first():
        if section.course:
            move_up=False
        else:
            sections_of_grandparent=section.parent.return_siblings()
            if section.parent == sections_of_grandparent.first():
                move_up=False

    if section == siblings.last():
        if section.course:
            move_down=False
        else:
            if not sections_of_grandparent:
                sections_of_grandparent=section.parent.return_siblings()
            if section.parent == sections_of_grandparent.last():
                move_down=False

    return {'thread_section': section, 
            'id': section.id,
            'ltag': context['ltag'],
            'move_left': move_left,
            'move_right': move_right,
            'move_up': move_up,
            'move_down': move_down,
    }

@register.inclusion_tag('micourses/threads/thread_content.html', takes_context=True)
def thread_content(context, content):
    student = context.get('student')
    enrollment = context.get('enrollment')

    # check if student already completed content
    try:
        completed = content.contentrecord_set\
            .get(enrollment=enrollment).complete
    except ObjectDoesNotExist:
        completed = False

    return {'thread_content': content, 
            'id': content.id,
            'student': student,
            'enrollment': enrollment,
            'completed': completed,
    }


@register.inclusion_tag('micourses/threads/thread_content_edit.html', 
                        takes_context=True)
def thread_content_edit(context, content):
    move_up=False
    move_down=False
    if content.find_previous() or content.section.find_previous():
        move_up=True
    if content.find_next() or content.section.find_next():
        move_down=True

    return {'thread_content': content, 
            'id': content.id,
            'move_up': move_up,
            'move_down': move_down,
    }
