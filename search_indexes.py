"""
Serializers for the orders app.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product

from .models import CustomOrderRequest, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""

    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "artisan",
            "product_title",
            "product_image_url",
            "quantity",
            "unit_price",
            "shipping_price",
            "customization_note",
            "item_status",
            "line_total",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "artisan",
            "product_title",
            "product_image_url",
            "unit_price",
            "shipping_price",
            "created_at",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listings."""

    items_count = serializers.SerializerMethodField()
    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "status",
            "payment_status",
            "subtotal",
            "shipping_total",
            "total",
            "items_count",
            "created_at",
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full serializer for order detail view."""

    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    is_cancellable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "status",
            "payment_status",
            "shipping_name",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "subtotal",
            "shipping_total",
            "tax_amount",
            "discount_amount",
            "total",
            "tracking_number",
            "tracking_url",
            "carrier",
            "customer_note",
            "items",
            "is_cancellable",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
            "completed_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]


class CartItemInputSerializer(serializers.Serializer):
    """Serializer for individual cart items during checkout."""

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    customization_note = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an order from cart items."""

    items = CartItemInputSerializer(many=True, min_length=1)
    shipping_name = serializers.CharField(max_length=200)
    shipping_address_line1 = serializers.CharField(max_length=255)
    shipping_address_line2 = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    shipping_city = serializers.CharField(max_length=100)
    shipping_state = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    shipping_postal_code = serializers.CharField(max_length=20)
    shipping_country = serializers.CharField(max_length=100)
    customer_note = serializers.CharField(
        required=False, allow_blank=True, max_length=2000
    )

    def validate_items(self, items):
        """Validate stock availability for all items."""
        product_ids = [item["product_id"] for item in items]
        products = Product.objects.filter(
            id__in=product_ids, is_active=True, status=Product.Status.ACTIVE
        )
        product_map = {str(p.id): p for p in products}

        errors = []
        for item in items:
            pid = str(item["product_id"])
            if pid not in product_map:
                errors.append(f"Product {pid} is not available.")
                continue
            product = product_map[pid]
            if product.stock_quantity < item["quantity"]:
                errors.append(
                    f'Insufficient stock for "{product.title}". '
                    f"Available: {product.stock_quantity}."
                )
        if errors:
            raise serializers.ValidationError(errors)
        return items

    def create(self, validated_data):
        """Create order with order items and update stock."""
        items_data = validated_data.pop("items")
        customer = self.context["request"].user

        order = Order.objects.create(customer=customer, **validated_data)

        for item_data in items_data:
            product = Product.objects.select_for_update().get(
                id=item_data["product_id"]
            )
            primary_image = product.images.filter(is_primary=True).first()
            image_url = ""
            if primary_image and primary_image.image:
                image_url = primary_image.image.url
            elif product.images.exists():
                first_img = product.images.first()
                image_url = first_img.image.url if first_img.image else ""

            OrderItem.objects.create(
                order=order,
                product=product,
                artisan=product.artisan,
                product_title=product.title,
                product_image_url=image_url,
                quantity=item_data["quantity"],
                unit_price=product.price,
                shipping_price=product.effective_shipping_price,
                customization_note=item_data.get("customization_note", ""),
            )

            # Decrease stock
            product.stock_quantity -= item_data["quantity"]
            product.total_sales += item_data["quantity"]
            if product.stock_quantity <= 0:
                product.stock_quantity = 0
                product.status = Product.Status.SOLD_OUT
            product.save(
                update_fields=["stock_quantity", "total_sales", "status"]
            )

        order.calculate_totals()
        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""

    status = serializers.ChoiceField(choices=Order.Status.choices)
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    tracking_url = serializers.URLField(required=False, allow_blank=True)
    carrier = serializers.CharField(required=False, allow_blank=True)
    internal_note = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        """Validate status transitions."""
        order = self.context.get("order")
        if not order:
            return value

        valid_transitions = {
            Order.Status.PENDING: [
                Order.Status.CONFIRMED,
                Order.Status.CANCELLED,
            ],
            Order.Status.CONFIRMED: [
                Order.Status.PROCESSING,
                Order.Status.CANCELLED,
            ],
            Order.Status.PROCESSING: [
                Order.Status.SHIPPED,
                Order.Status.CANCELLED,
            ],
            Order.Status.SHIPPED: [
                Order.Status.DELIVERED,
            ],
            Order.Status.DELIVERED: [
                Order.Status.COMPLETED,
                Order.Status.REFUNDED,
            ],
            Order.Status.COMPLETED: [
                Order.Status.REFUNDED,
            ],
        }

        allowed = valid_transitions.get(order.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from '{order.get_status_display()}' "
                f"to '{dict(Order.Status.choices).get(value)}'."
            )
        return value

    def update(self, order, validated_data):
        new_status = validated_data["status"]
        now = timezone.now()

        order.status = new_status
        if new_status == Order.Status.CONFIRMED:
            order.confirmed_at = now
        elif new_status == Order.Status.SHIPPED:
            order.shipped_at = now
            order.tracking_number = validated_data.get(
                "tracking_number", order.tracking_number
            )
            order.tracking_url = validated_data.get(
                "tracking_url", order.tracking_url
            )
            order.carrier = validated_data.get("carrier", order.carrier)
        elif new_status == Order.Status.DELIVERED:
            order.delivered_at = now
        elif new_status == Order.Status.COMPLETED:
            order.completed_at = now
        elif new_status == Order.Status.CANCELLED:
            order.cancelled_at = now
            # Restore stock for cancelled orders
            for item in order.items.all():
                if item.product:
                    item.product.stock_quantity += item.quantity
                    if item.product.status == Product.Status.SOLD_OUT:
                        item.product.status = Product.Status.ACTIVE
                    item.product.save(update_fields=["stock_quantity", "status"])

        if validated_data.get("internal_note"):
            order.internal_note = validated_data["internal_note"]

        order.save()
        return order


class CustomOrderRequestSerializer(serializers.ModelSerializer):
    """Serializer for custom order requests."""

    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    artisan_name = serializers.CharField(
        source="artisan.get_full_name", read_only=True
    )

    class Meta:
        model = CustomOrderRequest
        fields = [
            "id",
            "customer",
            "customer_name",
            "artisan",
            "artisan_name",
            "custom_order_template",
            "linked_order",
            "title",
            "description",
            "reference_image",
            "budget_min",
            "budget_max",
            "desired_delivery_date",
            "quoted_price",
            "quoted_days",
            "artisan_note",
            "status",
            "quoted_at",
            "accepted_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "linked_order",
            "quoted_price",
            "quoted_days",
            "artisan_note",
            "status",
            "quoted_at",
            "accepted_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


class CustomOrderQuoteSerializer(serializers.Serializer):
    """Serializer for artisan quoting on a custom order request."""

    quoted_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.01
    )
    quoted_days = serializers.IntegerField(min_value=1)
    artisan_note = serializers.CharField(
        required=False, allow_blank=True, max_length=2000
    )
