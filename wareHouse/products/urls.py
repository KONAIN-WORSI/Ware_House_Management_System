from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # product urls
    path('', views.product_list, name='product_list'),
    path('products/product_create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/update/', views.product_update, name='product_update'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),

    # category urls
    path('category/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
]
