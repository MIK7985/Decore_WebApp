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
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client-site/<int:pk>/', views.client_site_detail, name='client_site_detail'),
    path('my-sites/', views.worker_sites, name='worker_sites'),
    path('<int:pk>/materials/pdf/', views.download_site_materials_pdf, name='download_site_materials_pdf'),
]
