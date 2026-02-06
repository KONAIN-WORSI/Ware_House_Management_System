from django.contrib import admin
from .models import Warehouse, StorageLocation, StorageZone
from django.utils.html import format_html

# Register your models here.
@admin.register(Warehouse)
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

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def capacity_display(self, obj):
        percentage = obj.capacity_percentage()
        color = 'green' if percentage > 70 else 'orange' if percentage < 90 else 'red'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 5px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; color: white; padding: 2px 5px; font-size: 11px;">{:.1f}%</div>'
            '</div>',
            percentage, color, percentage
        )
    capacity_display.short_description = 'Capacity'

    def status_badge(self, obj):
        colors = {
            'active':'green',
            'inactive':'gray',
            'maintenance':'orange'
        }

        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(StorageZone)
class StorageZoneAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'warehouse',
        'zone_type',
        'capacity',
        'temperature_range',
        'locations_count',
        'is_active'
    ]

    list_filter = ['warehouse','zone_type','is_active']
    search_fields = ['name','code','warehouse__name']

    fieldsets = (
        ('Basic Information', {
            'fields':('name', 'code', 'zone_type', 'description')
        }),
        ('Capacity & Temperature', {
            'fields':('capacity','temperature','temperature_max')
        }),
        ('Status', {
            'fields':('is_active',)
        })
    )

    def temperature_range(self, obj):
        if obj.temperature_min is not None and obj.temperature_max is not None:
            return f'{obj.temperature_min} C - {obj.temperature_max} C'
        return '-'
    temperature_range.short_description = 'Temperature Range'

    def locations_count(self, obj):
        count = obj.get_total_locations()
        return format_html(
            '<span class="badge badge-info">{}</span>', count)
    locations_count.short_description = 'Locations'


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'warehouse',
        'zone',
        'position_display',
        'capacity',
        'occupied_badge',
        'is_active'
    ]

    list_filter = ['warehouse','zone','is_active', 'is_occupied']
    search_fields = ['code', 'aisle', 'rack', 'shelf', 'warehouse__name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('warehouse', 'zone', 'code')
        }),
        ('Position & Capacity', {
            'fields': ('aisle', 'rack', 'shelf', 'capacity')
        }),
        ('Capacity & Status', {
            'fields': ('is_active', 'is_occupied')
        }),
        ('Notes', {
            'fields':('notes',)
        })
    )

    def position_display(self, obj):
        return obj.get_display_name()
    position_display.short_description = 'Position'

    def occupied_badge(self, obj):
        if obj.is_occupied:
           return format_html('<span style="color: red;">● Occupied</span>')
        return format_html('<span style="color: green;">● Available</span>')
    occupied_badge.short_description = 'Status'




    
