"""URL configuration for tenants module."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.tenants.views import TenantViewSet

app_name = "tenants"

router = DefaultRouter()
router.register("", TenantViewSet, basename="tenant")

urlpatterns = router.urls
