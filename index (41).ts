"""
IP-based rate-limiting middleware for HandCraft.

Provides a secondary layer on top of DRF throttling, acting at the
middleware level to block clearly abusive traffic before it reaches views.
"""

import logging
import time
from collections import defaultdict
from threading import Lock

from django.http import JsonResponse

logger = logging.getLogger("handcraft.ratelimit")

# In-memory store (replace with Redis in production for multi-process)
_request_log = defaultdict(list)
_lock = Lock()

# Defaults (can be overridden via settings)
DEFAULT_RATE_LIMIT = 300          # max requests per window
DEFAULT_RATE_WINDOW_SECONDS = 60  # window size in seconds
BLOCK_DURATION_SECONDS = 120      # how long to block after exceeding limit

_blocked_ips = {}


class RateLimitMiddleware:
    """
    Middleware-level rate limiter that blocks IPs exceeding a request
    threshold within a rolling time window.

    Add to MIDDLEWARE in settings:
        'middleware.rate_limit.RateLimitMiddleware'

    Configure via settings (optional):
        RATE_LIMIT_MAX_REQUESTS = 300
        RATE_LIMIT_WINDOW_SECONDS = 60
        RATE_LIMIT_BLOCK_SECONDS = 120
    """

    def __init__(self, get_response):
        self.get_response = get_response

        from django.conf import settings
        self.max_requests = getattr(settings, "RATE_LIMIT_MAX_REQUESTS", DEFAULT_RATE_LIMIT)
        self.window = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", DEFAULT_RATE_WINDOW_SECONDS)
        self.block_duration = getattr(settings, "RATE_LIMIT_BLOCK_SECONDS", BLOCK_DURATION_SECONDS)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def __call__(self, request):
        ip = self._get_client_ip(request)
        now = time.time()

        # Check if IP is currently blocked
        if ip in _blocked_ips:
            if now < _blocked_ips[ip]:
                logger.warning("Blocked request from rate-limited IP: %s", ip)
                return JsonResponse(
                    {
                        "error": True,
                        "message": "Too many requests. Please try again later.",
                        "status_code": 429,
                    },
                    status=429,
                )
            else:
                # Block expired
                del _blocked_ips[ip]

        # Record the request timestamp
        with _lock:
            cutoff = now - self.window
            _request_log[ip] = [t for t in _request_log[ip] if t > cutoff]
            _request_log[ip].append(now)
            request_count = len(_request_log[ip])

        if request_count > self.max_requests:
            _blocked_ips[ip] = now + self.block_duration
            logger.warning(
                "Rate limit exceeded for IP %s (%d requests in %ds). Blocked for %ds.",
                ip,
                request_count,
                self.window,
                self.block_duration,
            )
            return JsonResponse(
                {
                    "error": True,
                    "message": "Too many requests. Please try again later.",
                    "status_code": 429,
                },
                status=429,
            )

        response = self.get_response(request)
        response["X-RateLimit-Remaining"] = max(0, self.max_requests - request_count)
        return response
