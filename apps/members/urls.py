"""URL configuration for members module."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.members.views import (
    InvitationAcceptView,
    InvitationViewSet,
    MemberViewSet,
    MyMembershipsView,
)

app_name = "members"

router = DefaultRouter()
router.register("", MemberViewSet, basename="member")
router.register("invitations", InvitationViewSet, basename="invitation")

urlpatterns = [
    # User's memberships across all tenants
    path("my/", MyMembershipsView.as_view(), name="my-memberships"),
    # Public invitation acceptance endpoint
    path("invite/<str:token>/", InvitationAcceptView.as_view(), name="accept-invitation"),
    # Tenant-scoped endpoints
    path("", include(router.urls)),
]
