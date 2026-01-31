from itertools import product
from django import forms
from .models import Product, ProductCategory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'category', 'description',
            'purchase_price', 'selling_price', 'unit',
            'reorder_level', 'shelf_life_days', 'image', 'status'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. VEG-001'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter barcode (optional)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter product description'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter purchase price'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter selling price'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reorder_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reorder level'
            }),
            'shelf_life_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter shelf life in days'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'images/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }

        # Add labels
        labels = {
            'name': 'Product Name',
            'sku': 'SKU',
            'barcode': 'Barcode',
            'category': 'Category',
            'description': 'Description',
            'purchase_price': 'Purchase Price',
            'selling_price': 'Selling Price',
            'unit': 'Unit',
            'reorder_level': 'Reorder Level',
            'shelf_life_days': 'Shelf Life (Days)',
            'image': 'Product Image',
            'status': 'Status'
        }

    def clean_selling_price(self):
        "validate selling price is greater then purchase price"

        purchase_price = self.cleaned_data.get('purchase_price')
        selling_price = self.cleaned_data.get('selling_price')

        if purchase_price and selling_price:
            if selling_price <  purchase_price:
                raise forms.ValidationError(
                    'Selling price cannot be less than purchase price.'
                )
        return selling_price

    def clean_sku(self):
        'Ensure SKU is unique'
        sku = self. cleaned_data.get('sku')
        instance_id = self.instance.id if self.instance else None

        if Product.objects.filter(sku=sku).exclude(id=instance_id).exists():
            raise forms.ValidationError('SKU alredy exists.')

        return sku.upper()


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'is_active']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter category description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

        # Add labels
        labels = {
            'name': 'Category Name',
            'description': 'Description',
            'is_active': 'Active'
        }
