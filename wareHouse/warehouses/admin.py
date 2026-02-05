from django.contrib import admin
from .models import Warehouse, StorageLocation, StorageZone

# Register your models here.
@login_required
class WarehouseAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'city',
        'manager',
        'phone',
        'capacity_display',
        'status_badge',
        'is_active',
        'created_at'
    ]

    list_filter = ['status', 'is_active','city','created_at']
    search_fields = ['name','code','city','address']
    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = ['created_at','updated_at','created_by']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'slug', 'description')
        }),
        ('Location Details', {
            'fields': ('address','city','state','postal_code','country')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email','manager')
        }),
        ('Capacity & Status', {
            'fields': ('total_capacity','status','is_active')
        }),
        ('Metadata', {
            'fields': ('created_at','updated_at','created_by'),
            'classes': ('collapse',)
        })
    )

    



    
