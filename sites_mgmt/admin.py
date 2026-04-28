from django.contrib import admin
from .models import WorkSite, EmployeeAssignment

@admin.register(WorkSite)
class WorkSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name', 'location', 'client_name')

@admin.register(EmployeeAssignment)
class EmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'site', 'assigned_date', 'is_active')
    list_filter = ('is_active',)
