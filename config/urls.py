"""URL configuration for arch-modular-saas-django project."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Authentication (allauth)
    path("accounts/", include("allauth.urls")),
    # API endpoints
    path("api/", include("apps.tenants.urls")),
    path("api/", include("apps.authentication.urls")),
    path("api/", include("apps.members.urls")),
    path("api/", include("apps.billing.urls")),
    path("api/", include("apps.features.urls")),
    # Health check
    path("health/", include("apps.shared.urls")),
]
