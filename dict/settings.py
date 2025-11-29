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
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "tradewise.up.railway.app",
    "127.0.0.1", 
    "localhost",
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    ".railway.app",
    ".onrender.com",  # Add this for Render
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise.up.railway.app",
    "https://*.railway.app",
    "https://tradewise-hub.com",
    "https://www.tradewise-hub.com",
    "https://*.onrender.com",  # Add this for Render
]

# ==============================
# DATABASE
# ==============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
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
# EMAIL CONFIGURATION - FIXED & USING .ENV
# ==============================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # Using Gmail SMTP as per your .env
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "theofficialtradewise@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = "TradeWise <noreply@tradewise-hub.com>"
SERVER_EMAIL = "TradeWise <noreply@tradewise-hub.com>"

# Optional: Fallback to console email in development if no password is set
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("🔧 DEVELOPMENT: Console email backend (no email password set)")
else:
    print(f"✅ SMTP configured for: {EMAIL_HOST_USER}")

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
SECURE_SSL_REDIRECT = False  # Keep disabled for now
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
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
print(f"📧 EMAIL: {'Gmail SMTP' if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' else 'Console Backend'}")
print(f"🐛 DEBUG: {DEBUG}")
print("=" * 50)