"""
Views for the reviews app.
"""

from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsArtisan, IsOwnerOrReadOnly
from apps.products.models import Product

from .models import Review
from .serializers import (
    ArtisanReplySerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewStatsSerializer,
    ReviewUpdateSerializer,
)


class ProductReviewListView(generics.ListAPIView):
    """List reviews for a specific product."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    ordering_fields = ["created_at", "rating", "helpful_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return (
            Review.objects.filter(
                product__slug=product_slug,
                is_approved=True,
            )
            .select_related("customer", "product")
            .prefetch_related("images")
        )


class ProductReviewCreateView(APIView):
    """Create a review for a product."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_slug):
        try:
            product = Product.objects.get(slug=product_slug, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ReviewCreateSerializer(
            data=request.data,
            context={"request": request, "product": product},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class ReviewUpdateView(generics.UpdateAPIView):
    """Update own review."""

    serializer_class = ReviewUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return Review.objects.filter(customer=self.request.user)

    def perform_update(self, serializer):
        review = serializer.save()
        # Recalculate product rating
        review.product.update_rating()


class ReviewDeleteView(generics.DestroyAPIView):
    """Delete own review."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Review.objects.filter(customer=self.request.user)

    def perform_destroy(self, instance):
        product = instance.product
        instance.delete()
        # Recalculate product rating after deletion
        product.update_rating()
        try:
            product.artisan.artisan_profile.update_rating()
        except Exception:
            pass


class ArtisanReplyView(APIView):
    """Artisan replies to a review on their product."""

    permission_classes = [permissions.IsAuthenticated, IsArtisan]

    def post(self, request, pk):
        try:
            review = Review.objects.get(
                pk=pk, product__artisan=request.user
            )
        except Review.DoesNotExist:
            return Response(
                {"detail": "Review not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if review.artisan_reply:
            return Response(
                {"detail": "You have already replied to this review."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ArtisanReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(review, serializer.validated_data)

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_200_OK,
        )


class ReviewStatsView(APIView):
    """Get review statistics for a product."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, product_slug):
        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        reviews = Review.objects.filter(product=product, is_approved=True)
        stats = reviews.aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id"),
        )

        # Rating distribution
        distribution = {}
        for i in range(1, 6):
            distribution[str(i)] = reviews.filter(rating=i).count()

        data = {
            "average_rating": stats["average_rating"] or 0,
            "total_reviews": stats["total_reviews"],
            "rating_distribution": distribution,
        }

        serializer = ReviewStatsSerializer(data)
        return Response(serializer.data)


class MarkReviewHelpfulView(APIView):
    """Mark a review as helpful (increment counter)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, is_approved=True)
        except Review.DoesNotExist:
            return Response(
                {"detail": "Review not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent self-voting
        if review.customer == request.user:
            return Response(
                {"detail": "You cannot vote on your own review."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review.helpful_count += 1
        review.save(update_fields=["helpful_count"])

        return Response(
            {"helpful_count": review.helpful_count},
            status=status.HTTP_200_OK,
        )
