

class HTMLOutliner:
    def __init__(self, numbered=True, default_css_class=""):
        self.numbered=numbered
        self.default_css_class=default_css_class
        self.previous_level=0
    def list_tag(self):
        if self.numbered:
            return "ol"
        else:
            return "ul"
    def return_html_transition_string(self, new_level, css_class=""):
        level_difference=new_level-self.previous_level
        self.previous_level = new_level
        html_string=""
        
        # if same level, just return item tag
        if level_difference==0:
            html_string = "</li>\n<li>"
        # if higher level, start new list(s)
        elif level_difference > 0:
            if not css_class:
                css_class=self.default_css_class
            if css_class:
                css_class_string=" class='%s'" % css_class
            else:
                css_class_string=""
            for i in range(level_difference):
                html_string="%s\n<%s%s>\n<li>" \
                    % (html_string, self.list_tag(), css_class_string)
        # if lower level, end previous list(s)
        else:
            for i in range(-level_difference):
                html_string="%s</li>\n</%s>\n" \
                    % (html_string, self.list_tag())
            html_string = html_string + "</li>\n<li>"

        return html_string
    
    def return_html_close_string(self):
        html_string=""
        for i in range(self.previous_level):
            html_string="%s</li>\n</%s>\n" \
                % (html_string, self.list_tag())
        return html_string



def return_section_insert_html(code, thread_id=None):
    toggle_command = "$('#insert_section_%s').toggle();$('#insert_section_form_container_%s').toggle();" \
                     % (code, code)
    link_html= '<a onclick="%s" class="edit_link" id="insert_section_%s">[insert section]</a>' \
            % (toggle_command, code)

    from mithreads.forms import ThreadSectionForm
    form = ThreadSectionForm(auto_id='insert_section_form_%s_%%s' % code)
    if(thread_id):
        thread_arg = ", %s" % thread_id
    else:
        thread_arg = ""
    insert_command = "post_edit_section(%s, 'insert', $('#insert_section_form_%s')%s)" \
                    % (code, code, thread_arg)

    button_html = '<input type="button" value="Add section" onclick="%s;">' \
                  % insert_command
    button_html += '<input type="button" value="Cancel" onclick="%s;">' \
                   % toggle_command

    form_html = '<p>%s %s' % (form['section_name'].label_tag(), form['section_name'].as_widget())
    form_html += ' <span id="insert_section_form_%s_section_name_errors" class="error"></span></p>' % (code)
    form_html += '<p>%s %s' % (form['section_code'].label_tag(), form['section_code'].as_widget())
    form_html += ' <span id="insert_section_form_%s_section_code_errors" class="error"></span></p>' % (code)
    form_html += '<p id="insert_section_form_%s_errors" class="error"></p>' % code

    form_html =  '<form  id="insert_section_form_%s" action="" method="post" accept-charset="utf-8">%s<p>%s</p></form>' \
                 % (code, form_html, button_html)

    form_html = '<div id="insert_section_form_container_%s" class="thread_info_box" style="display: none"><h5>Insert section</h5>%s</div>' \
                % (code, form_html)

    return link_html+form_html


def return_section_delete_html(thread_section):
    toggle_command = "$('#delete_section_%s').toggle();$('#delete_section_form_%s').toggle();" \
                     % (thread_section.id, thread_section.id)
    add_warning_command = "console.log($('#delete_section_warning').html());$('#delete_section_course_info_%s').html($('#delete_section_warning').html())" % thread_section.id
    link_html= ' <a onclick="%s%s" class="edit_link" id="delete_section_%s">[delete]</a>' \
            % (toggle_command, add_warning_command, thread_section.id)

    delete_html = "<h5>Confirm delete section</h5><p>Are you sure you want to delete the section and all its content: %s?</p>" % thread_section.name
    delete_html += "<div id='delete_section_course_info_%s'></div>" % thread_section.id

    delete_command = "post_edit_section(%s, 'delete')"  % thread_section.id

    delete_html += '<p><input type="button" value="Yes" onclick="%s;">' % \
                   delete_command

    delete_html += '<input type="button" value="No" onclick="%s;" style="margin-left: 3px;"></p>' % toggle_command

    delete_html = '<div id="delete_section_form_%s" style="display: none" class="thread_info_box">%s</div>' % \
                  (thread_section.id, delete_html)

    return (link_html,delete_html)


def return_section_edit_html(thread_section):
    toggle_command = "$('#edit_section_%s').toggle();$('#edit_section_form_container_%s').toggle();" \
                     % (thread_section.id, thread_section.id)
    link_html= ' <a onclick="%s" class="edit_link" id="edit_section_%s">[edit]</a>' \
            % (toggle_command, thread_section.id)

    from mithreads.forms import ThreadSectionForm
    form = ThreadSectionForm(
        {'section_name': thread_section.name, 
         'section_code': thread_section.code}, 
        auto_id='edit_section_form_%s_%%s' % thread_section.id)
    edit_command = "post_edit_section(%s, 'edit', $('#edit_section_form_%s'))" \
                    % (thread_section.id, thread_section.id)

    button_html = '<input type="button" value="Edit section" onclick="%s;">' \
                  % edit_command
    button_html += '<input type="button" value="Cancel" onclick="%s;">' \
                   % toggle_command

    form_html = '<p>%s %s' % (form['section_name'].label_tag(), form['section_name'].as_widget())
    form_html += ' <span id="edit_section_form_%s_section_name_errors" class="error"></span></p>' % (thread_section.id)
    form_html += '<p>%s %s' % (form['section_code'].label_tag(), form['section_code'].as_widget())
    form_html += ' <span id="edit_section_form_%s_section_code_errors" class="error"></span></p>' % (thread_section.id)
    form_html += '<p id="edit_section_form_%s_errors" class="error"></p>' % thread_section.id

    form_html =  '<form id="edit_section_form_%s" action="" method="post" accept-charset="utf-8">%s<p>%s</p></form>' \
                 % (thread_section.id, form_html, button_html)

    form_html = '<div id="edit_section_form_container_%s" class="thread_info_box" style="display: none"><h5>Edit section</h5>%s</div>' \
                % (thread_section.id, form_html)


    return link_html+form_html


def return_content_insert_html(code, thread_id=None):
    load_command = "$('#insert_content_%s').toggle();get_content_form({section_id: %s});" % (code, code);
    link_html= '<a onclick="%s" class="edit_link" id="insert_content_%s">[insert content]</a>' \
            % (load_command, code)
    link_html += "<div id='insert_content_form_%s'></div>" % code

    return link_html
