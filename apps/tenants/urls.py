"""URL configuration for tenants module."""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tenants.views import TenantViewSet

app_name = "tenants"

router = DefaultRouter()
router.register("", TenantViewSet, basename="tenant")

urlpatterns = [
    path("", include(router.urls)),
]
