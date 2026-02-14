from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Main Reports Dashboard
    path('', views.reports_dashboard, name='reports_dashboard'),
    
    # Inventory Reports
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('inventory/export/', views.inventory_report_export, name='inventory_export'),
    
    # Low Stock Report
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    
    # Stock Movement Report
    path('stock-movements/', views.stock_movement_report, name='stock_movement_report'),
    path('stock-movements/export/', views.stock_movement_export, name='stock_movement_export'),
    
    # Expiry Report
    path('expiry/', views.expiry_report, name='expiry_report'),
    
    # Warehouse Performance
    path('warehouse-performance/', views.warehouse_performance_report, name='warehouse_performance'),
    
    # Product Performance
    path('product-performance/', views.product_performance_report, name='product_performance'),
    
    # Profit Analysis
    path('profit-analysis/', views.profit_analysis_report, name='profit_analysis'),
]