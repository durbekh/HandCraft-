"""
Views for the favorites app.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ArtisanProfile
from apps.products.models import Product

from .models import FavoriteShop, Wishlist
from .serializers import (
    FavoriteShopSerializer,
    FavoriteShopToggleSerializer,
    WishlistSerializer,
    WishlistToggleSerializer,
)


class WishlistListView(generics.ListAPIView):
    """List the authenticated user's wishlist items."""

    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Wishlist.objects.filter(user=self.request.user)
            .select_related("product__artisan", "product__category")
            .prefetch_related("product__images")
        )


class WishlistAddView(generics.CreateAPIView):
    """Add a product to the wishlist."""

    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]


class WishlistRemoveView(generics.DestroyAPIView):
    """Remove a product from the wishlist."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class WishlistToggleView(APIView):
    """Toggle a product in the wishlist (add if not present, remove if present)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WishlistToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product_id=product_id,
        )

        if created:
            return Response(
                {
                    "status": "added",
                    "item": WishlistSerializer(
                        wishlist_item, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            wishlist_item.delete()
            return Response(
                {"status": "removed"},
                status=status.HTTP_200_OK,
            )


class WishlistCheckView(APIView):
    """Check if a product is in the user's wishlist."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        exists = Wishlist.objects.filter(
            user=request.user, product_id=product_id
        ).exists()
        return Response({"is_wishlisted": exists})


# ─── Favorite Shops ─────────────────────────────────────────────


class FavoriteShopListView(generics.ListAPIView):
    """List the authenticated user's favorite shops."""

    serializer_class = FavoriteShopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            FavoriteShop.objects.filter(user=self.request.user)
            .select_related("artisan__user")
        )


class FavoriteShopAddView(generics.CreateAPIView):
    """Follow a shop (add to favorites)."""

    serializer_class = FavoriteShopSerializer
    permission_classes = [permissions.IsAuthenticated]


class FavoriteShopRemoveView(generics.DestroyAPIView):
    """Unfollow a shop (remove from favorites)."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteShop.objects.filter(user=self.request.user)


class FavoriteShopToggleView(APIView):
    """Toggle following a shop."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FavoriteShopToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        artisan_id = serializer.validated_data["artisan_id"]

        favorite, created = FavoriteShop.objects.get_or_create(
            user=request.user,
            artisan_id=artisan_id,
        )

        if created:
            return Response(
                {
                    "status": "followed",
                    "item": FavoriteShopSerializer(
                        favorite, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            favorite.delete()
            return Response(
                {"status": "unfollowed"},
                status=status.HTTP_200_OK,
            )


class FavoriteShopCheckView(APIView):
    """Check if a shop is in the user's favorites."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, artisan_id):
        exists = FavoriteShop.objects.filter(
            user=request.user, artisan_id=artisan_id
        ).exists()
        return Response({"is_following": exists})
