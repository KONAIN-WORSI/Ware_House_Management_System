from django.urls import path
from . import views

app_name = 'warehouses'

urlpatterns = [
    # Warehouse URLs
    path('', views.warehouse_list, name='warehouse_list'),
    path('<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('create/', views.warehouse_create, name='warehouse_create'),
    path('<int:pk>/update/', views.warehouse_update, name='warehouse_update'),
    path('<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),
    
    # Storage Zone URLs
    path('<int:warehouse_pk>/zones/', views.zone_list, name='zone_list'),
    path('<int:warehouse_pk>/zones/create/', views.zone_create, name='zone_create'),
    
    # Storage Location URLs
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
]