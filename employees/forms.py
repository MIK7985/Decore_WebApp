from django import forms
from .models import Employee
from sites_mgmt.models import WorkSite

class EmployeeForm(forms.ModelForm):
    assigned_site = forms.ModelChoiceField(
        queryset=WorkSite.objects.filter(status='active'),
        required=False,
        empty_label="-- Select Default Site --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and getattr(self.user, 'role', '') != 'admin' and not getattr(self.user, 'is_superuser', False):
            # Non-admins cannot create other office_staff
            filtered_choices = [(k, v) for k, v in Employee.ROLE_CHOICES if k != 'office_staff']
            self.fields['role'].choices = filtered_choices
            self.fields['role'].widget.choices = filtered_choices

    class Meta:
        model = Employee
        fields = ['name','phone','role','profile_pic','daily_wage','assigned_site','address','joining_date','status','emergency_contact','notes']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name'}),
            'profile_pic': forms.FileInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control','placeholder':'+91 XXXXX XXXXX'}),
            'role': forms.Select(attrs={'class':'form-select'}),
            'daily_wage': forms.NumberInput(attrs={'class':'form-control','step':'0.01','min':'0'}),
            'address': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'joining_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'emergency_contact': forms.TextInput(attrs={'class':'form-control'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            qs = Employee.objects.filter(phone=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("An employee with this phone number already exists.")
        return phone
