from django import forms
from .models import WorkSite, EmployeeAssignment
from employees.models import Employee

class WorkSiteForm(forms.ModelForm):
    class Meta:
        model = WorkSite
        fields = ['name','location','square_feet','start_date','end_date','description','status','client_name','client_phone','client_email','estimated_cost']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'location': forms.TextInput(attrs={'class':'form-control'}),
            'square_feet': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'start_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'end_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3, 'maxlength':'500', 'placeholder': 'Max 500 characters'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'client_name': forms.TextInput(attrs={'class':'form-control'}),
            'client_phone': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'10-digit mobile number',
                'pattern': '[0-9]{10}',
                'title': 'Phone number must be exactly 10 digits',
                'maxlength':'10',
                'minlength':'10',
                'type': 'tel',
                'oninput':"this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
            }),
            'client_email': forms.EmailInput(attrs={'class':'form-control'}),
            'estimated_cost': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
        }

    def clean_client_phone(self):
        phone = self.cleaned_data.get('client_phone')
        if phone:
            import re
            if not re.fullmatch(r'\d{10}', phone):
                raise forms.ValidationError("Client phone number must be exactly 10 digits.")
        return phone

class SitePaymentForm(forms.ModelForm):
    class Meta:
        from .models import SitePayment
        model = SitePayment
        fields = ['amount', 'payment_date', 'method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class':'form-control', 'step':'0.01'}),
            'payment_date': forms.DateInput(attrs={'class':'form-control', 'type':'date'}),
            'method': forms.Select(attrs={'class':'form-select'}),
            'reference_number': forms.TextInput(attrs={'class':'form-control'}),
            'notes': forms.Textarea(attrs={'class':'form-control', 'rows': 2}),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = EmployeeAssignment
        fields = ['employee','supervisor','assigned_date','end_date','notes']
        widgets = {
            'employee': forms.Select(attrs={'class':'form-select'}),
            'supervisor': forms.Select(attrs={'class':'form-select'}),
            'assigned_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'end_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2, 'maxlength': '500', 'placeholder': 'Max 500 characters'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active')
        self.fields['supervisor'].queryset = Employee.objects.filter(status='active', role='main_worker')
        self.fields['supervisor'].required = False
