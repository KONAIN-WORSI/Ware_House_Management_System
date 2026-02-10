from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, F
from .models import Inventory, StockMovement, StockAlert

# Register your models here.
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'warehouse',
        'storage_location',
        'quantity',
        'reserved_quantity',
        'available_quantity',
        'batch_number',
        'is_expired',
        'is_low_stock',
        'last_restocked'
    ]
    
    list_filter = [
        'warehouse',
        'product__category',
        'expiry_date'
    ]
    search_fields = ['product__name', 'product__sku', 'batch_number', 'warehouse__name']

    def quantity_display(self, obj):
        return f"{obj.quantity} {obj.product.unit}"
    quantity_display.short_description = 'Quantity'

    def available_display(self, obj):
        available = obj.available_quantity
        return format_html(
            '<span style="color: {};">{} {}</span>',
            'green' if available > 0 else 'red',
            available,
            obj.product.unit
        )
    available_display.short_description = 'Available'

    def expiry_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">⚠️ Expired</span>')
        elif obj.is_expiring_soon:
            days = obj.days_until_expiry
            return format_html('<span style="color: orange;">⚠️ Expiring in {} days</span>', days)
        elif obj.expiry_date:
            return format_html(f'<span style="color:green;">{obj.days_until_expiry} days</span>,', obj.days_until_expiry)
        
        return '-'
    expiry_status.short_description = 'Expiry Status'

    def stock_status(self, obj):
        if obj.available_quantity == 0:
            return format_html('<span style="color: red;">OUT OF STOCK</span>')
        elif obj.available_quantity <= obj.reorder_level:
            return format_html('<span style="color: orange;">LOW STOCK</span>')
        else:
            return format_html('<span style="color: green;">IN STOCK</span>')
    stock_status.short_description = 'Stock Status'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = []
