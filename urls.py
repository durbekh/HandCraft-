"""
Custom permissions for the accounts app.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsArtisan(BasePermission):
    """Allow access only to users with the artisan role."""

    message = "You must be an artisan to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_artisan
        )


class IsCustomer(BasePermission):
    """Allow access only to users with the customer role."""

    message = "You must be a customer to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_customer
        )


class IsAdminUser(BasePermission):
    """Allow access only to admin users."""

    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: allow owners to edit, everyone else read-only.
    Expects the object to have a 'user' attribute or an 'artisan' attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Check for direct user ownership
        if hasattr(obj, "user"):
            return obj.user == request.user
        # Check for artisan ownership (e.g., products)
        if hasattr(obj, "artisan"):
            return obj.artisan == request.user
        # Check for customer ownership (e.g., orders)
        if hasattr(obj, "customer"):
            return obj.customer == request.user
        return False


class IsArtisanOwnerOrReadOnly(BasePermission):
    """
    Allow artisan owners to modify their products; read-only for everyone else.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and request.user.is_artisan
            and obj.artisan == request.user
        )


class IsOrderParticipant(BasePermission):
    """Allow access to order only for the buyer or the artisan involved."""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return obj.customer == request.user or obj.artisan == request.user
