from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.core import mail
from django.test.utils import override_settings

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LoginEmailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
            first_name='Test'
        )

    def test_login_email_sent(self):
        # Trigger the login signal manually
        user_logged_in.send(sender=User, request=None, user=self.user)
        
        # Verify that one message has been sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify the subject and recipient
        self.assertEqual(mail.outbox[0].subject, 'Welcome to URBN Clothing — Login Successful')
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Hello Test,', mail.outbox[0].body)
