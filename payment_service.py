"""
Celery configuration for HandCraft project.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("handcraft")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# ─── Periodic Tasks ─────────────────────────────────────────────
app.conf.beat_schedule = {
    "auto-complete-delivered-orders": {
        "task": "apps.orders.tasks.auto_complete_delivered_orders",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    "send-order-reminder-emails": {
        "task": "apps.orders.tasks.send_order_reminder_emails",
        "schedule": crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    "cleanup-expired-custom-requests": {
        "task": "apps.orders.tasks.cleanup_expired_custom_requests",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
}

# ─── Task Routing ───────────────────────────────────────────────
app.conf.task_routes = {
    "apps.orders.tasks.*": {"queue": "orders"},
    "apps.accounts.tasks.*": {"queue": "accounts"},
    "apps.products.tasks.*": {"queue": "products"},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for verifying Celery is working."""
    print(f"Request: {self.request!r}")
