# dict/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==============================
# BASE DIRECTORY
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# CORE SETTINGS
# ==============================
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-local-only")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    ".onrender.com",
    "127.0.0.1", 
    "localhost",
    ".railway.app",
    ".up.railway.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise-hub.com",
    "https://www.tradewise-hub.com",
    "https://*.onrender.com",
    "https://*.railway.app",
    "https://*.up.railway.app",
]

# ==============================
# DATABASE - USING POSTGRES FROM ENV
# ==============================
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ==============================
# APPLICATION DEFINITION
# ==============================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dict.urls"
WSGI_APPLICATION = "dict.wsgi.application"

# ==============================
# TEMPLATES
# ==============================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

# ==============================
# EMAIL CONFIGURATION - GMAIL SMTP FROM ENV
# ==============================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"TradeWise <{EMAIL_HOST_USER}>"
SERVER_EMAIL = f"TradeWise <{EMAIL_HOST_USER}>"

# Fallback to console email in development if no password is set
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("🔧 DEVELOPMENT: Console email backend (no email password set)")
else:
    print(f"✅ SMTP configured for: {EMAIL_HOST_USER}")

# ==============================
# PAYMENT CONFIGURATION - FROM ENV
# ==============================
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")

# ==============================
# SITE URL CONFIGURATION - FROM ENV
# ==============================
SITE_URL = os.environ.get("SITE_URL", "https://www.tradewise-hub.com")

# ==============================
# STATIC FILES
# ==============================
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ==============================
# SECURITY
# ==============================
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================
# AUTH
# ==============================
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ==============================
# INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ==============================
# DEFAULT AUTO FIELD
# ==============================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

print("=" * 50)
print("🚀 SETTINGS LOADED SUCCESSFULLY")
print(f"📧 EMAIL: Gmail SMTP - {EMAIL_HOST_USER}")
print(f"💰 PAYMENTS: {'Configured' if PAYSTACK_SECRET_KEY else 'Not Configured'}")
print(f"🐛 DEBUG: {DEBUG}")
print(f"🌐 SITE URL: {SITE_URL}")
print("=" * 50)