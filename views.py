"""
Serializers for the accounts app.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import ArtisanProfile, CustomerProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user role and name."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
        }
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "role",
            "phone",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        role = attrs.get("role", User.Role.CUSTOMER)
        if role not in [User.Role.CUSTOMER, User.Role.ARTISAN]:
            raise serializers.ValidationError(
                {"role": "Role must be 'customer' or 'artisan'."}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # Create associated profile
        if user.role == User.Role.ARTISAN:
            ArtisanProfile.objects.create(
                user=user,
                shop_name=f"{user.first_name}'s Workshop",
                slug=slugify(f"{user.first_name}-{user.last_name}-{str(user.id)[:8]}"),
            )
        else:
            CustomerProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "avatar",
            "phone",
            "date_of_birth",
            "is_email_verified",
            "created_at",
        ]
        read_only_fields = ["id", "email", "role", "is_email_verified", "created_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "phone",
            "date_of_birth",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs


class ArtisanProfileSerializer(serializers.ModelSerializer):
    """Serializer for artisan profile details."""

    user = UserSerializer(read_only=True)
    full_location = serializers.CharField(read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ArtisanProfile
        fields = [
            "id",
            "user",
            "shop_name",
            "slug",
            "bio",
            "tagline",
            "cover_image",
            "location_city",
            "location_state",
            "location_country",
            "full_location",
            "website",
            "instagram",
            "accepts_custom_orders",
            "average_rating",
            "total_reviews",
            "total_sales",
            "is_verified",
            "is_featured",
            "product_count",
            "joined_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "average_rating",
            "total_reviews",
            "total_sales",
            "is_verified",
            "is_featured",
            "joined_at",
        ]

    def get_product_count(self, obj):
        return obj.user.products.filter(is_active=True).count()


class ArtisanProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating artisan profile."""

    class Meta:
        model = ArtisanProfile
        fields = [
            "shop_name",
            "bio",
            "tagline",
            "cover_image",
            "location_city",
            "location_state",
            "location_country",
            "website",
            "instagram",
            "accepts_custom_orders",
        ]

    def validate_shop_name(self, value):
        instance = self.instance
        if (
            ArtisanProfile.objects.filter(shop_name=value)
            .exclude(pk=instance.pk if instance else None)
            .exists()
        ):
            raise serializers.ValidationError("This shop name is already taken.")
        return value

    def update(self, instance, validated_data):
        if "shop_name" in validated_data:
            validated_data["slug"] = slugify(validated_data["shop_name"])
        return super().update(instance, validated_data)


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for customer profile details."""

    user = UserSerializer(read_only=True)
    full_shipping_address = serializers.CharField(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "user",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "full_shipping_address",
            "total_orders",
            "total_spent",
            "created_at",
        ]
        read_only_fields = ["id", "total_orders", "total_spent", "created_at"]


class ArtisanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for artisan listings."""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = ArtisanProfile
        fields = [
            "id",
            "user_name",
            "avatar",
            "shop_name",
            "slug",
            "tagline",
            "location_city",
            "location_country",
            "average_rating",
            "total_reviews",
            "total_sales",
            "is_verified",
            "is_featured",
        ]
