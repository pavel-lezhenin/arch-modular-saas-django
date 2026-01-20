"""URL configuration for features module."""
from __future__ import annotations

from django.urls import path

from apps.features.views import FeatureCheckView, FeatureListView, TenantFeaturesView

app_name = "features"

urlpatterns = [
    # List all available features
    path("", FeatureListView.as_view(), name="list"),
    # Tenant feature management
    path("tenant/", TenantFeaturesView.as_view(), name="tenant-features"),
    # Check specific feature
    path("check/<str:feature_code>/", FeatureCheckView.as_view(), name="check"),
]
