"""
Favorites models for HandCraft.

Defines Wishlist and FavoriteShop for customer favorites.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Wishlist(models.Model):
    """
    A product saved to a user's wishlist.
    Each user can have one entry per product.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    note = models.CharField(
        _("note"),
        max_length=255,
        blank=True,
        help_text=_("Optional note about why you saved this product."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("wishlist item")
        verbose_name_plural = _("wishlist items")
        ordering = ["-created_at"]
        unique_together = ["user", "product"]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.product.title}"


class FavoriteShop(models.Model):
    """
    A shop (artisan) followed by a user.
    Each user can follow each artisan only once.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_shops",
    )
    artisan = models.ForeignKey(
        "accounts.ArtisanProfile",
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("favorite shop")
        verbose_name_plural = _("favorite shops")
        ordering = ["-created_at"]
        unique_together = ["user", "artisan"]

    def __str__(self):
        return f"{self.user.get_full_name()} follows {self.artisan.shop_name}"
