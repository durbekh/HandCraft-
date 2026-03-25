"""
URL patterns for the products app.
"""

from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    # Products
    path("", views.ProductListView.as_view(), name="product-list"),
    path("create/", views.ProductCreateView.as_view(), name="product-create"),
    path("my/", views.MyProductListView.as_view(), name="my-products"),
    path("search/", views.ProductSearchView.as_view(), name="product-search"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path(
        "<slug:slug>/update/",
        views.ProductUpdateView.as_view(),
        name="product-update",
    ),
    path(
        "<slug:slug>/delete/",
        views.ProductDeleteView.as_view(),
        name="product-delete",
    ),
    # Product images
    path(
        "<uuid:product_id>/images/",
        views.ProductImageUploadView.as_view(),
        name="product-image-upload",
    ),
    path(
        "images/<uuid:pk>/delete/",
        views.ProductImageDeleteView.as_view(),
        name="product-image-delete",
    ),
    # Artisan products
    path(
        "artisan/<uuid:artisan_id>/",
        views.ArtisanProductListView.as_view(),
        name="artisan-products",
    ),
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    # Tags
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    # Custom orders
    path(
        "custom-orders/",
        views.CustomOrderListView.as_view(),
        name="custom-order-list",
    ),
    path(
        "custom-orders/<uuid:pk>/",
        views.CustomOrderDetailView.as_view(),
        name="custom-order-detail",
    ),
]
