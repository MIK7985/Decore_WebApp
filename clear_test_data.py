import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decore_developers.settings')
django.setup()

from django.contrib.auth import get_user_model
from employees.models import Employee
from sites_mgmt.models import WorkSite, WorkArea, WorkAreaImage, SitePayment, EmployeeAssignment
from attendance.models import Attendance
from salary.models import SalarySummary, AdvanceRequest
from inventory.models import Item, StorageStock, SiteStock, DispatchOrder, DispatchItem, MaterialRequest, DeliveryLog, DeliveryLogItem, StorageFacility

User = get_user_model()

def clear_test_data():
    print("WARNING: This will delete ALL data except Superuser accounts.")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != 'YES':
        print("Operation cancelled.")
        return

    print("Deleting Salary Records...")
    SalarySummary.objects.all().delete()
    AdvanceRequest.objects.all().delete()

    print("Deleting Attendance...")
    Attendance.objects.all().delete()

    print("Deleting Site Data & Payments...")
    WorkAreaImage.objects.all().delete()
    WorkArea.objects.all().delete()
    SitePayment.objects.all().delete()
    EmployeeAssignment.objects.all().delete()
    WorkSite.objects.all().delete()

    print("Deleting Inventory Data...")
    DeliveryLogItem.objects.all().delete()
    DeliveryLog.objects.all().delete()
    MaterialRequest.objects.all().delete()
    DispatchItem.objects.all().delete()
    DispatchOrder.objects.all().delete()
    SiteStock.objects.all().delete()
    StorageStock.objects.all().delete()
    Item.objects.all().delete()
    StorageFacility.objects.all().delete()

    print("Deleting Employees...")
    Employee.objects.all().delete()

    print("Deleting Non-Admin Users (Clients, Staff, etc.)...")
    # Keep superusers
    users_deleted, _ = User.objects.filter(is_superuser=False).delete()
    print(f"Deleted {users_deleted} user accounts.")

    print("\n✅ All test data has been completely wiped. Your admin account is safe!")

if __name__ == '__main__':
    clear_test_data()
