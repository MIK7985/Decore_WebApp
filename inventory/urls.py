from django.urls import path
from . import views

urlpatterns = [
    path('storages/', views.storage_list, name='storage_list'),
    path('storages/add/', views.storage_add, name='storage_add'),
    path('storages/<int:pk>/', views.storage_detail, name='storage_detail'),
    path('storages/<int:pk>/edit/', views.storage_edit, name='storage_edit'),
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_add, name='item_add'),
    path('items/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('requests/', views.material_request_list, name='material_request_list'),
    path('requests/<int:pk>/status/', views.material_request_update_status, name='material_request_update_status'),
    path('deliveries/', views.delivery_log_list, name='delivery_log_list'),
    path('deliveries/add/', views.delivery_log_create, name='delivery_log_create'),
    path('deliveries/<int:pk>/edit/', views.delivery_log_edit, name='delivery_log_edit'),
]
