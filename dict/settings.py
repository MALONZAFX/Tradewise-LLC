# dict/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
load_dotenv()

# ==============================
# BASE DIRECTORY
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# ENVIRONMENT DETECTION - FIXED!
# ==============================
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or \
                os.environ.get('ON_RENDER') == 'true' or \
                'railway.app' in os.environ.get('ALLOWED_HOSTS', '') or \
                'tradewise-hub.com' in os.environ.get('ALLOWED_HOSTS', '')

IS_LOCAL = not IS_PRODUCTION

# ==============================
# CORE SETTINGS
# ==============================
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-local-only")

if IS_LOCAL:
    DEBUG = True
    print("🔧 LOCAL DEVELOPMENT: Debug mode enabled")
else:
    DEBUG = os.environ.get("DEBUG", "False") == "True"
    if DEBUG:
        print("⚠️  PRODUCTION WARNING: Debug mode is enabled in production!")

ALLOWED_HOSTS = [
    "tradewise.up.railway.app",
    "127.0.0.1",
    "localhost",
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    ".railway.app",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise.up.railway.app",
    "https://*.railway.app",
    "https://tradewise-hub.com",
    "https://www.tradewise-hub.com",
    "https://*.onrender.com",
]

# ==============================
# DATABASE
# ==============================
DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_PRODUCTION and DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    print("✅ PRODUCTION: Using PostgreSQL Database")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    if IS_PRODUCTION:
        print("⚠️  PRODUCTION: No DATABASE_URL found, using SQLite")
    else:
        print("✅ LOCAL: Using SQLite Database")

# ==============================
# PAYSTACK CONFIGURATION
# ==============================
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")

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

    # ✅ ADDED: Cloudinary
    "cloudinary",
    "cloudinary_storage",

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
# ERROR HANDLERS
# ==============================
handler404 = 'myapp.views.handler404'
handler500 = 'myapp.views.handler500'
handler403 = 'myapp.views.handler403'
handler400 = 'myapp.views.handler400'

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
                "myapp.context_processors.paystack_keys",
            ],
        },
    },
]

# ==============================
# EMAIL CONFIGURATION
# ==============================
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "theofficialtradewise@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = "TradeWise <theofficialtradewise@gmail.com>"
    SERVER_EMAIL = "TradeWise <theofficialtradewise@gmail.com>"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================
# STATIC FILES
# ==============================
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

if IS_PRODUCTION:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

WHITENOISE_ROOT = os.path.join(BASE_DIR, 'staticfiles')
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ==============================
# MEDIA FILES (LOCAL VS CLOUDINARY)
# ==============================
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

if IS_PRODUCTION:
    # ✅ ADDED: Cloudinary config (PRODUCTION ONLY)
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
        "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
    }

    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    print("☁️  PRODUCTION: Cloudinary media storage enabled")
else:
    print("📁 LOCAL: Using filesystem media storage")

# ==============================
# SECURITY
# ==============================
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
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
print(f"🌍 ENVIRONMENT: {'PRODUCTION' if IS_PRODUCTION else 'LOCAL DEVELOPMENT'}")
print(f"🐛 DEBUG: {DEBUG}")
print(f"🗄️ DATABASE: {'PostgreSQL' if IS_PRODUCTION and DATABASE_URL else 'SQLite'}")
print(f"📦 STATIC FILES: {STATICFILES_STORAGE}")
print("=" * 50)
# dict/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
load_dotenv()

# ==============================
# BASE DIRECTORY
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# ENVIRONMENT DETECTION - FIXED!
# ==============================
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or \
                os.environ.get('ON_RENDER') == 'true' or \
                'railway.app' in os.environ.get('ALLOWED_HOSTS', '') or \
                'tradewise-hub.com' in os.environ.get('ALLOWED_HOSTS', '')

IS_LOCAL = not IS_PRODUCTION

# ==============================
# CORE SETTINGS
# ==============================
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-local-only")

if IS_LOCAL:
    DEBUG = True
    print("🔧 LOCAL DEVELOPMENT: Debug mode enabled")
else:
    DEBUG = os.environ.get("DEBUG", "False") == "True"
    if DEBUG:
        print("⚠️  PRODUCTION WARNING: Debug mode is enabled in production!")

ALLOWED_HOSTS = [
    "tradewise.up.railway.app",
    "127.0.0.1",
    "localhost",
    "tradewise-hub.com",
    "www.tradewise-hub.com",
    ".railway.app",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tradewise.up.railway.app",
    "https://*.railway.app",
    "https://tradewise-hub.com",
    "https://www.tradewise-hub.com",
    "https://*.onrender.com",
]

# ==============================
# DATABASE
# ==============================
DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_PRODUCTION and DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    print("✅ PRODUCTION: Using PostgreSQL Database")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    if IS_PRODUCTION:
        print("⚠️  PRODUCTION: No DATABASE_URL found, using SQLite")
    else:
        print("✅ LOCAL: Using SQLite Database")

# ==============================
# PAYSTACK CONFIGURATION
# ==============================
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")

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

    # ✅ ADDED: Cloudinary
    "cloudinary",
    "cloudinary_storage",

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
# ERROR HANDLERS
# ==============================
handler404 = 'myapp.views.handler404'
handler500 = 'myapp.views.handler500'
handler403 = 'myapp.views.handler403'
handler400 = 'myapp.views.handler400'

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
                "myapp.context_processors.paystack_keys",
            ],
        },
    },
]

# ==============================
# EMAIL CONFIGURATION
# ==============================
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "theofficialtradewise@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = "TradeWise <theofficialtradewise@gmail.com>"
    SERVER_EMAIL = "TradeWise <theofficialtradewise@gmail.com>"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================
# STATIC FILES
# ==============================
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

if IS_PRODUCTION:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

WHITENOISE_ROOT = os.path.join(BASE_DIR, 'staticfiles')
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ==============================
# MEDIA FILES (LOCAL VS CLOUDINARY)
# ==============================
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

if IS_PRODUCTION:
    # ✅ ADDED: Cloudinary config (PRODUCTION ONLY)
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
        "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
    }

    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    print("☁️  PRODUCTION: Cloudinary media storage enabled")
else:
    print("📁 LOCAL: Using filesystem media storage")

# ==============================
# SECURITY
# ==============================
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
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
print(f"🌍 ENVIRONMENT: {'PRODUCTION' if IS_PRODUCTION else 'LOCAL DEVELOPMENT'}")
print(f"🐛 DEBUG: {DEBUG}")
print(f"🗄️ DATABASE: {'PostgreSQL' if IS_PRODUCTION and DATABASE_URL else 'SQLite'}")
print(f"📦 STATIC FILES: {STATICFILES_STORAGE}")
print("=" * 50)
