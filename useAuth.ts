"""
Custom validators for HandCraft.

Reusable validators for file uploads, image dimensions, and business rules.
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_image_extension(value):
    """
    Validate that the uploaded file has an allowed image extension.

    Allowed extensions are defined in settings.ALLOWED_IMAGE_EXTENSIONS.
    """
    allowed = getattr(
        settings, "ALLOWED_IMAGE_EXTENSIONS", ["jpg", "jpeg", "png", "webp", "gif"]
    )
    ext = os.path.splitext(value.name)[1].lstrip(".").lower()
    if ext not in allowed:
        raise ValidationError(
            _("Unsupported image format '%(ext)s'. Allowed: %(allowed)s."),
            params={"ext": ext, "allowed": ", ".join(allowed)},
        )


def validate_image_size(value):
    """
    Validate that the uploaded image does not exceed the max size.

    Max size is defined in settings.MAX_IMAGE_SIZE_MB (default 5 MB).
    """
    max_mb = getattr(settings, "MAX_IMAGE_SIZE_MB", 5)
    max_bytes = max_mb * 1024 * 1024
    if value.size > max_bytes:
        raise ValidationError(
            _("Image size %(size)s MB exceeds the %(max)s MB limit."),
            params={
                "size": round(value.size / (1024 * 1024), 2),
                "max": max_mb,
            },
        )


def validate_price_positive(value):
    """Ensure a price value is strictly positive."""
    if value is not None and value <= 0:
        raise ValidationError(
            _("Price must be greater than zero. Got %(value)s."),
            params={"value": value},
        )


def validate_no_profanity(value):
    """
    Basic profanity filter for user-generated text.

    Uses a small blocklist; production deployments should integrate
    a dedicated moderation service.
    """
    blocklist = [
        "spam", "scam", "phishing",
    ]
    lower = value.lower()
    for word in blocklist:
        if word in lower:
            raise ValidationError(
                _("Content contains prohibited language."),
            )


def validate_phone_number(value):
    """Validate international phone number format (E.164-like)."""
    import re

    pattern = r"^\+?1?\d{9,15}$"
    if not re.match(pattern, value):
        raise ValidationError(
            _("Enter a valid phone number (e.g., +12125551234). Got '%(value)s'."),
            params={"value": value},
        )
