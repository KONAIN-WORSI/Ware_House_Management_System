from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import PurchaseOrder, SalesOrder
from .forms import PurchaseOrderForm, SalesOrderForm

# =====================
# PURCHASE ORDER VIEWS
# =====================

@login_required
def purchase_order_list(request):
    """List all purchase orders"""
    orders = PurchaseOrder.objects.select_related(
        'supplier', 'deliver_to_warehouse', 'created_by'
    ).all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(po_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
        'search_query': search_query,
        'selected_status': status,
    }
    
    return render(request, 'orders/purchase_order_list.html', context)


@login_required
def purchase_order_detail(request, pk):
    """View purchase order details"""
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'deliver_to_warehouse', 'created_by'),
        pk=pk
    )
    
    items = order.items.select_related('product')
    
    context = {
        'order': order,
        'items': items,
    }
    
    return render(request, 'orders/purchase_order_detail.html', context)


@login_required
def purchase_order_create(request):
    """Create new purchase order"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, f'Purchase Order {order.po_number} created successfully!')
            return redirect('orders:purchase_order_detail', pk=order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm()
    
    context = {
        'form': form,
        'title': 'Create Purchase Order',
    }
    
    return render(request, 'orders/purchase_order_form.html', context)


# =====================
# SALES ORDER VIEWS
# =====================

@login_required
def sales_order_list(request):
    """List all sales orders"""
    orders = SalesOrder.objects.select_related('from_warehouse', 'created_by').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(so_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
        'search_query': search_query,
        'selected_status': status,
    }
    
    return render(request, 'orders/sales_order_list.html', context)


@login_required
def sales_order_detail(request, pk):
    """View sales order details"""
    order = get_object_or_404(
        SalesOrder.objects.select_related('from_warehouse', 'created_by'),
        pk=pk
    )
    
    items = order.items.select_related('product')
    
    context = {
        'order': order,
        'items': items,
    }
    
    return render(request, 'orders/sales_order_detail.html', context)


@login_required
def sales_order_create(request):
    """Create new sales order"""
    if request.method == 'POST':
        form = SalesOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, f'Sales Order {order.so_number} created successfully!')
            return redirect('orders:sales_order_detail', pk=order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SalesOrderForm()
    
    context = {
        'form': form,
        'title': 'Create Sales Order',
    }
    
    return render(request, 'orders/sales_order_form.html', context)