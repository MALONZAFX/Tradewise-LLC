import os
import django
from django.conf import settings

# ===========================
# LIVE OLD DATABASE CONFIG
# ===========================
settings.configure(
    DEBUG=False,
    TIME_ZONE="Africa/Nairobi",
    USE_TZ=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'railway',  # From your old DB
            'USER': 'postgres',
            'PASSWORD': 'qpLTmpXZehATbQoWQdIkfiuiZQZEztyP',
            'HOST': 'shinkansen.proxy.rlwy.net',
            'PORT': '56563',
        }
    },
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.admin",
        "myapp",  # Replace with your actual app(s)
        # Add any other apps that contain data you want exported
    ],
)

# ===========================
# SETUP DJANGO
# ===========================
django.setup()

from django.core.management import call_command

# ===========================
# EXPORT DATA
# ===========================
EXPORT_FILE = "backup.json"

with open(EXPORT_FILE, "w", encoding="utf-8") as f:
    call_command(
        "dumpdata",
        "--natural-primary",
        "--natural-foreign",
        exclude=["contenttypes", "sessions"],
        stdout=f
    )

print(f"✅ Backup completed successfully! File saved as: {EXPORT_FILE}")
