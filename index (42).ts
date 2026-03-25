"""
Request logging middleware for HandCraft.

Logs method, path, status code, and response time for every request.
Useful for monitoring and debugging in all environments.
"""

import logging
import time

logger = logging.getLogger("handcraft.requests")


class RequestLoggingMiddleware:
    """
    Middleware that logs each HTTP request with timing information.

    Add to MIDDLEWARE in settings:
        'middleware.request_logging.RequestLoggingMiddleware'
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()

        # Attach start time so views can read it if needed
        request._request_start_time = start_time

        response = self.get_response(request)

        duration_ms = (time.monotonic() - start_time) * 1000

        user_repr = (
            str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else "anonymous"
        )

        logger.info(
            "%s %s %s %dms user=%s",
            request.method,
            request.get_full_path(),
            response.status_code,
            int(duration_ms),
            user_repr,
        )

        # Expose timing in a response header (useful for front-end dev tools)
        response["X-Request-Duration-Ms"] = f"{duration_ms:.0f}"

        return response
