from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F

from .models import Supplier, SupplierProduct
from .forms import SupplierForm, SupplierProductForm

# =====================
# SUPPLIER VIEWS
# =====================

@login_required
def supplier_list(request):
    """List all suppliers with search and filters"""
    suppliers = Supplier.objects.annotate(
        total_orders=Count('purchase_orders'),
        total_purchases=Sum('purchase_orders__total_amount')
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(contact_person__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        suppliers = suppliers.filter(status=status)
    
    # Filter by rating
    rating = request.GET.get('rating', '')
    if rating:
        suppliers = suppliers.filter(rating=rating)
    
    # Pagination
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    suppliers_page = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers_page,
        'search_query': search_query,
        'selected_status': status,
        'selected_rating': rating,
    }
    
    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def supplier_detail(request, pk):
    """View supplier details"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get supplier products
    supplier_products = supplier.supplier_products.select_related('product')
    
    # Get recent purchase orders
    recent_orders = supplier.purchase_orders.order_by('-order_date')[:10]
    
    context = {
        'supplier': supplier,
        'supplier_products': supplier_products,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'suppliers/supplier_detail.html', context)


@login_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            messages.success(request, f'Supplier "{supplier.name}" created successfully!')
            return redirect('suppliers:supplier_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
        'title': 'Add New Supplier',
        'button_text': 'Create Supplier'
    }
    
    return render(request, 'suppliers/supplier_form.html', context)


@login_required
def supplier_update(request, pk):
    """Update supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully!')
            return redirect('suppliers:supplier_detail', pk=supplier.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
        'title': 'Edit Supplier',
        'button_text': 'Update Supplier'
    }
    
    return render(request, 'suppliers/supplier_form.html', context)


@login_required
def supplier_delete(request, pk):
    """Delete supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier_name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier "{supplier_name}" deleted successfully!')
        return redirect('suppliers:supplier_list')
    
    context = {
        'supplier': supplier,
    }
    
    return render(request, 'suppliers/supplier_confirm_delete.html', context)