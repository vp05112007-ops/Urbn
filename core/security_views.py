import json
import pyotp
import qrcode
import base64
from io import BytesIO

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import TwoFactorAuth, LoginSession, SecurityEvent, UserProfile

@login_required
def verify_2fa_login(request):
    if not request.session.get('pending_2fa'):
        return redirect('profile')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token', '').strip()
            
            two_factor = request.user.two_factor
            totp = pyotp.TOTP(two_factor.totp_secret)
            
            if totp.verify(token) or token in two_factor.recovery_codes:
                if token in two_factor.recovery_codes:
                    two_factor.recovery_codes.remove(token)
                    two_factor.save()
                    
                request.session['pending_2fa'] = False
                return JsonResponse({'success': True, 'redirect_url': '/profile/'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid code.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
            
    return render(request, 'account/verify_2fa.html')

@login_required
def enable_2fa_request(request):
    if request.method == 'POST':
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        if two_factor.is_enabled:
            return JsonResponse({'success': False, 'message': '2FA is already enabled.'}, status=400)
            
        secret = pyotp.random_base32()
        request.session['temp_2fa_secret'] = secret
        
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name="URBN Clothing")
        
        img = qrcode.make(provisioning_uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return JsonResponse({
            'success': True,
            'qr_code': f"data:image/png;base64,{img_str}",
            'secret': secret
        })
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def verify_enable_2fa(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token', '').strip()
            secret = request.session.get('temp_2fa_secret')
            
            if not secret:
                return JsonResponse({'success': False, 'message': 'No pending 2FA setup found.'}, status=400)
                
            totp = pyotp.TOTP(secret)
            if totp.verify(token):
                two_factor, _ = TwoFactorAuth.objects.get_or_create(user=request.user)
                two_factor.totp_secret = secret
                two_factor.is_enabled = True
                
                import uuid
                recovery_codes = [str(uuid.uuid4()).replace('-', '')[:10] for _ in range(8)]
                two_factor.recovery_codes = recovery_codes
                two_factor.save()
                
                del request.session['temp_2fa_secret']
                
                SecurityEvent.objects.create(
                    user=request.user,
                    event_type="2FA enabled",
                    device_info=request.META.get('HTTP_USER_AGENT', 'Unknown')
                )
                
                return JsonResponse({'success': True, 'recovery_codes': recovery_codes})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid code.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def disable_2fa(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            password = data.get('password')
            
            if not request.user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Incorrect password.'}, status=400)
                
            if hasattr(request.user, 'two_factor'):
                request.user.two_factor.is_enabled = False
                request.user.two_factor.totp_secret = None
                request.user.two_factor.recovery_codes = []
                request.user.two_factor.save()
                
                SecurityEvent.objects.create(
                    user=request.user,
                    event_type="2FA disabled",
                    device_info=request.META.get('HTTP_USER_AGENT', 'Unknown')
                )
                return JsonResponse({'success': True, 'message': '2FA has been disabled.'})
            return JsonResponse({'success': False, 'message': '2FA is not enabled.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def logout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_key = data.get('session_key')
            if session_key == request.session.session_key:
                logout(request)
                return JsonResponse({'success': True, 'redirect_url': '/profile/'})
                
            session = LoginSession.objects.get(session_key=session_key, user=request.user)
            session.is_active = False
            session.save()
            return JsonResponse({'success': True})
        except LoginSession.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Session not found.'}, status=404)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def logout_all_other_sessions(request):
    if request.method == 'POST':
        LoginSession.objects.filter(user=request.user).exclude(session_key=request.session.session_key).update(is_active=False)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def update_security_notifications(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            notifications = user_profile.security_notifications
            
            for key in ['new_login', 'password_changed', 'email_changed', '2fa_changes', 'suspicious_login']:
                if key in data:
                    notifications[key] = bool(data[key])
                    
            user_profile.security_notifications = notifications
            user_profile.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def upload_profile_photo(request):
    if request.method == 'POST':
        try:
            photo = request.FILES.get('profile_photo')
            if not photo:
                return JsonResponse({'success': False, 'message': 'No photo uploaded.'}, status=400)
                
            if photo.size > 5 * 1024 * 1024:  # 5MB
                return JsonResponse({'success': False, 'message': 'File too large. Maximum size is 5MB.'}, status=400)
                
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            
            # Delete old photo if exists
            if user_profile.profile_photo:
                user_profile.profile_photo.delete(save=False)
                
            user_profile.profile_photo = photo
            user_profile.save()
            
            return JsonResponse({'success': True, 'photo_url': user_profile.profile_photo.url})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)

@login_required
def remove_profile_photo(request):
    if request.method == 'POST':
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if user_profile.profile_photo:
            user_profile.profile_photo.delete()
            user_profile.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)
