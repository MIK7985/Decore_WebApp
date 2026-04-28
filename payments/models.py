from django.db import models
from django.utils import timezone

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='payments')
    salary_summary = models.ForeignKey('salary.SalarySummary', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='payments')
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.employee.name} – {self.month}/{self.year} – ₹{self.paid_amount}"

    def save(self, *args, **kwargs):
        self.pending_amount = self.total_amount - self.paid_amount
        if self.pending_amount <= 0:
            self.status = 'paid'
            self.pending_amount = 0
        elif self.paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)

    @property
    def month_name(self):
        import calendar
        return calendar.month_name[self.month]
