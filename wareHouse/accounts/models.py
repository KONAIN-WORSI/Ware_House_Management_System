from django.contrib.auth.models import AbstractUser
from django.db import models 
# Create your models here.

class User(AbstractUser): 
    """
    Custom user model with role-based access
    Extends django's built-in user model
    """

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Warehouse Manager'),
        ('staff', 'staff')
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='staff',
        help_text = 'User role for access control'
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to = 'profiles/',
        blank=True,
        null=True,
        default='profiles/default.jpg',
        help_text = 'Profile image for the user'
    )
    employee_id = models.CharField(
        max_length = 50,
        blank=True,
        null=True,
        unique=True,
        help_text = 'Unique employee ID'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text = 'Department where the user works'
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        help_text = 'Date when the user joined the warehouse'
    )
    is_active = models.BooleanField(
        default=True,
        help_text = 'Whether the user is active or not'
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        permissions = [
            ('can_approve_order', 'Can approve orders'),
            ('can_view_reports', 'Can view reports'),
            ('can_manage_inventory', 'Can manage inventory'),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        "Returns the user's full name"
        full_name = f"{self.first_name} {self.last_name}".strip() or self.username
        return full_name if full_name else self.username

    @property
    def is_admin(self):
        "checks is user is admin or super user"
        return self.role ==  'admin' or self.is_superuser

    @property
    def is_manager(self):
        "checks is user is manager"
        return self.role == 'manager'

    @property
    def is_staff_member(self):
        "checks is user is staff"
        return self.role == 'staff'