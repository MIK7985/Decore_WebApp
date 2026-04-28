from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'phone', 'daily_wage', 'status', 'joining_date')
    list_filter = ('role', 'status')
    search_fields = ('name', 'phone', 'address')
    list_per_page = 25
