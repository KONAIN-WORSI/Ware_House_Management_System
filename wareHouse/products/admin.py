from django.contrib import admin
from django.contrib.auth.forms import AdminPasswordChangeForm
from .models import ProductCategory, Product
from django.utils.html import format_html

# Register your models here.
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'products_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def products_count(self, obj):
        count = obj.get_product_count()
        return format_html('<span style="color: {};">{}</span>',
                           'green' if count > 0 else 'red',
                           count)
    products_count.short_description = 'Products Count'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview',
        'name',
        'slug',
        'category',
        'purchase_price',
        'selling_price',
        'profit_display',
        'unit',
        'status_badge',
        'created_at'
    ]

    list_filter = ['status', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'barcode']
    prepopulated_fields = {'slug': ('name',)}

    
