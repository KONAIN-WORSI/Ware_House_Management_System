from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator, MinValueValidator
from django.utils.text import slugify
from orders.models import PurchaseOrder

User = get_user_model()

# Create your models here.

class Supplier(models.Model):
    "Supplier/vendor model"  

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    ]

    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Excellent'),
        (4, '⭐⭐⭐⭐ Good'),
        (3, '⭐⭐⭐ Average'),
        (2, '⭐⭐ Below Average'),
        (1, '⭐ Poor'),
    ]

    # basic information
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    code  = models.CharField(max_length=100, unique=True, help_text="Unique code for the supplier")

    # contact information
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(validators=[EmailValidator()], blank=True, null=True)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True, null=True)

    # address information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    # bussiness details
    company_registration = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True, help_text="Tax ID or VAT number")


    # payment terms
    payment_terms = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="e.g. Net 30, COD, Advance Payment"
    )

    credit_limit = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Maximum amount the supplier is allowed to credit"
    )

    # rating & status
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        default=3,
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
    )

    is_active = models.BooleanField(default=True)

    # notes
    notes = models.TextField(blank=True, null=True)

    # Metadata
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_suppliers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_total_orders(self):
        "get total number of purchase orders"
        return self.purchase_orders.count()

    def get_total_purchases(self):
        "get total purchase amount"
        total = self.purchase_orders.filter(status='completed').aggregate(
            total=models.Sum('total_amount')
        )['total']
        return total or 0

    def get_pending_orders(self):
        "get count of pending orders"
        return self.purchase_orders.filter(status='pending').count()


class SupplierProduct(models.Model):
    "products supplied by each supplier with their prices"

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='supplied_products'
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='suppliers'
    )

    # supplier pricing
    supplier_sku = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="Supplier-specific SKU for the product"
    )

    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price of the product for the supplier"
    )

    minimum_order_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Minimum order quantity for the supplier"
    )

    # lead time
    lead_time_days = models.IntegerField(
        default=0,
        help_text="Lead time in days for the supplier"
    )

    # availability
    is_available = models.BooleanField(
        default=True,
        help_text="Is the product available for purchase from the supplier"
    )

    is_preferred = models.BooleanField(
        default=False,
        help_text="Is the product a preferred choice for the supplier"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['supplier', 'product']
        verbose_name = 'Supplier Product'
        verbose_name_plural = 'Supplier Products'
        unique_together = ['supplier', 'product']

    def __str__(self):
        return f"{self.product.name} - {self.supplier.name}"

