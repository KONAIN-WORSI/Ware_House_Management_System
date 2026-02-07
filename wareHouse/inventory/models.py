from random import choices
from tabnanny import verbose
from tokenize import blank_re
from django.core import validators
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Q
from django.utils import timezone
from products.models import Product
from warehouses.models import Warehouse, StorageLocation


User = get_user_model()

class Inventory(models.Model):
    "current stock levels for each product in each warehouse This is the master inventory table - real-time stock tracking"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_records'
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='inventory_records'
    )
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.CASCADE,
        related_name='inventory_records'
    )

    # stock quantities
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='current available quantity'
    )
    reserved_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='quantity reserved for orders or sales'
    )

    # batch information (for tracking specific lots)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    manufacturing_date = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)

    # Metadata
    last_restocked = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['product', 'warehouse']
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventory Records'
        unique_together = ['product', 'warehouse', 'batch_number']

        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.code}: {self.quantity} {self.product.unit}"

    @property
    def available_quantity(self):
        'calculate available quantity (quantity - reserved_quantity)'
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        "check if stock is below a reorder level"
        return self.quantity <= self.product.reorder_level

    @property
    def is_expired(self):
        'check if product has expired'
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def days_until_expiry(self):
        "calculate days until expiry (if expiry date is set)"
        if self.expiry_date:
            delta = self.expiry_date.date() - timezone.now().date()
            return delta.days
        return None
    
    @property
    def is_expiring_soon(self):
        "check if product is expiring in next 3 days"
        days = self.days_until_expiry
        if days is not None:
            return 0 <= days <= 3
        return False

    @property
    def get_total_value(self):
        "calculate total value of inventory value purchase price"
        return self.quantity * self.product.purchase_price

    @property
    def get_potential_revenue(self):
        "calculate potential revenue at selling price"
        return self.quantity * self.product.selling_price


class StockMovement(models.Model):
    "Track all stock movements (IN/OUT/TRANSFER) complete audit trail of inventory changes"

    MOVEMENT_TYPE_CHOICES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('TRANSFER', 'Transfer'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'purchase from Supplier'),
        ('sale', 'Sale to Customer'),
        ('return', 'Customer Return'),
        ('damage', 'Damage/Spoiled'),
        ('wastage', 'Wastage'),
        ('transfer', 'Warehouse Transfer'),
        ('adjustment', 'Stock Adjustment'),
        ('opening', 'Opening Stock'),
    ]

    # movement details
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_number = models.CharField(max_length=100, unique=True, help_text='e.g., SM-2023-001')

    # product & location
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )


    # source (for OUT and TRANSFER)
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='outgoing_movements',
        null=True,
        blank=True
    )
    from_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        related_name='outgoing_movements',
        null=True,
        blank=True
    )

    # Destination (for IN and TRANSFER)
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='incoming_movements',
        null=True,
        blank=True
    )

    to_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        related_name='incoming_movements',
        null=True,
        blank=True
    )

    # Quantity & Pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='quantity moved in this transaction'
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='price per unit of the product'
    )

    total_amount = models.DecimalField(
        max_digit=12,
        decimal_places=2,
        editable=False,
        help_text='total amount (quantity * unit_price)'
    )

    # batch information
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)

    # customer / Supplier information
    party_name = models.CharField(max_length=200, blank=True, null=True, help_text='name of customer or supplier')

    # notes and reasons
    notes = models.TextField(blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True, null=True, help_text='reason for movement')

    # metadata
    movement_date = models.DateTimeField(default=timezone.now, help_text='date and time of movement')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date', '-created_at']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['movement_date']),
            models.Index(fields=['product', 'movement_date']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.product.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        # calculate total amount
        self.total_amount = self.quantity * self.unit_price

        # generate reference number if not exists
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()

        # save the movement
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # update inventory after saving
        if is_new:
            self.update_inventory()

