import json
import random
import string
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

from .models import Address, EmailVerificationOTP, UserProfile, Product, Collection

def landing(request):
    return render(request, 'landing.html')

def clone(request):
    return render(request, 'clone.html')

def home(request):
    trending_products = Product.objects.filter(is_active=True, is_trending=True)[:4]
    collections = Collection.objects.filter(is_active=True).order_by('display_order')[:3]
    return render(request, 'home.html', {'trending_products': trending_products, 'collections': collections})

def categories(request):
    return render(request, 'categories.html')

def trending(request):
    best_sellers = Product.objects.filter(is_active=True, is_trending=True)[:4]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True)[:4]
    return render(request, 'trending.html', {'best_sellers': best_sellers, 'new_arrivals': new_arrivals})

def collections(request):
    collections = Collection.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'collections.html', {'collections': collections})

def customize(request):
    return render(request, 'customize.html')

import os

def cart(request):
    context = {
        'razorpay_key_id': os.environ.get('RAZORPAY_KEY_ID', '')
    }
    return render(request, 'cart.html', context)

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = request.user.addresses.all()
    has_password = request.user.has_usable_password()
    is_google_user = request.user.socialaccount_set.filter(provider='google').exists() if hasattr(request.user, 'socialaccount_set') else False
    
    login_sessions = request.user.login_sessions.filter(is_active=True).order_by('-last_active')
    security_events = request.user.security_events.order_by('-timestamp')[:20]
    
    context = {
        'profile': user_profile,
        'addresses': addresses,
        'has_password': has_password,
        'is_google_user': is_google_user,
        'login_sessions': login_sessions,
        'security_events': security_events,
        'current_session_key': request.session.session_key,
    }
    return render(request, 'profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # User fields
            request.user.first_name = data.get('first_name', '').strip()
            request.user.last_name = data.get('last_name', '').strip()
            request.user.save()
            
            # UserProfile fields
            user_profile.display_name = data.get('display_name', '').strip()
            user_profile.phone = data.get('phone', '').strip()
            
            dob = data.get('date_of_birth')
            if dob:
                user_profile.date_of_birth = dob
            else:
                user_profile.date_of_birth = None
            
            user_profile.country = data.get('country', '').strip()
            user_profile.preferred_language = data.get('preferred_language', 'English').strip()
            user_profile.clothing_size = data.get('clothing_size', '').strip()
            user_profile.preferred_fit = data.get('preferred_fit', '').strip()
            user_profile.preferred_categories = data.get('preferred_categories', [])
            
            user_profile.save()
            
            return JsonResponse({'success': True, 'message': 'Profile updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def change_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if request.user.has_usable_password():
                if not current_password:
                    return JsonResponse({'success': False, 'message': 'Current password is required.'}, status=400)
                if not request.user.check_password(current_password):
                    return JsonResponse({'success': False, 'message': 'Incorrect current password.'}, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match.'}, status=400)
                
            try:
                validate_password(new_password, request.user)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': ' '.join(e.messages)}, status=400)
                
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            return JsonResponse({'success': True, 'message': 'Password changed successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def add_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('is_default'):
                request.user.addresses.update(is_default=False)
            
            address = Address.objects.create(
                user=request.user,
                full_name=data.get('full_name', ''),
                phone=data.get('phone', ''),
                address_line_1=data.get('address_line_1', ''),
                address_line_2=data.get('address_line_2', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                postal_code=data.get('postal_code', ''),
                country=data.get('country', ''),
                is_default=bool(data.get('is_default', False))
            )
            return JsonResponse({'success': True, 'address_id': address.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('is_default') and not address.is_default:
                request.user.addresses.update(is_default=False)
                
            address.full_name = data.get('full_name', address.full_name)
            address.phone = data.get('phone', address.phone)
            address.address_line_1 = data.get('address_line_1', address.address_line_1)
            address.address_line_2 = data.get('address_line_2', address.address_line_2)
            address.city = data.get('city', address.city)
            address.state = data.get('state', address.state)
            address.postal_code = data.get('postal_code', address.postal_code)
            address.country = data.get('country', address.country)
            address.is_default = bool(data.get('is_default', address.is_default))
            address.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def delete_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def set_default_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        request.user.addresses.update(is_default=False)
        address.is_default = True
        address.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def request_email_change(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_email = data.get('new_email', '').strip()
            
            if not new_email:
                return JsonResponse({'success': False, 'message': 'New email is required.'}, status=400)
                
            if new_email == request.user.email:
                return JsonResponse({'success': False, 'message': 'This is already your current email.'}, status=400)
                
            if User.objects.filter(email__iexact=new_email).exists():
                return JsonResponse({'success': False, 'message': 'This email is already associated with an account.'}, status=400)
                
            recent_requests = EmailVerificationOTP.objects.filter(user=request.user, created_at__gte=timezone.now() - timedelta(minutes=5)).count()
            if recent_requests >= 3:
                return JsonResponse({'success': False, 'message': 'Too many requests. Please wait a few minutes.'}, status=429)
                
            otp_plain = ''.join(random.choices(string.digits, k=6))
            otp_hash = make_password(otp_plain)
            
            otp_obj = EmailVerificationOTP.objects.create(
                user=request.user,
                new_email=new_email,
                otp_hash=otp_hash,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            html_message = render_to_string('emails/email_verification.html', {'otp': otp_plain, 'user': request.user})
            send_mail(
                subject='Verify your new URBN Clothing email',
                message=f'Your verification code is: {otp_plain}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
                html_message=html_message
            )
            
            return JsonResponse({'success': True, 'message': 'Verification code sent.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
def verify_email_change(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_email = data.get('new_email', '').strip()
            otp_entered = data.get('otp', '').strip()
            
            if not otp_entered:
                return JsonResponse({'success': False, 'message': 'OTP is required.'}, status=400)
                
            otp_obj = EmailVerificationOTP.objects.filter(user=request.user, new_email=new_email, verified=False).order_by('-created_at').first()
            
            if not otp_obj:
                return JsonResponse({'success': False, 'message': 'No pending verification found for this email.'}, status=400)
                
            if otp_obj.expires_at < timezone.now():
                return JsonResponse({'success': False, 'message': 'Verification code has expired.'}, status=400)
                
            if otp_obj.attempts >= 5:
                return JsonResponse({'success': False, 'message': 'Too many failed attempts. Please request a new code.'}, status=400)
                
            if not check_password(otp_entered, otp_obj.otp_hash):
                otp_obj.attempts += 1
                otp_obj.save()
                return JsonResponse({'success': False, 'message': 'Invalid verification code.'}, status=400)
                
            otp_obj.verified = True
            otp_obj.save()
            
            request.user.email = new_email
            request.user.save()
            
            html_message = render_to_string('emails/email_changed.html', {'user': request.user})
            send_mail(
                subject='Your URBN Clothing email was changed',
                message='Your email address has been successfully updated.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
                html_message=html_message
            )
            
            return JsonResponse({'success': True, 'message': 'Email updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
