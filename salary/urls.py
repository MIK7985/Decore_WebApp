from django.urls import path
from . import views
urlpatterns = [
    path('', views.salary_list, name='salary_list'),
    path('download/csv/', views.download_salary_report, name='download_salary_report'),
    path('download/pdf/', views.download_salary_pdf, name='download_salary_pdf'),
    path('<int:pk>/', views.salary_detail, name='salary_detail'),
    path('<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('<int:pk>/finalize/', views.finalize_salary, name='finalize_salary'),
    path('advances/', views.advance_list, name='advance_list'),
    path('advances/request/', views.request_advance, name='request_advance'),
    path('advances/<int:pk>/update/', views.update_advance, name='update_advance'),
]
