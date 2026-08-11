from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def urbn_admin_check(user):
    if not user.is_authenticated:
        return False
    
    if not (user.is_active and user.is_staff):
        return False
        
    admin_email = getattr(settings, 'ADMIN_EMAIL', '').strip().lower()
    user_email = user.email.strip().lower()
    
    if user_email != admin_email:
        return False
        
    return True

def urbn_admin_required(function=None):
    """
    Decorator for views that checks that the user is logged in, is active,
    is a staff member, and matches the ADMIN_EMAIL exactly.
    """
    def check_and_call(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        
        if urbn_admin_check(request.user):
            return function(request, *args, **kwargs)
            
        raise PermissionDenied("You do not have permission to access the URBN Admin Dashboard.")

    return check_and_call
