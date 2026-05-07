from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import SalarySummary, AdvanceRequest
from employees.models import Employee
from attendance.models import Attendance
from core.decorators import admin_or_office_staff_required
import calendar
from decimal import Decimal


@login_required
@admin_or_office_staff_required
def salary_list(request):
    import datetime
    
    today = timezone.now().date()
    
    # Calculate the current week's Saturday
    days_ahead = 5 - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    current_saturday = today + datetime.timedelta(days=days_ahead)
    
    # Get filters
    year_str = request.GET.get('year')
    month_str = request.GET.get('month')
    
    if year_str and month_str:
        year = int(year_str)
        month = int(month_str)
    else:
        year = current_saturday.year
        month = current_saturday.month
    
    # Generate weeks for this month
    cal = calendar.monthcalendar(year, month)
    saturdays = []
    for w in cal:
        if w[calendar.SATURDAY] != 0:
            saturdays.append(datetime.date(year, month, w[calendar.SATURDAY]))
            
    weeks = []
    for i, sat in enumerate(saturdays):
        start = sat - datetime.timedelta(days=6)
        weeks.append({
            'week_num': i + 1,
            'start_date': start,
            'end_date': sat,
            'label': f"Week {i + 1} ({start.strftime('%b %d')} - {sat.strftime('%b %d')})"
        })
        
    # Default to current week if viewing current month, else week 1
    default_week = 1
    if year == current_saturday.year and month == current_saturday.month and weeks:
        for w in weeks:
            if w['start_date'] <= today <= w['end_date']:
                default_week = w['week_num']
                break
        else:
            # If today somehow doesn't match, check if current_saturday is in this list
            for w in weeks:
                if w['end_date'] == current_saturday:
                    default_week = w['week_num']
                    break
                
    week_str = request.GET.get('week')
    if week_str:
        week_num = int(week_str)
    else:
        week_num = default_week
    
    # Ensure week_num is valid
    if week_num < 1 or week_num > len(weeks):
        week_num = 1
        
    selected_week = weeks[week_num - 1]
    start_date = selected_week['start_date']
    end_date = selected_week['end_date']
        
    # Auto-generate or update salaries for the viewed week
    employees = Employee.objects.filter(status='active')
    for emp in employees:
        att_records = Attendance.objects.filter(employee=emp, date__gte=start_date, date__lte=end_date)
        working_days = Decimal(str(sum(r.day_value for r in att_records)))
        
        unapplied_advances = AdvanceRequest.objects.filter(employee=emp, status='approved', salary_summary__isnull=True)
        advance_total = sum(a.get_final_amount for a in unapplied_advances)
        
        summary = SalarySummary.objects.filter(employee=emp, start_date=start_date, end_date=end_date).first()
        if summary:
            if summary.status != 'finalized':
                if working_days == 0 and summary.total_paid == 0:
                    summary.deducted_advances.update(salary_summary=None)
                    summary.delete() # Remove if no attendance and no payments made
                else:
                    gross = working_days * emp.daily_wage
                    summary.working_days = working_days
                    summary.daily_wage = emp.daily_wage
                    summary.gross_salary = gross
                    
                    # Calculate linked advances to ensure idempotency
                    linked_advances_total = sum(a.get_final_amount for a in summary.deducted_advances.all())
                    
                    summary.deductions = linked_advances_total + advance_total
                    summary.net_payable = gross - summary.deductions
                    summary.save()
                    
                    if advance_total > 0:
                        for adv in unapplied_advances:
                            adv.salary_summary = summary
                            adv.save()
        else:
            if working_days > 0:
                gross = working_days * emp.daily_wage
                summary = SalarySummary.objects.create(
                    employee=emp, start_date=start_date, end_date=end_date,
                    working_days=working_days, daily_wage=emp.daily_wage,
                    gross_salary=gross, deductions=advance_total, net_payable=gross-advance_total
                )
                if advance_total > 0:
                    for adv in unapplied_advances:
                        adv.salary_summary = summary
                        adv.save()
            
    summaries = SalarySummary.objects.filter(end_date=end_date).select_related('employee').prefetch_related('payments')
    total = summaries.aggregate(t=Sum('net_payable'))['t'] or 0
    total_paid = sum(s.total_paid for s in summaries)
    total_pending = sum(s.pending_amount for s in summaries)
    total_employees = summaries.count()
    
    months = [{'value': i, 'label': calendar.month_name[i]} for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]
        
    return render(request, 'salary/salary_list.html', {
        'summaries': summaries, 
        'start_date': start_date,
        'end_date': end_date,
        'total': total,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_employees': total_employees,
        'selected_year': year,
        'selected_month': month,
        'selected_week': week_num,
        'weeks': weeks,
        'months': months,
        'years': years
    })

@login_required
@admin_or_office_staff_required
def download_salary_report(request):
    import csv
    from django.http import HttpResponse
    
    import datetime
    
    end_date_str = request.GET.get('end_date')
    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except:
        end_date = timezone.now().date()
        
    start_date = end_date - datetime.timedelta(days=6)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="salary_report_week_{end_date_str}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([f'Salary Report for Week: {start_date.strftime("%d %b %Y")} to {end_date.strftime("%d %b %Y")}'])
    writer.writerow([])
    writer.writerow(['Employee Name', 'Daily Wage', 'Working Days', 'Gross Amount', 'Advance Deducted', 'Net Payable', 'Paid Amount', 'Pending Amount'])
    
    summaries = SalarySummary.objects.filter(end_date=end_date).select_related('employee')
    for s in summaries:
        writer.writerow([
            s.employee.name,
            f"{s.daily_wage:.2f}",
            s.working_days,
            f"{s.gross_salary:.2f}",
            f"{s.deductions:.2f}",
            f"{s.net_payable:.2f}",
            f"{s.total_paid:.2f}",
            f"{s.pending_amount:.2f}"
        ])
        
    return response

@login_required
@admin_or_office_staff_required
def download_salary_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    import calendar
    import os
    from django.conf import settings
    
    import datetime
    
    end_date_str = request.GET.get('end_date')
    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except:
        end_date = timezone.now().date()
        
    start_date = end_date - datetime.timedelta(days=6)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="salary_report_week_{end_date_str}.pdf"'
    
    # A4 dimensions are 595.27 x 841.89 points
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Create Header Table (Logo + Title)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-removebg-preview (1).png')
        
    header_data = []
    
    title_html = f"<font size=20 color='#0f172a'><b>Decore Developers</b></font><br/><br/><font size=10 color='#64748b'><b>OFFICIAL WEEKLY SALARY REPORT</b> &nbsp;&nbsp;|&nbsp;&nbsp; {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}</font>"
    title_p = Paragraph(title_html, styles['Normal'])
    
    if os.path.exists(logo_path):
        img = Image(logo_path, width=70, height=70, mask='auto')
        header_data.append([img, title_p])
        header_table = Table(header_data, colWidths=[80, 450])
    else:
        header_data.append([title_p])
        header_table = Table(header_data, colWidths=[530])
        
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    data = [['Employee Name', 'Wage', 'Days', 'Gross', 'Advance', 'Net', 'Pending']]
    
    summaries = SalarySummary.objects.filter(end_date=end_date).select_related('employee')
    total_gross = 0
    total_advance = 0
    total_net = 0
    total_pending = 0
    for s in summaries:
        data.append([
            s.employee.name,
            f"{s.daily_wage:.0f}",
            str(s.working_days),
            f"{s.gross_salary:.0f}",
            f"{s.deductions:.0f}",
            f"{s.net_payable:.0f}",
            f"{s.pending_amount:.0f}",
        ])
        total_gross += s.gross_salary
        total_advance += s.deductions
        total_net += s.net_payable
        total_pending += s.pending_amount
        
    data.append([
        'TOTAL', 
        '', 
        '', 
        f"{total_gross:.0f}", 
        f"{total_advance:.0f}", 
        f"{total_net:.0f}", 
        f"{total_pending:.0f}"
    ])
    
    # Total width of A4 is 595. Margins are 30+30=60. Available width = 535.
    table = Table(data, colWidths=[150, 55, 50, 70, 70, 70, 70])
    table.setStyle(TableStyle([
        # Header Row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#ffffff")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'), # Left align names
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Body Rows
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#334155")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 1), (-1, -2), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 10),
        
        # Grid lines
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor("#0f172a")),
        
        # Footer Row (Totals)
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#0f172a")),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response





@login_required
@admin_or_office_staff_required
def salary_detail(request, pk):
    summary = get_object_or_404(SalarySummary, pk=pk)
    att_records = Attendance.objects.filter(
        employee=summary.employee, date__gte=summary.start_date, date__lte=summary.end_date
    ).order_by('date')
    return render(request, 'salary/salary_detail.html', {
        'summary': summary, 'att_records': att_records,
    })


@login_required
@admin_or_office_staff_required
def salary_edit(request, pk):
    summary = get_object_or_404(SalarySummary, pk=pk)
    if request.method == 'POST':
        summary.deductions = Decimal(request.POST.get('deductions', '0'))
        summary.notes = request.POST.get('notes', '')
        summary.net_payable = summary.gross_salary - summary.deductions
        summary.status = request.POST.get('status', 'draft')
        summary.save()
        messages.success(request, 'Salary record updated.')
        return redirect('salary_detail', pk=pk)
    return render(request, 'salary/salary_edit.html', {'summary': summary})


@login_required
@admin_or_office_staff_required
def finalize_salary(request, pk):
    summary = get_object_or_404(SalarySummary, pk=pk)
    if request.method == 'POST':
        summary.status = 'finalized'
        summary.save()
        messages.success(request, f'Salary finalized for {summary.employee.name}.')
    return redirect('salary_detail', pk=pk)

@login_required
def request_advance(request):
    """Employee view to request an advance"""
    # Ensure only active employees can request
    if not (request.user.employee is not None) or not request.user.employee:
        messages.error(request, "Only registered employees can request advances.")
        return redirect('dashboard')
    
    if request.user.employee.status == 'inactive':
        messages.error(request, "Your account is deactivated. Contact your admin.")
        return redirect('dashboard')
        
    # Show history of requests for this employee
    my_requests = AdvanceRequest.objects.filter(employee=request.user.employee)
    
    # Check if they already have a pending request
    has_pending = my_requests.filter(status='pending').exists()
    
    # Calculate dynamic max advance (e.g., 15 days of wage or 20,000 max)
    daily_wage = request.user.employee.daily_wage
    max_advance = min(Decimal('20000'), daily_wage * 15) if daily_wage else Decimal('5000')
    
    if request.method == 'POST':
        if has_pending:
            messages.error(request, "You already have a pending advance request. Please wait for it to be reviewed.")
            return redirect('request_advance')
            
        amount_str = request.POST.get('amount')
        reason = request.POST.get('reason', '')
        
        try:
            amount = Decimal(amount_str)
            if amount > max_advance:
                messages.error(request, f"Advance amount cannot exceed your limit of ₹{max_advance:,.0f}.")
            elif amount <= 0:
                messages.error(request, "Please enter a valid amount.")
            elif len(reason) > 200:
                messages.error(request, "Reason must be 200 characters or less.")
            else:
                AdvanceRequest.objects.create(
                    employee=request.user.employee,
                    amount=amount,
                    reason=reason
                )
                messages.success(request, 'Advance request submitted successfully.')
                return redirect('request_advance')
        except Exception as e:
            messages.error(request, "Invalid amount entered.")
            
    return render(request, 'salary/request_advance.html', {
        'my_requests': my_requests, 
        'has_pending': has_pending,
        'max_advance': max_advance
    })

@login_required
@admin_or_office_staff_required
def advance_list(request):
    """Admin view to see all advance requests"""
    requests = AdvanceRequest.objects.select_related('employee', 'approved_by').all()
    return render(request, 'salary/advance_list.html', {'requests': requests})

@login_required
@admin_or_office_staff_required
def update_advance(request, pk):
    """Admin view to approve or reject an advance"""
    adv = get_object_or_404(AdvanceRequest, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        approved_amount_str = request.POST.get('approved_amount', '')
        
        if status in ['approved', 'rejected']:
            if status == 'approved':
                try:
                    if approved_amount_str:
                        adv.approved_amount = Decimal(approved_amount_str)
                    else:
                        adv.approved_amount = adv.amount
                except Exception:
                    messages.error(request, "Invalid approved amount.")
                    return redirect('advance_list')
            else:
                adv.approved_amount = None
                
            adv.status = status
            adv.admin_notes = admin_notes
            adv.approved_by = request.user
            adv.save()
            messages.success(request, f'Advance request {status}.')
            
        return redirect('advance_list')
        
    # Calculate Insights for Admin
    emp = adv.employee
    unapplied_advances = AdvanceRequest.objects.filter(employee=emp, status='approved', salary_summary__isnull=True)
    unapplied_total = sum(a.get_final_amount for a in unapplied_advances)
    
    # Calculate unfinalized/draft salary accrued
    unpaid_salary = SalarySummary.objects.filter(employee=emp, status='draft').aggregate(t=Sum('net_payable'))['t'] or Decimal('0')
    
    return render(request, 'salary/advance_edit.html', {
        'adv': adv,
        'unapplied_total': unapplied_total,
        'unpaid_salary': unpaid_salary
    })
