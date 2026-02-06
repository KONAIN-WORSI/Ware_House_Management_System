from email.policy import default
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
    phone = models.CharField(max_length=15, help_text='contact phone number of the warehouse')
    email = models.EmailField(blank=True, null=True)

    # manager
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        limit_choices_to={'role__in': ['admin', 'manager']}
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
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)

    def get_total_locations(self):
        return self.storage_locations.count()

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

    ZONE_TYPE_CHOICES = [
        ('dry', 'Dry Storage'),
        ('cold', 'Cold Storage'),
        ('frozen', 'Frozen Storage'),
        ('ambient', 'Ambient Storage'),
        ('hazmat', 'Hazardous Material Storage'),
    ]

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='storage_zones'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPE_CHOICES, default='dry')

    # capacity
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='capacity of the storage zone in square meters'
    )

    # temprature (for cold storage)
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='minimum temperature in Celsius'
    )

    temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='maximum temperature in Celsius'
    )

    description = models.TextField(blank=True, null=True, help_text='additional information about the storage zone')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['warehouse', 'name']
        verbose_name = 'Storage Zone'
        verbose_name_plural = 'Storage Zones'
        unique_together = ['warehouse', 'code']

    def __str__(self):
        return f'{self.warehouse.code} - {self.name}'

    def get_total_locations(self):
        return self.locations.count()


class StorageLocation(models.Model):
    "specific storage location within a zone (e.g. A1, B2, etc.)"

    LOCATION_TYPE_CHOICES = [
        ('rack', 'Rack'),
        ('shelf', 'Shelf'),
        ('bin', 'Bin'),
        ('pallet', 'Pallet'),
        ('floor', 'Floor Space'),
    ]

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='storage_locations'
    )

    zone = models.ForeignKey(
        StorageZone,
        on_delete=models.CASCADE,
        related_name='locations',
        blank=True,
        null=True,
    )

    # location identifier
    code = models.CharField(max_length=50, help_text='unique location code')
    aisle = models.CharField(max_length=10, blank=True, null=True, help_text='aisle identifier (e.g. A, B, etc.)')
    rack = models.CharField(max_length=10, blank=True, null=True, help_text='rack identifier (e.g. 1, 2, etc.)')
    shelf = models.CharField(max_length=10, blank=True, null=True, help_text='shelf identifier (e.g. 1, 2, etc.)')
    bin = models.CharField(max_length=10, blank=True, null=True, help_text='bin identifier (e.g. 1, 2, etc.)')

    # capacity
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='maximum weigth capacity in kg'
    )

    # status
    is_occupied = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # notes
    notes = models.TextField(blank=True, null=True, help_text='additional information about the storage location')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['warehouse', 'code']
        verbose_name = 'Storage Location'
        verbose_name_plural = 'Storage Locations'
        
    def __str__(self):
        return f'{self.warehouse.code} - {self.code}'

    def get_display_name(self):
        'return formatted location name'

        parts = []
        if self.aisle:
            parts.append(self.aisle)
        if self.rack:
            parts.append(self.rack)
        if self.shelf:
            parts.append(self.shelf)
        if self.bin:
            parts.append(self.bin)

        return ' - '.join(parts) if parts else self.code

