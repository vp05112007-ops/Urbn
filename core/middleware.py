from django.utils import timezone
from user_agents import parse
from .models import LoginSession, TwoFactorAuth
from django.shortcuts import redirect
from django.urls import reverse

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 1. 2FA Interception
            if request.session.get('pending_2fa'):
                allowed_paths = [reverse('verify_2fa_login'), reverse('account_logout')]
                if request.path not in allowed_paths and not request.path.startswith('/static/'):
                    return redirect('verify_2fa_login')

            # 2. Session Tracking
            if not request.session.session_key:
                request.session.create()
                
            session_key = request.session.session_key
            
            # Parse user agent
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            user_agent = parse(ua_string)
            
            device = user_agent.device.family
            browser = user_agent.browser.family
            os = user_agent.os.family
            
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            LoginSession.objects.update_or_create(
                session_key=session_key,
                defaults={
                    'user': request.user,
                    'device': device,
                    'browser': browser,
                    'os': os,
                    'ip_address': ip,
                    'last_active': timezone.now(),
                    'is_active': True
                }
            )
            
            # 3. Terminated session check
            try:
                login_session = LoginSession.objects.get(session_key=session_key)
                if not login_session.is_active:
                    from django.contrib.auth import logout
                    logout(request)
            except LoginSession.DoesNotExist:
                pass

        response = self.get_response(request)
        return response
