from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Warehouse, StorageZone, StorageLocation
from .forms import WarehouseForm, StorageZoneForm, StorageLocationForm

# Create your views here.
# Warehouse Views

@login_required
def warehouse_list(request):
    'list all warehouses with search and filters'

    warehouses = Warehouse.objects.select_related('manager').annotate(
        total_zones = Count('storage_zones', distinct=True),
        total_locations = Count('storage_locations', distinct=True),
        total_products = Count('inventory_records__product', distinct=True)
    )

    # search 
    search_query = request.GET.get('search', '')
    if search_query:
        warehouses = warehouses.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(city__icontains=search_query)
        )

    # filter by status
    status = request.GET.get('status', '')
    if status:
        warehouses = warehouses.filter(status=status)

    # filter by active status
    active = request.GET.get('active', '')
    if active == 'true':
        warehouses = warehouses.filter(is_active=True)
    elif active == 'false':
        warehouses = warehouses.filter(is_active=False)

    # Calculate totals for summary cards
    # Evaluate queryset to avoid multiple DB hits when iterating
    warehouses_list = list(warehouses)
    total_zones_count = sum(w.total_zones for w in warehouses_list)
    total_locations_count = sum(w.total_locations for w in warehouses_list)
    total_products_count = sum(w.total_products for w in warehouses_list)

    context = {
        'warehouses': warehouses_list,
        'search_query': search_query,
        'selected_status': status,
        'selected_active': active,
        'total_zones_count': total_zones_count,
        'total_locations_count': total_locations_count,
        'total_products_count': total_products_count,
    }

    return render(request, 'warehouses/warehouse_list.html', context)


@login_required
def warehouse_detail(request, pk):
    'view single warehouse details'
    warehouse = get_object_or_404(Warehouse, pk=pk)

    # get zones and locations
    zones = warehouse.storage_zones.all()
    locations = warehouse.storage_locations.all()[:10]

    context = {
        'warehouse':warehouse,
        'zones':zones,
        'locations':locations
    }

    return render(request, 'warehouses/warehouse_detail.html', context)

@login_required
def warehouse_create(request):
    'create a new warehouse'

    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.created_by = request.user
            warehouse.save()
            messages.success(request, f'Warehouse {warehouse.code} created successfully')   
            return redirect('warehouses:warehouse_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WarehouseForm()

    context = {
        'form':form,
        'title':'Add new warehouse',
        'button_text':'Create Warehouse'
    }

    return render(request, 'warehouses/warehouse_form.html', context)


@login_required
def warehouse_update(request, pk):
    'update a  warehouse'

    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)

        if form.is_valid():
            form.save()
            messages.success(request, f'Warehouse {warehouse.code} updated successfully')
            return redirect('warehouses:warehouse_detail', pk=warehouse.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WarehouseForm(instance=warehouse)

    context = {
        'form':form,
        'title':'Edit warehouse',
        'button_text':'Update Warehouse'
    }

    return render(request, 'warehouses/warehouse_form.html', context)

@login_required
def warehouse_delete(request, pk):
    'delete a warehouse'
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        warehouse_code = warehouse.code
        warehouse.delete()
        messages.success(request, f'Warehouse {warehouse_code} deleted successfully')
        return redirect('warehouses:warehouse_list')
    
    context = {
        'warehouse':warehouse
    }

    return render(request, 'warehouses/warehouse_confirm_delete.html', context)


# storage zone views

@login_required
def zone_list(request, warehouse_pk):
    'list all storage zones for a warehouse'
    warehouse = get_object_or_404(Warehouse, pk=warehouse_pk)
    zones = warehouse.storage_zones.annotate(total_locations=Count('locations'))

    context = {
        'warehouse':warehouse,
        'zones':zones
    }

    return render(request, 'warehouses/zone_list.html', context)


@login_required
def zone_create(request, warehouse_pk):
    'create a new storage zone for a warehouse'
    warehouse = get_object_or_404(Warehouse, pk=warehouse_pk)

    if request.method == 'POST':
        form = StorageZoneForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.warehouse = warehouse
            zone.save()
            messages.success(request, f'Zone {zone.code} created successfully')
            return redirect('warehouses:zone_list', warehouse_pk=warehouse.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
        
    else:
        form = StorageZoneForm(initial={'warehouse':warehouse})

    context = {
        'form':form,
        'warehouse':warehouse,
        'title':'Add new zone',
        'button_text':'Create Zone'
    }

    return render(request, 'warehouses/zone_form.html', context)


# storage location views
@login_required
def location_list(request):
    'list all storage locatons with filters'
    locations = StorageLocation.objects.select_related('warehouse', 'zone').all()

    # filters by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        locations = locations.filter(warehouse_id=warehouse_id)

    
    # filters by availability
    available = request.GET.get('available', '')
    if available == 'true':
        locations = locations.filter(is_occupied=False, is_active=True)
    elif available == 'false':
        locations = locations.filter(is_occupied=True)

    # pagination
    paginator = Paginator(locations, 10)
    page_number = request.GET.get('page')
    locations = paginator.get_page(page_number)

    warehouses = Warehouse.objects.filter(is_active=True)

    context = {
        'locations':locations,
        'warehouses':warehouses,
        'selected_warehouse':warehouse_id,
        'selected_available':available
    }

    return render(request, 'warehouses/location_list.html', context)


@login_required
def location_create(request):
    'create a new storage location'

    if request.method == 'POST':
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location {location.code} created successfully')
            return redirect('warehouses:location_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StorageLocationForm()

    context = {
        'form': form,
        'title':'Add new storage location'
    }

    return render(request, 'warehouses/location_form.html', context)



