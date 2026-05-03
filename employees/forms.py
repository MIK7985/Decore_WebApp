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
        
        # Determine if the user is a manager (Admin or Office Staff)
        is_manager = self.user and (self.user.role in ['admin', 'office_staff'] or self.user.is_superuser)
        
        if self.user:
            # If not a manager, they are likely editing their own profile
            if not is_manager:
                # Remove sensitive business fields for standard employees
                restricted_fields = ['name', 'role', 'daily_wage', 'assigned_site', 'joining_date', 'status', 'notes']
                for field_name in restricted_fields:
                    if field_name in self.fields:
                        del self.fields[field_name]
            
            # Non-admins cannot set roles to office_staff
            if getattr(self.user, 'role', '') != 'admin' and not getattr(self.user, 'is_superuser', False):
                if 'role' in self.fields:
                    filtered_choices = [(k, v) for k, v in Employee.ROLE_CHOICES if k != 'office_staff']
                    self.fields['role'].choices = filtered_choices
                    self.fields['role'].widget.choices = filtered_choices

    class Meta:
        model = Employee
        fields = ['name','phone','role','profile_pic','daily_wage','assigned_site','address','joining_date','status','emergency_contact','notes']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name'}),
            'profile_pic': forms.FileInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'10-digit mobile number', 
                'pattern': '[0-9]{10}', 
                'title': 'Phone number must be exactly 10 digits', 
                'maxlength': '10', 
                'minlength': '10', 
                'type': 'tel', 
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
            }),
            'role': forms.Select(attrs={'class':'form-select'}),
            'daily_wage': forms.NumberInput(attrs={
                'class':'form-control',
                'step':'1',
                'min':'0', 
                'max':'3000',
                'oninput': "if(this.value > 3000) this.value = 3000; if(this.value < 0) this.value = 0;"
            }),
            'address': forms.Textarea(attrs={'class':'form-control','rows':3, 'maxlength':'500', 'placeholder':'Max 500 characters'}),
            'joining_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'emergency_contact': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'10-digit emergency number', 
                'pattern': '[0-9]{10}', 
                'title': 'Phone number must be exactly 10 digits', 
                'maxlength': '10', 
                'minlength': '10', 
                'type': 'tel', 
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
            }),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2, 'maxlength':'500', 'placeholder':'Max 500 characters'}),
        }

    def clean_daily_wage(self):
        wage = self.cleaned_data.get('daily_wage')
        if wage and wage > 3000:
            raise forms.ValidationError("Daily wage cannot exceed ₹3,000.")
        return wage

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            import re
            if not re.fullmatch(r'\d{10}', phone):
                raise forms.ValidationError("Mobile number must be exactly 10 digits.")
                
            qs = Employee.objects.filter(phone=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("An employee with this phone number already exists.")
        return phone

    def clean_emergency_contact(self):
        contact = self.cleaned_data.get('emergency_contact')
        if contact:
            import re
            if not re.fullmatch(r'\d{10}', contact):
                raise forms.ValidationError("Emergency contact must be exactly 10 digits.")
        return contact

