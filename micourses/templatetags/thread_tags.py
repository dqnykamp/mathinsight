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
    course=context['course']
    thread_contents = section.thread_contents.all()
    thread_contents = course.thread_content_select_related_content_objects(thread_contents)

    child_sections = section.child_sections.all()
    
    return {'thread_section': section, 
            'id': section.id,
            'student': context.get('student'),
            'enrollment': context.get('enrollment'),
            'ltag': context['ltag'],
            'course': course,
            'thread_contents': thread_contents,
            'content_records': context.get('content_records'),
            'child_sections': child_sections,
    }

@register.inclusion_tag('micourses/threads/thread_section_edit.html',
                        takes_context=True)
def thread_section_edit(context, section):

    course=context['course']
    thread_contents = section.thread_contents.all()
    thread_contents = course.thread_content_select_related_content_objects(thread_contents)
    siblings = list(context['child_sections'])
    sections_of_grandparent = context.get('sibling_sections')
    child_sections = section.child_sections.all()


    move_left=True
    move_right=True
    move_up=True
    move_down=True

    try:
        first_sibling = siblings[0]
        last_sibling = siblings[-1]
    except IndexError:
        first_sibling = None
        last_sibling = None
        
    
    if section.course:
        move_left = False
    
    if section == first_sibling:
        move_right = False

    if section == first_sibling:
        if section.course:
            move_up=False
        else:
            sections_of_grandparent = list(sections_of_grandparent)
            try:
                if section.parent == sections_of_grandparent[0]:
                    move_up=False
            except IndexError:
                pass

    if section == last_sibling:
        if section.course:
            move_down=False
        else:
            sections_of_grandparent = list(sections_of_grandparent)
            try:
                if section.parent == sections_of_grandparent[-1]:
                    move_down=False
            except IndexError:
                pass

    return {'thread_section': section, 
            'id': section.id,
            'ltag': context['ltag'],
            'move_left': move_left,
            'move_right': move_right,
            'move_up': move_up,
            'move_down': move_down,
            'child_sections': child_sections,
            'sibling_sections': siblings,
            'course': course,
            'thread_contents': thread_contents,
            'all_thread_contents': context['all_thread_contents'],
    }

@register.inclusion_tag('micourses/threads/thread_content.html', takes_context=True)
def thread_content(context, content):
    student = context.get('student')
    enrollment = context.get('enrollment')
    content_records = context.get('content_records')

    completed=False
    if content_records:
        try:
            completed = content_records[content.id].complete
        except KeyError:
            pass

    return {'thread_content': content, 
            'id': content.id,
            'student': student,
            'enrollment': enrollment,
            'completed': completed,
    }


@register.inclusion_tag('micourses/threads/thread_content_edit.html', 
                        takes_context=True)
def thread_content_edit(context, content):
    all_thread_contents = context['all_thread_contents']
    
    move_up=False
    move_down=False
    if content.find_previous(thread_contents=all_thread_contents) or content.section.find_previous():
        move_up=True
    if content.find_next(thread_contents=all_thread_contents) or content.section.find_next():
        move_down=True

    return {'thread_content': content, 
            'id': content.id,
            'move_up': move_up,
            'move_down': move_down,
    }
