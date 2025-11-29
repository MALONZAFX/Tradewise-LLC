# dict/settings.py
from pathlib import Path
import os

# ==============================
# BASE DIRECTORY
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# ENVIRONMENT VARIABLES - FIXED SYNTAX
# ==============================

# SECURITY & CORE - Use get() with defaults for local development
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-local-only")
DEBUG = os.environ.get("DEBUG", "True") == "True"

# SITE URLs
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000")
PRODUCTION_SITE_URL = os.environ.get("PRODUCTION_SITE_URL", SITE_URL)

# PAYMENTS
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "dev-paystack-secret")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "dev-paystack-public")

# ==============================
# ALLOWED HOSTS
# ==============================
ALLOWED_HOSTS = [
    "tradewise.up.railway.app",
    "127.0.0.1", 
    "localhost",
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    ".railway.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise.up.railway.app",
    "https://*.railway.app",
    "https://tradewise-hub.com",
    "https://www.tradewise-hub.com",
]

CORS_ORIGIN_ALLOW_ALL = True

# ==============================
# INSTALLED APPS
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

# ==============================
# MIDDLEWARE
# ==============================
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

# ==============================
# URLS & WSGI
# ==============================
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
# DATABASE - SQLITE ONLY (FIXED)
# ==============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ==============================
# PASSWORD VALIDATION
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================
# INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ==============================
# STATIC & MEDIA FILES
# ==============================
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ==============================
# EMAIL SETTINGS - SENDGRID WITH FALLBACK
# ==============================
# Check if SendGrid API key is available
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

if DEBUG:
    # Local development - use console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("🔧 EMAIL: Using console backend (development)")
elif SENDGRID_API_KEY:
    # Production - use SendGrid if API key exists
    try:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = "smtp.sendgrid.net"
        EMAIL_PORT = 587
        EMAIL_USE_TLS = True
        EMAIL_HOST_USER = "apikey"
        EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
        
        # Test connection (non-blocking quick test)
        from django.core import mail
        connection = mail.get_connection()
        connection.open()
        connection.close()
        print("✅ EMAIL: SendGrid SMTP configured successfully")
        
    except Exception as e:
        print(f"❌ EMAIL: SendGrid failed - {e}")
        print("🔄 EMAIL: Falling back to console backend")
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # No SendGrid API key - use console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("⚠️ EMAIL: No SENDGRID_API_KEY found, using console backend")

# Sender information
DEFAULT_FROM_EMAIL = "TradeWise <noreply@tradewise-hub.com>"
SERVER_EMAIL = "noreply@tradewise-hub.com"
ADMIN_EMAIL = "theofficialtradewise@gmail.com"

# Better timeout for production
EMAIL_TIMEOUT = 10
EMAIL_USE_SSL = False

# ==============================
# AUTH REDIRECTS
# ==============================
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ==============================
# SECURITY SETTINGS - FIXED REDIRECTS
# ==============================
# TEMPORARILY DISABLE SSL REDIRECTS TO FIX THE LOOP
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Railway proxy settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# ==============================
# SESSION SETTINGS
# ==============================
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# ==============================
# SECURITY HEADERS
# ==============================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ==============================
# DEFAULT AUTO FIELD
# ==============================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# LOGGING
# ==============================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ==============================
# DEVELOPMENT SETTINGS
# ==============================
if DEBUG:
    SILENCED_SYSTEM_CHECKS = [
        "security.W001",
        "security.W002", 
        "security.W003",
        "security.W004",
        "security.W008",
        "security.W009",
        "security.W012",
        "security.W016",
    ]

# ==============================
# VERIFICATION PRINT
# ==============================
print("=" * 50)
print("🚀 SETTINGS LOADED SUCCESSFULLY")
print(f"🔑 SECRET_KEY: {'Loaded' if os.environ.get('SECRET_KEY') else 'Using default (local)'}")
print(f"📧 EMAIL_BACKEND: {'SendGrid SMTP' if not DEBUG and SENDGRID_API_KEY else 'Console (fallback)'}")
print(f"🗄️ DATABASE: SQLite (Production & Local)")
print(f"💰 PAYSTACK: {'Loaded' if os.environ.get('PAYSTACK_SECRET_KEY') else 'Using defaults (local)'}")
print(f"🌐 SITE_URL: {SITE_URL}")
print(f"🌐 PRODUCTION_URL: {PRODUCTION_SITE_URL}")
print(f"🐛 DEBUG: {DEBUG}")
print("=" * 50)