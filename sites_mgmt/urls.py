from django.urls import path
from . import views
urlpatterns = [
    path('', views.site_list, name='site_list'),
    path('add/', views.site_add, name='site_add'),
    path('<int:pk>/', views.site_detail, name='site_detail'),
    path('<int:pk>/edit/', views.site_edit, name='site_edit'),
    path('<int:pk>/delete/', views.site_delete, name='site_delete'),
    path('<int:site_pk>/assign/', views.assign_employee, name='assign_employee'),
    path('assignment/<int:pk>/remove/', views.remove_assignment, name='remove_assignment'),
    path('<int:site_pk>/areas/add/', views.site_area_add, name='site_area_add'),
    path('areas/<int:area_pk>/update/', views.site_area_update, name='site_area_update'),
    path('areas/<int:area_pk>/delete/', views.site_area_delete, name='site_area_delete'),
    path('areas/<int:area_pk>/comment/', views.site_area_comment, name='site_area_comment'),
    path('areas/image/<int:image_pk>/delete/', views.delete_area_image, name='delete_area_image'),
    path('<int:site_pk>/payment/add/', views.site_add_payment, name='site_add_payment'),
    path('payment/<int:payment_pk>/delete/', views.site_delete_payment, name='site_delete_payment'),
    path('payment/<int:payment_pk>/receipt/', views.download_payment_receipt, name='download_payment_receipt'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client-finance/', views.client_finance, name='client_finance'),
    path('client-site/<int:pk>/', views.client_site_detail, name='client_site_detail'),
    path('my-sites/', views.worker_sites, name='worker_sites'),
    path('<int:pk>/materials/pdf/', views.download_site_materials_pdf, name='download_site_materials_pdf'),
]
