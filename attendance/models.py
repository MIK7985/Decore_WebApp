from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('1_5_days', '1.5 Days'),
        ('holiday', 'Holiday'),
        ('leave', 'Leave'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='attendances')
    site = models.ForeignKey('sites_mgmt.WorkSite', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.name} – {self.date} – {self.get_status_display()}"

    @property
    def day_value(self):
        if self.status == 'present': return 1.0
        if self.status == 'half_day': return 0.5
        if self.status == '1_5_days': return 1.5
        return 0.0

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal

@receiver(post_save, sender=Attendance)
@receiver(post_delete, sender=Attendance)
def update_salary_on_attendance_change(sender, instance, **kwargs):
    from salary.models import SalarySummary
    
    import datetime
    
    date_val = instance.date
    if isinstance(date_val, str):
        date_val = datetime.datetime.strptime(date_val, '%Y-%m-%d').date()
        
    emp = instance.employee
    month = date_val.month
    year = date_val.year
    
    # Recalculate working days directly
    att_records = Attendance.objects.filter(employee=emp, date__month=month, date__year=year)
    working_days = Decimal('0')
    for r in att_records:
        if r.status == 'present':
            working_days += Decimal('1')
        elif r.status == 'half_day':
            working_days += Decimal('0.5')
        elif r.status == '1_5_days':
            working_days += Decimal('1.5')
            
    gross = working_days * emp.daily_wage
    
    # Update or create the Summary
    summary, created = SalarySummary.objects.get_or_create(
        employee=emp, month=month, year=year,
        defaults={
            'working_days': working_days,
            'daily_wage': emp.daily_wage,
            'gross_salary': gross,
            'net_payable': gross,
            'deductions': Decimal('0'),
            'status': 'draft',
        }
    )
    
    if not created:
        if summary.status != 'finalized': # Do not alter officially finalized payrolls
            summary.working_days = working_days
            summary.daily_wage = emp.daily_wage
            summary.gross_salary = gross
            summary.net_payable = gross - summary.deductions
            summary.save()
