from django.db import models
from django.utils import timezone

class SalarySummary(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('finalized', 'Finalized'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='salary_summaries')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    month = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    working_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    daily_wage = models.DecimalField(max_digits=8, decimal_places=2)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_payable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-end_date', '-year', '-month']

    def __str__(self):
        if self.start_date and self.end_date:
            return f"{self.employee.name} – {self.start_date.strftime('%b %d')} to {self.end_date.strftime('%b %d, %Y')} – ₹{float(self.pending_amount):.2f}"
        return f"{self.employee.name} – {self.month}/{self.year} – ₹{float(self.pending_amount):.2f}"

    @property
    def month_name(self):
        import calendar
        return calendar.month_name[self.month]

    @property
    def total_paid(self):
        from django.db.models import Sum
        return self.payments.aggregate(t=Sum('paid_amount'))['t'] or 0

    @property
    def pending_amount(self):
        return max(self.net_payable - self.total_paid, 0)

class AdvanceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='advance_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    request_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    salary_summary = models.ForeignKey('SalarySummary', on_delete=models.SET_NULL, null=True, blank=True, related_name='deducted_advances')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"{self.employee.name} - ₹{self.amount} ({self.get_status_display()})"
