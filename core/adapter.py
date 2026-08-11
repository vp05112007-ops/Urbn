from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.conf import settings

class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_authenticated:
            admin_email = getattr(settings, 'ADMIN_EMAIL', '').strip().lower()
            if request.user.email.strip().lower() == admin_email and request.user.is_staff and request.user.is_active:
                return reverse('admin_dashboard')
        return reverse('home')
        
    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        # Do NOT show "Successfully signed in as..." or other allauth messages
        pass
