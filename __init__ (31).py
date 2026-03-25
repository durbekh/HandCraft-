"""
Admin configuration for the products app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, CustomOrder, Product, ProductImage, Tag


class ProductImageInline(admin.TabularInline):
    """Inline admin for product images."""

    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "is_primary", "sort_order", "image_preview"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""

    list_display = [
        "title",
        "artisan",
        "category",
        "price",
        "stock_quantity",
        "status",
        "average_rating",
        "total_sales",
        "is_active",
        "is_featured",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_active",
        "is_featured",
        "is_free_shipping",
        "is_customizable",
        "category",
    ]
    search_fields = ["title", "description", "artisan__email", "sku"]
    list_editable = ["is_active", "is_featured", "status"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = [
        "average_rating",
        "total_reviews",
        "total_sales",
        "view_count",
        "created_at",
        "updated_at",
    ]
    inlines = [ProductImageInline]
    filter_horizontal = ["tags"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "artisan",
                    "title",
                    "slug",
                    "description",
                    "short_description",
                    "category",
                    "tags",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "price",
                    "compare_at_price",
                    "cost_per_item",
                )
            },
        ),
        (
            "Inventory",
            {
                "fields": (
                    "stock_quantity",
                    "sku",
                )
            },
        ),
        (
            "Dimensions & Shipping",
            {
                "fields": (
                    "weight_grams",
                    "length_cm",
                    "width_cm",
                    "height_cm",
                    "shipping_price",
                    "is_free_shipping",
                    "processing_time_days",
                )
            },
        ),
        (
            "Customization",
            {
                "fields": (
                    "materials",
                    "is_customizable",
                    "customization_instructions",
                )
            },
        ),
        (
            "Status & Visibility",
            {
                "fields": (
                    "status",
                    "is_active",
                    "is_featured",
                )
            },
        ),
        (
            "Stats (read-only)",
            {
                "fields": (
                    "average_rating",
                    "total_reviews",
                    "total_sales",
                    "view_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""

    list_display = ["name", "parent", "sort_order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["sort_order", "is_active"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""

    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
    """Admin for CustomOrder model."""

    list_display = [
        "title",
        "artisan",
        "base_price",
        "max_price",
        "estimated_days",
        "status",
        "created_at",
    ]
    list_filter = ["status", "category"]
    search_fields = ["title", "artisan__email"]
