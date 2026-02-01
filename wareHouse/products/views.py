from django.shortcuts import render, get_list_or_404, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ProductCategory, Product
from .forms import ProductCategoryForm, ProductForm


# Create your views here.
@login_required
def product_list(request):
    'list all products with search and filters'

    products = Product.objects.select_related('category', 'created_by').all()

    # search 
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # filters by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)

    # filter by status
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            products = products.filter(is_active=True)
        elif status == 'inactive':
            products = products.filter(is_active=False)
        elif status == 'low_stock':
            # we will implement this later
            pass

    
    # pagination
    paginator = Paginator(products, 10) # 10 products per page
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)

    # get all categories for filter dropdown
    categories = ProductCategory.objects.filter(is_active=True)

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'category_id': category_id,
        'status': status,
    }
    
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, pk):
    'view single product details'

    product = get_object_or_404(Product, pk=pk)

    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)

@login_required
def product_create(request):
    "create new product"

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(request, f'Product {product.name} created successfully!')
            return redirect('products:product_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'title': 'Add new product',
        'button_text': 'Create Product',
    }

    return render(request, 'products/product_form.html', context)

@login_required
def product_update(request, pk):
    "update existing product"

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.updated_by = request.user
            product.save()
            messages.success(request, f'Product {product.name} updated successfully!')
            return redirect('products:product_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'title': 'Edit product',
        'button_text': 'Update Product',
    }
    
    return render(request, 'products/product_form.html', context)

@login_required
def product_delete(request, pk):
    "delete product"

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product {product_name} deleted successfully!')
        return redirect('products:product_list')

    context = {
        'product': product,
        'title': 'Delete product',
        'button_text': 'Delete Product',
    }

    return render(request, 'products/product_confirm_delete.html', context)


# category views
@login_required
def category_list(request):
    'list all product categories'

    categories = ProductCategory.objects.all()

    context = {
        'categories': categories,
    }

    return render(request, 'products/category_list.html', context)

@login_required
def category_create(request):
    'create new category'

    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, f'Category {category.name} created successfully!')
            return redirect('products:category_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductCategoryForm()

    context = {
        'form': form,
        'title': 'Add new category',
    }

    return render(request, 'products/category_form.html', context)
