from itertools import product
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
from wareHouse import inventory
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

    def generate_reference_number(self):
        "generate unique reference number for stock movement"

        date_str = timezone.now().strftime('%Y-%m-%d')

        # get last movement for today
        last_movement = StockMovement.objects.filter(
            reference_number__startswith=f'SM-{date_str}'
        ).order_by('-reference_number').first()

        if last_movement:
            # extract sequence number and increment
            last_seq = int(last_movement.reference_number.split('-')[-1])
            new_seq = last_seq + 1
        else:
            # start with 1 if no previous movement
            new_seq = 1

        return f'SM-{date_str}-{new_seq:04d}'

    def update_inventory(self):
        "update inventory based on movement type"

        if self.movement_type == 'in':
            # stock in - increase inventory
            self.stock_in()
        elif self.movement_type == 'out':
            # stock out - decrease inventory
            self.stock_out()
        elif self.movement_type == 'transfer':
            # transfer - adjust both source and destination
            self.stock_transfer()
        elif self.movement_type == 'adjust':
            # adjust - manual change in inventory
            self.stock_adjustment()

    def stock_in(self):
        # handle stock in - increase inventory
        if not self.to_warehouse:
            raise ValueError("Destination warehouse is required for stock in")

        # get or create inventory record
        inventory, created = Inventory.objects.get_or_create(
            product=self.product,
            warehouse=self.to_warehouse,
            batch_number=self.batch_number or '',
            defaults={
                'storage_location': self.to_location,
                'quantity':0,
                'expiry_date':self.expiry_date
            }
        )

        # increase quantity
        inventory.quantity = F('quantity') + self.quantity
        if self.to_location:
            inventory.storage_location = self.to_location
        inventory.save()

        # refresh from database
        inventory.refresh_from_db()

        # update location status
        if self.to_location:
            self.to_location.is_occupies = True
            self.to_location.save()


    def stock_out(self):
        # handle stock out -decrease inventory

        if not self.from_warehouse:
            raise ValueError("Source warehouse is required for stock out")

        # find inventory record
        try:
            inventory = Inventory.objects.get(
                product=self.product,
                warehouse=self.from_warehouse,
                batch_number=self.batch_number or '',
            )
        except Inventory.DoesNotExist:
            raise ValueError(f"No inventory record found for {self.product.name} product and batch number")

        # check if enough stock
        if inventory.quantity < self.quantity:
            raise ValueError(f"Insufficient stock. Available: {inventory.quantity}, Required: {self.quantity}")

        # decrease quantity
        inventory.quantity = F('quantity') - self.quantity
        inventory.save()

        # referesh from database
        inventory.refresh_from_db()

        # if quantity is 0, mark location as available
        if inventory.quantity == 0:
            if inventory.storage_location:
                inventory.storage_location.is_occupies = False
                inventory.storage_location.save()

    
    def stock_transfer(self):
        # handle stock transfer - move between warehouses

        if not self.from_warehouse or not self.to_warehouse:
            raise ValueError("Source and destination warehouses are required for stock transfer")

        # decrease from source
        self.stock_out()

        # increase at destination
        self.stock_in()

    def stock_adjustment(self):
        # handle stock adjustment - manual change in inventory
        if not self.warehouse:
            raise ValueError("Warehouse is required for stock adjustment")

        # get or create inventory record
        inventory, created = Inventory.objects.get_or_create(
            product=self.product,
            warehouse=self.warehouse,
            batch_number=self.batch_number or '',
            defaults={
                'quantity':0           
            }
        )

        # set to exact quantity (adjustment sets absolute value)
        inventory.quantity = self.quantity
        inventory.save()


class StockAlert(models.Model):
    # Track stock alerts (low_stock, expiring soon, etc.)

    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock Alert'),
        ('out_of_stock', 'Out of Stock Alert'),
        ('expiring_soon', 'Expiring Soon Alert'),
        ('expired', 'Expired'),
    ]

    STATU_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='alerts',
    )

    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATU_CHOICES,
        default='active',
    )

    message = models.TextField()

    acknowledged_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Alert'
        verbose_name_plural = 'Stock Alerts'

    def __str__(self):
        return f"{self.alert_type} - {self.inventory.product.name}"

    def acknowledge(self):
        # mark alert as acknowledged
        self.status = 'acknowledged'
        self.acknowledge_by = user
        self.acknowledged_at = timezone.now()
        self.save()

    def resolve(self):
        # mark alert as resolved
        self.status = 'resolved'
        self.save()
