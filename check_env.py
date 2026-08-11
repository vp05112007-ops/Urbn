import os
from dotenv import load_dotenv
import django

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "urbn_project.settings")
django.setup()

from django.conf import settings

print("GOOGLE_CLIENT_ID loaded:", bool(os.environ.get("GOOGLE_CLIENT_ID")))
print("GOOGLE_CLIENT_SECRET loaded:", bool(os.environ.get("GOOGLE_CLIENT_SECRET")))

providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
print("Google provider config keys:", providers.get('google', {}).keys())
