from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from datetime import timedelta
from .models import Inventory, StockMovement, StockAlert
from .forms import StockInForm, StockOutForm, StockTransferForm, StockAdjustmentForm
from products.models import Product
from warehouses.models import Warehouse


# Create your views here.

# INVENTORY VIEWS
@login_required
def inventory_list(request):
    """
    Display a list of all inventories with pagination.
    """

    inventory_records = Inventory.objects.select_related('product', 'warehouse', 'storage_location').filter(quantity__gt=0)

    # search 
    search_query = request.GET.get('search', '')
    if search_query:
        inventory_records = inventory_records.filter(
            Q(product__name__icontains=search_query) |
            Q(product__sku__icontains=search_query) |
            Q(batch_number__icontains=search_query)
        )

    # filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_id)

    # filter by stock status
    stock_status = request.GET.get('status', '')

    if stock_status == 'low':
        inventory_records = [inv for inv in inventory_records if inv.is_low_stock]
    elif stock_status == 'expiring':
        inventory_records = [inv for inv in inventory_records if inv.is_expiring_soon]
    elif stock_status == 'expired':
        inventory_records = [inv for inv in inventory_records if inv.is_expired]


    # calculate summary stats
    total_value = sum(inv.get_total_value for inv in inventory_records)
    total_items = len(inventory_records)
    low_stock_count = sum(1 for inv in inventory_records if inv.is_low_stock)
    expiring_count = sum(1 for inv in inventory_records if inv.is_expiring_soon)

    # pagination
    if isinstance(inventory_records, list):
        # already filtered by python
        paginator = Paginator(inventory_records, 20)
    else:
        paginator = Paginator(inventory_records, 20)

    page_number = request.GET.get('page')
    inventory_page = paginator.get_page(page_number)

    warehouses = Warehouse.objects.filter(is_active=True)

    content = {
        'inventory_page': inventory_page,
        'warehouses': warehouses,
        'total_value': total_value,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
        'stock_status': stock_status,
        'search_query': search_query,
        'warehouse_id': warehouse_id,
    }

    return render(request, 'inventory/inventory_list.html', content)


@login_required
def inventory_detail(request, pk):
    'view detail inventory information'
    inventory = get_object_or_404(Inventory.objects.select_related('product', 'warehouse', 'storage_location'), pk=pk)

    # get  recent stock movements for this product in this warehouse
    movements = StockMovement.objects.filter(
        Q(from_warehouse=inventory.warehouse) | Q(to_warehouse=inventory.warehouse),
        product=inventory.product
    ).select_related('from_warehouse', 'to_warehouse', 'recorded_by').order_by('-movement_date')[:10]

    content = {
        'inventory': inventory,
        'movements':movements   
    }

    return render(request, 'inventory/inventory_detail.html', content)

@login_required
def stock_in(request):
    'handle stock in operations'
    if request.method == 'POST':
        form = StockInForm(request.POST)
        if form.is_valid():
            try:
                movement = form.save(commit=False)
                movement.recorded_by = request.user
                movement.save()
                messages.success(request, f'Stock IN recorded: {movement.quantity} {movement.product.unit} of {movement.product.name}')
                return redirect('inventory:stock_movement_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = StockInForm()

    content = {
        'form': form,
        'title':'Stock In - Receive Inventory',
        'movement_type':'in'
    }

    return render(request, 'inventory/stock_movement_form.html', content)


@login_required
def stock_out(request):
    "record outgoing stock"
     
    if request.method == 'POST':
        form = StockOutForm(request.POST)
        if form.is_valid():
            try:
                movement = form.save(commit=False)
                movement.recorded_by = request.user
                movement.save()
                messages.success(request, f'Stock OUT recorded: {movement.quantity} {movement.product.unit} of {movement.product.name}')
                return redirect('inventory:stock_movement_list')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = StockOutForm()

    content = {
        'form':form,
        'title':'Stock Out - Dispatch Inventory',
        'movement_type':'out'
    }

    return render(request, 'inventory/stock_movement_form.html', content)


@login_required
def stock_transfer(request):
    "transfer stock between warehouses"

    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        if form.is_valid():
            try:
                movement = form.save(commit=False)
                movement.recorded_by = request.user
                movement.save()
                messages.success(request, 
                f'Stock TRANSFER recorded: {movement.quantity} {movement.product.unit} of {movement.product.name}'
                f'from {movement.from_warehouse.code} to {movement.to_warehouse.code}'
                )
                return redirect('inventory:stock_movement_list')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = StockTransferForm()

    content = {
        'form':form,
        'title':'Stock Transfer - Move Inventory',
        'movement_type':'transfer'
    }

    return render(request, 'inventory/stock_movement_form.html', content)


@login_required
def stock_adjustment(request):
    "adjust stock for corrections"

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                movement = form.save(commit=False)
                movement.recorded_by = request.user
                movement.save()
                messages.success(request, 
                f'Stock ADJUSTMENT recorded: {movement.product.name} set to {movement.quantity} {movement.product.unit}'
                f'for {movement.warehouse.code}'
                )
                return redirect('inventory:stock_movement_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = StockAdjustmentForm()

    content = {
        'form':form,
        'title':'Stock Adjustment - Correct Inventory',
        'movement_type':'adjustment'
    }

    return render(request, 'inventory/stock_movement_form.html', content)

@login_required
def stock_movement_list(request):
    "list all stock movements with filters"
    movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'recorded_by'
    ).all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        movements = movements.filter(
            Q(reference_number__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(party_name__icontains=search_query)
        )
    
    # Filter by movement type
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        movements = movements.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        movements = movements.filter(movement_date__gte=date_from)
    if date_to:
        movements = movements.filter(movement_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(movements, 20)
    page_number = request.GET.get('page')
    movements_page = paginator.get_page(page_number)
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    content = {
        'movements': movements_page,
        'warehouses': warehouses,
        'search_query': search_query,
        'selected_type': movement_type,
        'selected_warehouse': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'inventory/stock_movement_list.html', content)


@login_required
def stock_movement_detail(request, pk):
    """View stock movement details"""
    movement = get_object_or_404(
        StockMovement.objects.select_related(
            'product', 'from_warehouse', 'to_warehouse',
            'from_location', 'to_location', 'recorded_by'
        ),
        pk=pk
    )
    
    content = {
        'movement': movement,
    }
    
    return render(request, 'inventory/stock_movement_detail.html', content)


@login_required
def inventory_dashboard(request):
    """Inventory overview dashboard"""
    # Total inventory value
    total_value = Inventory.objects.annotate(
        value=F('quantity') * F('product__purchase_price')
    ).aggregate(total=Sum('value'))['total'] or 0
    
    # Total products in stock
    total_products = Inventory.objects.filter(quantity__gt=0).count()
    
    # Low stock items
    low_stock_items = [
        inv for inv in Inventory.objects.select_related('product').filter(quantity__gt=0)
        if inv.is_low_stock
    ]
    
    # Expiring soon
    expiring_soon = [
        inv for inv in Inventory.objects.select_related('product').filter(
            expiry_date__isnull=False,
            quantity__gt=0
        ) if inv.is_expiring_soon
    ]
    
    # Recent movements
    recent_movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse'
    ).order_by('-movement_date')[:10]
    
    # Stock by warehouse
    warehouse_stock = Warehouse.objects.filter(is_active=True).annotate(
        total_items=Count('inventory_records', filter=Q(inventory_records__quantity__gt=0)),
        total_value=Sum(F('inventory_records__quantity') * F('inventory_records__product__purchase_price'))
    )
    
    content = {
        'total_value': total_value,
        'total_products': total_products,
        'low_stock_count': len(low_stock_items),
        'expiring_count': len(expiring_soon),
        'low_stock_items': low_stock_items[:5],
        'expiring_soon': expiring_soon[:5],
        'recent_movements': recent_movements,
        'warehouse_stock': warehouse_stock,
    }
    
    return render(request, 'inventory/dashboard.html', content)


@login_required
def acknowledge_alert(request, pk):
    """Acknowledge a stock alert"""
    alert = get_object_or_404(StockAlert, pk=pk)
    alert.acknowledge(request.user)
    messages.success(request, f"Alert for {alert.inventory.product.name} acknowledged.")
    return redirect('inventory:alerts')


@login_required
def stock_alerts(request):
    """View all stock alerts"""
    # filters
    status = request.GET.get('status', 'active')
    
    alerts = StockAlert.objects.select_related(
        'inventory__product', 'inventory__warehouse'
    ).order_by('-created_at')
    
    if status:
        alerts = alerts.filter(status=status)
    
    content = {
        'alerts': alerts,
        'selected_status': status,
    }
    
    return render(request, 'inventory/alerts.html', content)