"""
Django settings for MDRegistry project.

This file controls:
- project configuration
- installed apps
- database connection (SQL Server 2022 via Windows Auth)
- templates, static files, media files
"""

from pathlib import Path
import os

# =========================
# BASE DIRECTORY
# =========================

# BASE_DIR points to the MDRegistry folder (where manage.py lives)
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# SECURITY SETTINGS
# =========================

# Secret key (keep this secret in production!)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-later")

X_FRAME_OPTIONS = "SAMEORIGIN"

# DEBUG=True for development only
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# Allowed hosts during development
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]


# =========================
# INSTALLED APPLICATIONS
# =========================

INSTALLED_APPS = [
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Your project apps
    "apps.organization",
    "apps.records",
    "apps.workflow",
    "apps.accounts.apps.AccountsConfig",

]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================
# SECURITY HARDENING (PRODUCTION)
# =========================
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False  # Django reads CSRF cookie in JS sometimes; keep default
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "same-origin"
    # If you deploy behind HTTPS, consider setting:
    # SECURE_SSL_REDIRECT = True
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

# =========================
# UPLOAD LIMITS
# =========================
# Attachments (.pdf/.docx/.xlsx/.png/.jpg etc.)
MAX_ATTACHMENT_SIZE_BYTES = int(os.getenv("MAX_ATTACHMENT_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10MB
# Excel import file size
MAX_IMPORT_SIZE_BYTES = int(os.getenv("MAX_IMPORT_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5MB
# Allowed attachment extensions (lowercase, include dot)
ALLOWED_ATTACHMENT_EXTS = set(
    e.strip().lower()
    for e in os.getenv("ALLOWED_ATTACHMENT_EXTS", ".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg").split(",")
    if e.strip()
)


# =========================
# URL & APPLICATION ENTRY POINTS
# =========================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# =========================
# TEMPLATES (MVT - Templates)
# =========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # Global templates directory
        "DIRS": [BASE_DIR / "templates"],

        # Also look for templates inside each app
        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.accounts.context_processors.role_flags",
                "apps.workflow.context_processors.workflow_pending_counts",
            ],
        },
    },
]


# =========================
# DATABASE CONFIGURATION (FIXED)
# =========================
"""
You are using:
- SQL Server 2022
- Windows Authentication
- Database name: MDRegistryDB
- ODBC Driver 18 for SQL Server

IMPORTANT:
- Do NOT set USER or PASSWORD
- Use Trusted_Connection=yes
"""

DATABASES = {
    "default": {
        "ENGINE": "mssql",

        # ✅ Correct database name
        "NAME": "MDRegistryDB",

        # ⚠️ MUST match the Server name you use in SSMS
        # Examples:
        # "DESKTOP-A8L26RI"
        # "DESKTOP-A8L26RI\\SQLEXPRESS"
        "HOST": r"DESKTOP-A8L26RI\SQLEXPRESS",

        "PORT": "",

        # Windows Authentication → leave empty
        "USER": "",
        "PASSWORD": "",

        "OPTIONS": {
            "driver": "ODBC Driver 18 for SQL Server",
            "Trusted_Connection": "yes",
            "extra_params":"TrustServerCertificate=yes;",
        },
    }
}


# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================
# LANGUAGE & TIME ZONE
# =========================

LANGUAGE_CODE = "en-us"

# Change if needed
TIME_ZONE = "Africa/Lagos"

USE_I18N = True
USE_TZ = True


# =========================
# STATIC FILES (CSS, JS)
# =========================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# =========================
# MEDIA FILES (Uploads / Attachments)
# =========================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# DEFAULT PRIMARY KEY FIELD TYPE
# =========================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
