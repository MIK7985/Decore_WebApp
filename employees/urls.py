from django.urls import path
from . import views
urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('add/', views.employee_add, name='employee_add'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('<int:pk>/reset-password/', views.employee_reset_password, name='employee_reset_password'),
    path('<int:pk>/update-photo/', views.employee_update_photo, name='employee_update_photo'),
    path('<int:pk>/remove-photo/', views.employee_remove_photo, name='employee_remove_photo'),
    path('api/', views.employee_api, name='employee_api'),
    path('download-pdf/', views.download_employees_pdf, name='download_employees_pdf'),
]
