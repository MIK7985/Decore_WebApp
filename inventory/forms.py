from django import forms
from .models import StorageFacility, Item, StorageStock, DispatchOrder, DispatchItem, MaterialRequest, DeliveryLog, DeliveryLogItem
from employees.models import Employee

class StorageFacilityForm(forms.ModelForm):
    class Meta:
        model = StorageFacility
        fields = ['name', 'location', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Storage 1 (Kochi)'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full address or area'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = Employee.objects.filter(role='storage_manager', status='active')

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'unit', 'unit_price', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Gypsum Board (Balath)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add selection prompts to dropdowns
        self.fields['unit'].choices = [('', '-- Select Unit --')] + list(self.fields['unit'].choices)[1:]
        self.fields['category'].choices = [('', '-- Select Category --')] + list(self.fields['category'].choices)[1:]

class AddStockForm(forms.Form):
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select an Item to Add/Update"
    )
    quantity_to_add = forms.DecimalField(
        max_digits=10, decimal_places=2, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount to add (use negative to reduce)'}),
        help_text="How many units did you manufacture or receive?"
    )

class MaterialRequestForm(forms.ModelForm):
    class Meta:
        model = MaterialRequest
        fields = ['site', 'item', 'custom_item_name', 'quantity', 'notes']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select', 'id': 'itemSelect'}),
            'custom_item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type item name if not in list', 'id': 'customItemInput'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount required', 'step': 'any'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional: e.g. Urgent, needed tomorrow'}),
        }

    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        if employee:
            from sites_mgmt.models import WorkSite
            # Get sites where this employee has an active assignment
            active_site_ids = employee.assignments.filter(is_active=True).values_list('site_id', flat=True)
            self.fields['site'].queryset = WorkSite.objects.filter(id__in=active_site_ids)
            if active_site_ids:
                self.fields['site'].initial = active_site_ids[0]
                
        # Make item not strictly required in HTML so we can submit custom
        self.fields['item'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        custom_item = cleaned_data.get('custom_item_name')
        
        if not item and not custom_item:
            raise forms.ValidationError("Please select an item from the list or enter a custom item name.")
            
        return cleaned_data

class DeliveryLogForm(forms.ModelForm):
    class Meta:
        model = DeliveryLog
        fields = ['source_storage', 'site', 'date', 'notes']
        widgets = {
            'source_storage': forms.Select(attrs={'class': 'form-select'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional: e.g. Left with site manager'}),
        }
        
class DeliveryLogItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryLogItem
        fields = ['item', 'quantity']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': 'any', 'min': '0.01', 'placeholder': 'Qty'}),
        }
        
    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return qty

class DeliveryLogItemFormSet(forms.BaseInlineFormSet):
    pass
