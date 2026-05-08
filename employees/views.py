from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Employee
from .models import Employee
from .forms import EmployeeForm
from core.decorators import admin_required, admin_or_office_staff_required


@login_required
@admin_or_office_staff_required
def employee_list(request):
    employees = Employee.objects.all()
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if query:
        employees = employees.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    if role_filter:
        employees = employees.filter(role=role_filter)
    if status_filter:
        employees = employees.filter(status=status_filter)

    paginator = Paginator(employees, 15)
    employees = paginator.get_page(request.GET.get('page'))

    return render(request, 'employees/employee_list.html', {
        'employees': employees,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'role_choices': Employee.ROLE_CHOICES,
    })


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Security check: Standard employees can only see their own profile
    if not request.user.can_manage:
        if request.user.employee is None or request.user.employee.id != employee.id:
            messages.error(request, "Access denied. You can only view your own profile.")
            if request.user.employee is not None:
                return redirect('employee_detail', pk=request.user.employee.pk)
            return redirect('login')
    from attendance.models import Attendance
    from sites_mgmt.models import EmployeeAssignment
    from django.utils import timezone
    import datetime
    today = timezone.now().date()
    assignments = EmployeeAssignment.objects.filter(employee=employee).select_related('site').order_by('-assigned_date')
    recent_attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    monthly_salary = employee.get_monthly_salary(today.month, today.year)
    already_marked_today = Attendance.objects.filter(employee=employee, date=today).exists()
    
    requires_password_change = False
    if employee.user_account and employee.user_account.last_login is None:
        requires_password_change = True
        
    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'assignments': assignments,
        'recent_attendance': recent_attendance,
        'monthly_salary': monthly_salary,
        'today': today,
        'already_marked_today': already_marked_today,
        'requires_password_change': requires_password_change,
    })


@admin_or_office_staff_required
def employee_add(request):
    form = EmployeeForm(request.POST or None, request.FILES or None, user=request.user)
    if form.is_valid():
        emp = form.save()
        assigned_site = form.cleaned_data.get('assigned_site')
        
        if assigned_site:
            from sites_mgmt.models import EmployeeAssignment
            EmployeeAssignment.objects.create(employee=emp, site=assigned_site, is_active=True)
            
        # --- Auto-generate Login Credentials ---
        from core.models import CustomUser
        
        # Base username on employee_id (e.g., DC001)
        username = emp.employee_id
        password = 'password123' # Default password for all auto-generated staffs
        
        # Ensure username uniqueness just in case
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{emp.employee_id}_{counter}"
            counter += 1
            
        user = CustomUser.objects.create_user(username=username, password=password)
        user.role = emp.role
        user.first_name = emp.name.split(' ')[0]
        user.employee = emp
        user.save()
        
        messages.success(request, f'Employee "{emp.name}" ({emp.employee_id}) added! 🔐 Auto-Login -> ID: {username} | Password: {password}')
        return redirect('employee_list')
        
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_edit(request, pk):
    from sites_mgmt.models import EmployeeAssignment
    from django.utils import timezone
    employee = get_object_or_404(Employee, pk=pk)
    
    # Permission Check: Admin, Office Staff, OR the employee themselves
    is_manager = request.user.role in ['admin', 'office_staff'] or request.user.is_superuser
    is_self = request.user.employee is not None and request.user.employee.id == employee.id
    
    if not (is_manager or is_self):
        messages.error(request, "Permission Denied. You cannot edit this profile.")
        return redirect('dashboard')
    
    current_assignment = EmployeeAssignment.objects.filter(employee=employee, is_active=True).first()
    initial_data = {'assigned_site': current_assignment.site if current_assignment else None}
    
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee, initial=initial_data, user=request.user)
    
    if form.is_valid():
        emp = form.save()
        assigned_site = form.cleaned_data.get('assigned_site')
        
        # Only allow managers to update site assignments
        if is_manager:
            if assigned_site:
                # Update or create active assignment
                if not current_assignment or current_assignment.site != assigned_site:
                    if current_assignment:
                        current_assignment.is_active = False
                        current_assignment.end_date = timezone.now().date()
                        current_assignment.save()
                    EmployeeAssignment.objects.create(employee=emp, site=assigned_site, is_active=True)
            else:
                if current_assignment:
                    current_assignment.is_active = False
                    current_assignment.end_date = timezone.now().date()
                    current_assignment.save()

        messages.success(request, f'Profile for "{employee.name}" updated.')
        return redirect('employee_detail', pk=pk)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Edit Profile' if is_self else 'Edit Employee', 'employee': employee})


@admin_or_office_staff_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        if employee.status == 'active':
            employee.status = 'inactive'
            msg = 'deactivated'
        else:
            employee.status = 'active'
            msg = 'activated'
        employee.save()
        messages.success(request, f'Employee "{employee.name}" {msg}.')
        return redirect('employee_detail', pk=pk)
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})


@admin_or_office_staff_required
def employee_reset_password(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        if hasattr(employee, 'user_account') and employee.user_account:
            user = employee.user_account
            new_password = 'password123'
            user.set_password(new_password)
            user.save()
            messages.success(request, f'Password for {employee.name} reset to: {new_password}')
        else:
            messages.error(request, f'No user account found for {employee.name}.')
    return redirect('employee_detail', pk=pk)


@login_required
def employee_api(request):
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    employees = Employee.objects.filter(status='active')
    if q:
        employees = employees.filter(name__icontains=q)
    if role:
        employees = employees.filter(role=role)
    data = [{'id': e.id, 'name': e.name, 'role': e.get_role_display(), 'daily_wage': str(e.daily_wage)} for e in employees[:30]]
    return JsonResponse({'employees': data})

@login_required
def employee_update_photo(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Check permission: Must be Admin OR the employee themselves
    if not (request.user.can_manage or (request.user.employee is not None and request.user.employee.id == employee.id)):
        messages.error(request, "Permission Denied. You cannot update this profile photo.")
        return redirect('dashboard')
        
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        employee.profile_pic = request.FILES['profile_pic']
        employee.save()
        messages.success(request, "Profile photo updated successfully!")
        
    return redirect('employee_detail', pk=pk)

@login_required
def employee_remove_photo(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if not (request.user.can_manage or (request.user.employee is not None and request.user.employee.id == employee.id)):
        messages.error(request, "Permission Denied. You cannot update this profile photo.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        if employee.profile_pic:
            employee.profile_pic.delete()
            employee.save()
            messages.success(request, "Profile photo removed successfully!")
            
    return redirect('employee_detail', pk=pk)


@login_required
def download_employees_pdf(request):
    employees = Employee.objects.all().order_by('employee_id')
    
    # Filter using GET params exactly like the list view
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if query:
        employees = employees.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    if role_filter:
        employees = employees.filter(role=role_filter)
    if status_filter:
        employees = employees.filter(status=status_filter)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="employees_list.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=40, bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=20,
    )
    elements.append(Paragraph("Decore ERP - Employees List", title_style))
    elements.append(Spacer(1, 10))

    # Table Header
    data = [['ID', 'Name', 'Phone', 'Role', 'Status']]

    # Table Rows
    for emp in employees:
        data.append([
            emp.employee_id or '-',
            emp.name,
            emp.phone or '-',
            emp.get_role_display(),
            emp.get_status_display()
        ])

    table = Table(data, colWidths=[60, 160, 100, 120, 80])
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
