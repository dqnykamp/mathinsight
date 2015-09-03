from django import forms
from micourses.models import PRESENT, ABSENT, EXCUSED

input_formats = ['%Y-%m-%d',      # '2006-10-25'
                 '%m/%d/%Y',      # '10/25/2006'
                 '%m/%d/%y',      # '10/25/06'
                 '%b %d %Y',      # 'Oct 25 2006'
                 '%b %d, %Y',     # 'Oct 25, 2006'
                 '%d %b %Y',      # '25 Oct 2006'
                 '%d %b, %Y',     # '25 Oct, 2006'
                 '%B %d %Y',      # 'October 25 2006'
                 '%B %d, %Y',     # 'October 25, 2006'
                 '%d %B %Y',      # '25 October 2006'
                 '%d %B, %Y']    # '25 October, 2006'

class DateForm(forms.Form):
    date = forms.DateField(input_formats=input_formats)




def attendance_dates_form_factory(course, student):

    thestudent=student

    class AttendanceDatesForm(forms.Form):
        student = forms.ModelChoiceField\
            (queryset=course.enrolled_students_ordered(), \
                 widget=forms.HiddenInput,\
                 initial=thestudent)
        
        def __init__(self, *args, **kwargs):
            try:
                dates = kwargs.pop('dates')
            except:
                dates =[]
            super(AttendanceDatesForm, self).__init__(*args, **kwargs)

            for i, attendance_date in enumerate(dates):
                self.fields['date_%s' % i] = forms.ChoiceField\
                    (label=str(attendance_date['date']),\
                         initial=attendance_date['present'],\
                         choices=((PRESENT,  PRESENT),(ABSENT, ABSENT),
                                  (EXCUSED, EXCUSED)),\
                         widget=forms.RadioSelect,
                     )
                
        def date_attendance(self):
            for name, value in self.cleaned_data.items():
                if name.startswith('date_'):
                    yield (self.fields[name].label, value)

    return AttendanceDatesForm


def select_student_form_factory(course):

    class SelectStudentForm(forms.Form):
        student = forms.ModelChoiceField(queryset=course\
                                         .enrolled_students_ordered())

    return SelectStudentForm
