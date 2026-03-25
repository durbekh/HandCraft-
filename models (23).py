"""
Order models for HandCraft.

Defines Order, OrderItem, and CustomOrderRequest.
"""

import uuid

import shortuuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def generate_order_number():
    """Generate a unique order number."""
    return f"HC-{shortuuid.ShortUUID().random(length=10).upper()}"


class Order(models.Model):
    """
    Represents a customer order. An order can contain items from
    multiple artisans, but each OrderItem references a single artisan.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        PROCESSING = "processing", _("Processing")
        SHIPPED = "shipped", _("Shipped")
        DELIVERED = "delivered", _("Delivered")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        REFUNDED = "refunded", _("Refunded")

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        PAID = "paid", _("Paid")
        FAILED = "failed", _("Failed")
        REFUNDED = "refunded", _("Refunded")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        _("order number"),
        max_length=20,
        unique=True,
        default=generate_order_number,
        db_index=True,
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    payment_status = models.CharField(
        _("payment status"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    # Shipping address (snapshot at order time)
    shipping_name = models.CharField(_("shipping name"), max_length=200)
    shipping_address_line1 = models.CharField(_("address line 1"), max_length=255)
    shipping_address_line2 = models.CharField(
        _("address line 2"), max_length=255, blank=True
    )
    shipping_city = models.CharField(_("city"), max_length=100)
    shipping_state = models.CharField(_("state"), max_length=100, blank=True)
    shipping_postal_code = models.CharField(_("postal code"), max_length=20)
    shipping_country = models.CharField(_("country"), max_length=100)
    # Pricing
    subtotal = models.DecimalField(
        _("subtotal"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )
    shipping_total = models.DecimalField(
        _("shipping total"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )
    tax_amount = models.DecimalField(
        _("tax amount"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )
    discount_amount = models.DecimalField(
        _("discount amount"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )
    total = models.DecimalField(
        _("total"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )
    # Tracking
    tracking_number = models.CharField(
        _("tracking number"), max_length=100, blank=True
    )
    tracking_url = models.URLField(_("tracking URL"), blank=True)
    carrier = models.CharField(_("carrier"), max_length=100, blank=True)
    # Notes
    customer_note = models.TextField(_("customer note"), blank=True)
    internal_note = models.TextField(_("internal note"), blank=True)
    # Timestamps
    confirmed_at = models.DateTimeField(_("confirmed at"), blank=True, null=True)
    shipped_at = models.DateTimeField(_("shipped at"), blank=True, null=True)
    delivered_at = models.DateTimeField(_("delivered at"), blank=True, null=True)
    completed_at = models.DateTimeField(_("completed at"), blank=True, null=True)
    cancelled_at = models.DateTimeField(_("cancelled at"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["-created_at", "status"]),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def calculate_totals(self):
        """Recalculate order totals from items."""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.shipping_total = sum(item.shipping_price for item in items)
        self.total = self.subtotal + self.shipping_total + self.tax_amount - self.discount_amount
        self.save(
            update_fields=["subtotal", "shipping_total", "total"]
        )

    @property
    def is_cancellable(self):
        return self.status in [
            self.Status.PENDING,
            self.Status.CONFIRMED,
        ]

    @property
    def artisans(self):
        """Return distinct artisans involved in this order."""
        artisan_ids = self.items.values_list("artisan", flat=True).distinct()
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.filter(id__in=artisan_ids)


class OrderItem(models.Model):
    """Individual item within an order, linked to a product and artisan."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
    )
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="sold_items",
        null=True,
    )
    # Snapshot of product data at order time
    product_title = models.CharField(_("product title"), max_length=255)
    product_image_url = models.URLField(_("product image URL"), blank=True)
    quantity = models.PositiveIntegerField(
        _("quantity"),
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _("unit price"),
        max_digits=10,
        decimal_places=2,
    )
    shipping_price = models.DecimalField(
        _("shipping price"),
        max_digits=8,
        decimal_places=2,
        default=0.00,
    )
    customization_note = models.TextField(
        _("customization note"), blank=True
    )
    item_status = models.CharField(
        _("item status"),
        max_length=20,
        choices=Order.Status.choices,
        default=Order.Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self):
        return f"{self.product_title} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class CustomOrderRequest(models.Model):
    """
    A customer's request for a custom order from an artisan.
    Follows the flow: submitted -> quoted -> accepted/declined -> order created.
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", _("Submitted")
        QUOTED = "quoted", _("Quoted")
        ACCEPTED = "accepted", _("Accepted")
        DECLINED = "declined", _("Declined")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        EXPIRED = "expired", _("Expired")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_order_requests",
    )
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_custom_requests",
        limit_choices_to={"role": "artisan"},
    )
    custom_order_template = models.ForeignKey(
        "products.CustomOrder",
        on_delete=models.SET_NULL,
        related_name="requests",
        blank=True,
        null=True,
    )
    linked_order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        related_name="custom_request",
        blank=True,
        null=True,
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"))
    reference_image = models.ImageField(
        _("reference image"),
        upload_to="custom_requests/%Y/%m/",
        blank=True,
        null=True,
    )
    budget_min = models.DecimalField(
        _("budget minimum"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    budget_max = models.DecimalField(
        _("budget maximum"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    desired_delivery_date = models.DateField(
        _("desired delivery date"), blank=True, null=True
    )
    # Artisan quote
    quoted_price = models.DecimalField(
        _("quoted price"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    quoted_days = models.PositiveIntegerField(
        _("quoted days to complete"), blank=True, null=True
    )
    artisan_note = models.TextField(_("artisan note"), blank=True)
    # Status
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    quoted_at = models.DateTimeField(_("quoted at"), blank=True, null=True)
    accepted_at = models.DateTimeField(_("accepted at"), blank=True, null=True)
    expires_at = models.DateTimeField(
        _("expires at"),
        blank=True,
        null=True,
        help_text=_("Quote expiration date."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("custom order request")
        verbose_name_plural = _("custom order requests")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Custom request: {self.title} ({self.get_status_display()})"
