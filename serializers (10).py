"""
Serializers for the favorites app.
"""

from rest_framework import serializers

from apps.accounts.serializers import ArtisanListSerializer
from apps.products.serializers import ProductListSerializer

from .models import FavoriteShop, Wishlist


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlist items."""

    product_detail = ProductListSerializer(source="product", read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "product",
            "product_detail",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_product(self, value):
        request = self.context.get("request")
        if request and Wishlist.objects.filter(
            user=request.user, product=value
        ).exists():
            raise serializers.ValidationError(
                "This product is already in your wishlist."
            )
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class WishlistToggleSerializer(serializers.Serializer):
    """Serializer for toggling a product in the wishlist."""

    product_id = serializers.UUIDField()

    def validate_product_id(self, value):
        from apps.products.models import Product

        try:
            Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        return value


class FavoriteShopSerializer(serializers.ModelSerializer):
    """Serializer for favorite shops."""

    artisan_detail = ArtisanListSerializer(source="artisan", read_only=True)

    class Meta:
        model = FavoriteShop
        fields = [
            "id",
            "artisan",
            "artisan_detail",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_artisan(self, value):
        request = self.context.get("request")
        if request and FavoriteShop.objects.filter(
            user=request.user, artisan=value
        ).exists():
            raise serializers.ValidationError(
                "You are already following this shop."
            )
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class FavoriteShopToggleSerializer(serializers.Serializer):
    """Serializer for toggling a shop follow."""

    artisan_id = serializers.UUIDField()

    def validate_artisan_id(self, value):
        from apps.accounts.models import ArtisanProfile

        try:
            ArtisanProfile.objects.get(id=value)
        except ArtisanProfile.DoesNotExist:
            raise serializers.ValidationError("Artisan profile not found.")
        return value
