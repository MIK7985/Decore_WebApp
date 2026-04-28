from django.urls import path
from . import views
urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('salary/', views.salary_report, name='salary_report'),
    path('site-labor/', views.site_labor_report, name='site_labor_report'),
    path('payments/', views.payment_report, name='payment_report'),
]
