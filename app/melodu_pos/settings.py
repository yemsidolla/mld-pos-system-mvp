"""Django settings for Melodu POS & Inventory Control System."""
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=None):
    value = os.environ.get(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def env_int(name, default=0):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return int(value)


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "phase-0-dev-secret-key-change-me")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0-mvp")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["localhost", "127.0.0.1", "0.0.0.0", "web"],
)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "batch_upload.apps.BatchUploadConfig",
    "catalog.apps.CatalogConfig",
    "inventory.apps.InventoryConfig",
    "labels.apps.LabelsConfig",
    "pos.apps.PosConfig",
    "reports.apps.ReportsConfig",
    "audit.apps.AuditConfig",
    "system_logs.apps.SystemLogsConfig",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.CashierAdminBlockMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- Development-only auth bypass (see core/dev_auth.py) ---
# A deliberate auth backdoor for browsing a LOCAL instance without logging in.
# The gate is an allowlist: it activates only when DEBUG is true AND every
# ALLOWED_HOSTS entry is a loopback host. Any real domain, public IP, or "*"
# makes dev_auth_bypass_active REFUSE TO START. Production and SIT have public
# hosts, so a misconfiguration there crashes the boot instead of opening the
# door. The guard lives in core.dev_auth so settings and tests share one
# definition — it cannot be weakened without failing a test.
DEV_AUTH_BYPASS = env_bool("DEV_AUTH_BYPASS", False)
DEV_AUTH_BYPASS_USER = os.environ.get("DEV_AUTH_BYPASS_USER", "")
if DEV_AUTH_BYPASS:
    from core.dev_auth import dev_auth_bypass_active

    if dev_auth_bypass_active(DEBUG, DEV_AUTH_BYPASS, ALLOWED_HOSTS):
        # Insert immediately after AuthenticationMiddleware, which populates
        # request.user; the bypass then overrides it to a dev user.
        _auth_i = MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        MIDDLEWARE.insert(_auth_i + 1, "core.dev_auth.DevAuthBypassMiddleware")

ROOT_URLCONF = "melodu_pos.urls"
LOGIN_URL = "/dashboard/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/dashboard/login/"


# --- Authentication mode (V6) ------------------------------------------------
# AUTH_MODE=local  → username/password against the local Django user table.
# AUTH_MODE=oidc   → staff log in through Authentik (OIDC); the local form stays
#                    reachable as an emergency path while LOCAL_LOGIN_ENABLED.
AUTH_MODE = os.environ.get("AUTH_MODE", "local").strip().lower()
OIDC_ENABLED = AUTH_MODE == "oidc"
LOCAL_LOGIN_ENABLED = env_bool("LOCAL_LOGIN_ENABLED", True)

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
if OIDC_ENABLED:
    INSTALLED_APPS.append("mozilla_django_oidc")
    AUTHENTICATION_BACKENDS.insert(0, "accounts.oidc.MeloduOIDCBackend")

OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")
OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO", "RS256")
OIDC_RP_SCOPES = os.environ.get("OIDC_SCOPES", "openid email profile")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT", "")
OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT", "")
OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT", "")
OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_ENDPOINT", "")
# Authentik "end session" URL. Optional: when set, dashboard logout also ends
# the Authentik SSO session so the next visit asks for credentials again.
OIDC_OP_LOGOUT_ENDPOINT = os.environ.get("OIDC_OP_LOGOUT_ENDPOINT", "")
OIDC_GROUPS_CLAIM = os.environ.get("OIDC_GROUPS_CLAIM", "groups")
OIDC_CREATE_USER = env_bool("OIDC_AUTO_CREATE_USER", True)
OIDC_SYNC_GROUPS = env_bool("OIDC_SYNC_GROUPS", True)
LOGIN_REDIRECT_URL_FAILURE = "/dashboard/login/?oidc_error=1"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.dashboard_context",
            ],
        },
    },
]

WSGI_APPLICATION = "melodu_pos.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "melodu_pos"),
        "USER": os.environ.get("POSTGRES_USER", "melodu"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "melodu_dev_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("km", "ភាសាខ្មែរ"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Phnom_Penh")
USE_I18N = True
USE_TZ = True


DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT / "data"))
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", DATA_ROOT / "static"))
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", DATA_ROOT / "media"))
USE_S3_MEDIA = env_bool("USE_S3_MEDIA", False)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
if USE_S3_MEDIA:
    INSTALLED_APPS.append("storages")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("S3_STORAGE_BUCKET_NAME", "melodu-media")
    AWS_S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", "")
    AWS_S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY", "")
    AWS_S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://garage:3900")
    AWS_S3_REGION_NAME = os.environ.get("S3_REGION_NAME", "us-east-1")
    AWS_S3_SIGNATURE_VERSION = os.environ.get("S3_SIGNATURE_VERSION", "s3v4")
    AWS_S3_ADDRESSING_STYLE = os.environ.get("S3_ADDRESSING_STYLE", "path")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = env_bool("S3_QUERYSTRING_AUTH", True)
    AWS_QUERYSTRING_EXPIRE = env_int("S3_QUERYSTRING_EXPIRE", 3600)
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": os.environ.get("S3_MEDIA_CACHE_CONTROL", "max-age=86400"),
    }

    s3_storage_options = {
        "bucket_name": AWS_STORAGE_BUCKET_NAME,
        "access_key": AWS_S3_ACCESS_KEY_ID,
        "secret_key": AWS_S3_SECRET_ACCESS_KEY,
        "endpoint_url": AWS_S3_ENDPOINT_URL,
        "region_name": AWS_S3_REGION_NAME,
        "signature_version": AWS_S3_SIGNATURE_VERSION,
        "addressing_style": AWS_S3_ADDRESSING_STYLE,
        "file_overwrite": AWS_S3_FILE_OVERWRITE,
        "default_acl": AWS_DEFAULT_ACL,
        "querystring_auth": AWS_QUERYSTRING_AUTH,
        "querystring_expire": AWS_QUERYSTRING_EXPIRE,
        "object_parameters": AWS_S3_OBJECT_PARAMETERS,
    }
    custom_domain = os.environ.get("S3_CUSTOM_DOMAIN", "").strip()
    if custom_domain:
        s3_storage_options["custom_domain"] = custom_domain
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": s3_storage_options,
    }
LOG_DIR = Path(os.environ.get("DJANGO_LOG_DIR", DATA_ROOT / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", False)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamped",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "timestamped",
            "level": "INFO",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "timestamped",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "melodu_pos": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "core": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
