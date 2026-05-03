from django.db import models
from django.utils import timezone

class Employee(models.Model):
    ROLE_CHOICES = [
        ('main_worker', 'Main Worker'),
        ('helper', 'Helper'),
        ('driver', 'Driver'),
        ('storage_manager', 'Storage Manager'),
        ('office_staff', 'Office Staff'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    daily_wage = models.DecimalField(max_digits=8, decimal_places=2)
    address = models.TextField()
    joining_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    emergency_contact = models.CharField(max_length=15, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.employee_id or 'No ID'})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.employee_id:
            self.employee_id = f"DC{self.pk:03d}"
            # Re-save only the employee_id
            kwargs.pop('force_insert', None)
            super().save(update_fields=['employee_id'])

    def get_monthly_salary(self, month, year):
        from attendance.models import Attendance
        from decimal import Decimal
        records = Attendance.objects.filter(employee=self, date__month=month, date__year=year)
        days = sum(r.day_value for r in records)
        return Decimal(str(days)) * self.daily_wage

    def get_total_present_days(self, month, year):
        from attendance.models import Attendance
        records = Attendance.objects.filter(employee=self, date__month=month, date__year=year)
        return sum(r.day_value for r in records)
