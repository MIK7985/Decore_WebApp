from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
import datetime
from .decorators import admin_or_office_staff_required

def csrf_failure(request, reason=""):
    messages.error(request, "Your session has expired or you've been logged out in another window. Please log in again.")
    return redirect('login_view')
def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', '') == 'client':
            return redirect('client_dashboard')
        if not request.user.can_manage and hasattr(request.user, 'employee') and request.user.employee:
            return redirect('employee_detail', pk=request.user.employee.pk)
        return redirect('dashboard')
    
    if request.method == 'POST':
        login_input = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=login_input, password=password)
        
        if not user:
            from employees.models import Employee
            try:
                emp = Employee.objects.filter(phone=login_input).first()
                if emp and hasattr(emp, 'user_account') and emp.user_account:
                    user = authenticate(request, username=emp.user_account.username, password=password)
            except Exception:
                pass

        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            if getattr(user, 'role', '') == 'client':
                return redirect('client_dashboard')
            if not user.can_manage and hasattr(user, 'employee') and user.employee:
                return redirect('employee_detail', pk=user.employee.pk)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            
    response = render(request, 'core/login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form, 'title': 'Change Password'})


@login_required
@admin_or_office_staff_required
def dashboard(request):
    from employees.models import Employee
    from sites_mgmt.models import WorkSite, EmployeeAssignment
    from attendance.models import Attendance
    from salary.models import SalarySummary
    from payments.models import Payment
    from inventory.models import DeliveryLog, MaterialRequest

    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    current_month = today.month
    current_year = today.year

    total_employees = Employee.objects.filter(status='active').count()
    active_sites = WorkSite.objects.filter(status='active').count()

    monthly_salary = SalarySummary.objects.filter(
        month=current_month, year=current_year
    ).aggregate(total=Sum('net_payable'))['total'] or 0

    pending_payments = Payment.objects.filter(
        status__in=['pending', 'partial']
    ).aggregate(total=Sum('pending_amount'))['total'] or 0

    today_present = Attendance.objects.filter(date=today, status__in=['present', '1_5_days']).count()
    today_absent = Attendance.objects.filter(date=today, status='absent').count()
    today_half = Attendance.objects.filter(date=today, status='half_day').count()

    today_deliveries = DeliveryLog.objects.filter(date=today).count()
    pending_requests = MaterialRequest.objects.filter(status='pending').count()

    recent_employees = Employee.objects.filter(status='active').order_by('-joining_date')[:5]
    sites = WorkSite.objects.filter(status='active').prefetch_related('assignments', 'areas')[:6]

    # Role distribution chart
    role_counts = Employee.objects.filter(status='active').values('role').annotate(count=Count('id'))
    role_labels = [r['role'].replace('_', ' ').title() for r in role_counts]
    role_data = [r['count'] for r in role_counts]

    # Recent payments
    recent_payments = Payment.objects.select_related('employee').order_by('-payment_date')[:5]

    context = {
        'total_employees': total_employees,
        'active_sites': active_sites,
        'monthly_salary': monthly_salary,
        'pending_payments': pending_payments,
        'today_present': today_present,
        'today_absent': today_absent,
        'today_half': today_half,
        'today_deliveries': today_deliveries,
        'pending_requests': pending_requests,
        'recent_employees': recent_employees,
        'sites': sites,
        'role_labels': role_labels,
        'role_data': role_data,
        'recent_payments': recent_payments,
        'today': today,
        'current_month_name': today.strftime('%B %Y'),
        'is_employee': False,
    }
    return render(request, 'core/dashboard.html', context)


def download_invoice_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Invoice_Decore_ERP.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=20, textColor=colors.HexColor("#0f172a"))
    heading_style = ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor("#0f172a"))
    normal_style = styles['Normal']

    elements.append(Paragraph("<b>INVOICE & PROPOSAL</b>", title_style))
    elements.append(Paragraph("<b>To:</b> [Client / Company Name]", normal_style))
    elements.append(Paragraph("<b>Date:</b> April 27, 2026", normal_style))
    elements.append(Paragraph("<b>Invoice #:</b> INV-2026-001", normal_style))
    elements.append(Paragraph("<b>Project:</b> Enterprise POP Work Management System (ERP)", normal_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>1. Professional Services & Software Development</b>", heading_style))
    elements.append(Paragraph("<i>Custom ERP Web Application (Source Code & Licensing)</i>", normal_style))
    desc = "Included Modules:<br/>- Core Dashboard: Real-time analytics, financial summaries.<br/>- Workforce Management: Profiles, roles, document handling.<br/>- Smart Attendance Engine: Auto-sorting, 'One-Day, One-Attendance', Overtime calculations.<br/>- Financial Suite: Salary calculations, Advance requests, Payments.<br/>- Inventory & Logistics: Material requests, delivery logs.<br/>- Premium UI/UX: Glassmorphic design, mobile-responsive."
    elements.append(Paragraph(desc, normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Cost:</b> ₹ 1,50,000", normal_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>2. Cloud Infrastructure & Deployment (AWS)</b>", heading_style))
    elements.append(Paragraph("<i>Production-ready deployment on Amazon Web Services.</i>", normal_style))
    desc2 = "Included Services:<br/>- Amazon EC2: Secure Linux server provisioning.<br/>- Amazon RDS: Managed PostgreSQL database with daily backups.<br/>- Amazon S3: Cloud storage for media and PDF generation.<br/>- SSL & Domain: Secure HTTPS lock and Route53 DNS setup."
    elements.append(Paragraph(desc2, normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Cost:</b> ₹ 25,000", normal_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>3. Ongoing Hosting & Maintenance</b>", heading_style))
    elements.append(Paragraph("<i>Monthly AWS Resource Costs & Technical Support.</i>", normal_style))
    desc3 = "Includes:<br/>- Monthly AWS Server & Database costs.<br/>- Security patches and database monitoring.<br/>- Minor bug fixes and technical support."
    elements.append(Paragraph(desc3, normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Cost:</b> ₹ 8,000 / month", normal_style))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("<b>Total Investment Summary</b>", heading_style))
    data = [
        ['Description', 'Amount'],
        ['Software Development & Core Features', '₹ 1,50,000'],
        ['AWS Infrastructure Setup (One-time)', '₹ 25,000'],
        ['Subtotal (Due upon deployment)', '₹ 1,75,000'],
        ['', ''],
        ['Annual Hosting & Maintenance (Optional)', '₹ 96,000 / year']
    ]
    t = Table(data, colWidths=[300, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))
    ]))
    elements.append(t)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Important Details & Terms to Notice:</b>", heading_style))
    terms = "1. <b>Ownership:</b> Full ownership of source code transferred upon final payment.<br/>2. <b>Scalability:</b> AWS architecture designed to scale seamlessly without downtime.<br/>3. <b>Training:</b> Includes 2 complimentary remote training sessions for Administrators.<br/>4. <b>Payment Terms:</b> 50% deposit required prior to deployment; remaining 50% due on launch."
    elements.append(Paragraph(terms, normal_style))

    doc.build(elements)
    return response
