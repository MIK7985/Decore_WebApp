from django import forms
from .models import Attendance
from employees.models import Employee
from sites_mgmt.models import WorkSite

from django.core.exceptions import NON_FIELD_ERRORS

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee','site','date','status']
        widgets = {
            'employee': forms.Select(attrs={'class':'form-select'}),
            'site': forms.Select(attrs={'class':'form-select'}),
            'date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'status': forms.Select(attrs={'class':'form-select'}),
        }
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "Attendance is already marked for this employee on this date.",
            }
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active')
        self.fields['site'].queryset = WorkSite.objects.filter(status='active')
        self.fields['site'].required = False

class BulkAttendanceForm(forms.Form):
    site = forms.ModelChoiceField(queryset=WorkSite.objects.filter(status='active'),
                                  widget=forms.Select(attrs={'class':'form-select'}), required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'class':'form-control','type':'date'}))
