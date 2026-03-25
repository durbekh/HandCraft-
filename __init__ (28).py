"""
Views for the orders app.
"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsArtisan, IsOrderParticipant

from .models import CustomOrderRequest, Order
from .serializers import (
    CustomOrderQuoteSerializer,
    CustomOrderRequestSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
)
from .tasks import send_order_confirmation_email, send_order_status_update_email


class OrderListView(generics.ListAPIView):
    """List orders for the authenticated user (customer or artisan)."""

    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "payment_status"]
    ordering_fields = ["created_at", "total"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_artisan:
            # Artisan sees orders containing their items
            return Order.objects.filter(
                items__artisan=user
            ).distinct().prefetch_related("items")
        # Customer sees their own orders
        return Order.objects.filter(customer=user).prefetch_related("items")


class OrderDetailView(generics.RetrieveAPIView):
    """Get order detail. Accessible by the customer or involved artisan."""

    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_artisan:
            return Order.objects.filter(
                items__artisan=user
            ).distinct().prefetch_related("items")
        return Order.objects.filter(customer=user).prefetch_related("items")


class OrderCreateView(APIView):
    """Create a new order from cart items."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Send confirmation email asynchronously
        send_order_confirmation_email.delay(str(order.id))

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderStatusUpdateView(APIView):
    """Update order status (artisan or admin only)."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify permission: artisan of items in order, or the customer for cancellation
        user = request.user
        is_involved_artisan = order.items.filter(artisan=user).exists()
        is_customer = order.customer == user

        if not (is_involved_artisan or is_customer or user.is_admin_user):
            return Response(
                {"detail": "You do not have permission to update this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Customers can only cancel
        if is_customer and not is_involved_artisan:
            if request.data.get("status") != Order.Status.CANCELLED:
                return Response(
                    {"detail": "Customers can only cancel orders."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not order.is_cancellable:
                return Response(
                    {"detail": "This order can no longer be cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = OrderStatusUpdateSerializer(
            data=request.data, context={"order": order}
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.update(order, serializer.validated_data)

        # Send status update email
        send_order_status_update_email.delay(str(updated_order.id))

        return Response(OrderDetailSerializer(updated_order).data)


class CustomerOrderCancelView(APIView):
    """Cancel an order (customer only, before shipping)."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, customer=request.user)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not order.is_cancellable:
            return Response(
                {"detail": "This order can no longer be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderStatusUpdateSerializer(
            data={"status": Order.Status.CANCELLED},
            context={"order": order},
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.update(order, serializer.validated_data)

        send_order_status_update_email.delay(str(updated_order.id))

        return Response(
            {"message": "Order cancelled successfully."},
            status=status.HTTP_200_OK,
        )


# ─── Custom Order Requests ───────────────────────────────────────


class CustomOrderRequestListView(generics.ListCreateAPIView):
    """List and create custom order requests."""

    serializer_class = CustomOrderRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "artisan"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_artisan:
            return CustomOrderRequest.objects.filter(artisan=user)
        return CustomOrderRequest.objects.filter(customer=user)


class CustomOrderRequestDetailView(generics.RetrieveAPIView):
    """Get custom order request detail."""

    serializer_class = CustomOrderRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CustomOrderRequest.objects.filter(
            models.Q(customer=user) | models.Q(artisan=user)
        )


class CustomOrderQuoteView(APIView):
    """Artisan sends a quote for a custom order request."""

    permission_classes = [permissions.IsAuthenticated, IsArtisan]

    def post(self, request, pk):
        try:
            custom_request = CustomOrderRequest.objects.get(
                pk=pk, artisan=request.user
            )
        except CustomOrderRequest.DoesNotExist:
            return Response(
                {"detail": "Custom order request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if custom_request.status != CustomOrderRequest.Status.SUBMITTED:
            return Response(
                {"detail": "This request has already been quoted or closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CustomOrderQuoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        custom_request.quoted_price = serializer.validated_data["quoted_price"]
        custom_request.quoted_days = serializer.validated_data["quoted_days"]
        custom_request.artisan_note = serializer.validated_data.get(
            "artisan_note", ""
        )
        custom_request.status = CustomOrderRequest.Status.QUOTED
        custom_request.quoted_at = timezone.now()
        custom_request.expires_at = timezone.now() + timedelta(days=7)
        custom_request.save()

        return Response(
            CustomOrderRequestSerializer(custom_request).data,
            status=status.HTTP_200_OK,
        )


class CustomOrderAcceptView(APIView):
    """Customer accepts a quoted custom order."""

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            custom_request = CustomOrderRequest.objects.get(
                pk=pk, customer=request.user
            )
        except CustomOrderRequest.DoesNotExist:
            return Response(
                {"detail": "Custom order request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if custom_request.status != CustomOrderRequest.Status.QUOTED:
            return Response(
                {"detail": "This request is not in a quotable state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if custom_request.expires_at and custom_request.expires_at < timezone.now():
            custom_request.status = CustomOrderRequest.Status.EXPIRED
            custom_request.save(update_fields=["status"])
            return Response(
                {"detail": "This quote has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        custom_request.status = CustomOrderRequest.Status.ACCEPTED
        custom_request.accepted_at = timezone.now()
        custom_request.save(update_fields=["status", "accepted_at"])

        return Response(
            CustomOrderRequestSerializer(custom_request).data,
            status=status.HTTP_200_OK,
        )


class CustomOrderDeclineView(APIView):
    """Customer declines a quoted custom order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            custom_request = CustomOrderRequest.objects.get(
                pk=pk, customer=request.user
            )
        except CustomOrderRequest.DoesNotExist:
            return Response(
                {"detail": "Custom order request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if custom_request.status not in [
            CustomOrderRequest.Status.QUOTED,
            CustomOrderRequest.Status.SUBMITTED,
        ]:
            return Response(
                {"detail": "This request cannot be declined."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        custom_request.status = CustomOrderRequest.Status.DECLINED
        custom_request.save(update_fields=["status"])

        return Response(
            {"message": "Custom order request declined."},
            status=status.HTTP_200_OK,
        )
