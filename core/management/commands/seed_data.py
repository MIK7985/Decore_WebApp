"""
Management command to seed demo data for Decore Developers.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Seed demo data for Decore Developers POP Management System'

    def handle(self, *args, **kwargs):
        from core.models import CustomUser
        from employees.models import Employee
        from sites_mgmt.models import WorkSite, EmployeeAssignment
        from attendance.models import Attendance

        self.stdout.write('Seeding demo data...')

        # Create users
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser('admin', 'admin@decore.com', 'admin123')
            admin.role = 'admin'
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            admin.save()
            self.stdout.write(self.style.SUCCESS('✓ Admin user created (admin / admin123)'))

        if not CustomUser.objects.filter(username='accountant').exists():
            acc = CustomUser.objects.create_user('accountant', 'acc@decore.com', 'acc123')
            acc.role = 'accountant'
            acc.first_name = 'Rajan'
            acc.last_name = 'Nair'
            acc.save()
            self.stdout.write(self.style.SUCCESS('✓ Accountant user created (accountant / acc123)'))

        # Create employees
        employees_data = [
            {'name': 'Mohammed Shafi', 'phone': '9876543210', 'role': 'main_worker', 'daily_wage': 800, 'address': 'Tirur, Malappuram'},
            {'name': 'Suresh Kumar', 'phone': '9876543211', 'role': 'main_worker', 'daily_wage': 750, 'address': 'Tirur, Malappuram'},
            {'name': 'Anwar Hussain', 'phone': '9876543212', 'role': 'helper', 'daily_wage': 550, 'address': 'Kottakkal, Malappuram'},
            {'name': 'Raju Thomas', 'phone': '9876543213', 'role': 'helper', 'daily_wage': 500, 'address': 'Tirur, Malappuram'},
            {'name': 'Biju Varghese', 'phone': '9876543214', 'role': 'helper', 'daily_wage': 520, 'address': 'Perinthalmanna'},
            {'name': 'Santhosh P', 'phone': '9876543215', 'role': 'driver', 'daily_wage': 600, 'address': 'Tirur, Malappuram'},
            {'name': 'Arun Krishnan', 'phone': '9876543216', 'role': 'helper', 'daily_wage': 480, 'address': 'Ponnani'},
            {'name': 'Vineeth Menon', 'phone': '9876543217', 'role': 'main_worker', 'daily_wage': 820, 'address': 'Thrissur'},
        ]

        created_emps = []
        for data in employees_data:
            emp, created = Employee.objects.get_or_create(
                name=data['name'],
                defaults={**data, 'joining_date': timezone.now().date() - datetime.timedelta(days=90)}
            )
            created_emps.append(emp)
            if created:
                self.stdout.write(f'  ✓ Employee: {emp.name}')

        # Create work sites
        sites_data = [
            {'name': 'Green Valley Villa', 'location': 'Tirur, Malappuram', 'square_feet': 2400, 'start_date': timezone.now().date() - datetime.timedelta(days=45), 'status': 'active'},
            {'name': 'Al-Barakah Residence', 'location': 'Kottakkal, Malappuram', 'square_feet': 1800, 'start_date': timezone.now().date() - datetime.timedelta(days=30), 'status': 'active'},
            {'name': 'Sunrise Apartments Block B', 'location': 'Tirur Town', 'square_feet': 4200, 'start_date': timezone.now().date() - datetime.timedelta(days=60), 'status': 'active'},
            {'name': 'Nair Residence', 'location': 'Ponnani', 'square_feet': 1500, 'start_date': timezone.now().date() - datetime.timedelta(days=90), 'end_date': timezone.now().date() - datetime.timedelta(days=10), 'status': 'completed'},
        ]

        created_sites = []
        for data in sites_data:
            site, created = WorkSite.objects.get_or_create(name=data['name'], defaults=data)
            created_sites.append(site)
            if created:
                self.stdout.write(f'  ✓ Site: {site.name}')

        # Assign employees to active sites
        active_sites = [s for s in created_sites if s.status == 'active']
        if active_sites and created_emps:
            assignments = [
                (active_sites[0], created_emps[0], None),
                (active_sites[0], created_emps[2], created_emps[0]),
                (active_sites[0], created_emps[3], created_emps[0]),
                (active_sites[1], created_emps[1], None),
                (active_sites[1], created_emps[4], created_emps[1]),
                (active_sites[2], created_emps[7], None),
                (active_sites[2], created_emps[6], created_emps[7]),
            ]
            for site, emp, supervisor in assignments:
                EmployeeAssignment.objects.get_or_create(
                    site=site, employee=emp,
                    defaults={'supervisor': supervisor, 'assigned_date': timezone.now().date() - datetime.timedelta(days=20)}
                )

        # Seed attendance for last 30 days
        import random
        today = timezone.now().date()
        for emp in created_emps[:6]:
            for i in range(30):
                day = today - datetime.timedelta(days=i)
                if day.weekday() < 6:  # Mon-Sat
                    status = random.choices(['present', 'absent', 'half_day'], weights=[75, 15, 10])[0]
                    Attendance.objects.get_or_create(
                        employee=emp, date=day,
                        defaults={'status': status}
                    )

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded successfully!'))
        self.stdout.write(self.style.WARNING('Login credentials:'))
        self.stdout.write('  Admin:      admin / admin123')
        self.stdout.write('  Accountant: accountant / acc123')
