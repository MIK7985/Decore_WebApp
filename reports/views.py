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
    for emp in employees:
        records = Attendance.objects.filter(employee=emp, date__month=month, date__year=year)
        if site_id:
            records = records.filter(site_id=site_id)
        present = records.filter(status='present').count()
        absent = records.filter(status='absent').count()
        half = records.filter(status='half_day').count()
        effective_days = present + half * 0.5
        report_data.append({
            'employee': emp,
            'present': present, 'absent': absent, 'half': half,
            'effective_days': effective_days,
            'salary': effective_days * float(emp.daily_wage),
        })

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    sites = WorkSite.objects.filter(status='active')

    return render(request, 'reports/attendance_report.html', {
        'report_data': report_data, 'month': month, 'year': year,
        'month_name': calendar.month_name[month], 'months': months, 'years': years,
        'sites': sites, 'site_id': site_id,
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
    for site in sites:
        assignments = EmployeeAssignment.objects.filter(site=site, is_active=True).select_related('employee')
        labor_cost = 0
        for a in assignments:
            labor_cost += float(a.employee.get_monthly_salary(month, year))
        report_data.append({'site': site, 'workers': assignments.count(), 'labor_cost': labor_cost})
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(timezone.now().date().year - 2, timezone.now().date().year + 1))
    return render(request, 'reports/site_labor_report.html', {
        'report_data': report_data, 'month': month, 'year': year,
        'month_name': calendar.month_name[month], 'months': months, 'years': years,
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
