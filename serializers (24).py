"""
Celery tasks for the orders app.

Handles asynchronous order processing, email notifications,
and scheduled maintenance tasks.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email to the customer."""
    try:
        from .models import Order

        order = Order.objects.select_related("customer").prefetch_related(
            "items"
        ).get(id=order_id)

        subject = f"Order Confirmation - {order.order_number}"
        message = (
            f"Dear {order.customer.get_full_name()},\n\n"
            f"Thank you for your order!\n\n"
            f"Order Number: {order.order_number}\n"
            f"Total: ${order.total}\n"
            f"Items: {order.items.count()}\n\n"
            f"We'll notify you when your order ships.\n\n"
            f"Best regards,\nThe HandCraft Team"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            fail_silently=False,
        )

        logger.info(
            "Order confirmation email sent for order %s to %s",
            order.order_number,
            order.customer.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to send order confirmation email for order %s: %s",
            order_id,
            str(exc),
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_email(self, order_id):
    """Send order status update email to the customer."""
    try:
        from .models import Order

        order = Order.objects.select_related("customer").get(id=order_id)

        status_messages = {
            Order.Status.CONFIRMED: "Your order has been confirmed by the artisan.",
            Order.Status.PROCESSING: "Your order is being prepared.",
            Order.Status.SHIPPED: (
                f"Your order has been shipped! "
                f"Tracking: {order.tracking_number or 'N/A'}"
            ),
            Order.Status.DELIVERED: "Your order has been delivered.",
            Order.Status.COMPLETED: "Your order is complete. Thank you for shopping with us!",
            Order.Status.CANCELLED: "Your order has been cancelled.",
            Order.Status.REFUNDED: "Your order has been refunded.",
        }

        status_message = status_messages.get(
            order.status, f"Your order status has been updated to: {order.get_status_display()}"
        )

        subject = f"Order Update - {order.order_number}"
        message = (
            f"Dear {order.customer.get_full_name()},\n\n"
            f"{status_message}\n\n"
            f"Order Number: {order.order_number}\n\n"
            f"Best regards,\nThe HandCraft Team"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            fail_silently=False,
        )

        logger.info(
            "Order status update email sent for order %s (status: %s)",
            order.order_number,
            order.status,
        )
    except Exception as exc:
        logger.error(
            "Failed to send order status email for order %s: %s",
            order_id,
            str(exc),
        )
        raise self.retry(exc=exc)


@shared_task
def auto_complete_delivered_orders():
    """
    Auto-complete orders that have been in 'delivered' status
    for more than ORDER_AUTO_COMPLETE_DAYS.
    """
    from .models import Order

    auto_complete_days = getattr(settings, "ORDER_AUTO_COMPLETE_DAYS", 14)
    cutoff_date = timezone.now() - timedelta(days=auto_complete_days)

    orders = Order.objects.filter(
        status=Order.Status.DELIVERED,
        delivered_at__lte=cutoff_date,
    )

    count = 0
    for order in orders:
        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=["status", "completed_at"])
        count += 1

        # Update artisan sales count
        for item in order.items.select_related("artisan").all():
            if item.artisan:
                try:
                    profile = item.artisan.artisan_profile
                    profile.total_sales += item.quantity
                    profile.save(update_fields=["total_sales"])
                except Exception:
                    pass

        # Update customer stats
        try:
            customer_profile = order.customer.customer_profile
            customer_profile.total_orders += 1
            customer_profile.total_spent += order.total
            customer_profile.save(update_fields=["total_orders", "total_spent"])
        except Exception:
            pass

    logger.info("Auto-completed %d delivered orders.", count)
    return count


@shared_task
def send_order_reminder_emails():
    """Send reminder emails for orders pending artisan confirmation."""
    from .models import Order

    cutoff = timezone.now() - timedelta(hours=48)
    pending_orders = Order.objects.filter(
        status=Order.Status.PENDING,
        created_at__lte=cutoff,
    ).select_related("customer")

    count = 0
    for order in pending_orders:
        artisans = order.artisans
        for artisan in artisans:
            subject = f"Reminder: Order {order.order_number} awaiting confirmation"
            message = (
                f"Dear {artisan.get_full_name()},\n\n"
                f"You have an order ({order.order_number}) that has been "
                f"pending for more than 48 hours. Please confirm or review it.\n\n"
                f"Best regards,\nThe HandCraft Team"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[artisan.email],
                fail_silently=True,
            )
            count += 1

    logger.info("Sent %d order reminder emails.", count)
    return count


@shared_task
def cleanup_expired_custom_requests():
    """Mark expired custom order quotes as expired."""
    from .models import CustomOrderRequest

    expired = CustomOrderRequest.objects.filter(
        status=CustomOrderRequest.Status.QUOTED,
        expires_at__lt=timezone.now(),
    )

    count = expired.update(status=CustomOrderRequest.Status.EXPIRED)
    logger.info("Marked %d custom order requests as expired.", count)
    return count
