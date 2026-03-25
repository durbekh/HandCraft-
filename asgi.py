"""
Serializers for the products app.
"""

from rest_framework import serializers

from apps.accounts.serializers import ArtisanListSerializer

from .models import Category, CustomOrder, Product, ProductImage, Tag


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""

    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "children",
            "product_count",
            "sort_order",
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True, status="active").count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for product tags."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "sort_order"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings."""

    artisan_name = serializers.CharField(
        source="artisan.get_full_name", read_only=True
    )
    artisan_shop = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    primary_image = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "price",
            "compare_at_price",
            "is_on_sale",
            "discount_percentage",
            "artisan",
            "artisan_name",
            "artisan_shop",
            "category",
            "category_name",
            "primary_image",
            "average_rating",
            "total_reviews",
            "total_sales",
            "is_free_shipping",
            "is_featured",
            "stock_quantity",
            "created_at",
        ]

    def get_artisan_shop(self, obj):
        try:
            return obj.artisan.artisan_profile.shop_name
        except Exception:
            return None

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        if primary:
            return ProductImageSerializer(primary).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail view."""

    artisan_profile = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    effective_shipping_price = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "short_description",
            "price",
            "compare_at_price",
            "is_on_sale",
            "discount_percentage",
            "stock_quantity",
            "sku",
            "weight_grams",
            "length_cm",
            "width_cm",
            "height_cm",
            "materials",
            "processing_time_days",
            "shipping_price",
            "is_free_shipping",
            "effective_shipping_price",
            "is_customizable",
            "customization_instructions",
            "status",
            "is_featured",
            "average_rating",
            "total_reviews",
            "total_sales",
            "view_count",
            "artisan",
            "artisan_profile",
            "category",
            "tags",
            "images",
            "created_at",
            "updated_at",
        ]

    def get_artisan_profile(self, obj):
        try:
            profile = obj.artisan.artisan_profile
            return ArtisanListSerializer(profile).data
        except Exception:
            return None


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "title",
            "description",
            "short_description",
            "price",
            "compare_at_price",
            "cost_per_item",
            "stock_quantity",
            "sku",
            "weight_grams",
            "length_cm",
            "width_cm",
            "height_cm",
            "materials",
            "processing_time_days",
            "shipping_price",
            "is_free_shipping",
            "is_customizable",
            "customization_instructions",
            "category",
            "tags",
            "status",
            "images",
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        compare_at_price = attrs.get("compare_at_price")
        price = attrs.get("price", getattr(self.instance, "price", None))
        if compare_at_price and price and compare_at_price <= price:
            raise serializers.ValidationError(
                {
                    "compare_at_price": "Compare-at price must be greater than the selling price."
                }
            )
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        validated_data["artisan"] = self.context["request"].user
        product = Product.objects.create(**validated_data)
        product.tags.set(tags)
        return product

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class ProductImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading product images."""

    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary", "sort_order"]

    def validate(self, attrs):
        product = self.context.get("product")
        if product and product.images.count() >= 10:
            raise serializers.ValidationError(
                "Maximum of 10 images per product."
            )
        return attrs


class CustomOrderSerializer(serializers.ModelSerializer):
    """Serializer for custom order templates."""

    artisan_name = serializers.CharField(
        source="artisan.get_full_name", read_only=True
    )

    class Meta:
        model = CustomOrder
        fields = [
            "id",
            "artisan",
            "artisan_name",
            "title",
            "description",
            "base_price",
            "max_price",
            "estimated_days",
            "category",
            "example_image",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "artisan", "created_at"]

    def create(self, validated_data):
        validated_data["artisan"] = self.context["request"].user
        return super().create(validated_data)
