from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

User = get_user_model()


class PurchaseOrder(models.Model):
    """
    Purchase Orders from Suppliers
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Order Information
    po_number = models.CharField(max_length=50, unique=True, help_text="e.g., PO-2024-001")
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    
    # Delivery Details
    deliver_to_warehouse = models.ForeignKey(
        'warehouses.Warehouse',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders_created'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_approved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['order_date']),
        ]
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate PO number if not exists
        if not self.po_number:
            self.po_number = self.generate_po_number()
        
        # Calculate total
        self.calculate_total()
        
        super().save(*args, **kwargs)
    
    def generate_po_number(self):
        """Generate unique PO number"""
        date_str = timezone.now().strftime('%Y%m%d')
        last_po = PurchaseOrder.objects.filter(
            po_number__startswith=f'PO-{date_str}'
        ).order_by('-po_number').first()
        
        if last_po:
            last_seq = int(last_po.po_number.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f'PO-{date_str}-{new_seq:04d}'
    
    def calculate_total(self):
        """Calculate order totals"""
        items_total = self.items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or 0
        
        self.subtotal = items_total
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.shipping_cost - 
            self.discount_amount
        )
    
    def get_items_count(self):
        """Get total number of items"""
        return self.items.count()
    
    def mark_as_received(self):
        """Mark order as received and create stock movements"""
        if self.status != 'ordered':
            raise ValueError("Only ordered POs can be marked as received")
        
        self.status = 'received'
        self.actual_delivery_date = timezone.now().date()
        self.save()
        
        # Create stock movements for each item
        from inventory.models import StockMovement
        for item in self.items.all():
            StockMovement.objects.create(
                movement_type='in',
                transaction_type='purchase',
                product=item.product,
                to_warehouse=self.deliver_to_warehouse,
                quantity=item.quantity,
                unit_price=item.unit_price,
                reference_number=f"{self.po_number}-{item.id}",
                party_name=self.supplier.name,
                notes=f"Received from PO: {self.po_number}",
                recorded_by=self.created_by
            )


class PurchaseOrderItem(models.Model):
    """
    Line items in a Purchase Order
    """
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    
    # Quantity & Pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    # Delivery
    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Notes
    notes = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update PO totals
        self.purchase_order.calculate_total()
        self.purchase_order.save()
    
    @property
    def is_fully_received(self):
        """Check if item is fully received"""
        return self.quantity_received >= self.quantity
    
    @property
    def pending_quantity(self):
        """Get pending quantity"""
        return self.quantity - self.quantity_received


class SalesOrder(models.Model):
    """
    Sales Orders to Customers
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Order Information
    so_number = models.CharField(max_length=50, unique=True, help_text="e.g., SO-2024-001")
    
    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=15)
    
    # Delivery Address
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100)
    delivery_state = models.CharField(max_length=100)
    delivery_postal_code = models.CharField(max_length=20)
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    
    # Warehouse
    from_warehouse = models.ForeignKey(
        'warehouses.Warehouse',
        on_delete=models.PROTECT,
        related_name='sales_orders'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI/Digital Wallet'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit', 'Credit'),
        ],
        default='cash'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        default='unpaid'
    )
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_orders_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        indexes = [
            models.Index(fields=['so_number']),
            models.Index(fields=['order_date']),
        ]
    
    def __str__(self):
        return f"{self.so_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate SO number if not exists
        if not self.so_number:
            self.so_number = self.generate_so_number()
        
        # Calculate total
        self.calculate_total()
        
        super().save(*args, **kwargs)
    
    def generate_so_number(self):
        """Generate unique SO number"""
        date_str = timezone.now().strftime('%Y%m%d')
        last_so = SalesOrder.objects.filter(
            so_number__startswith=f'SO-{date_str}'
        ).order_by('-so_number').first()
        
        if last_so:
            last_seq = int(last_so.so_number.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f'SO-{date_str}-{new_seq:04d}'
    
    def calculate_total(self):
        """Calculate order totals"""
        items_total = self.items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or 0
        
        self.subtotal = items_total
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.delivery_charge - 
            self.discount_amount
        )
    
    def get_items_count(self):
        """Get total number of items"""
        return self.items.count()
    
    def mark_as_shipped(self):
        """Mark order as shipped and create stock movements"""
        if self.status not in ['confirmed', 'processing']:
            raise ValueError("Only confirmed/processing orders can be shipped")
        
        self.status = 'shipped'
        self.save()
        
        # Create stock movements for each item
        from inventory.models import StockMovement
        for item in self.items.all():
            StockMovement.objects.create(
                movement_type='out',
                transaction_type='sale',
                product=item.product,
                from_warehouse=self.from_warehouse,
                quantity=item.quantity,
                unit_price=item.unit_price,
                reference_number=f"{self.so_number}-{item.id}",
                party_name=self.customer_name,
                notes=f"Shipped for SO: {self.so_number}",
                recorded_by=self.created_by
            )


class SalesOrderItem(models.Model):
    """
    Line items in a Sales Order
    """
    
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sales_order_items'
    )
    
    # Quantity & Pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    # Notes
    notes = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Sales Order Item'
        verbose_name_plural = 'Sales Order Items'
    
    def __str__(self):
        return f"{self.sales_order.so_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update SO totals
        self.sales_order.calculate_total()
        self.sales_order.save()