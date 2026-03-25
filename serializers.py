"""
Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import ArtisanProfile, CustomerProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model using email as the identifier."""

    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_email_verified",
        "created_at",
    ]
    list_filter = ["role", "is_active", "is_email_verified", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "avatar", "phone", "date_of_birth")},
        ),
        (
            _("Roles & Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(ArtisanProfile)
class ArtisanProfileAdmin(admin.ModelAdmin):
    """Admin for ArtisanProfile."""

    list_display = [
        "shop_name",
        "user",
        "location_country",
        "average_rating",
        "total_sales",
        "is_verified",
        "is_featured",
        "joined_at",
    ]
    list_filter = ["is_verified", "is_featured", "location_country"]
    search_fields = ["shop_name", "user__email", "user__first_name"]
    readonly_fields = ["average_rating", "total_reviews", "total_sales", "joined_at"]
    prepopulated_fields = {"slug": ("shop_name",)}
    list_editable = ["is_verified", "is_featured"]


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin for CustomerProfile."""

    list_display = [
        "user",
        "shipping_city",
        "shipping_country",
        "total_orders",
        "total_spent",
    ]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["total_orders", "total_spent"]
