from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('office_staff', 'Office Staff'),
        ('main_worker', 'Main Worker'),
        ('helper', 'Helper'),
        ('driver', 'Driver'),
        ('storage_manager', 'Storage Manager'),
        ('client', 'Client'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='helper')
    phone = models.CharField(max_length=15, blank=True)
    employee = models.OneToOneField(
        'employees.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='user_account'
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_office_staff(self):
        return self.role == 'office_staff'

    @property
    def can_manage(self):
        return self.role in ['admin', 'office_staff'] or self.is_superuser
