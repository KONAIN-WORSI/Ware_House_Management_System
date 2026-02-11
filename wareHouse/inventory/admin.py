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
    list_display = [
        'reference_number',
        'movement_type_badge',
        'transaction_type',
        'product',
        'quantity_display',
        'from_warehouse',
        'to_warehouse',
        'movement_date',
        'recorded_by',
    ]

    list_filter = ['movement_type', 'transaction_type','movement_date','from_warehouse','to_warehouse']
    search_fields = ['reference_number','product__name','party_name']
    date_hierarchy = 'movement_date'

    readonly_fields = ['reference_number', 'total_amount', 'created_at']

    fieldsets = (
        ('Movement Information', {
            'fields':('reference_number','movement_type','transaction_type','movement_date')
        }),
        ('Product Details', {
            'fields':('product','quantity','unit_price','total_amount','batch_number','expiry_date')
        }),
        ('Source (From)', {
            'fields':('from_warehouse', 'from_location')
        }),
        ('Destination (To)', {
            'fields':('to_warehouse', 'to_location')
        }),
        ('Additional Information', {
            'fields':('party_name','notes','reason')
        }),
        ('Metadata', {
            'fields': ('recorded_by', 'created_at'),
            'classes':('collapse',)
        }),
        
    )

    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

    def movement_type_badge(self, obj):
        colors = {
            'in':'green',
            'out':'red',
            'transfer':'blue',
            'adjustment':'orange'
        }

        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.movement_type, 'gray'),
            obj.get_movement_type_display()
        )
    movement_type_badge.short_description = 'Movement Type'

    def quantity_display(self, obj):
        return f"{obj.quantity} {obj.product.unit}"
    quantity_display.short_description = 'Quantity'



@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_type_badge',
        'inventory',
        'message',
        'status_badge',
        'acknowledged_by',
        'created_at'
    ]

    list_filter = ['alert_type', 'status', 'created_at']
    search_fields = ['inventory__product__name', 'message']

    readonly_fields = ['created_at', 'updated_at']

    def alert_type_badge(self, obj):
        colors = {
            'low_stock':'orange',
            'out_of_stock':'red',
            'expiring_soon':'yellow',
            'expired':'darkred'
        }

        return format_html(
            '<span style="background: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.alert_type, 'gray'),
            obj.get_alert_type_display()
        )
    alert_type_badge.short_description = 'Alert Type'

    def status_badge(self, obj):
        colors = {
            'active':'green',
            'acknowledged':'blue',
            'resolved':'orange'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    

    
