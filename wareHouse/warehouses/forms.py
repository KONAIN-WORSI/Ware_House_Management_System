from django import forms
from django.forms import widgets
from .models import Warehouse, StorageLocation, StorageZone


class WarehouseForm(forms.ModelForm):
    'form for creating/updating warehouses'

    class Meta:
        model = Warehouse
        fields = '__all__'

        widgets = {
            'name':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Enter warehouse name'
            }),
            'code':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. WH-001'
            }),
            'address':forms.TextInput(attrs={
                'class':'form-control',
                'rows':3,
                'placeholder':'Enter warehouse address'
            }),
            'city':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'City'
            }),
            'state':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'State/Province'
            }),
            'postal_code':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Postal Code'
            }),
            'country':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Country'
            }),
            'phone':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Phone Number'
            }),
            'email':forms.EmailInput(attrs={
                'class':'form-control',
                'placeholder':'Email Address'
            }),
            'manager':forms.Select(attrs={
                'class':'form-select',
            }),
            'total_capacity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'Total Capacity (in square meters)'
            }),
            'status':forms.Select(attrs={
                'class':'form-select'
            }),
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'rows':3,
                'placeholder':'Enter warehouse description'
            }),
        }

    def clean_code(self):
        'ensure warehouse code is unique and uppercase'

        code = self.cleaned_data.get('code')
        instance_id = self.instance.id if self.instance else None

        if Warehouse.objects.filter(code=code).exclude(id=instance_id).exists():
            raise forms.ValidationError('This warehouse code alredy exists.')
        
        return code.upper()


class StorageLocationForm(forms.ModelForm):
    'form for creating/updating storage locations'
    class Meta:
        model = StorageLocation
        fields = '__all__'

        widgets = {
            'warehouse':forms.Select(attrs={'class':'form-select'}),
            'zone':forms.Select(attrs={'class':'form-select'}),
            'code':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. A-12-03'
            }),
            'aisle':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. A-12-03'
            }),
            'rack':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. A-12-03'
            }),
            'shelf':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. A-12-03'
            }),
            'bin':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. A-12-03'
            }),
            'capacity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'kg',
                'step':'0.1'
            }),
            'is_active':forms.CheckboxInput(attrs={
                'class':'form-check-input'
            }),
            'notes':forms.Textarea(attrs={
                'class':'form-control',
                'rows':3,
                'placeholder':'Enter any additional notes'
            }),
        }
    
    def clean_code(self):
        'ensure the location code is unique and uppercase'

        code = self.cleaned_data.get('code')
        instance_id = self.instance.id if self.instance else None

        if StorageLocation.objects.filter(code=code).exclude(id=instance_id).exists():
            raise forms.ValidationError('This location code alredy exists.')
        
        return code.upper()

class StorageZoneForm(forms.ModelForm):
    'form for creating/updating storage zones'
    class Meta:
        model = StorageZone
        exclude = ['warehouse']

        widgets = {
            'code':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'e.g. Z-01'
            }),
            'name':forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Zone Name'
            }),
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'rows':3,
                'placeholder':'Enter zone description'
            }),
            'zone_type':forms.Select(attrs={'class':'form-select'}),
            'capacity':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'Square Meters',
                'step':'0.1'
            }),
            'temperature':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'Temperature (°C)',
                'step':'0.1'
            }),
            'temperature_max':forms.NumberInput(attrs={
                'class':'form-control',
                'placeholder':'Max Temperature (°C)',
                'step':'0.1'
            }),
            'is_active':forms.CheckboxInput(attrs={
                'class':'form-check-input'
            }),
        }


        