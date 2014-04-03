from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

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

