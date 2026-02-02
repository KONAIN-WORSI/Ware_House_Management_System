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
        'unit',
        'status_badge',
        'created_at'
    ]

    list_filter = ['status', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'barcode']
    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = ['created_at', 'updated_at', 'created_by', 'image_preview']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'barcode', 'category')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Pricing', {
            'fields': ('purchase_price', 'selling_price', 'unit')
        }),
        ('Stock Management', {
            'fields': ('reorder_level', 'shelf_life_days')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return 'No Image'
    image_preview.short_description = 'Image Preview'

    def profit_display(self, obj):
        profit = obj.profit_amount
        margin = obj.profit_margin

        if profit > 0:
            return format_html(
                '<span style="color: green;">{:.2f} ({:.2f}%)</span>',
                profit, margin
            )
        return format_html(
            '<span style="color: red;">{:.2f} ({:.2f}%)</span>',
            profit
        )
    profit_display.short_description = 'Profit'

    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'orange',
            'disconnected': 'red'
        }

        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'