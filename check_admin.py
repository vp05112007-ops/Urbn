import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urbn_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.conf import settings

def promote_admin():
    admin_email = settings.ADMIN_EMAIL
    try:
        user = User.objects.get(email__iexact=admin_email)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"SUCCESS: Promoted existing user {admin_email} to admin.")
    except User.DoesNotExist:
        print(f"WARNING: The admin account for {admin_email} does not exist.")
        print(f"Please log in via Google with {admin_email} to create the account first, then run this script again.")
    except User.MultipleObjectsReturned:
        print(f"ERROR: Multiple accounts found for {admin_email}. Please resolve duplicates.")

if __name__ == '__main__':
    promote_admin()
