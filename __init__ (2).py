"""
Account models for HandCraft.

Defines custom User model with role-based access, ArtisanProfile for sellers,
and CustomerProfile for buyers.
"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model using email as the primary identifier.
    Supports three roles: Customer, Artisan, and Admin.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        ARTISAN = "artisan", _("Artisan")
        ADMIN = "admin", _("Admin")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
    )
    phone = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message=_("Enter a valid phone number (e.g., +12125551234)."),
            )
        ],
    )
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)
    is_email_verified = models.BooleanField(_("email verified"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_artisan(self):
        return self.role == self.Role.ARTISAN

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class ArtisanProfile(models.Model):
    """
    Extended profile for artisan users. Contains shop information,
    bio, and business details.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artisan_profile",
    )
    shop_name = models.CharField(
        _("shop name"),
        max_length=200,
        unique=True,
        db_index=True,
    )
    slug = models.SlugField(
        _("slug"),
        max_length=200,
        unique=True,
        db_index=True,
    )
    bio = models.TextField(_("bio"), max_length=2000, blank=True)
    tagline = models.CharField(_("tagline"), max_length=255, blank=True)
    cover_image = models.ImageField(
        _("cover image"),
        upload_to="artisan_covers/%Y/%m/",
        blank=True,
        null=True,
    )
    location_city = models.CharField(_("city"), max_length=100, blank=True)
    location_state = models.CharField(_("state/province"), max_length=100, blank=True)
    location_country = models.CharField(_("country"), max_length=100, blank=True)
    website = models.URLField(_("website"), blank=True)
    instagram = models.CharField(_("Instagram handle"), max_length=100, blank=True)
    accepts_custom_orders = models.BooleanField(
        _("accepts custom orders"), default=True
    )
    average_rating = models.DecimalField(
        _("average rating"),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    total_reviews = models.PositiveIntegerField(_("total reviews"), default=0)
    total_sales = models.PositiveIntegerField(_("total sales"), default=0)
    is_verified = models.BooleanField(_("verified artisan"), default=False)
    is_featured = models.BooleanField(_("featured artisan"), default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("artisan profile")
        verbose_name_plural = _("artisan profiles")
        ordering = ["-joined_at"]

    def __str__(self):
        return self.shop_name

    @property
    def full_location(self):
        parts = filter(
            None, [self.location_city, self.location_state, self.location_country]
        )
        return ", ".join(parts)

    def update_rating(self):
        """Recalculate average rating from all product reviews."""
        from apps.reviews.models import Review

        reviews = Review.objects.filter(product__artisan=self.user)
        aggregation = reviews.aggregate(
            avg_rating=models.Avg("rating"),
            count=models.Count("id"),
        )
        self.average_rating = aggregation["avg_rating"] or 0.00
        self.total_reviews = aggregation["count"]
        self.save(update_fields=["average_rating", "total_reviews"])


class CustomerProfile(models.Model):
    """
    Extended profile for customer users. Contains shipping address
    and preference information.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    shipping_address_line1 = models.CharField(
        _("address line 1"), max_length=255, blank=True
    )
    shipping_address_line2 = models.CharField(
        _("address line 2"), max_length=255, blank=True
    )
    shipping_city = models.CharField(_("city"), max_length=100, blank=True)
    shipping_state = models.CharField(_("state/province"), max_length=100, blank=True)
    shipping_postal_code = models.CharField(
        _("postal code"), max_length=20, blank=True
    )
    shipping_country = models.CharField(
        _("country"), max_length=100, default="US", blank=True
    )
    total_orders = models.PositiveIntegerField(_("total orders"), default=0)
    total_spent = models.DecimalField(
        _("total spent"),
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("customer profile")
        verbose_name_plural = _("customer profiles")

    def __str__(self):
        return f"Customer: {self.user.get_full_name()}"

    @property
    def full_shipping_address(self):
        parts = filter(
            None,
            [
                self.shipping_address_line1,
                self.shipping_address_line2,
                self.shipping_city,
                self.shipping_state,
                self.shipping_postal_code,
                self.shipping_country,
            ],
        )
        return ", ".join(parts)
