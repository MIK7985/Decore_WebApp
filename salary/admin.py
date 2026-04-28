from django.contrib import admin
from .models import SalarySummary

@admin.register(SalarySummary)
class SalarySummaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'working_days', 'net_payable', 'status')
    list_filter = ('status', 'year', 'month')
    search_fields = ('employee__name',)
