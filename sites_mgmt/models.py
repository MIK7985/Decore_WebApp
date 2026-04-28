from django.db import models
from django.utils import timezone

class WorkSite(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    square_feet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    client_name = models.CharField(max_length=200, blank=True)
    client_phone = models.CharField(max_length=15, blank=True)
    client_email = models.EmailField(blank=True)
    client_user = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='client_sites')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def is_completed(self):
        return self.status == 'completed'
        
    def get_material_cost(self):
        return sum(log.get_total_cost() for log in self.deliveries_received.all())

    def __str__(self):
        return f"{self.name} – {self.location}"

    def get_assigned_employees(self):
        return self.assignments.filter(is_active=True).select_related('employee')

    def get_labor_cost(self, month, year):
        # Legacy method
        total = 0
        for assignment in self.assignments.filter(is_active=True):
            total += float(assignment.employee.get_monthly_salary(month, year))
        return total

    def get_total_labor_cost(self):
        from decimal import Decimal
        total = Decimal('0')
        for att in self.attendances.all().select_related('employee'):
            if att.status == 'present':
                day_value = Decimal('1')
            elif att.status == 'half_day':
                day_value = Decimal('0.5')
            else:
                day_value = Decimal('0')
            total += day_value * att.employee.daily_wage
        return total

    def get_profit_loss(self):
        est = self.estimated_cost or 0
        mat = self.get_material_cost() or 0
        lab = self.get_total_labor_cost() or 0
        return est - (mat + lab)

    def get_overall_progress(self):
        areas = self.areas.all()
        if not areas:
            return 0
        total = sum([a.progress_percentage for a in areas])
        return total // areas.count()


class EmployeeAssignment(models.Model):
    site = models.ForeignKey(WorkSite, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='assignments')
    supervisor = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='supervised_assignments')
    assigned_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('site', 'employee')
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.employee.name} @ {self.site.name}"

class WorkArea(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    site = models.ForeignKey(WorkSite, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.site.name}"

class WorkAreaImage(models.Model):
    work_area = models.ForeignKey(WorkArea, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='work_area_images/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.work_area.name}"
