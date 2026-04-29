from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from employees.models import Employee
from sites_mgmt.models import WorkSite, EmployeeAssignment
from attendance.models import Attendance
from salary.models import SalarySummary
from payments.models import Payment
from core.decorators import admin_or_office_staff_required
import calendar


@login_required
@admin_or_office_staff_required
def report_dashboard(request):
    return render(request, 'reports/report_dashboard.html')


@login_required
@admin_or_office_staff_required
def attendance_report(request):
    month = int(request.GET.get('month', timezone.now().date().month))
    year = int(request.GET.get('year', timezone.now().date().year))
    site_id = request.GET.get('site', '')

    employees = Employee.objects.filter(status='active')
    report_data = []
    totals = {'present': 0, 'absent': 0, 'half': 0, 'effective': 0, 'salary': 0}

    for emp in employees:
        records = Attendance.objects.filter(employee=emp, date__month=month, date__year=year)
        if site_id:
            records = records.filter(site_id=site_id)
        
        present = records.filter(status='present').count()
        absent = records.filter(status='absent').count()
        half = records.filter(status='half_day').count()
        extra = records.filter(status='1_5_days').count()
        
        effective_days = float(present) + (float(half) * 0.5) + (float(extra) * 1.5)
        salary_est = effective_days * float(emp.daily_wage)
        
        report_data.append({
            'employee': emp,
            'present': present, 'absent': absent, 'half': half, 'extra': extra,
            'effective_days': effective_days,
            'salary': salary_est,
        })
        
        totals['present'] += present
        totals['absent'] += absent
        totals['half'] += half
        totals['extra'] = totals.get('extra', 0) + extra
        totals['effective'] += effective_days
        totals['salary'] += salary_est

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    sites = WorkSite.objects.filter(status='active')

    return render(request, 'reports/attendance_report.html', {
        'report_data': report_data, 'month': month, 'year': year,
        'month_name': calendar.month_name[month], 'months': months, 'years': years,
        'sites': sites, 'site_id': site_id, 'totals': totals
    })


@login_required
@admin_or_office_staff_required
def salary_report(request):
    month = int(request.GET.get('month', timezone.now().date().month))
    year = int(request.GET.get('year', timezone.now().date().year))
    summaries = SalarySummary.objects.filter(month=month, year=year).select_related('employee')
    total_gross = summaries.aggregate(t=Sum('gross_salary'))['t'] or 0
    total_net = summaries.aggregate(t=Sum('net_payable'))['t'] or 0
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    return render(request, 'reports/salary_report.html', {
        'summaries': summaries, 'month': month, 'year': year,
        'month_name': calendar.month_name[month], 'months': months, 'years': years,
        'total_gross': total_gross, 'total_net': total_net,
    })


@login_required
@admin_or_office_staff_required
def site_labor_report(request):
    month = int(request.GET.get('month', timezone.now().date().month))
    year = int(request.GET.get('year', timezone.now().date().year))
    sites = WorkSite.objects.filter(status='active')
    report_data = []
    
    grand_total_cost = 0
    grand_total_workers = 0

    # Get all active employees once for optimization
    all_employees = {e.id: e for e in Employee.objects.filter(status='active')}

    for site in sites:
        # Get all attendance records for this site in the given month
        site_attendance = Attendance.objects.filter(site=site, date__month=month, date__year=year)
        
        # Unique workers at this site this month
        worker_ids = site_attendance.values_list('employee_id', flat=True).distinct()
        worker_count = worker_ids.count()
        
        site_labor_cost = 0
        for worker_id in worker_ids:
            emp = all_employees.get(worker_id)
            if not emp: continue
            
            # Calculate cost specifically for this site
            worker_site_records = site_attendance.filter(employee_id=worker_id)
            effective_days = 0
            for r in worker_site_records:
                if r.status == 'present': effective_days += 1
                elif r.status == 'half_day': effective_days += 0.5
                elif r.status == '1_5_days': effective_days += 1.5
            
            site_labor_cost += float(effective_days) * float(emp.daily_wage)
        
        report_data.append({
            'site': site, 
            'workers': worker_count, 
            'labor_cost': site_labor_cost
        })
        grand_total_cost += site_labor_cost
        grand_total_workers += worker_count

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    return render(request, 'reports/site_labor_report.html', {
        'report_data': report_data, 
        'month': month, 'year': year,
        'month_name': calendar.month_name[month], 
        'months': months, 'years': years,
        'grand_total_cost': grand_total_cost,
        'grand_total_workers': grand_total_workers
    })


@login_required
@admin_or_office_staff_required
def payment_report(request):
    month = int(request.GET.get('month', timezone.now().date().month))
    year = int(request.GET.get('year', timezone.now().date().year))
    payments = Payment.objects.filter(month=month, year=year).select_related('employee')
    total_paid = payments.aggregate(t=Sum('paid_amount'))['t'] or 0
    total_pending = payments.aggregate(t=Sum('pending_amount'))['t'] or 0
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    return render(request, 'reports/payment_report.html', {
        'payments': payments, 'month': month, 'year': year,
        'month_name': calendar.month_name[month], 'months': months, 'years': years,
        'total_paid': total_paid, 'total_pending': total_pending,
    })
