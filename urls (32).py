"""
Filters for the products app.
"""

import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Filter set for product listings."""

    # Price range
    min_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="Minimum price"
    )
    max_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="Maximum price"
    )

    # Category
    category = django_filters.UUIDFilter(
        field_name="category__id", label="Category ID"
    )
    category_slug = django_filters.CharFilter(
        field_name="category__slug", label="Category slug"
    )

    # Tags
    tags = django_filters.CharFilter(
        method="filter_by_tags", label="Tags (comma-separated slugs)"
    )

    # Artisan
    artisan = django_filters.UUIDFilter(
        field_name="artisan__id", label="Artisan ID"
    )
    artisan_country = django_filters.CharFilter(
        field_name="artisan__artisan_profile__location_country",
        lookup_expr="iexact",
        label="Artisan country",
    )

    # Rating
    min_rating = django_filters.NumberFilter(
        field_name="average_rating",
        lookup_expr="gte",
        label="Minimum average rating",
    )

    # Shipping
    free_shipping = django_filters.BooleanFilter(
        field_name="is_free_shipping", label="Free shipping only"
    )

    # Customizable
    customizable = django_filters.BooleanFilter(
        field_name="is_customizable", label="Customizable products only"
    )

    # Status
    status = django_filters.ChoiceFilter(
        choices=Product.Status.choices, label="Product status"
    )

    # In stock
    in_stock = django_filters.BooleanFilter(
        method="filter_in_stock", label="In stock only"
    )

    # On sale
    on_sale = django_filters.BooleanFilter(
        method="filter_on_sale", label="On sale only"
    )

    # Featured
    featured = django_filters.BooleanFilter(
        field_name="is_featured", label="Featured only"
    )

    # Materials
    materials = django_filters.CharFilter(
        method="filter_by_materials", label="Materials (comma-separated)"
    )

    class Meta:
        model = Product
        fields = [
            "min_price",
            "max_price",
            "category",
            "category_slug",
            "tags",
            "artisan",
            "artisan_country",
            "min_rating",
            "free_shipping",
            "customizable",
            "status",
            "in_stock",
            "on_sale",
            "featured",
            "materials",
        ]

    def filter_by_tags(self, queryset, name, value):
        """Filter by comma-separated tag slugs."""
        tag_slugs = [slug.strip() for slug in value.split(",") if slug.strip()]
        if tag_slugs:
            return queryset.filter(tags__slug__in=tag_slugs).distinct()
        return queryset

    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock."""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset

    def filter_on_sale(self, queryset, name, value):
        """Filter products that are on sale."""
        if value:
            return queryset.filter(
                compare_at_price__isnull=False,
                compare_at_price__gt=0,
            ).exclude(compare_at_price__lte=models.F("price"))
        return queryset

    def filter_by_materials(self, queryset, name, value):
        """Filter by materials (comma-separated, OR logic)."""
        materials = [m.strip() for m in value.split(",") if m.strip()]
        if materials:
            q_objects = Q()
            for material in materials:
                q_objects |= Q(materials__icontains=material)
            return queryset.filter(q_objects)
        return queryset
