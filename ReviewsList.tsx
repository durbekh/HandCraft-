"""
General-purpose helper functions for HandCraft.
"""

import hashlib
import os
import re
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from django.utils.text import slugify


def generate_unique_slug(model_class, value: str, slug_field: str = "slug") -> str:
    """
    Generate a unique slug for a model instance.

    Appends a numeric suffix (-2, -3, ...) when the base slug already exists.
    """
    base_slug = slugify(value)
    slug = base_slug
    counter = 1
    while model_class.objects.filter(**{slug_field: slug}).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug


def money_round(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to the given number of decimal places using banker's rounding."""
    quantize_str = Decimal(10) ** -places
    return value.quantize(quantize_str, rounding=ROUND_HALF_UP)


def calculate_commission(amount: Decimal, commission_pct: int = 10) -> dict:
    """
    Calculate platform commission and artisan payout.

    Returns a dict with 'commission', 'payout', and 'total'.
    """
    commission = money_round(amount * Decimal(commission_pct) / Decimal(100))
    payout = money_round(amount - commission)
    return {
        "total": amount,
        "commission": commission,
        "payout": payout,
        "commission_pct": commission_pct,
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a user-uploaded filename.

    Strips dangerous characters and prepends a short UUID to prevent collisions.
    """
    name, ext = os.path.splitext(filename)
    # Keep only alphanumerics, hyphens, and underscores
    name = re.sub(r"[^\w\-]", "_", name)
    short_id = uuid.uuid4().hex[:8]
    return f"{name}_{short_id}{ext.lower()}"


def truncate_string(value: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string at a word boundary."""
    if len(value) <= max_length:
        return value
    truncated = value[: max_length - len(suffix)]
    # Cut at the last space to avoid splitting a word
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + suffix


def mask_email(email: str) -> str:
    """
    Mask an email address for privacy.

    'john.doe@example.com' -> 'j*****e@example.com'
    """
    try:
        local, domain = email.rsplit("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    except (ValueError, IndexError):
        return "***@***.***"


def file_hash(file_obj, algorithm: str = "sha256") -> str:
    """
    Compute a hex digest for a file-like object.

    Useful for deduplicating uploaded images.
    """
    h = hashlib.new(algorithm)
    for chunk in file_obj.chunks(8192):
        h.update(chunk)
    return h.hexdigest()
