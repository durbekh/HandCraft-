"""
Review models for HandCraft.

Defines Review and ReviewImage for product reviews with ratings.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    """
    Product review with star rating. Only customers who purchased
    and received the product can leave a review.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    order_item = models.OneToOneField(
        "orders.OrderItem",
        on_delete=models.SET_NULL,
        related_name="review",
        blank=True,
        null=True,
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Rating from 1 to 5 stars."),
    )
    title = models.CharField(_("title"), max_length=200, blank=True)
    comment = models.TextField(_("comment"), max_length=2000)
    # Artisan reply
    artisan_reply = models.TextField(
        _("artisan reply"), max_length=1000, blank=True
    )
    artisan_replied_at = models.DateTimeField(
        _("artisan replied at"), blank=True, null=True
    )
    # Moderation
    is_approved = models.BooleanField(_("approved"), default=True)
    is_reported = models.BooleanField(_("reported"), default=False)
    # Metadata
    is_verified_purchase = models.BooleanField(
        _("verified purchase"), default=False
    )
    helpful_count = models.PositiveIntegerField(
        _("helpful votes"), default=0
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")
        ordering = ["-created_at"]
        # One review per customer per product
        unique_together = ["product", "customer"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["customer", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"Review by {self.customer.get_full_name()} on "
            f"{self.product.title} ({self.rating} stars)"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product average rating
        self.product.update_rating()
        # Update artisan average rating
        try:
            self.product.artisan.artisan_profile.update_rating()
        except Exception:
            pass


class ReviewImage(models.Model):
    """Images attached to a review."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        _("image"),
        upload_to="reviews/%Y/%m/",
    )
    alt_text = models.CharField(_("alt text"), max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("review image")
        verbose_name_plural = _("review images")
        ordering = ["created_at"]

    def __str__(self):
        return f"Image for review by {self.review.customer.get_full_name()}"
