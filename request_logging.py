"""
URL patterns for the reviews app.
"""

from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    # Product reviews
    path(
        "products/<slug:product_slug>/",
        views.ProductReviewListView.as_view(),
        name="product-review-list",
    ),
    path(
        "products/<slug:product_slug>/create/",
        views.ProductReviewCreateView.as_view(),
        name="product-review-create",
    ),
    path(
        "products/<slug:product_slug>/stats/",
        views.ReviewStatsView.as_view(),
        name="product-review-stats",
    ),
    # Individual reviews
    path(
        "<uuid:pk>/update/",
        views.ReviewUpdateView.as_view(),
        name="review-update",
    ),
    path(
        "<uuid:pk>/delete/",
        views.ReviewDeleteView.as_view(),
        name="review-delete",
    ),
    path(
        "<uuid:pk>/reply/",
        views.ArtisanReplyView.as_view(),
        name="review-reply",
    ),
    path(
        "<uuid:pk>/helpful/",
        views.MarkReviewHelpfulView.as_view(),
        name="review-helpful",
    ),
]
