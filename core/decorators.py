from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_or_office_staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.role in ['admin', 'office_staff'] or request.user.is_superuser):
            messages.error(request, 'Insufficient permissions.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
