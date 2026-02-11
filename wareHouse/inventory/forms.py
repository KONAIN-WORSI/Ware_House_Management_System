from django import forms
from django.utils import timezone
from .models import Inventory, StockMovement
from products.models import Product
from warehouses.models import Warehouse, StorageLocation
from datetime import timedelta


class StockInForm(forms.ModelForm):
    "form for recording incoming stock"

    class Meta:
        model = StockMovement
        fields = '__all__'

        widgets = {
            'product':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_warehouse':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_location':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'quantity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'unit_price':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'batch_number':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Batch Number'    
            }),
            'expiry_date':forms.DateInput(attrs={
                'class':'form-control',
                'type':'date'
            }),
            'party_name':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Party Name'
            }),
            'notes':forms.Textarea(attrs={
                'class':'form-control',
                'placeholder':'Notes'
            }),
            'movement_date':forms.DateTimeInput(attrs={
                'class':'form-control',
                'type':'datetime-local'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set initial movement date to now
        if not self.instance.pk:
            self.initial['movement_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')

        if product and product.shelf_life_days and not cleaned_data.get('expiry_date'):
            movement_date = cleaned_data.get('movement_date') or timezone.now()
            cleaned_data['expiry_date'] = (movement_date + timedelta(days=product.shelf_life_days)).date()

        return cleaned_data


    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.movement_type = 'in'
        instance.transaction_type = 'purchase'

        if commit:
            instance.save()

        return instance


class StockOutForm(forms.ModelForm):
    "form for recording outgoing stock (sales, wastage, damage)"

    class Meta:
        model = StockMovement
        fields = '__all__'

        widgets = {
            'product':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'from_warehouse':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'from_location':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'quantity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'unit_price':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'party_name':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Party Name'
            }),
            'transaction_type':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'batch_number':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Batch Number'
            }),
            'movement_date':forms.DateTimeInput(attrs={
                'class':'form-control',
                'type':'datetime-local'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set initial movement date to now
        if not self.instance.pk:
            self.initial['movement_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

        # filter transaction types for stock out
        self.fields['transaction_type'].choices = [
            ('sales', 'Sales to cutomer'),
            ('wastage', 'Wastage'),
            ('damage', 'Damage/Spoiled'),
        ]

        def save(self, commit=True):
            instance = super().save(commit=False)
            instance.movement_type = 'out'

            if commit:
                instance.save()
            return instance


class StockTransferForm(forms.ModelForm):
    "form for transferring stock between warehouses"

    class Meta:
        model = StockMovement
        fields = '__all__'

        widgets = {
            'product':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'from_warehouse':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'from_location':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_warehouse':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_location':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'quantity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'unit_price':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'movement_date':forms.DateTimeInput(attrs={
                'class':'form-control',
                'type':'datetime-local'
            }),
            'batch_number':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Batch Number'
            }),
            'note':forms.Textarea(attrs={
                'class':'form-control',
                'placeholder':'Transfer Note'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set initial movement date to now
        if not self.instance.pk:
            self.initial['movement_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        from_warehouse = cleaned_data.get('from_warehouse')
        to_warehouse = cleaned_data.get('to_warehouse')

        if from_warehouse and to_warehouse and from_warehouse == to_warehouse:
            raise forms.ValidationError("Source and destination warehouses must be different.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.movement_type = 'transfer'
        instance.transaction_type = 'transfer'

        if commit:
            instance.save()
        return instance

class StockAdjustmentForm(forms.ModelForm):
    "form for adjusting stock quantity"

    class Meta:
        model = StockMovement
        fields = '__all__'

        widgets = {
            'product':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_warehouse':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'to_location':forms.Select(attrs={
                'class':'form-select',
                'required':True
            }),
            'quantity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'unit_price':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'0.00',
                'step':0.01,
                'required':True
            }),
            'movement_date':forms.DateTimeInput(attrs={
                'class':'form-control',
                'type':'datetime-local'
            }),
            'batch_number':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Batch Number'
            }),
            'note':forms.Textarea(attrs={
                'class':'form-control',
                'placeholder':'Adjustment Note'
            }),
            'reason':forms.Select(attrs={
                'class':'form-select',
                'placeholder':'Adjustment Reason',
                'required':True
            }),

        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.movement_type = 'adjustment'
        instance.transaction_type = 'adjustment'

        if commit:
            instance.save()
        return instance

        
