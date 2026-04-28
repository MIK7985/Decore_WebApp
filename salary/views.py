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
    
    # Get filters
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
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
        
    # Default to week 1 if not provided, or to the current week if current month
    default_week = 1
    if year == today.year and month == today.month and weeks:
        found = False
        for w in weeks:
            if w['start_date'] <= today <= w['end_date']:
                default_week = w['week_num']
                found = True
                break
        if not found:
            if today > weeks[-1]['end_date']:
                default_week = weeks[-1]['week_num']
            elif today < weeks[0]['start_date']:
                default_week = 1
                
    week_num = int(request.GET.get('week', default_week))
    
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
        working_days = Decimal(str(sum(1 if r.status == 'present' else 0.5 if r.status == 'half_day' else 0 for r in att_records)))
        
        unapplied_advances = AdvanceRequest.objects.filter(employee=emp, status='approved', salary_summary__isnull=True)
        advance_total = sum(a.amount for a in unapplied_advances)
        
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
                    
                    if advance_total > 0:
                        summary.deductions += advance_total
                        
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
    writer.writerow(['Employee Name', 'Daily Wage', 'Working Days', 'Total Amount', 'Paid Amount', 'Pending Amount'])
    
    summaries = SalarySummary.objects.filter(end_date=end_date).select_related('employee')
    for s in summaries:
        writer.writerow([
            s.employee.name,
            f"{s.daily_wage:.2f}",
            s.working_days,
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
    from reportlab.lib.pagesizes import letter, landscape
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
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Create Header Table (Logo + Title)
    # Prefer Logo.png as it might have a cleaner white background than the removebg one which turns black in PDF
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-removebg-preview (1).png')
        
    header_data = []
    
    title_html = f"<font size=26 color='#0f172a'><b>Decore Developers</b></font><br/><br/><font size=12 color='#64748b'><b>OFFICIAL WEEKLY SALARY REPORT</b> &nbsp;&nbsp;|&nbsp;&nbsp; {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}</font>"
    title_p = Paragraph(title_html, styles['Normal'])
    
    if os.path.exists(logo_path):
        # Use mask='auto' to fix black background issues with transparent PNGs
        img = Image(logo_path, width=80, height=80, mask='auto')
        header_data.append([img, title_p])
        header_table = Table(header_data, colWidths=[100, 500])
    else:
        header_data.append([title_p])
        header_table = Table(header_data, colWidths=[600])
        
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    data = [['Employee Name', 'Daily Wage', 'Working Days', 'Total Amount', 'Paid', 'Pending']]
    
    summaries = SalarySummary.objects.filter(end_date=end_date).select_related('employee')
    total_payable = 0
    total_paid = 0
    total_pending = 0
    for s in summaries:
        data.append([
            s.employee.name,
            f"Rs.{s.daily_wage:.2f}",
            str(s.working_days),
            f"Rs.{s.net_payable:.2f}",
            f"Rs.{s.total_paid:.2f}",
            f"Rs.{s.pending_amount:.2f}",
        ])
        total_payable += s.net_payable
        total_paid += s.total_paid
        total_pending += s.pending_amount
        
    data.append(['TOTAL', '', '', f"Rs.{total_payable:.2f}", f"Rs.{total_paid:.2f}", f"Rs.{total_pending:.2f}"])
        
    table = Table(data, colWidths=[160, 80, 80, 100, 100, 100])
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
    if not hasattr(request.user, 'employee') or not request.user.employee:
        messages.error(request, "Only registered employees can request advances.")
        return redirect('dashboard')
    
    if request.user.employee.status == 'inactive':
        messages.error(request, "Your account is deactivated. Contact your admin.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        try:
            AdvanceRequest.objects.create(
                employee=request.user.employee,
                amount=Decimal(amount),
                reason=reason
            )
            messages.success(request, 'Advance request submitted successfully.')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error submitting request: {e}")
            
    # Show history of requests for this employee
    my_requests = AdvanceRequest.objects.filter(employee=request.user.employee)
    return render(request, 'salary/request_advance.html', {'my_requests': my_requests})

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
        
        if status in ['approved', 'rejected']:
            adv.status = status
            adv.admin_notes = admin_notes
            adv.approved_by = request.user
            adv.save()
            messages.success(request, f'Advance request {status}.')
            
            # Note: The admin will need to manually add this approved advance 
            # to the "Deductions" when editing the weekly SalarySummary.
            # (In a more complex system, this could auto-apply to the next salary).
            
        return redirect('advance_list')
    return render(request, 'salary/advance_edit.html', {'adv': adv})
