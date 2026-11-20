"""Django settings for the Pharmacy Student Dashboard.

DATABASES
---------
  * USERS_DATABASE_URL  -> logins / accounts   (Django "default" database)
  * DATABASE_URL        -> student marks + events ("student_data" database)

  - Neither set        : two local SQLite files (db_users.sqlite3, db_students.sqlite3)
  - Only DATABASE_URL  : ONE hosted PostgreSQL holds everything
  - Both set           : two separate hosted databases
"""
import hashlib
import os
import secrets
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

ON_RENDER = bool(os.environ.get("RENDER"))
DEBUG = os.environ.get("DJANGO_DEBUG", "0" if ON_RENDER else "1") == "1"


def _secret_key():
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    seed = os.environ.get("DATABASE_URL", "") + os.environ.get("ADMIN_PASSWORD", "")
    if seed:
        return hashlib.sha256(("pharmacy-django-" + seed).encode()).hexdigest()
    return secrets.token_hex(32) if ON_RENDER else "local-development-secret-key"


SECRET_KEY = _secret_key()

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver", ".onrender.com"]
_extra = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS += [h.strip() for h in _extra.split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "portal",
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
    "config.middleware.RoleAccessMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# The old Flask templates (Jinja2) are reused as they are.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "environment": "config.jinja.environment",
            "context_processors": ["portal.context.globals"],
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,  # needed by the /django-admin/ site
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]


# ---------------------------- databases ----------------------------
def _db(url, sqlite_name):
    if url:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return dj_database_url.parse(url, conn_max_age=60, conn_health_checks=True)
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / sqlite_name}


_students_url = os.environ.get("DATABASE_URL", "").strip()
_users_url = os.environ.get("USERS_DATABASE_URL", "").strip()

if _users_url:
    DATABASES = {"default": _db(_users_url, ""), "student_data": _db(_students_url, "db_students.sqlite3")}
elif _students_url:
    DATABASES = {"default": _db(_students_url, "")}
else:
    DATABASES = {
        "default": _db("", "db_users.sqlite3"),
        "student_data": _db("", "db_students.sqlite3"),
    }

DATABASE_ROUTERS = ["config.routers.PortalRouter"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = []  # our own rule: minimum 8 characters
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]

LOGIN_URL = "/login"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
DISPLAY_TZ_OFFSET_MINUTES = int(os.environ.get("DISPLAY_TZ_OFFSET_MINUTES", "330"))

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

SESSION_COOKIE_AGE = 60 * 60 * 12
SESSION_COOKIE_SECURE = ON_RENDER
CSRF_COOKIE_SECURE = ON_RENDER
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
if ON_RENDER:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024

# Portal options
STUDENT_SIGNUP_CODE = os.environ.get("STUDENT_SIGNUP_CODE", "").strip()
MIN_CLASS_FOR_COMPARISON = 5
DEV_ADMIN_EMAIL = "admin@pharmacy.local"
DEV_ADMIN_PASSWORD = "Admin@12345"
# True only on your own laptop with no ADMIN_* variables (set by setup_portal)
DEV_ADMIN = False

CSRF_FAILURE_VIEW = "portal.views.csrf_failed"
