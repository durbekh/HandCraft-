"""
Development settings for HandCraft.

Extends base settings with development-specific configurations.
"""

from .base import *  # noqa: F401, F403

# ─── Debug Mode ──────────────────────────────────────────────────
DEBUG = True

# ─── Allowed Hosts ───────────────────────────────────────────────
ALLOWED_HOSTS = ["*"]

# ─── Installed Apps ──────────────────────────────────────────────
INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

# ─── Middleware ──────────────────────────────────────────────────
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

# ─── Debug Toolbar ───────────────────────────────────────────────
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
]

# Allow debug toolbar to work inside Docker
import socket

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# ─── Email Backend ───────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── CORS ────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ─── Renderers ───────────────────────────────────────────────────
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# ─── Throttling (relaxed for dev) ────────────────────────────────
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "10000/hour",
}

# ─── File Storage (Local in development) ────────────────────────
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ─── Logging ─────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
