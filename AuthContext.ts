"""
Custom pagination classes for HandCraft API.

Referenced in settings.base REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'].
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard paginator used across the API.

    Supports `page` and `page_size` query parameters.
    Clients can request up to 100 items per page.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "example": 123,
                },
                "total_pages": {
                    "type": "integer",
                    "example": 7,
                },
                "current_page": {
                    "type": "integer",
                    "example": 1,
                },
                "page_size": {
                    "type": "integer",
                    "example": 20,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://api.example.org/items/?page=2",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://api.example.org/items/?page=1",
                },
                "results": schema,
            },
        }


class SmallResultsSetPagination(PageNumberPagination):
    """Smaller page size for endpoints like messages or notifications."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class LargeResultsSetPagination(PageNumberPagination):
    """Larger page size for catalog-heavy endpoints."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
