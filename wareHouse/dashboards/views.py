from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta

from products.models import Product, ProductCategory
from warehouses.models import Warehouse
from inventory.models import Inventory, StockMovement, StockAlert

@login_required
def dashboard(request):
    """Main dashboard with comprehensive overview"""
    
    # =====================
    # KEY METRICS
    # =====================
    
    # Total Inventory Value
    total_inventory_value = Inventory.objects.annotate(
        value=F('quantity') * F('product__purchase_price')
    ).aggregate(total=Sum('value'))['total'] or 0
    
    # Potential Revenue (if all sold at selling price)
    potential_revenue = Inventory.objects.annotate(
        revenue=F('quantity') * F('product__selling_price')
    ).aggregate(total=Sum('revenue'))['total'] or 0
    
    # Potential Profit
    potential_profit = potential_revenue - total_inventory_value
    
    # Total Products in Stock
    total_products_in_stock = Inventory.objects.filter(quantity__gt=0).count()
    
    # Total Warehouses
    total_warehouses = Warehouse.objects.filter(is_active=True).count()
    
    # =====================
    # ALERTS & WARNINGS
    # =====================
    
    # Low Stock Items
    low_stock_items = []
    for inv in Inventory.objects.select_related('product', 'warehouse').filter(quantity__gt=0):
        if inv.is_low_stock:
            low_stock_items.append(inv)
    
    # Out of Stock Items
    out_of_stock_products = Product.objects.filter(
        is_active=True
    ).exclude(
        inventory_records__quantity__gt=0
    ).count()
    
    # Expiring and Expired Items
    expiring_soon = []
    expired_items = []
    for inv in Inventory.objects.select_related('product', 'warehouse').filter(
        expiry_date__isnull=False,
        quantity__gt=0
    ):
        if inv.is_expired:
            expired_items.append(inv)
        elif inv.is_expiring_soon:
            expiring_soon.append(inv)
    
    # =====================
    # RECENT ACTIVITY
    # =====================
    
    # Recent Stock Movements (last 10)
    recent_movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'recorded_by'
    ).order_by('-movement_date')[:10]
    
    # Today's Stock Movements Summary
    today = timezone.now().date()
    today_movements = StockMovement.objects.filter(movement_date__date=today)
    
    stock_in_today = today_movements.filter(movement_type='in').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    stock_out_today = today_movements.filter(movement_type='out').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # =====================
    # WAREHOUSE BREAKDOWN
    # =====================
    
    warehouse_stats = []
    for warehouse in Warehouse.objects.filter(is_active=True):
        inventory_count = Inventory.objects.filter(
            warehouse=warehouse,
            quantity__gt=0
        ).count()
        
        warehouse_value = Inventory.objects.filter(
            warehouse=warehouse
        ).annotate(
            value=F('quantity') * F('product__purchase_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        
        warehouse_stats.append({
            'warehouse': warehouse,
            'inventory_count': inventory_count,
            'total_value': warehouse_value,
        })
    
    # =====================
    # CATEGORY BREAKDOWN
    # =====================
    
    category_stats = []
    for category in ProductCategory.objects.all():
        category_value = Inventory.objects.filter(
            product__category=category
        ).annotate(
            value=F('quantity') * F('product__purchase_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        
        if category_value > 0:
            category_stats.append({
                'category': category,
                'value': category_value,
            })
    
    # =====================
    # TOP PRODUCTS BY VALUE
    # =====================
    
    top_products_by_value = Inventory.objects.filter(
        quantity__gt=0
    ).annotate(
        total_value=F('quantity') * F('product__purchase_price')
    ).select_related('product', 'warehouse').order_by('-total_value')[:5]
    
    # =====================
    # MOVEMENT TRENDS (Last 7 days)
    # =====================
    
    last_7_days = []
    stock_in_trend = []
    stock_out_trend = []
    
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        last_7_days.append(date.strftime('%a'))
        
        # Stock IN for this day
        in_qty = StockMovement.objects.filter(
            movement_date__date=date,
            movement_type='in'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_in_trend.append(float(in_qty))
        
        # Stock OUT for this day
        out_qty = StockMovement.objects.filter(
            movement_date__date=date,
            movement_type='out'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_out_trend.append(float(out_qty))
    
    import json
    chart_labels_json = json.dumps(last_7_days)
    stock_in_trend_json = json.dumps(stock_in_trend)
    stock_out_trend_json = json.dumps(stock_out_trend)
    
    # =====================
    # ACTIVE ALERTS
    # =====================
    
    active_alerts = StockAlert.objects.filter(
        status='active'
    ).select_related('inventory__product', 'inventory__warehouse').order_by('-created_at')[:5]
    
    context = {
        # Key Metrics
        'total_inventory_value': total_inventory_value,
        'potential_revenue': potential_revenue,
        'potential_profit': potential_profit,
        'total_products_in_stock': total_products_in_stock,
        'total_warehouses': total_warehouses,
        
        # Alerts
        'low_stock_count': len(low_stock_items),
        'low_stock_items': low_stock_items[:5],
        'out_of_stock_count': out_of_stock_products,
        'expiring_soon_count': len(expiring_soon),
        'expiring_soon': expiring_soon[:5],
        'expired_count': len(expired_items),
        'expired_items': expired_items[:5],
        
        # Activity
        'recent_movements': recent_movements,
        'stock_in_today': stock_in_today,
        'stock_out_today': stock_out_today,
        
        # Breakdowns
        'warehouse_stats': warehouse_stats,
        'category_stats': category_stats,
        'top_products': top_products_by_value,
        
        # Charts Data
        'chart_labels': chart_labels_json,
        'stock_in_trend': stock_in_trend_json,
        'stock_out_trend': stock_out_trend_json,
        
        # Alerts
        'active_alerts': active_alerts,
    }
    
    return render(request, 'dashboard/dashboard.html', context)