from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Payment
from .forms import PaymentForm
from employees.models import Employee
from core.decorators import admin_or_office_staff_required
import calendar
from django.http import JsonResponse


@login_required
@admin_or_office_staff_required
def payment_list(request):
    payments = Payment.objects.select_related('employee').all()
    status_filter = request.GET.get('status', '')
    month_filter = request.GET.get('month', '')
    year_filter = request.GET.get('year', str(timezone.now().date().year))
    q = request.GET.get('q', '')

    if status_filter:
        payments = payments.filter(status=status_filter)
    if month_filter:
        payments = payments.filter(month=month_filter)
    if year_filter:
        payments = payments.filter(year=year_filter)
    if q:
        payments = payments.filter(employee__name__icontains=q)

    from salary.models import SalarySummary
    total_paid = payments.aggregate(t=Sum('paid_amount'))['t'] or 0
    
    # Calculate truth global pending based on filtered summaries (if month/year used) or global otherwise
    s_queryset = SalarySummary.objects.all()
    if month_filter: s_queryset = s_queryset.filter(month=month_filter)
    if year_filter: s_queryset = s_queryset.filter(year=year_filter)
    if q: s_queryset = s_queryset.filter(employee__name__icontains=q)
    
    total_pending = sum(s.pending_amount for s in s_queryset)

    # Filter out summaries that actually have a pending balance to show in a separate section
    pending_dues = [s for s in s_queryset if s.pending_amount > 0]

    paginator = Paginator(payments, 20)
    payments = paginator.get_page(request.GET.get('page'))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    return render(request, 'payments/payment_list.html', {
        'payments': payments, 'status_filter': status_filter,
        'month_filter': month_filter, 'year_filter': year_filter, 'q': q,
        'total_paid': total_paid, 'total_pending': total_pending,
        'pending_dues': pending_dues,
        'months': months, 'status_choices': Payment.STATUS_CHOICES,
    })


@login_required
@admin_or_office_staff_required
def payment_add(request):
    import uuid
    initial = {'reference_number': f"PAY-{uuid.uuid4().hex[:6].upper()}"}
    summary_id = request.GET.get('summary_id')
    if summary_id:
        from salary.models import SalarySummary
        summary = get_object_or_404(SalarySummary, pk=summary_id)
        initial.update({
            'employee': summary.employee,
            'salary_summary': summary,
            'month': summary.end_date.month if summary.end_date else summary.month,
            'year': summary.end_date.year if summary.end_date else summary.year,
            'total_amount': summary.net_payable,
            'paid_amount': summary.pending_amount,
        })
        
    form = PaymentForm(request.POST or None, initial=initial)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.recorded_by = request.user
        payment.save()
        
        # Auto-Finalize salary if paid out
        if payment.salary_summary and payment.status == 'paid':
            payment.salary_summary.status = 'finalized'
            payment.salary_summary.save()
            
        messages.success(request, f'Payment recorded for {payment.employee.name}.')
        return redirect('payment_list')
    return render(request, 'payments/payment_form.html', {'form': form, 'title': 'Record Payment'})


@login_required
@admin_or_office_staff_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
@admin_or_office_staff_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    form = PaymentForm(request.POST or None, instance=payment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Payment updated.')
        return redirect('payment_detail', pk=pk)
    return render(request, 'payments/payment_form.html', {'form': form, 'title': 'Edit Payment', 'payment': payment})


@login_required
@admin_or_office_staff_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted.')
        return redirect('payment_list')
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})


@login_required
def employee_payment_history(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    
    # Check permissions: Admin/Accountant or the Employee themselves
    if not request.user.can_manage and (not hasattr(request.user, 'employee') or request.user.employee.pk != employee.pk):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    payments = Payment.objects.filter(employee=employee).order_by('-payment_date')
    total_paid = payments.aggregate(t=Sum('paid_amount'))['t'] or 0
    total_pending = payments.aggregate(t=Sum('pending_amount'))['t'] or 0
    return render(request, 'payments/employee_payment_history.html', {
        'employee': employee, 'payments': payments,
        'total_paid': total_paid, 'total_pending': total_pending,
    })

@login_required
@admin_or_office_staff_required
def api_get_pending_salary(request):
    emp_id = request.GET.get('employee_id')
    if not emp_id:
        return JsonResponse({'error': 'No employee ID provided'}, status=400)
    
    from salary.models import SalarySummary
    summaries = SalarySummary.objects.filter(employee_id=emp_id).order_by('-year', '-month')
    
    summary = None
    for s in summaries:
        if s.pending_amount > 0:
            summary = s
            break
    
    if summary:
        month = summary.end_date.month if summary.end_date else summary.month
        year = summary.end_date.year if summary.end_date else summary.year
        summary_text = f"{summary.employee.name} – {month}/{year} – ₹{float(summary.pending_amount):.2f}"
        if summary.end_date:
            summary_text = f"{summary.employee.name} – {summary.start_date.strftime('%b %d')} to {summary.end_date.strftime('%b %d, %Y')} – ₹{float(summary.pending_amount):.2f}"
            
        return JsonResponse({
            'success': True,
            'summary_id': summary.id,
            'summary_text': summary_text,
            'month': month,
            'year': year,
            'net_payable': float(summary.net_payable),
            'pending_amount': float(summary.pending_amount),
        })
    return JsonResponse({'success': False})
