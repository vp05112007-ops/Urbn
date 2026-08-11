import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "urbn_project.settings")
django.setup()

from allauth.socialaccount.models import SocialApp

apps = SocialApp.objects.all()
print("SocialApp count in DB:", apps.count())
for app in apps:
    print(f"App: {app.provider}, client_id: {app.client_id}")
