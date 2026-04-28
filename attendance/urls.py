from django.urls import path
from . import views
urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('download/pdf/', views.download_attendance_pdf, name='download_attendance_pdf'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('add/', views.attendance_add, name='attendance_add'),
    path('<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('employee/<int:employee_pk>/', views.employee_attendance, name='employee_attendance'),
]
