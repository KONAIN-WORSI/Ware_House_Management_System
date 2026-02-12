import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wareHouse.settings')
django.setup()

from products.models import Product, ProductCategory
from warehouses.models import Warehouse, StorageZone, StorageLocation
from inventory.models import Inventory, StockMovement
from accounts.models import User

def populate_dashboard_data():
    # 1. Ensure Categories and Products
    cat, _ = ProductCategory.objects.get_or_create(name="Electronics")
    cat2, _ = ProductCategory.objects.get_or_create(name="Furniture")
    
    p1, _ = Product.objects.get_or_create(
        sku="ELEC-001",
        defaults={
            "name": "Laptop",
            "category": cat,
            "purchase_price": 50000,
            "selling_price": 65000,
            "unit": "piece",
            "reorder_level": 5
        }
    )
    
    p2, _ = Product.objects.get_or_create(
        sku="FURN-001",
        defaults={
            "name": "Office Chair",
            "category": cat2,
            "purchase_price": 5000,
            "selling_price": 7500,
            "unit": "piece",
            "reorder_level": 10
        }
    )

    # 2. Ensure Warehouse
    admin = User.objects.filter(role='admin').first()
    if not admin:
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        admin.role = 'admin'
        admin.save()

    wh, _ = Warehouse.objects.get_or_create(
        code="WH-001",
        defaults={
            "name": "Central Warehouse",
            "city": "Mumbai",
            "state": "Maharashtra",
            "address": "Andheri East",
            "postal_code": "400001",
            "phone": "1234567890",
            "total_capacity": 10000,
            "manager": admin
        }
    )

    zone, _ = StorageZone.objects.get_or_create(
        warehouse=wh,
        code="ZA",
        defaults={"name": "Zone A", "capacity": 5000}
    )

    loc, _ = StorageLocation.objects.get_or_create(
        warehouse=wh,
        code="ZA-01",
        defaults={"zone": zone, "capacity": 1000}
    )

    # Pre-create Inventory to avoid ValueError on stock_out
    # We must ensure batch_number='' matches the model's logic if it uses '' instead of None
    for prod in [p1, p2]:
        Inventory.objects.get_or_create(
            product=prod,
            warehouse=wh,
            batch_number='',
            defaults={"quantity": 1000, "storage_location": loc}
        )

    # 3. Create Movements for Trends
    for i in range(20):
        days_ago = random.randint(0, 6)
        m_date = timezone.now() - timedelta(days=days_ago)
        m_type = random.choice(['in', 'out'])
        qty = random.randint(1, 10)
        prod = random.choice([p1, p2])
        
        ref = f"SM-TEST-{m_date.strftime('%Y%m%d%H%M%S')}-{i}"
        
        StockMovement.objects.create(
            reference_number=ref,
            product=prod,
            movement_type=m_type,
            transaction_type="purchase" if m_type == 'in' else "sale",
            quantity=qty,
            unit_price=prod.purchase_price if m_type == 'in' else prod.selling_price,
            to_warehouse=wh if m_type == 'in' else None,
            from_warehouse=wh if m_type == 'out' else None,
            movement_date=m_date,
            recorded_by=admin,
            batch_number=''
        )

    print("Dashboard test data populated successfully.")

if __name__ == "__main__":
    populate_dashboard_data()
