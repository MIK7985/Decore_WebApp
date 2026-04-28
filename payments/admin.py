from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'total_amount', 'paid_amount', 'pending_amount', 'status', 'payment_date')
    list_filter = ('status', 'method', 'year')
    search_fields = ('employee__name',)
