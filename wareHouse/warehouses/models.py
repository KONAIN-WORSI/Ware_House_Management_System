from enum import unique
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.text import slugify

# Create your models here.
User = get_user_model()

class Warehouse(models.Model):
    "main warehouse model"

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance')
    ]

    # basic information
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=100, unique=True, help_text='warehouse code e.g. WH-001')
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    # loaction address information
    address = models.TextField(help_text='full address of the warehouse')
    city = models.CharField(max_length=100, help_text='city of the warehouse')
    state = models.CharField(max_length=100, help_text='state of the warehouse')
    postal_code = models.CharField(max_length=20, help_text='postal code of the warehouse')
    country = models.CharField(max_length=100, default='Nepal', help_text='country of the warehouse')

    # contact information
    phone = models.CharField(max_lentgth=15, help_text='contact phone number of the warehouse')
    email = models.EmailField(blank=True, null=True)

    # manager
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        limit_choices_to={'role_in': ['admin', 'manager']}
    )

    # capacity 
    total_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='total capacity of the warehouse in square meters'
    )

    # status 
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='current status of the warehouse'
    )
    is_active = models.BooleanField(default=True)

    # description
    description = models.TextField(blank=True, null=True, help_text='additional information about the warehouse')

    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_warehouses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_total_locations(self):
        return self.locations.count()

    def get_occupied_capacity(self):
        return 0

    def get_available_capacity(self):
        return self.total_capacity - self.get_occupied_capacity()

    def capacity_percentage(self):
        if self.total_capacity == 0:
            return 0
        return (self.get_occupied_capacity() / self.total_capacity) * 100


class StorageZone(models.Model):
    "storage zones with in a warehouse(e.g. cold storage, dry storage)"

    