"""
Analytics service for HandCraft.

Aggregates shop and platform metrics.  Queries are cached in Redis
so dashboards stay responsive under heavy read loads.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 15  # 15 minutes


class AnalyticsService:
    """Read-only analytics queries for dashboards."""

    # ── Artisan Dashboard ────────────────────────────────────────

    @staticmethod
    def get_artisan_dashboard(artisan_user) -> dict:
        """
        Return key metrics for an artisan's shop dashboard.

        Results are cached per-artisan for CACHE_TTL seconds.
        """
        cache_key = f"analytics:artisan:{artisan_user.id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from apps.orders.models import Order, OrderItem
        from apps.products.models import Product
        from apps.reviews.models import Review

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # Products
        products = Product.objects.filter(artisan=artisan_user)
        active_products = products.filter(is_active=True, status=Product.Status.ACTIVE).count()
        total_products = products.count()

        # Orders (items sold by this artisan)
        sold_items = OrderItem.objects.filter(artisan=artisan_user)
        total_revenue = sold_items.aggregate(
            revenue=Sum(F("unit_price") * F("quantity"))
        )["revenue"] or Decimal("0.00")

        recent_revenue = sold_items.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(
            revenue=Sum(F("unit_price") * F("quantity"))
        )["revenue"] or Decimal("0.00")

        orders_last_30 = (
            Order.objects.filter(items__artisan=artisan_user, created_at__gte=thirty_days_ago)
            .distinct()
            .count()
        )

        # Reviews
        reviews = Review.objects.filter(product__artisan=artisan_user)
        avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0.0
        total_reviews = reviews.count()

        # Views
        total_views = products.aggregate(views=Sum("view_count"))["views"] or 0

        data = {
            "active_products": active_products,
            "total_products": total_products,
            "total_revenue": float(total_revenue),
            "revenue_last_30_days": float(recent_revenue),
            "orders_last_30_days": orders_last_30,
            "average_rating": round(float(avg_rating), 2),
            "total_reviews": total_reviews,
            "total_product_views": total_views,
        }
        cache.set(cache_key, data, CACHE_TTL)
        return data

    # ── Platform-wide (admin) ────────────────────────────────────

    @staticmethod
    def get_platform_stats() -> dict:
        """
        Return platform-wide statistics for admin dashboards.

        Cached globally for CACHE_TTL seconds.
        """
        cache_key = "analytics:platform"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        from django.contrib.auth import get_user_model

        from apps.orders.models import Order
        from apps.products.models import Product
        from apps.reviews.models import Review

        User = get_user_model()
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        data = {
            "total_users": User.objects.filter(is_active=True).count(),
            "total_artisans": User.objects.filter(role="artisan", is_active=True).count(),
            "total_customers": User.objects.filter(role="customer", is_active=True).count(),
            "new_users_last_30_days": User.objects.filter(created_at__gte=thirty_days_ago).count(),
            "total_products": Product.objects.filter(is_active=True).count(),
            "total_orders": Order.objects.count(),
            "orders_last_30_days": Order.objects.filter(created_at__gte=thirty_days_ago).count(),
            "total_revenue": float(
                Order.objects.filter(
                    payment_status="paid"
                ).aggregate(total=Sum("total"))["total"] or 0
            ),
            "revenue_last_30_days": float(
                Order.objects.filter(
                    payment_status="paid", created_at__gte=thirty_days_ago
                ).aggregate(total=Sum("total"))["total"] or 0
            ),
            "total_reviews": Review.objects.count(),
            "average_order_value": float(
                Order.objects.filter(
                    payment_status="paid"
                ).aggregate(avg=Avg("total"))["avg"] or 0
            ),
        }
        cache.set(cache_key, data, CACHE_TTL)
        return data

    # ── Top items ────────────────────────────────────────────────

    @staticmethod
    def get_top_products(limit: int = 10) -> list:
        """Return the top-selling active products."""
        from apps.products.models import Product

        return list(
            Product.objects.filter(is_active=True)
            .order_by("-total_sales")
            .values("id", "title", "slug", "total_sales", "average_rating", "price")[:limit]
        )

    @staticmethod
    def get_top_artisans(limit: int = 10) -> list:
        """Return the top-rated artisans."""
        from apps.accounts.models import ArtisanProfile

        return list(
            ArtisanProfile.objects.filter(user__is_active=True)
            .order_by("-average_rating", "-total_sales")
            .values("id", "shop_name", "slug", "average_rating", "total_sales")[:limit]
        )
