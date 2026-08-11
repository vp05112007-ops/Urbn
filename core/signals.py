from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import SecurityEvent, UserProfile, Cart
from django.contrib.auth.models import User
from user_agents import parse
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def send_login_email(sender, request, user, **kwargs):
    if user.email:
        first_name = user.first_name if user.first_name else user.username
        
        subject = "Welcome to URBN Clothing — Login Successful"
        message = f"""Hello {first_name},

Welcome to URBN Clothing.
Your account has been successfully signed in.

We're glad to have you with us. Explore our latest streetwear collections and discover your style.

If you did not perform this login, please secure your account immediately.

Stay stylish,
URBN Clothing
Premium Streetwear
"""
        
        try:
            print(f"URBN LOGIN SIGNAL TRIGGERED FOR: {user.email}")
            res = send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@urbnclothing.com'),
                recipient_list=[user.email],
                fail_silently=False,
            )
            print("SEND_MAIL RESULT:", res)
        except Exception as e:
            print(f"SMTP FAILED: {str(e)}")
            logger.error(f"Failed to send login email to {user.email}: {str(e)}")
            
    # Track login in SecurityEvent
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(ua_string)
    device_info = f"{user_agent.browser.family} on {user_agent.os.family}"
    
    # Check if 2FA is enabled
    if hasattr(user, 'two_factor') and user.two_factor.is_enabled:
        request.session['pending_2fa'] = True
    
    SecurityEvent.objects.create(
        user=user,
        event_type="successful login",
        device_info=device_info
    )

    # Merge Anonymous Cart
    session_key = request.session.session_key
    if session_key:
        try:
            anon_cart = Cart.objects.get(session_key=session_key, user=None)
            user_cart, _ = Cart.objects.get_or_create(user=user)
            
            for item in anon_cart.items.all():
                existing = user_cart.items.filter(
                    product_id=item.product_id,
                    selected_color=item.selected_color,
                    selected_size=item.selected_size,
                    selected_fit=item.selected_fit,
                    custom_text=item.custom_text,
                    placement=item.placement
                ).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                else:
                    item.cart = user_cart
                    item.save()
            anon_cart.delete()
        except Cart.DoesNotExist:
            pass

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user:
        ua_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(ua_string)
        device_info = f"{user_agent.browser.family} on {user_agent.os.family}"
        SecurityEvent.objects.create(
            user=user,
            event_type="logout",
            device_info=device_info
        )

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    login = credentials.get('username') or credentials.get('email')
    if login:
        try:
            user = User.objects.get(email=login)
            ua_string = request.META.get('HTTP_USER_AGENT', '') if request else ''
            user_agent = parse(ua_string)
            device_info = f"{user_agent.browser.family} on {user_agent.os.family}"
            SecurityEvent.objects.create(
                user=user,
                event_type="failed login attempt",
                device_info=device_info
            )
        except User.DoesNotExist:
            pass
