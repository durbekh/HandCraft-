"""
URL patterns for the accounts app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Current user
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    path(
        "me/change-password/",
        views.ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "me/customer-profile/",
        views.CustomerProfileUpdateView.as_view(),
        name="customer-profile",
    ),
    path(
        "me/artisan-profile/",
        views.ArtisanProfileUpdateView.as_view(),
        name="artisan-profile-update",
    ),
    # Artisan profiles (public)
    path("artisans/", views.ArtisanListView.as_view(), name="artisan-list"),
    path(
        "artisans/<slug:slug>/",
        views.ArtisanDetailView.as_view(),
        name="artisan-detail",
    ),
]
