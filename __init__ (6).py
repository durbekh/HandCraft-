"""
Views for the accounts app.
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import ArtisanProfile
from .permissions import IsArtisan, IsOwnerOrReadOnly
from .serializers import (
    ArtisanListSerializer,
    ArtisanProfileSerializer,
    ArtisanProfileUpdateSerializer,
    ChangePasswordSerializer,
    CustomerProfileSerializer,
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view that returns user details with tokens."""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user (customer or artisan)."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = UserSerializer(user).data
        return Response(
            {
                "message": "Registration successful.",
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    """Get or update the currently authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data

        # Include role-specific profile
        if request.user.is_artisan:
            try:
                profile = ArtisanProfileSerializer(
                    request.user.artisan_profile
                ).data
                data["artisan_profile"] = profile
            except ArtisanProfile.DoesNotExist:
                data["artisan_profile"] = None
        elif request.user.is_customer:
            try:
                profile = CustomerProfileSerializer(
                    request.user.customer_profile
                ).data
                data["customer_profile"] = profile
            except Exception:
                data["customer_profile"] = None

        return Response(data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"message": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


class ArtisanListView(generics.ListAPIView):
    """List all artisan profiles with optional filtering."""

    serializer_class = ArtisanListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["location_country", "is_verified", "is_featured"]
    search_fields = ["shop_name", "bio", "tagline", "user__first_name", "user__last_name"]
    ordering_fields = ["average_rating", "total_sales", "joined_at", "shop_name"]
    ordering = ["-is_featured", "-average_rating"]

    def get_queryset(self):
        return ArtisanProfile.objects.select_related("user").filter(
            user__is_active=True
        )


class ArtisanDetailView(generics.RetrieveAPIView):
    """Get detailed artisan profile by ID or slug."""

    serializer_class = ArtisanProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return ArtisanProfile.objects.select_related("user").filter(
            user__is_active=True
        )


class ArtisanProfileUpdateView(APIView):
    """Update the authenticated artisan's profile."""

    permission_classes = [permissions.IsAuthenticated, IsArtisan]

    def get(self, request):
        try:
            profile = request.user.artisan_profile
        except ArtisanProfile.DoesNotExist:
            return Response(
                {"detail": "Artisan profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ArtisanProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        try:
            profile = request.user.artisan_profile
        except ArtisanProfile.DoesNotExist:
            return Response(
                {"detail": "Artisan profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ArtisanProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ArtisanProfileSerializer(profile).data)


class CustomerProfileUpdateView(APIView):
    """Update the authenticated customer's profile (shipping address)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.customer_profile
        except Exception:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CustomerProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        try:
            profile = request.user.customer_profile
        except Exception:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CustomerProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
