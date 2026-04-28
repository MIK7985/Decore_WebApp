from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Attendance
from .forms import AttendanceForm, BulkAttendanceForm
from employees.models import Employee
from sites_mgmt.models import WorkSite, EmployeeAssignment
import datetime


@login_required
def attendance_list(request):
    records = Attendance.objects.select_related('employee', 'site').all()
    
    # Permission: Employees can only view their own history. 
    if not request.user.can_manage:
        if hasattr(request.user, 'employee') and request.user.employee:
            records = records.filter(employee=request.user.employee)
        else:
            records = records.none()
            
    date_filter = request.GET.get('date', '')
    month_filter = request.GET.get('month', '')
    site_filter = request.GET.get('site', '')
    emp_filter = request.GET.get('employee', '')

    # Set Defaults based on role if no filter is provided
    if not request.user.can_manage and not month_filter and not date_filter:
        month_filter = timezone.now().strftime('%Y-%m')
    elif request.user.can_manage and not date_filter and not month_filter:
        date_filter = str(timezone.now().date())

    if date_filter:
        records = records.filter(date=date_filter)
    if month_filter:
        try:
            year, month = month_filter.split('-')
            records = records.filter(date__year=year, date__month=month)
        except ValueError:
            pass
    if site_filter:
        records = records.filter(site_id=site_filter)
    if emp_filter:
        records = records.filter(employee__name__icontains=emp_filter)

    paginator = Paginator(records, 20)
    records = paginator.get_page(request.GET.get('page'))
    sites = WorkSite.objects.filter(status='active')

    return render(request, 'attendance/attendance_list.html', {
        'records': records, 'date_filter': date_filter, 'month_filter': month_filter,
        'site_filter': site_filter, 'emp_filter': emp_filter, 'sites': sites,
    })

@login_required
def download_attendance_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, portrait
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet
    import os
    from django.conf import settings
    
    records = Attendance.objects.select_related('employee', 'site').all()
    
    if not request.user.can_manage:
        if hasattr(request.user, 'employee') and request.user.employee:
            records = records.filter(employee=request.user.employee)
        else:
            records = records.none()
            
    date_filter = request.GET.get('date', str(timezone.now().date()))
    site_filter = request.GET.get('site', '')
    emp_filter = request.GET.get('employee', '')

    if date_filter:
        records = records.filter(date=date_filter)
    if site_filter:
        records = records.filter(site_id=site_filter)
    if emp_filter:
        records = records.filter(employee__name__icontains=emp_filter)
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{date_filter}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=portrait(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-removebg-preview (1).png')
        
    header_data = []
    title_html = f"<font size=22 color='#0f172a'><b>Decore Developers</b></font><br/><br/><font size=12 color='#64748b'><b>DAILY ATTENDANCE REPORT</b> &nbsp;&nbsp;|&nbsp;&nbsp; {date_filter}</font>"
    title_p = Paragraph(title_html, styles['Normal'])
    
    if os.path.exists(logo_path):
        img = Image(logo_path, width=70, height=70, mask='auto')
        header_data.append([img, title_p])
        header_table = Table(header_data, colWidths=[90, 400])
    else:
        header_data.append([title_p])
        header_table = Table(header_data, colWidths=[490])
        
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # Table Data
    data = [['Employee Name', 'Worksite', 'Status']]
    for r in records:
        site_name = r.site.name if r.site else 'N/A'
        
        status_text = r.get_status_display()
        if r.status == 'present':
            status_cell = Paragraph(f"<font color='#10b981'><b>{status_text}</b></font>", styles['Normal'])
        elif r.status == 'absent':
            status_cell = Paragraph(f"<font color='#ef4444'><b>{status_text}</b></font>", styles['Normal'])
        elif r.status == 'half_day':
            status_cell = Paragraph(f"<font color='#f59e0b'><b>{status_text}</b></font>", styles['Normal'])
        else:
            status_cell = Paragraph(f"<font color='#64748b'><b>{status_text}</b></font>", styles['Normal'])
            
        data.append([r.employee.name, site_name, status_cell])
        
    if len(data) == 1:
        data.append(['No attendance records found.', '', ''])
        
    table = Table(data, colWidths=[200, 160, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#ffffff")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#334155")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    elements.append(table)
    doc.build(elements)
    return response

@login_required
def mark_attendance(request):
    """Bulk attendance marking for a site and date"""
    # Roles Permissions
    # Accountants and Admins can access this full bulk page

    today_str = str(timezone.now().date())
    date = request.GET.get('date', today_str)
    
    # Employees cannot edit past attendance (Force date to today)
    if not request.user.can_manage:
        if date != today_str:
            messages.warning(request, "You can only mark attendance for today.")
        date = today_str

    site_id = request.GET.get('site', '')
    site = None
    # Exclude office staff as they don't need attendance marking
    employees = Employee.objects.filter(status='active').exclude(role='office_staff')

    # Employee Role constraint: Only mark for self
    if not request.user.can_manage:
        if not hasattr(request.user, 'employee') or not request.user.employee:
            messages.error(request, "No employee profile linked to your account.")
            return redirect('dashboard')
        if request.user.employee.status == 'inactive':
            messages.error(request, "Your account is deactivated. Contact your admin.")
            return redirect('dashboard')
        employees = employees.filter(id=request.user.employee.id)

    if site_id:
        site = get_object_or_404(WorkSite, pk=site_id)
        assigned = EmployeeAssignment.objects.filter(site=site, is_active=True).values_list('employee_id', flat=True)
        employees = employees.filter(id__in=assigned)

    existing = {a.employee_id: a for a in Attendance.objects.filter(date=date, employee__in=employees)}
    already_marked = False
    if not request.user.can_manage and len(existing) > 0:
        already_marked = True

    if request.method == 'POST':
        post_date = request.POST.get('date', date)
        if not request.user.can_manage and post_date != today_str:
            post_date = today_str # Strict guard for payload manipulation
            
        for emp in employees:
            status_key = f'status_{emp.id}'
            
            # If the employee already has attendance and the form didn't send a new status, 
            # it means the inputs were disabled on the frontend to prevent accidental overwrite. Skip updating.
            if status_key not in request.POST and emp.id in existing:
                continue
                
            status = request.POST.get(status_key, '')
            if not status:
                continue
            
            # Additional safety: Employees cannot overwrite an already marked attendance
            if not request.user.can_manage and emp.id in existing:
                if existing[emp.id].status != status:
                    messages.warning(request, "You have already marked your attendance today. Contact admin to modify.")
                continue

            # Row-level Site Selection
            emp_site_id = request.POST.get(f'site_{emp.id}')
            emp_site = None
            if emp_site_id:
                emp_site = WorkSite.objects.filter(pk=emp_site_id).first()
            else:
                emp_site = site # fallback to global filter if any

            att, created = Attendance.objects.update_or_create(
                employee=emp, date=post_date,
                defaults={'status': status, 'site': emp_site, 'marked_by': request.user}
            )
        if request.user.can_manage or len(employees) > 0:
            messages.success(request, f'Attendance marked for {post_date}.')
        # Redirect to the list view specifically scoped to the date they just modified
        from django.urls import reverse
        return redirect(f"{reverse('attendance_list')}?date={post_date}")

    sites = WorkSite.objects.filter(status='active')
    if not request.user.can_manage and hasattr(request.user, 'employee'):
        assigned_site_ids = EmployeeAssignment.objects.filter(employee=request.user.employee, is_active=True).values_list('site_id', flat=True)
        sites = sites.filter(id__in=assigned_site_ids)

    return render(request, 'attendance/mark_attendance.html', {
        'employees': employees, 'date': date, 'site': site,
        'sites': sites, 'existing': existing,
        'already_marked': already_marked,
        'status_choices': Attendance.STATUS_CHOICES,
    })


@login_required
def attendance_add(request):
    if not request.user.is_admin:
        messages.error(request, "Access Denied. Only Admins can add custom attendance records.")
        return redirect('attendance_list')
        
    form = AttendanceForm(request.POST or None)
    if form.is_valid():
        att = form.save(commit=False)
        att.marked_by = request.user
        att.save()
        messages.success(request, 'Attendance record saved.')
        return redirect('attendance_list')
    return render(request, 'attendance/attendance_form.html', {'form': form, 'title': 'Add Attendance'})


@login_required
def attendance_edit(request, pk):
    if not request.user.is_admin:
        messages.error(request, "Access Denied. Only Admins can edit past attendance records.")
        return redirect('attendance_list')
        
    record = get_object_or_404(Attendance, pk=pk)
    form = AttendanceForm(request.POST or None, instance=record)
    if form.is_valid():
        form.save()
        messages.success(request, 'Attendance updated.')
        return redirect('attendance_list')
    return render(request, 'attendance/attendance_form.html', {'form': form, 'title': 'Edit Attendance', 'record': record})


@login_required
def attendance_delete(request, pk):
    if not request.user.is_admin:
        messages.error(request, "Access Denied. Only Admins can delete attendance records.")
        return redirect('attendance_list')
        
    record = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Record deleted.')
        return redirect('attendance_list')
    return render(request, 'attendance/attendance_confirm_delete.html', {'record': record})


@login_required
def employee_attendance(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    
    if not request.user.can_manage:
        if not hasattr(request.user, 'employee') or request.user.employee.id != employee.id:
            messages.error(request, "Permission Denied. You can only view your own attendance history.")
            return redirect('dashboard')
            
    records = Attendance.objects.filter(employee=employee).order_by('-date')
    month = request.GET.get('month', timezone.now().date().month)
    year = request.GET.get('year', timezone.now().date().year)
    records_filtered = records.filter(date__month=month, date__year=year)
    paginator = Paginator(records, 30)
    records = paginator.get_page(request.GET.get('page'))
    return render(request, 'attendance/employee_attendance.html', {
        'employee': employee, 'records': records,
        'records_filtered': records_filtered, 'month': int(month), 'year': int(year),
    })
