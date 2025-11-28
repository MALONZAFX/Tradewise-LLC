# dict/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# ==============================
# Load .env
# ==============================
load_dotenv()

# ==============================
# BASE DIRECTORY
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# SECRET KEY & DEBUG
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-key-for-dev")
DEBUG = os.getenv("DEBUG", "True") == "True"

# ==============================
# ALLOWED HOSTS
# ==============================
ALLOWED_HOSTS = [
    "tradewise.up.railway.app",
    "127.0.0.1", 
    "localhost",
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    "*",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise.up.railway.app",
    "http://127.0.0.1:8000",
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
# DATABASE - FORCE SQLITE
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
# EMAIL SETTINGS - FROM ENV
# ==============================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"TradeWise <{EMAIL_HOST_USER}>"
SERVER_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 30
EMAIL_USE_SSL = False

# ==============================
# AUTH REDIRECTS
# ==============================
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ==============================
# SECURITY SETTINGS - DISABLED FOR DEVELOPMENT
# ==============================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==============================
# PAYMENT SETTINGS - FROM ENV
# ==============================
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")

# ==============================
# SESSION SETTINGS
# ==============================
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# ==============================
# SECURITY HEADERS
# ==============================
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# ==============================
# DEFAULT AUTO FIELD
# ==============================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# LOGGING - VERBOSE FOR DEBUGGING
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
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# ==============================
# DEVELOPMENT SETTINGS
# ==============================
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
# SITE URL FROM ENV
# ==============================
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000,https://www.tradewise-hub.com")

print("=" * 50)
print("🚀 TRADEWISE SETTINGS LOADED")
print(f"📁 Database: SQLite at {DATABASES['default']['NAME']}")
print(f"🐛 Debug: {DEBUG}")
print(f"📧 Email Backend: {EMAIL_BACKEND}")
print(f"📧 Email Host: {EMAIL_HOST}:{EMAIL_PORT}")
print(f"🔑 Email User: {EMAIL_HOST_USER}")
print(f"💰 Paystack Public Key Loaded: {'Yes' if PAYSTACK_PUBLIC_KEY else 'No'}")
print(f"💰 Paystack Secret Key Loaded: {'Yes' if PAYSTACK_SECRET_KEY else 'No'}")
print("=" * 50)