"""
Serializers for the reviews app.
"""

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    """Serializer for review images."""

    class Meta:
        model = ReviewImage
        fields = ["id", "image", "alt_text", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for review display."""

    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    customer_avatar = serializers.ImageField(
        source="customer.avatar", read_only=True
    )
    images = ReviewImageSerializer(many=True, read_only=True)
    product_title = serializers.CharField(
        source="product.title", read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "product_title",
            "customer",
            "customer_name",
            "customer_avatar",
            "rating",
            "title",
            "comment",
            "artisan_reply",
            "artisan_replied_at",
            "is_verified_purchase",
            "helpful_count",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "artisan_reply",
            "artisan_replied_at",
            "is_verified_purchase",
            "helpful_count",
            "created_at",
            "updated_at",
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a review."""

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        max_length=5,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Review
        fields = [
            "rating",
            "title",
            "comment",
            "uploaded_images",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        product = self.context["product"]

        # Check if user already reviewed this product
        if Review.objects.filter(
            product=product, customer=request.user
        ).exists():
            raise serializers.ValidationError(
                "You have already reviewed this product."
            )

        # Check if user has purchased and received this product
        from apps.orders.models import Order, OrderItem

        has_purchased = OrderItem.objects.filter(
            order__customer=request.user,
            product=product,
            order__status__in=[
                Order.Status.DELIVERED,
                Order.Status.COMPLETED,
            ],
        ).exists()

        if has_purchased:
            attrs["is_verified_purchase"] = True

        return attrs

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        product = self.context["product"]
        customer = self.context["request"].user

        review = Review.objects.create(
            product=product,
            customer=customer,
            **validated_data,
        )

        # Create review images
        max_images = getattr(settings, "MAX_REVIEW_IMAGES", 5)
        for i, image in enumerate(uploaded_images[:max_images]):
            ReviewImage.objects.create(
                review=review,
                image=image,
                sort_order=i,
            )

        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a review."""

    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]


class ArtisanReplySerializer(serializers.Serializer):
    """Serializer for artisan replying to a review."""

    artisan_reply = serializers.CharField(max_length=1000)

    def update(self, review, validated_data):
        review.artisan_reply = validated_data["artisan_reply"]
        review.artisan_replied_at = timezone.now()
        review.save(update_fields=["artisan_reply", "artisan_replied_at"])
        return review


class ReviewStatsSerializer(serializers.Serializer):
    """Serializer for review statistics."""

    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    rating_distribution = serializers.DictField(
        child=serializers.IntegerField()
    )
