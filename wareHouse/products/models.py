from itertools import product
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from inventory.models import Inventory
from django.db.models import Sum

# Create your models here.
User = get_user_model()

class ProductCategory(models.Model):
    " product category like vegetables, fruits, grains, etc"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_product_count(self):
        return self.products.filter(is_active=True).count()

class Product(models.Model):
    "main product model"

    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('gm', 'Gram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('dozen', 'Dozen'),
        ('pair', 'Pair'),
        ('piece', 'Piece'),
        ('bundle', 'Bundle'),
        ('box', 'Box'),
        ('unit', 'Unit'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('disconnected', 'Disconnected'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, help_text="Barcode", blank=True, null=True)

    # category
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True,
    )

    # description
    description = models.TextField(blank=True, null=True)

    # pricing
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Purchase price per unit",
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Selling price per unit",
    )

    # unit of measure
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')

    # stock management
    reorder_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Minimum stock level to trigger reorder",
    )

    # shelf life (for perishable items)
    shelf_life_days = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Shelf life in days (for perishable items)",
    )

    # Image
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
    )

    # status
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)

    # metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    
    @property
    def profit_margin(self):
        'calculate profit margin percentage'
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0

    def get_current_stock(self):
        "get current stock quantity accross all warehouses"
        total = Inventory.objects.filter(product=self).aggregate(
            total= Sum('quantity')
        )['total']
        return total or 0

    def get_stock_by_warehouse(self):
        "get stock breakdown by warehouse"
        return Inventory.objects.filter(product=self).select_related('warehouse')

    def is_low_stock(self):
        "check if stock is below reorder level"
        return self.get_current_stock() <= self.reorder_level

    def is_out_of_stock(self):
        "check if product is out of stock"
        return self.get_current_stock() == 0

        
