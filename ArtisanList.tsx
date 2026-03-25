"""
Centralised email service for HandCraft.

All outbound emails go through this service so we can swap providers,
add tracking, or switch to async sending in one place.
"""

import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """High-level email sending service."""

    @staticmethod
    def _send(
        subject: str,
        to_emails: List[str],
        text_body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email and return True on success.

        Parameters
        ----------
        subject : str
        to_emails : list[str]
        text_body : str
            Plain-text fallback.
        html_body : str | None
            Optional HTML version.
        from_email : str | None
            Defaults to settings.DEFAULT_FROM_EMAIL.
        reply_to : list[str] | None
        """
        sender = from_email or settings.DEFAULT_FROM_EMAIL
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=sender,
            to=to_emails,
            reply_to=reply_to or [],
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        try:
            msg.send(fail_silently=False)
            logger.info("Email sent: '%s' -> %s", subject, to_emails)
            return True
        except Exception:
            logger.exception("Failed to send email: '%s' -> %s", subject, to_emails)
            return False

    # ── Pre-built notification emails ────────────────────────────

    @classmethod
    def send_welcome_email(cls, user) -> bool:
        """Send a welcome email after registration."""
        subject = "Welcome to HandCraft!"
        text_body = (
            f"Hi {user.first_name},\n\n"
            f"Welcome to HandCraft -- the marketplace for handmade goods.\n\n"
            f"{'Start setting up your shop!' if user.is_artisan else 'Browse unique handmade items!'}\n\n"
            f"Best regards,\nThe HandCraft Team"
        )
        return cls._send(subject, [user.email], text_body)

    @classmethod
    def send_order_confirmation(cls, order) -> bool:
        """Send order confirmation to the customer."""
        subject = f"Order Confirmation - {order.order_number}"
        items_text = "\n".join(
            f"  - {item.product_title} x{item.quantity}  ${item.line_total}"
            for item in order.items.all()
        )
        text_body = (
            f"Hi {order.customer.first_name},\n\n"
            f"Thank you for your order!\n\n"
            f"Order: {order.order_number}\n"
            f"Items:\n{items_text}\n\n"
            f"Subtotal: ${order.subtotal}\n"
            f"Shipping: ${order.shipping_total}\n"
            f"Total: ${order.total}\n\n"
            f"We'll notify you when your order ships.\n\n"
            f"Best regards,\nThe HandCraft Team"
        )
        return cls._send(subject, [order.customer.email], text_body)

    @classmethod
    def send_order_shipped(cls, order) -> bool:
        """Notify the customer that their order has shipped."""
        subject = f"Your Order {order.order_number} Has Shipped!"
        tracking_info = ""
        if order.tracking_number:
            tracking_info = f"Tracking: {order.tracking_number}\n"
            if order.tracking_url:
                tracking_info += f"Track online: {order.tracking_url}\n"
        text_body = (
            f"Hi {order.customer.first_name},\n\n"
            f"Great news! Your order {order.order_number} has been shipped.\n\n"
            f"{tracking_info}\n"
            f"Carrier: {order.carrier or 'N/A'}\n\n"
            f"Best regards,\nThe HandCraft Team"
        )
        return cls._send(subject, [order.customer.email], text_body)

    @classmethod
    def send_new_message_notification(cls, recipient, sender_name: str, conversation_subject: str) -> bool:
        """Notify a user about a new message."""
        subject = f"New message from {sender_name} on HandCraft"
        text_body = (
            f"Hi {recipient.first_name},\n\n"
            f"{sender_name} sent you a message"
            f"{' about: ' + conversation_subject if conversation_subject else ''}.\n\n"
            f"Log in to HandCraft to read and reply.\n\n"
            f"Best regards,\nThe HandCraft Team"
        )
        return cls._send(subject, [recipient.email], text_body)

    @classmethod
    def send_review_notification(cls, artisan, product_title: str, rating: int) -> bool:
        """Notify artisan about a new review on their product."""
        subject = f"New {rating}-star review on {product_title}"
        text_body = (
            f"Hi {artisan.first_name},\n\n"
            f"You received a new {rating}-star review on \"{product_title}\".\n\n"
            f"Log in to HandCraft to read the full review and respond.\n\n"
            f"Best regards,\nThe HandCraft Team"
        )
        return cls._send(subject, [artisan.email], text_body)
