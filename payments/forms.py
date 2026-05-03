from django import forms
from .models import Payment
from employees.models import Employee
from salary.models import SalarySummary

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['employee','salary_summary','month','year','total_amount','paid_amount','payment_date','method','reference_number','notes']
        widgets = {
            'employee': forms.Select(attrs={'class':'form-select'}),
            'salary_summary': forms.Select(attrs={'class':'form-select'}),
            'month': forms.Select(attrs={'class':'form-select'}, choices=[(i,f'{i:02d}') for i in range(1,13)]),
            'year': forms.NumberInput(attrs={'class':'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'payment_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'method': forms.Select(attrs={'class':'form-select'}),
            'reference_number': forms.TextInput(attrs={'class':'form-control'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2, 'maxlength': '500', 'placeholder': 'Max 500 characters'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active')
        self.fields['salary_summary'].required = False
        self.fields['salary_summary'].queryset = SalarySummary.objects.all()
