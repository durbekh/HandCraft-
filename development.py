"""
Views for the products app.
"""

from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsArtisan, IsArtisanOwnerOrReadOnly

from .filters import ProductFilter
from .models import Category, CustomOrder, Product, ProductImage, Tag
from .serializers import (
    CategorySerializer,
    CustomOrderSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer,
    ProductListSerializer,
    TagSerializer,
)


class ProductListView(generics.ListAPIView):
    """List products with filtering, searching, and sorting."""

    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class = ProductFilter
    search_fields = ["title", "description", "materials", "tags__name"]
    ordering_fields = [
        "price",
        "created_at",
        "average_rating",
        "total_sales",
        "view_count",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, status=Product.Status.ACTIVE)
            .select_related("artisan", "category")
            .prefetch_related("images", "tags")
        )


class ProductDetailView(generics.RetrieveAPIView):
    """Get detailed product information."""

    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            "artisan", "category"
        ).prefetch_related("images", "tags")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Product.objects.filter(pk=instance.pk).update(
            view_count=instance.view_count + 1
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProductCreateView(generics.CreateAPIView):
    """Create a new product (artisan only)."""

    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtisan]

    def perform_create(self, serializer):
        serializer.save(artisan=self.request.user)


class ProductUpdateView(generics.UpdateAPIView):
    """Update an existing product (owner artisan only)."""

    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtisanOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.filter(artisan=self.request.user)


class ProductDeleteView(generics.DestroyAPIView):
    """Delete (archive) a product (owner artisan only)."""

    permission_classes = [permissions.IsAuthenticated, IsArtisanOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.filter(artisan=self.request.user)

    def perform_destroy(self, instance):
        # Soft delete: archive instead of hard delete
        instance.status = Product.Status.ARCHIVED
        instance.is_active = False
        instance.save(update_fields=["status", "is_active"])


class ArtisanProductListView(generics.ListAPIView):
    """List products belonging to a specific artisan."""

    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        artisan_id = self.kwargs.get("artisan_id")
        return (
            Product.objects.filter(
                artisan_id=artisan_id,
                is_active=True,
                status=Product.Status.ACTIVE,
            )
            .select_related("category")
            .prefetch_related("images", "tags")
        )


class MyProductListView(generics.ListAPIView):
    """List the authenticated artisan's products (all statuses)."""

    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtisan]
    filterset_class = ProductFilter

    def get_queryset(self):
        return (
            Product.objects.filter(artisan=self.request.user)
            .select_related("category")
            .prefetch_related("images", "tags")
        )


class ProductImageUploadView(APIView):
    """Upload images for a product."""

    permission_classes = [permissions.IsAuthenticated, IsArtisan]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id, artisan=request.user)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductImageUploadSerializer(
            data=request.data,
            context={"product": product},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)

        return Response(
            ProductImageSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )


class ProductImageDeleteView(generics.DestroyAPIView):
    """Delete a product image."""

    permission_classes = [permissions.IsAuthenticated, IsArtisan]

    def get_queryset(self):
        return ProductImage.objects.filter(product__artisan=self.request.user)


class ProductSearchView(generics.ListAPIView):
    """
    Full-text search for products.
    Falls back to Django ORM if Elasticsearch is unavailable.
    """

    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query:
            return Product.objects.none()

        return (
            Product.objects.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(materials__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(category__name__icontains=query),
                is_active=True,
                status=Product.Status.ACTIVE,
            )
            .distinct()
            .select_related("artisan", "category")
            .prefetch_related("images", "tags")
        )


class CategoryListView(generics.ListAPIView):
    """List all active top-level categories with children."""

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent__isnull=True)


class CategoryDetailView(generics.RetrieveAPIView):
    """Get category detail with children."""

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class TagListView(generics.ListAPIView):
    """List all tags."""

    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = Tag.objects.all()
    search_fields = ["name"]


class CustomOrderListView(generics.ListCreateAPIView):
    """List and create custom order templates."""

    serializer_class = CustomOrderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = CustomOrder.objects.select_related("artisan", "category")
        artisan_id = self.request.query_params.get("artisan")
        if artisan_id:
            queryset = queryset.filter(artisan_id=artisan_id)
        return queryset.filter(status=CustomOrder.Status.AVAILABLE)

    def perform_create(self, serializer):
        serializer.save(artisan=self.request.user)


class CustomOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a custom order template."""

    serializer_class = CustomOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsArtisanOwnerOrReadOnly]

    def get_queryset(self):
        return CustomOrder.objects.filter(artisan=self.request.user)
