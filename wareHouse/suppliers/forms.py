from django import forms
from .models import Supplier, SupplierProduct

class SupplierForm(forms.ModelForm):
    """Form for creating/updating suppliers"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'code', 'contact_person', 'email', 'phone', 'alternate_phone',
            'address', 'city', 'state', 'postal_code', 'country',
            'company_registration', 'tax_id', 'payment_terms', 'credit_limit',
            'rating', 'status', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SUP-001'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary phone'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternate phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'company_registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration number'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VAT/TIN'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Net 30'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
        }
    
    def clean_code(self):
        """Ensure supplier code is unique and uppercase"""
        code = self.cleaned_data.get('code')
        instance_id = self.instance.id if self.instance else None
        
        if Supplier.objects.filter(code=code).exclude(id=instance_id).exists():
            raise forms.ValidationError('This supplier code already exists.')
        
        return code.upper()


class SupplierProductForm(forms.ModelForm):
    """Form for adding products to suppliers"""
    
    class Meta:
        model = SupplierProduct
        fields = [
            'supplier', 'product', 'supplier_sku', 'unit_price',
            'minimum_order_quantity', 'lead_time_days', 'is_available', 'is_preferred'
        ]
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'supplier_sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Supplier's SKU"}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Days'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_preferred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }