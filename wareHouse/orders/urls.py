from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Purchase Order URLs
    path('purchase/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase/create/', views.purchase_order_create, name='purchase_order_create'),
    
    # Sales Order URLs
    path('sales/', views.sales_order_list, name='sales_order_list'),
    path('sales/<int:pk>/', views.sales_order_detail, name='sales_order_detail'),
    path('sales/create/', views.sales_order_create, name='sales_order_create'),
]