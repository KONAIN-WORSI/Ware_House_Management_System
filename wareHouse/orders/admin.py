from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'quantity_received']
    readonly_fields = ['line_total']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number',
        'supplier',
        'order_date',
        'deliver_to_warehouse',
        'total_amount',
        'status_badge',
        'items_count',
        'created_by'
    ]
    
    list_filter = ['status', 'order_date', 'supplier', 'deliver_to_warehouse']
    search_fields = ['po_number', 'supplier__name']
    date_hierarchy = 'order_date'
    
    readonly_fields = ['po_number', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'supplier', 'order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Delivery', {
            'fields': ('deliver_to_warehouse', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'shipping_cost', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_and_conditions')
        }),
        ('Metadata', {
            'fields': ('created_by', 'approved_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'approved': 'blue',
            'ordered': 'purple',
            'received': 'green',
            'completed': 'darkgreen',
            'cancelled': 'red'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def items_count(self, obj):
        return obj.get_items_count()
    items_count.short_description = 'Items'


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['line_total']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = [
        'so_number',
        'customer_name',
        'customer_phone',
        'order_date',
        'from_warehouse',
        'total_amount',
        'payment_status_badge',
        'status_badge',
        'items_count'
    ]
    
    list_filter = ['status', 'payment_status', 'order_date', 'from_warehouse']
    search_fields = ['so_number', 'customer_name', 'customer_phone']
    date_hierarchy = 'order_date'
    
    readonly_fields = ['so_number', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    
    inlines = [SalesOrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('so_number', 'order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Delivery Address', {
            'fields': ('delivery_address', 'delivery_city', 'delivery_state', 'delivery_postal_code')
        }),
        ('Order Details', {
            'fields': ('from_warehouse', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'delivery_charge', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
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
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'confirmed': 'blue',
            'processing': 'purple',
            'shipped': 'teal',
            'delivered': 'green',
            'completed': 'darkgreen',
            'cancelled': 'red'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'unpaid': 'red',
            'partial': 'orange',
            'paid': 'green'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.payment_status, 'gray'),
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    
    def items_count(self, obj):
        return obj.get_items_count()
    items_count.short_description = 'Items'