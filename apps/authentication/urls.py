"""URL configuration for authentication module."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.authentication.views import (
    MeView,
    PasswordChangeView,
    RegistrationView,
    SessionViewSet,
    UserViewSet,
)

app_name = "authentication"

router = DefaultRouter()
router.register("sessions", SessionViewSet, basename="session")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("", include(router.urls)),
]
