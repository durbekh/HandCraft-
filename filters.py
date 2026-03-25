"""
Admin configuration for the orders app.
"""

from django.contrib import admin

from .models import CustomOrderRequest, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""

    model = OrderItem
    extra = 0
    readonly_fields = [
        "product",
        "artisan",
        "product_title",
        "quantity",
        "unit_price",
        "shipping_price",
        "line_total",
    ]
    fields = [
        "product_title",
        "artisan",
        "quantity",
        "unit_price",
        "shipping_price",
        "line_total",
        "item_status",
        "customization_note",
    ]

    def line_total(self, obj):
        return obj.line_total

    line_total.short_description = "Line Total"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""

    list_display = [
        "order_number",
        "customer",
        "status",
        "payment_status",
        "subtotal",
        "shipping_total",
        "total",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "created_at"]
    search_fields = [
        "order_number",
        "customer__email",
        "customer__first_name",
        "shipping_name",
    ]
    readonly_fields = [
        "order_number",
        "customer",
        "subtotal",
        "shipping_total",
        "tax_amount",
        "discount_amount",
        "total",
        "confirmed_at",
        "shipped_at",
        "delivered_at",
        "completed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "order_number",
                    "customer",
                    "status",
                    "payment_status",
                )
            },
        ),
        (
            "Shipping Address",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address_line1",
                    "shipping_address_line2",
                    "shipping_city",
                    "shipping_state",
                    "shipping_postal_code",
                    "shipping_country",
                )
            },
        ),
        (
            "Totals",
            {
                "fields": (
                    "subtotal",
                    "shipping_total",
                    "tax_amount",
                    "discount_amount",
                    "total",
                )
            },
        ),
        (
            "Tracking",
            {
                "fields": (
                    "tracking_number",
                    "tracking_url",
                    "carrier",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": (
                    "customer_note",
                    "internal_note",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "confirmed_at",
                    "shipped_at",
                    "delivered_at",
                    "completed_at",
                    "cancelled_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(CustomOrderRequest)
class CustomOrderRequestAdmin(admin.ModelAdmin):
    """Admin for CustomOrderRequest model."""

    list_display = [
        "title",
        "customer",
        "artisan",
        "status",
        "quoted_price",
        "quoted_days",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "title",
        "customer__email",
        "artisan__email",
    ]
    readonly_fields = [
        "customer",
        "quoted_at",
        "accepted_at",
        "created_at",
        "updated_at",
    ]
