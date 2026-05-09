from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import WorkSite, EmployeeAssignment
from .forms import WorkSiteForm, AssignmentForm
from core.decorators import admin_required, admin_or_office_staff_required


@login_required
@admin_or_office_staff_required
def site_list(request):
    sites = WorkSite.objects.all()
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if q:
        sites = sites.filter(Q(name__icontains=q) | Q(location__icontains=q))
    if status:
        sites = sites.filter(status=status)
    paginator = Paginator(sites, 12)
    sites = paginator.get_page(request.GET.get('page'))
    return render(request, 'sites_mgmt/site_list.html', {
        'sites': sites, 'q': q, 'status': status,
        'status_choices': WorkSite.STATUS_CHOICES,
    })


@login_required
def site_detail(request, pk):
    site = get_object_or_404(WorkSite, pk=pk)
    
    # Security check
    if not request.user.can_manage and request.user.role != 'driver':
        if request.user.employee is not None:
            is_assigned = EmployeeAssignment.objects.filter(site=site, employee=request.user.employee, is_active=True).exists()
            if not is_assigned:
                messages.error(request, "Access denied. You are not assigned to this site.")
                return redirect('worker_sites')
        else:
            return redirect('login')
    assignments = EmployeeAssignment.objects.filter(site=site).select_related('employee','supervisor')
    today = timezone.now().date()
    labor_cost = site.get_labor_cost(today.month, today.year)
    
    is_assigned_main_worker = False
    if request.user.employee is not None and request.user.employee.role == 'main_worker':
        is_assigned_main_worker = assignments.filter(employee=request.user.employee, is_active=True).exists()
        
    from inventory.models import DeliveryLogItem
    from django.db.models import Sum
    
    delivered_materials = DeliveryLogItem.objects.filter(log__site=site).values(
        'item__name', 'item__unit', 'item__unit_price'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('item__name')
    
    total_material_cost = sum(
        item['total_quantity'] * item['item__unit_price'] for item in delivered_materials
    )
        
    return render(request, 'sites_mgmt/site_detail.html', {
        'site': site, 'assignments': assignments, 'labor_cost': labor_cost, 'today': today,
        'is_assigned_main_worker': is_assigned_main_worker,
        'delivered_materials': delivered_materials, 'total_material_cost': total_material_cost,
    })


@admin_or_office_staff_required
def site_add(request):
    form = WorkSiteForm(request.POST or None)
    if form.is_valid():
        site = form.save(commit=False)
        if site.client_phone and site.client_name:
            from core.models import CustomUser
            username = site.client_phone
            user, created = CustomUser.objects.get_or_create(username=username, defaults={
                'first_name': site.client_name.split()[0] if site.client_name else '',
                'last_name': ' '.join(site.client_name.split()[1:]) if len(site.client_name.split()) > 1 else '',
                'role': 'client',
                'phone': site.client_phone,
                'email': site.client_email,
            })
            if created:
                user.set_password(site.client_phone)
                user.save()
            site.client_user = user
        site.save()
        messages.success(request, f'Work site "{site.name}" created. Client Login: {site.client_phone} (PW: {site.client_phone})')
        return redirect('site_detail', pk=site.pk)
    return render(request, 'sites_mgmt/site_form.html', {'form': form, 'title': 'Add Work Site'})


@admin_or_office_staff_required
def site_edit(request, pk):
    site = get_object_or_404(WorkSite, pk=pk)
    form = WorkSiteForm(request.POST or None, instance=site)
    if form.is_valid():
        site = form.save(commit=False)
        if site.client_phone and site.client_name:
            from core.models import CustomUser
            username = site.client_phone
            user, created = CustomUser.objects.get_or_create(username=username, defaults={
                'first_name': site.client_name.split()[0] if site.client_name else '',
                'last_name': ' '.join(site.client_name.split()[1:]) if len(site.client_name.split()) > 1 else '',
                'role': 'client',
                'phone': site.client_phone,
                'email': site.client_email,
            })
            if created:
                user.set_password(site.client_phone)
                user.save()
            site.client_user = user
        site.save()
        messages.success(request, f'Site "{site.name}" updated.')
        return redirect('site_detail', pk=pk)
    return render(request, 'sites_mgmt/site_form.html', {'form': form, 'title': 'Edit Site', 'site': site})


@admin_or_office_staff_required
def site_delete(request, pk):
    site = get_object_or_404(WorkSite, pk=pk)
    if request.method == 'POST':
        site.status = 'completed'
        site.save()
        messages.success(request, f'Site "{site.name}" marked as completed.')
        return redirect('site_list')
    return render(request, 'sites_mgmt/site_confirm_delete.html', {'site': site})


@admin_or_office_staff_required
def assign_employee(request, site_pk):
    site = get_object_or_404(WorkSite, pk=site_pk)
    form = AssignmentForm(request.POST or None)
    if form.is_valid():
        assignment = form.save(commit=False)
        assignment.site = site
        assignment.save()
        messages.success(request, f'{assignment.employee.name} assigned to {site.name}.')
        return redirect('site_detail', pk=site_pk)
    return render(request, 'sites_mgmt/assign_form.html', {'form': form, 'site': site})


@login_required
def remove_assignment(request, pk):
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)
    site_pk = assignment.site.pk
    if request.method == 'POST':
        assignment.is_active = False
        assignment.end_date = timezone.now().date()
        assignment.save()
        messages.success(request, f'{assignment.employee.name} removed from site.')
        return redirect('site_detail', pk=site_pk)
    return render(request, 'sites_mgmt/remove_assignment.html', {'assignment': assignment})

@login_required
def worker_sites(request):
    if not (request.user.employee is not None) or not request.user.employee:
        return redirect('dashboard')
        
    assignments = EmployeeAssignment.objects.filter(employee=request.user.employee, is_active=True).select_related('site')
    if assignments.count() == 1:
        return redirect('site_detail', pk=assignments.first().site.pk)
    
    return render(request, 'sites_mgmt/worker_sites.html', {'assignments': assignments})

@login_required
def client_dashboard(request):
    if getattr(request.user, 'role', '') != 'client':
        return redirect('dashboard')
    sites = request.user.client_sites.all()
    
    # If the client only has 1 project, jump straight to the project details
    if sites.count() == 1:
        return redirect('client_site_detail', pk=sites.first().pk)
        
    return render(request, 'sites_mgmt/client_dashboard.html', {'sites': sites})

@login_required
def client_finance(request):
    from django.db.models import Sum
    if getattr(request.user, 'role', '') != 'client':
        return redirect('dashboard')
        
    sites = request.user.client_sites.all()
    total_estimated = sites.aggregate(total=Sum('estimated_cost'))['total'] or 0
    total_paid = sum(site.amount_paid for site in sites)
    total_balance = sum(site.balance_due for site in sites)
    
    # Get all payments across all sites, ordered by newest
    from .models import SitePayment
    payments = SitePayment.objects.filter(site__in=sites).order_by('-payment_date', '-id')
    
    context = {
        'total_estimated': total_estimated,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'payments': payments,
        'sites': sites
    }
    return render(request, 'sites_mgmt/client_finance.html', context)

@login_required
def client_site_detail(request, pk):
    if getattr(request.user, 'role', '') != 'client':
        return redirect('dashboard')
    site = get_object_or_404(WorkSite, pk=pk, client_user=request.user)
    areas = site.areas.all().prefetch_related('images')
    return render(request, 'sites_mgmt/client_site_detail.html', {'site': site, 'areas': areas})

@login_required
def site_area_add(request, site_pk):
    from .models import WorkArea
    site = get_object_or_404(WorkSite, pk=site_pk)
    
    can_edit = request.user.can_manage
    if not can_edit and request.user.employee is not None and request.user.employee.role == 'main_worker':
        can_edit = EmployeeAssignment.objects.filter(site=site, employee=request.user.employee, is_active=True).exists()
    if not can_edit:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            WorkArea.objects.create(site=site, name=name)
            messages.success(request, f'Area "{name}" added.')
    return redirect('site_detail', pk=site_pk)

@login_required
def site_area_update(request, area_pk):
    from .models import WorkArea, WorkAreaImage, EmployeeAssignment
    area = get_object_or_404(WorkArea, pk=area_pk)
    
    can_edit = request.user.can_manage
    is_main_worker = False
    if not can_edit and request.user.employee is not None and request.user.employee.role == 'main_worker':
        is_main_worker = EmployeeAssignment.objects.filter(site=area.site, employee=request.user.employee, is_active=True).exists()
        can_edit = is_main_worker
        
    if not can_edit:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        new_name = request.POST.get('name')
        if new_name:
            area.name = new_name
        area.status = request.POST.get('status', area.status)
        area.progress_percentage = request.POST.get('progress_percentage', area.progress_percentage)
        area.save()
        
        # Check for image upload - strictly admin only
        if request.user.can_manage:
            images = request.FILES.getlist('images')
            for image in images:
                WorkAreaImage.objects.create(work_area=area, image=image)
            
        messages.success(request, f'Area "{area.name}" updated.')
    return redirect('site_detail', pk=area.site.pk)

@login_required
def site_area_delete(request, area_pk):
    from .models import WorkArea
    area = get_object_or_404(WorkArea, pk=area_pk)
    
    # Only admins or office staff can delete areas
    if not request.user.can_manage:
        messages.error(request, 'Permission denied. Only admins can delete work areas.')
        return redirect('dashboard')
        
    site_pk = area.site.pk
    if request.method == 'POST':
        area_name = area.name
        area.delete()
        messages.success(request, f'Work Area "{area_name}" deleted successfully.')
        
    return redirect('site_detail', pk=site_pk)

@login_required
def delete_area_image(request, image_pk):
    from .models import WorkAreaImage
    image = get_object_or_404(WorkAreaImage, pk=image_pk)
    area = image.work_area
    site = area.site
    
    # Only admins can delete photos
    can_edit = request.user.can_manage
    
    if not can_edit:
        messages.error(request, 'Permission denied. Only admins can delete photos.')
        return redirect('site_detail', pk=site.pk)
        
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully.')
        
    return redirect('site_detail', pk=site.pk)

@admin_or_office_staff_required
def site_add_payment(request, site_pk):
    from .forms import SitePaymentForm
    site = get_object_or_404(WorkSite, pk=site_pk)
    form = SitePaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.site = site
        payment.save()
        messages.success(request, f'Payment of ₹{payment.amount} recorded successfully.')
        return redirect('site_detail', pk=site_pk)
    return render(request, 'sites_mgmt/site_payment_form.html', {'form': form, 'site': site})

@admin_or_office_staff_required
def site_delete_payment(request, payment_pk):
    from .models import SitePayment
    payment = get_object_or_404(SitePayment, pk=payment_pk)
    site_pk = payment.site.pk
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment record deleted.')
        return redirect('site_detail', pk=site_pk)
    return redirect('site_detail', pk=site_pk)

@login_required
def download_payment_receipt(request, payment_pk):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from django.http import HttpResponse
    import os
    from django.conf import settings
    
    from .models import SitePayment
    payment = get_object_or_404(SitePayment, pk=payment_pk)
    
    # Check permissions
    if getattr(request.user, 'role', '') == 'client':
        if request.user not in [payment.site.client_user]:
            messages.error(request, 'Permission denied.')
            return redirect('dashboard')
    elif not request.user.can_manage:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.site.name.replace(" ", "_")}_{payment.payment_date.strftime("%b_%d_%Y")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=10, textColor=colors.HexColor("#0f172a"), alignment=1)
    subtitle_style = ParagraphStyle(name='SubtitleStyle', parent=styles['Heading2'], fontSize=12, spaceAfter=20, textColor=colors.HexColor("#64748b"), alignment=1)
    heading_style = ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor("#0f172a"))
    normal_style = styles['Normal']
    
    # Header Section
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=80, height=80)
        elements.append(logo)
        elements.append(Spacer(1, 10))
        
    elements.append(Paragraph("<b>PAYMENT RECEIPT</b>", title_style))
    elements.append(Paragraph("<b>Decore Developers</b><br/>Thank you for your business.", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Receipt Info
    receipt_info = f"<b>Receipt No:</b> REC-{payment.id:04d}<br/>"
    receipt_info += f"<b>Date of Payment:</b> {payment.payment_date.strftime('%B %d, %Y')}<br/>"
    receipt_info += f"<b>Project Name:</b> {payment.site.name}<br/>"
    if payment.site.client_user:
        receipt_info += f"<b>Client Name:</b> {payment.site.client_user.get_full_name() or payment.site.client_user.username}<br/>"
    elements.append(Paragraph(receipt_info, normal_style))
    elements.append(Spacer(1, 20))
    
    # Payment Details Table
    data = [
        ['Description', 'Details'],
        ['Payment Method', payment.get_method_display()],
        ['Reference / Notes', payment.notes if payment.notes else 'N/A'],
        ['Amount Paid', f"Rs. {payment.amount:,.2f}"]
    ]
    
    t = Table(data, colWidths=[200, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1,-1), (1,-1), colors.HexColor("#16a34a")), # Green color for amount
        ('FONTSIZE', (1,-1), (1,-1), 14),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 40))
    
    # Footer Section
    footer_text = "<i>This is a computer-generated receipt and does not require a physical signature.</i><br/>"
    footer_text += "If you have any questions about this receipt, please contact <b>Decore Developers</b>."
    elements.append(Paragraph(footer_text, ParagraphStyle(name='Footer', parent=styles['Normal'], alignment=1, textColor=colors.gray, fontSize=9)))
    
    doc.build(elements)
    return response

@login_required
def download_site_materials_pdf(request, pk):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from django.http import HttpResponse
    from inventory.models import DeliveryLogItem
    from django.db.models import Sum

    site = get_object_or_404(WorkSite, pk=pk)
    
    delivered_materials = DeliveryLogItem.objects.filter(log__site=site).values(
        'item__name', 'item__unit', 'item__unit_price'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('item__name')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="materials_{site.name.replace(" ", "_")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Material Delivery Report: {site.name}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    is_admin = request.user.is_superuser or request.user.role == 'admin'
    
    if is_admin:
        data = [['Item Name', 'Quantity Delivered', 'Unit', 'Unit Price (INR)', 'Total Cost (INR)']]
    else:
        data = [['Item Name', 'Quantity Delivered', 'Unit']]
        
    total_cost = 0
    
    for mat in delivered_materials:
        row = [
            mat['item__name'],
            f"{mat['total_quantity']:.2f}",
            mat['item__unit'],
        ]
        
        if is_admin:
            cost = mat['total_quantity'] * mat['item__unit_price']
            total_cost += cost
            row.extend([f"{mat['item__unit_price']:.2f}", f"{cost:,.2f}"])
            
        data.append(row)
        
    if is_admin:
        data.append(['', '', '', 'Grand Total:', f"{total_cost:,.2f}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
    ]))
    
    elements.append(table)
    doc.build(elements)
    return response
