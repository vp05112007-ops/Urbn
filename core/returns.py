import os
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db.models import Sum
from PIL import Image

def is_return_eligible(order, order_item):
    """
    Check if a specific order item is eligible for return/exchange/replacement.
    Returns (True, None) or (False, "Reason")
    """
    if order.payment_status != 'PAID':
        return False, "Order payment is not complete."
        
    if order.order_status != 'DELIVERED':
        return False, "Item can only be returned after delivery."
        
    # Check if within the return window
    window_days = getattr(settings, 'RETURN_WINDOW_DAYS', 7)
    
    # We ideally need a delivered_at timestamp. Since we use order_status we will
    # fetch the latest StatusHistory entry where status was set to DELIVERED.
    delivered_entry = order.status_history.filter(status='DELIVERED').order_by('-created_at').first()
    
    if not delivered_entry:
        return False, "No delivery record found."
        
    expiration_date = delivered_entry.created_at + timedelta(days=window_days)
    if timezone.now() > expiration_date:
        return False, f"Return window of {window_days} days has expired."
        
    # Check quantities already returned/exchanged
    from .models import ReturnRequest
    
    active_requests = ReturnRequest.objects.filter(
        order_item=order_item,
    ).exclude(
        status__in=['REJECTED', 'CANCELLED']
    )
    
    requested_total = active_requests.aggregate(total=Sum('requested_quantity'))['total'] or 0
    
    if requested_total >= order_item.quantity:
        return False, "Full quantity already requested for return/exchange."
        
    available_qty = order_item.quantity - requested_total
    
    return True, {"available_qty": available_qty}


def validate_return_image(file):
    """
    Validates uploaded images to prevent executing malicious files or overloading storage.
    """
    # Check size (Max 5MB)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(f"Image {file.name} is too large. Maximum size is 5MB.")
        
    # Validate it's a real image using Pillow
    try:
        img = Image.open(file)
        img.verify() # Verify that it is, in fact, an image
    except Exception:
        raise ValidationError(f"The uploaded file {file.name} is not a valid image.")
    finally:
        file.seek(0)
        
    # Ensure extension matches
    ext = os.path.splitext(file.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(f"Invalid file extension ({ext}). Please upload JPG, PNG, or WEBP images.")

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_return_status_email(return_request, request=None):
    """
    Sends an email to the customer when the return request status changes.
    """
    try:
        user = return_request.user
        domain = 'urbnclothing.com'
        if request:
            from django.contrib.sites.shortcuts import get_current_site
            domain = get_current_site(request).domain
            
        context = {
            'return_request': return_request,
            'customer_name': user.first_name or user.username,
            'domain': domain,
            'status': return_request.get_status_display()
        }
        
        html_content = render_to_string('emails/return_status_update.html', context)
        text_content = strip_tags(render_to_string('emails/return_status_update.txt', context))
        
        subject = f"URBN Return Request #{return_request.request_number} Update"
        
        send_mail(
            subject,
            text_content,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@urbnclothing.com'),
            [user.email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending return status email: {e}")
