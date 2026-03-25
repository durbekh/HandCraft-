"""
Production settings for HandCraft.

Extends base settings with production-hardened configurations.
"""

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403

# ─── Debug Mode ──────────────────────────────────────────────────
DEBUG = False

# ─── Security ────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ─── Allowed Hosts ───────────────────────────────────────────────
ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="handcraft.com,www.handcraft.com",
    cast=Csv(),  # noqa: F405
)

# ─── Database Connection Pooling ─────────────────────────────────
DATABASES["default"]["CONN_MAX_AGE"] = 600  # noqa: F405
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"  # noqa: F405

# ─── AWS S3 Storage (Production) ────────────────────────────────
DEFAULT_FILE_STORAGE = "utils.storage.MediaS3Storage"
STATICFILES_STORAGE = "utils.storage.StaticS3Storage"

# ─── Email Backend ───────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# ─── Cache TTL ───────────────────────────────────────────────────
CACHES["default"]["TIMEOUT"] = 60 * 60  # 1 hour in production  # noqa: F405

# ─── Sentry ──────────────────────────────────────────────────────
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
    )

# ─── Logging ─────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": "django.utils.log.ServerFormatter",
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ─── Throttling (strict in production) ──────────────────────────
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "50/hour",
    "user": "500/hour",
}
