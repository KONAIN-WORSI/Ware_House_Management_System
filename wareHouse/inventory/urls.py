from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Inventory URLs
    path('', views.inventory_list, name='inventory_list'),
    path('<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('dashboard/', views.inventory_dashboard, name='dashboard'),
    
    # Stock Movement URLs
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('transfer/', views.stock_transfer, name='stock_transfer'),
    path('adjustment/', views.stock_adjustment, name='stock_adjustment'),
    
    # Stock Movement List
    path('movements/', views.stock_movement_list, name='stock_movement_list'),
    path('movements/<int:pk>/', views.stock_movement_detail, name='stock_movement_detail'),
    
    # Alerts
    path('alerts/', views.stock_alerts, name='alerts'),
    path('alerts/<int:pk>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
]
