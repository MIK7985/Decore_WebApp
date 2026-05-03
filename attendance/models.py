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

# Signal for automatically calculating weekly summaries is now handled dynamically in salary_list view
