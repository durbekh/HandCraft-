"""
Custom exception handling for HandCraft API.

Referenced in settings.base REST_FRAMEWORK['EXCEPTION_HANDLER'].
Provides consistent error response formatting.
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that normalises all error responses into:
        {
            "error": True,
            "message": "...",
            "errors": { ... }   # field-level, when applicable
            "status_code": 400
        }
    """
    # Let DRF handle the core logic first
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception -- log and return generic 500
        view = context.get("view", None)
        logger.exception(
            "Unhandled exception in %s: %s",
            view.__class__.__name__ if view else "unknown",
            str(exc),
        )
        return Response(
            {
                "error": True,
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalise validation errors
    errors = {}
    message = "An error occurred."

    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            message = str(detail)
        else:
            # Field-level errors
            errors = response.data
            message = "Validation failed."
    elif isinstance(response.data, list):
        message = " ".join(str(item) for item in response.data)

    response.data = {
        "error": True,
        "message": message,
        "status_code": response.status_code,
    }
    if errors:
        response.data["errors"] = errors

    return response


class ServiceUnavailableError(APIException):
    """Raised when an external service (payment gateway, email, etc.) is down."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable. Please try again later."
    default_code = "service_unavailable"


class InsufficientStockError(APIException):
    """Raised when a product does not have enough stock for the order."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Insufficient stock to fulfil this order."
    default_code = "insufficient_stock"


class PaymentFailedError(APIException):
    """Raised when a payment attempt fails."""

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Payment processing failed. Please try another method."
    default_code = "payment_failed"
