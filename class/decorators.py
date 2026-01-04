"""
Custom decorators for CLAS application
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def facilitator_required(view_func):
    """
    Decorator to ensure only facilitators can access the view
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role.name.upper() != "FACILITATOR":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("no_permission")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator to ensure only admins can access the view
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role.name.upper() != "ADMIN":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("no_permission")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def supervisor_required(view_func):
    """
    Decorator to ensure only supervisors can access the view
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role.name.upper() != "SUPERVISOR":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("no_permission")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*allowed_roles):
    """
    Decorator to ensure only users with specific roles can access the view
    Usage: @role_required('ADMIN', 'SUPERVISOR')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_role = request.user.role.name.upper()
            allowed_roles_upper = [role.upper() for role in allowed_roles]
            
            if user_role not in allowed_roles_upper:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("no_permission")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator