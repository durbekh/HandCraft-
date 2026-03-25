"""
URL patterns for the orders app.
"""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # Orders
    path("", views.OrderListView.as_view(), name="order-list"),
    path("create/", views.OrderCreateView.as_view(), name="order-create"),
    path("<uuid:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "<uuid:pk>/status/",
        views.OrderStatusUpdateView.as_view(),
        name="order-status-update",
    ),
    path(
        "<uuid:pk>/cancel/",
        views.CustomerOrderCancelView.as_view(),
        name="order-cancel",
    ),
    # Custom order requests
    path(
        "custom-requests/",
        views.CustomOrderRequestListView.as_view(),
        name="custom-request-list",
    ),
    path(
        "custom-requests/<uuid:pk>/",
        views.CustomOrderRequestDetailView.as_view(),
        name="custom-request-detail",
    ),
    path(
        "custom-requests/<uuid:pk>/quote/",
        views.CustomOrderQuoteView.as_view(),
        name="custom-request-quote",
    ),
    path(
        "custom-requests/<uuid:pk>/accept/",
        views.CustomOrderAcceptView.as_view(),
        name="custom-request-accept",
    ),
    path(
        "custom-requests/<uuid:pk>/decline/",
        views.CustomOrderDeclineView.as_view(),
        name="custom-request-decline",
    ),
]
