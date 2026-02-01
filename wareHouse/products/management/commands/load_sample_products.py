from django.core.management.base import BaseCommand
from products.models import ProductCategory, Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Load sample product data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample products...')
        
        # Get or create admin user
        user = User.objects.filter(is_superuser=True).first()
        
        # Create categories
        vegetables = ProductCategory.objects.get_or_create(
            name='Vegetables',
            defaults={'description': 'Fresh vegetables'}
        )[0]
        
        fruits = ProductCategory.objects.get_or_create(
            name='Fruits',
            defaults={'description': 'Fresh fruits'}
        )[0]
        
        grains = ProductCategory.objects.get_or_create(
            name='Grains',
            defaults={'description': 'Grains and cereals'}
        )[0]
        
        # Create products
        products_data = [
            ('Tomatoes', 'VEG-001', vegetables, 40, 60, 'kg', 3),
            ('Potatoes', 'VEG-002', vegetables, 30, 45, 'kg', 15),
            ('Onions', 'VEG-003', vegetables, 35, 50, 'kg', 20),
            ('Carrots', 'VEG-004', vegetables, 40, 60, 'kg', 10),
            ('Cauliflower', 'VEG-005', vegetables, 50, 80, 'piece', 5),
            ('Apples', 'FRT-001', fruits, 80, 120, 'kg', 10),
            ('Bananas', 'FRT-002', fruits, 40, 60, 'dozen', 5),
            ('Rice', 'GRN-001', grains, 50, 70, 'kg', 365),
        ]
        
        for name, sku, category, purchase, selling, unit, shelf_life in products_data:
            Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': category,
                    'purchase_price': purchase,
                    'selling_price': selling,
                    'unit': unit,
                    'shelf_life_days': shelf_life,
                    'reorder_level': 10,
                    'status': 'active',
                    'created_by': user
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Sample products loaded!'))
