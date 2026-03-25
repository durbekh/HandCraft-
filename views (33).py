"""
Product models for HandCraft.

Defines Product, Category, Tag, ProductImage, and CustomOrder.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Product category with optional parent for hierarchical structure."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    description = models.TextField(_("description"), blank=True)
    image = models.ImageField(
        _("image"),
        upload_to="categories/",
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(_("active"), default=True)
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def full_path(self):
        """Return full category path (e.g., 'Jewelry > Necklaces')."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Tag(models.Model):
    """Tags for product classification and discovery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("name"), max_length=50, unique=True)
    slug = models.SlugField(_("slug"), max_length=60, unique=True)

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Core product model. Each product belongs to an artisan and a category.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        ACTIVE = "active", _("Active")
        SOLD_OUT = "sold_out", _("Sold Out")
        ARCHIVED = "archived", _("Archived")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        limit_choices_to={"role": "artisan"},
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
    )
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)
    title = models.CharField(_("title"), max_length=255, db_index=True)
    slug = models.SlugField(_("slug"), max_length=280, unique=True)
    description = models.TextField(_("description"))
    short_description = models.CharField(
        _("short description"), max_length=500, blank=True
    )
    price = models.DecimalField(
        _("price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    compare_at_price = models.DecimalField(
        _("compare at price"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Original price before discount."),
    )
    cost_per_item = models.DecimalField(
        _("cost per item"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Cost to produce (not shown to customers)."),
    )
    stock_quantity = models.PositiveIntegerField(_("stock quantity"), default=1)
    sku = models.CharField(_("SKU"), max_length=50, blank=True, db_index=True)
    weight_grams = models.PositiveIntegerField(
        _("weight (grams)"), blank=True, null=True
    )
    length_cm = models.DecimalField(
        _("length (cm)"), max_digits=8, decimal_places=2, blank=True, null=True
    )
    width_cm = models.DecimalField(
        _("width (cm)"), max_digits=8, decimal_places=2, blank=True, null=True
    )
    height_cm = models.DecimalField(
        _("height (cm)"), max_digits=8, decimal_places=2, blank=True, null=True
    )
    materials = models.CharField(
        _("materials"),
        max_length=500,
        blank=True,
        help_text=_("Comma-separated list of materials used."),
    )
    processing_time_days = models.PositiveIntegerField(
        _("processing time (days)"),
        default=3,
        help_text=_("Number of business days to prepare the order."),
    )
    shipping_price = models.DecimalField(
        _("shipping price"),
        max_digits=8,
        decimal_places=2,
        default=0.00,
    )
    is_free_shipping = models.BooleanField(_("free shipping"), default=False)
    is_customizable = models.BooleanField(
        _("customizable"),
        default=False,
        help_text=_("Whether the buyer can request customizations."),
    )
    customization_instructions = models.TextField(
        _("customization instructions"),
        blank=True,
        help_text=_("Instructions for buyers on how to customize."),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_active = models.BooleanField(_("active"), default=True, db_index=True)
    is_featured = models.BooleanField(_("featured"), default=False)
    average_rating = models.DecimalField(
        _("average rating"),
        max_digits=3,
        decimal_places=2,
        default=0.00,
    )
    total_reviews = models.PositiveIntegerField(_("total reviews"), default=0)
    total_sales = models.PositiveIntegerField(_("total sales"), default=0)
    view_count = models.PositiveIntegerField(_("view count"), default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["artisan", "status"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["-created_at", "is_active"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if self.stock_quantity == 0 and self.status == self.Status.ACTIVE:
            self.status = self.Status.SOLD_OUT
        super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        return self.compare_at_price and self.compare_at_price > self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            discount = (
                (self.compare_at_price - self.price) / self.compare_at_price
            ) * 100
            return round(discount)
        return 0

    @property
    def effective_shipping_price(self):
        return 0 if self.is_free_shipping else self.shipping_price

    def update_rating(self):
        """Recalculate average rating from reviews."""
        from apps.reviews.models import Review

        reviews = Review.objects.filter(product=self)
        aggregation = reviews.aggregate(
            avg_rating=models.Avg("rating"),
            count=models.Count("id"),
        )
        self.average_rating = aggregation["avg_rating"] or 0.00
        self.total_reviews = aggregation["count"]
        self.save(update_fields=["average_rating", "total_reviews"])


class ProductImage(models.Model):
    """Images associated with a product."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        _("image"),
        upload_to="products/%Y/%m/",
    )
    alt_text = models.CharField(_("alt text"), max_length=255, blank=True)
    is_primary = models.BooleanField(_("primary image"), default=False)
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"Image for {self.product.title} (#{self.sort_order})"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class CustomOrder(models.Model):
    """
    Custom order template defined by an artisan.
    Describes what types of custom work they accept.
    """

    class Status(models.TextChoices):
        AVAILABLE = "available", _("Available")
        PAUSED = "paused", _("Paused")
        UNAVAILABLE = "unavailable", _("Unavailable")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_order_templates",
        limit_choices_to={"role": "artisan"},
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"))
    base_price = models.DecimalField(
        _("base price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    max_price = models.DecimalField(
        _("max price"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    estimated_days = models.PositiveIntegerField(
        _("estimated completion days"), default=14
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="custom_orders",
        null=True,
        blank=True,
    )
    example_image = models.ImageField(
        _("example image"),
        upload_to="custom_orders/%Y/%m/",
        blank=True,
        null=True,
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("custom order template")
        verbose_name_plural = _("custom order templates")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} by {self.artisan.get_full_name()}"
