from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User
# Register your models here.

@admin.register(User)
class CustomeUserAdmin(BaseUserAdmin):
    "custom admin for user model"

    list_display = [
        'username',
        'email',
        'get_full_name',
        'role',
        'employee_id',
        'is_active',
        'is_staff_member',
        'date_joined'
    ]

    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-date_joined']

    # fieldsets for editing new users       
    add_fieldsets = (
        ('Login Information', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personla Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone'),
        }),
        ('Role & Access', {
            'fields': ('role', 'employee_id', 'department', 'is_active')
        })
    )

    #  make certain fields readonly
    readonly_fields = ['date_joined', 'last_login']

    # customs action
    actions = ['activate_users', 'deactivate_users', 'make_manager', 'make_staff']

    def activate_users(self, request, queryset):
        "activate selected users"
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} users activated successfully")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        "deactivate selected users"
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} users deactivated successfully")
    deactivate_users.short_description = "Deactivate selected users"

    def make_manager(self, request, queryset):
        "make selected users managers"
        updated = queryset.update(role='manager')
        self.message_user(request, f"{updated} users made managers successfully")
    make_manager.short_description = "Set as a manager"

    def make_staff(self, request, queryset):
        "make selected users staff"
        updated = queryset.update(role='staff')
        self.message_user(request, f"{updated} users made staff successfully")
    make_staff.short_description = "Set as staff"
