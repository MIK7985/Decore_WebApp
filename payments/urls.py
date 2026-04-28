from django.urls import path
from . import views
urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('add/', views.payment_add, name='payment_add'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('employee/<int:employee_pk>/', views.employee_payment_history, name='employee_payment_history'),
    path('api/get-pending-salary/', views.api_get_pending_salary, name='api_get_pending_salary'),
]
