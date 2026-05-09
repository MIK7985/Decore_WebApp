import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decore_developers.settings')
django.setup()

from employees.models import Employee

def sync_all_roles():
    print("Scanning all employees to sync their login permissions...")
    employees = Employee.objects.all()
    updated_count = 0
    
    for emp in employees:
        if hasattr(emp, 'user_account') and emp.user_account:
            if emp.user_account.role != emp.role:
                print(f"Syncing {emp.name}: {emp.user_account.role} -> {emp.role}")
                emp.user_account.role = emp.role
                emp.user_account.save()
                updated_count += 1
                
    print(f"\n✅ Successfully synchronized permissions for {updated_count} employees!")

if __name__ == '__main__':
    sync_all_roles()
