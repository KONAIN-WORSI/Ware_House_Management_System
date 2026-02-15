from django.contrib import admin
from django.utils.html import format_html
from .models import Supplier, SupplierProduct

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'contact_person',
        'phone',
        'city',
        'rating_display',
        'status_badge',
        'total_orders',
        'is_active'
    ]
    
    list_filter = ['status', 'rating', 'is_active', 'city', 'created_at']
    search_fields = ['name', 'code', 'contact_person', 'phone', 'email']
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'rating', 'status')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone', 'alternate_phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Business Details', {
            'fields': ('company_registration', 'tax_id', 'payment_terms', 'credit_limit')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span title="{}">{}</span>', obj.get_rating_display(), stars)
    rating_display.short_description = 'Rating'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'blocked': 'red'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_orders(self, obj):
        return obj.get_total_orders()
    total_orders.short_description = 'Total Orders'


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = [
        'supplier',
        'product',
        'supplier_sku',
        'unit_price',
        'minimum_order_quantity',
        'lead_time_days',
        'is_preferred',
        'is_available'
    ]
    
    list_filter = ['is_available', 'is_preferred', 'supplier']
    search_fields = ['supplier__name', 'product__name', 'supplier_sku']