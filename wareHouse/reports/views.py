from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import csv

from products.models import Product, ProductCategory
from warehouses.models import Warehouse
from inventory.models import Inventory, StockMovement

# =====================
# MAIN REPORTS PAGE
# =====================

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    context = {
        'page_title': 'Reports & Analytics'
    }
    return render(request, 'reports/reports_dashboard.html', context)


# =====================
# INVENTORY REPORTS
# =====================

@login_required
def inventory_report(request):
    """Current inventory status report"""
    
    # Get filter parameters
    warehouse_id = request.GET.get('warehouse', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('status', '')
    
    # Base query
    inventory_records = Inventory.objects.select_related(
        'product', 'product__category', 'warehouse', 'storage_location'
    ).filter(quantity__gt=0)
    
    # Apply filters
    if warehouse_id:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_id)
    
    if category_id:
        inventory_records = inventory_records.filter(product__category_id=category_id)
    
    # Filter by stock status
    if stock_status:
        if stock_status == 'low':
            inventory_records = [inv for inv in inventory_records if inv.is_low_stock]
        elif stock_status == 'expiring':
            inventory_records = [inv for inv in inventory_records if inv.is_expiring_soon]
        elif stock_status == 'expired':
            inventory_records = [inv for inv in inventory_records if inv.is_expired]
    
    # Calculate summary statistics
    if isinstance(inventory_records, list):
        total_items = len(inventory_records)
        total_value = sum(inv.get_total_value() for inv in inventory_records)
        total_quantity = sum(inv.quantity for inv in inventory_records)
    else:
        total_items = inventory_records.count()
        total_value = inventory_records.annotate(
            value=F('quantity') * F('product__purchase_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        total_quantity = inventory_records.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Get filter options
    warehouses = Warehouse.objects.filter(is_active=True)
    categories = ProductCategory.objects.all()
    
    context = {
        'inventory_records': inventory_records,
        'total_items': total_items,
        'total_value': total_value,
        'total_quantity': total_quantity,
        'warehouses': warehouses,
        'categories': categories,
        'selected_warehouse': warehouse_id,
        'selected_category': category_id,
        'selected_status': stock_status,
    }
    
    return render(request, 'reports/inventory_report.html', context)


@login_required
def inventory_report_export(request):
    """Export inventory report to CSV"""
    
    # Get filters
    warehouse_id = request.GET.get('warehouse', '')
    category_id = request.GET.get('category', '')
    
    # Query data
    inventory_records = Inventory.objects.select_related(
        'product', 'product__category', 'warehouse'
    ).filter(quantity__gt=0)
    
    if warehouse_id:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_id)
    if category_id:
        inventory_records = inventory_records.filter(product__category_id=category_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventory_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Product Name', 'SKU', 'Category', 'Warehouse', 'Location',
        'Quantity', 'Unit', 'Purchase Price', 'Total Value',
        'Expiry Date', 'Batch Number'
    ])
    
    for inv in inventory_records:
        writer.writerow([
            inv.product.name,
            inv.product.sku,
            inv.product.category.name if inv.product.category else '-',
            inv.warehouse.name,
            inv.storage_location.code if inv.storage_location else '-',
            inv.quantity,
            inv.product.unit,
            inv.product.purchase_price,
            inv.get_total_value(),
            inv.expiry_date if inv.expiry_date else '-',
            inv.batch_number if inv.batch_number else '-',
        ])
    
    return response


# =====================
# LOW STOCK REPORT
# =====================

@login_required
def low_stock_report(request):
    """Report of products below reorder level"""
    
    warehouse_id = request.GET.get('warehouse', '')
    
    # Get all inventory
    inventory_records = Inventory.objects.select_related(
        'product', 'warehouse'
    ).filter(quantity__gt=0)
    
    if warehouse_id:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_id)
    
    # Filter low stock items
    low_stock_items = [inv for inv in inventory_records if inv.is_low_stock]
    
    # Sort by urgency (quantity vs reorder level)
    low_stock_items.sort(key=lambda x: x.quantity / x.product.reorder_level if x.product.reorder_level > 0 else 0)
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    context = {
        'low_stock_items': low_stock_items,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'total_items': len(low_stock_items),
    }
    
    return render(request, 'reports/low_stock_report.html', context)


# =====================
# STOCK MOVEMENT REPORT
# =====================

@login_required
def stock_movement_report(request):
    """Report of stock movements with filters"""
    
    # Get filter parameters
    movement_type = request.GET.get('type', '')
    warehouse_id = request.GET.get('warehouse', '')
    product_id = request.GET.get('product', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base query
    movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'recorded_by'
    ).all()
    
    # Apply filters
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    if warehouse_id:
        movements = movements.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    
    if product_id:
        movements = movements.filter(product_id=product_id)
    
    if date_from:
        movements = movements.filter(movement_date__gte=date_from)
    
    if date_to:
        movements = movements.filter(movement_date__lte=date_to)
    
    # Calculate summary
    total_movements = movements.count()
    total_value = movements.aggregate(total=Sum('total_amount'))['total'] or 0
    
    stock_in_count = movements.filter(movement_type='in').count()
    stock_out_count = movements.filter(movement_type='out').count()
    transfers_count = movements.filter(movement_type='transfer').count()
    
    # Get filter options
    warehouses = Warehouse.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    
    context = {
        'movements': movements[:100],  # Limit to 100 for performance
        'total_movements': total_movements,
        'total_value': total_value,
        'stock_in_count': stock_in_count,
        'stock_out_count': stock_out_count,
        'transfers_count': transfers_count,
        'warehouses': warehouses,
        'products': products,
        'selected_type': movement_type,
        'selected_warehouse': warehouse_id,
        'selected_product': product_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/stock_movement_report.html', context)


@login_required
def stock_movement_export(request):
    """Export stock movements to CSV"""
    
    # Get filters
    movement_type = request.GET.get('type', '')
    warehouse_id = request.GET.get('warehouse', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Query data
    movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'recorded_by'
    ).all()
    
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if warehouse_id:
        movements = movements.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    if date_from:
        movements = movements.filter(movement_date__gte=date_from)
    if date_to:
        movements = movements.filter(movement_date__lte=date_to)
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="stock_movements_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Reference', 'Date', 'Type', 'Transaction Type', 'Product',
        'Quantity', 'Unit Price', 'Total Amount', 'From Warehouse',
        'To Warehouse', 'Party Name', 'Recorded By'
    ])
    
    for movement in movements:
        writer.writerow([
            movement.reference_number,
            movement.movement_date.strftime('%Y-%m-%d %H:%M:%S'),
            movement.get_movement_type_display(),
            movement.get_transaction_type_display(),
            movement.product.name,
            movement.quantity,
            movement.unit_price,
            movement.total_amount,
            movement.from_warehouse.name if movement.from_warehouse else '-',
            movement.to_warehouse.name if movement.to_warehouse else '-',
            movement.party_name if movement.party_name else '-',
            movement.recorded_by.get_full_name() if movement.recorded_by else '-',
        ])
    
    return response


# =====================
# EXPIRY REPORT
# =====================

@login_required
def expiry_report(request):
    """Report of products expiring soon or expired"""
    
    warehouse_id = request.GET.get('warehouse', '')
    status = request.GET.get('status', 'expiring')  # expiring or expired
    
    # Get inventory with expiry dates
    inventory_records = Inventory.objects.select_related(
        'product', 'warehouse'
    ).filter(expiry_date__isnull=False, quantity__gt=0)
    
    if warehouse_id:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_id)
    
    # Filter by status
    if status == 'expiring':
        expiry_items = [inv for inv in inventory_records if inv.is_expiring_soon]
    elif status == 'expired':
        expiry_items = [inv for inv in inventory_records if inv.is_expired]
    else:
        expiry_items = list(inventory_records)
    
    # Sort by days until expiry
    expiry_items.sort(key=lambda x: x.days_until_expiry if x.days_until_expiry is not None else 999)
    
    # Calculate loss value for expired items
    if status == 'expired':
        total_loss = sum(inv.get_total_value() for inv in expiry_items)
    else:
        total_loss = 0
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    context = {
        'expiry_items': expiry_items,
        'warehouses': warehouses,
        'selected_warehouse': warehouse_id,
        'selected_status': status,
        'total_items': len(expiry_items),
        'total_loss': total_loss,
    }
    
    return render(request, 'reports/expiry_report.html', context)


# =====================
# WAREHOUSE PERFORMANCE REPORT
# =====================

@login_required
def warehouse_performance_report(request):
    """Performance report for each warehouse"""
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Default to last 30 days
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    if not date_to:
        date_to = timezone.now().date()
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    warehouse_stats = []
    for warehouse in warehouses:
        # Current inventory value
        inventory_value = Inventory.objects.filter(
            warehouse=warehouse
        ).annotate(
            value=F('quantity') * F('product__purchase_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        
        # Product count
        product_count = Inventory.objects.filter(
            warehouse=warehouse,
            quantity__gt=0
        ).count()
        
        # Stock movements in date range
        movements_in = StockMovement.objects.filter(
            to_warehouse=warehouse,
            movement_date__date__gte=date_from,
            movement_date__date__lte=date_to
        ).aggregate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        movements_out = StockMovement.objects.filter(
            from_warehouse=warehouse,
            movement_date__date__gte=date_from,
            movement_date__date__lte=date_to
        ).aggregate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        warehouse_stats.append({
            'warehouse': warehouse,
            'inventory_value': inventory_value,
            'product_count': product_count,
            'stock_in_count': movements_in['count'] or 0,
            'stock_in_value': movements_in['total'] or 0,
            'stock_out_count': movements_out['count'] or 0,
            'stock_out_value': movements_out['total'] or 0,
        })
    
    context = {
        'warehouse_stats': warehouse_stats,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/warehouse_performance_report.html', context)


# =====================
# PRODUCT PERFORMANCE REPORT
# =====================

@login_required
def product_performance_report(request):
    """Performance report for products"""
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category_id = request.GET.get('category', '')
    
    # Default to last 30 days
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    if not date_to:
        date_to = timezone.now().date()
    
    # Get products with movement activity
    products = Product.objects.filter(is_active=True)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    product_stats = []
    for product in products:
        # Current stock
        current_stock = Inventory.objects.filter(
            product=product
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Stock movements
        stock_in = StockMovement.objects.filter(
            product=product,
            movement_type='in',
            movement_date__date__gte=date_from,
            movement_date__date__lte=date_to
        ).aggregate(
            count=Count('id'),
            quantity=Sum('quantity'),
            value=Sum('total_amount')
        )
        
        stock_out = StockMovement.objects.filter(
            product=product,
            movement_type='out',
            movement_date__date__gte=date_from,
            movement_date__date__lte=date_to
        ).aggregate(
            count=Count('id'),
            quantity=Sum('quantity'),
            value=Sum('total_amount')
        )
        
        # Calculate turnover
        if stock_in['quantity'] and stock_out['quantity']:
            turnover_rate = (stock_out['quantity'] / stock_in['quantity']) * 100
        else:
            turnover_rate = 0
        
        product_stats.append({
            'product': product,
            'current_stock': current_stock,
            'stock_in_qty': stock_in['quantity'] or 0,
            'stock_out_qty': stock_out['quantity'] or 0,
            'stock_in_value': stock_in['value'] or 0,
            'stock_out_value': stock_out['value'] or 0,
            'turnover_rate': turnover_rate,
        })
    
    # Sort by turnover rate
    product_stats.sort(key=lambda x: x['turnover_rate'], reverse=True)
    
    categories = ProductCategory.objects.all()
    
    context = {
        'product_stats': product_stats[:50],  # Top 50
        'categories': categories,
        'selected_category': category_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/product_performance_report.html', context)


# =====================
# PROFIT ANALYSIS REPORT
# =====================

@login_required
def profit_analysis_report(request):
    """Profit analysis based on sales"""
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Default to current month
    if not date_from:
        date_from = timezone.now().date().replace(day=1)
    if not date_to:
        date_to = timezone.now().date()
    
    # Get sales (stock out as sales)
    sales = StockMovement.objects.filter(
        movement_type='out',
        transaction_type='sale',
        movement_date__date__gte=date_from,
        movement_date__date__lte=date_to
    ).select_related('product')
    
    # Calculate profit for each sale
    sales_data = []
    total_revenue = 0
    total_cost = 0
    
    for sale in sales:
        revenue = sale.total_amount
        cost = sale.quantity * sale.product.purchase_price
        profit = revenue - cost
        
        total_revenue += revenue
        total_cost += cost
        
        sales_data.append({
            'sale': sale,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': (profit / revenue * 100) if revenue > 0 else 0
        })
    
    total_profit = total_revenue - total_cost
    overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'sales_data': sales_data,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'overall_margin': overall_margin,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/profit_analysis_report.html', context)

