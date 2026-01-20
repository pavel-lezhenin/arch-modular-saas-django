"""URL configuration for arch-modular-saas-django project."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Authentication (allauth)
    path("accounts/", include("allauth.urls")),
    # API Authentication (dj-rest-auth)
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    # API Documentation (public)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API endpoints
    path("api/tenants/", include("apps.tenants.urls")),
    path("api/users/", include("apps.authentication.urls")),
    path("api/members/", include("apps.members.urls")),
    path("api/billing/", include("apps.billing.urls")),
    path("api/features/", include("apps.features.urls")),
    # Health check
    path("health/", include("apps.shared.urls")),
]
