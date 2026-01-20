"""Integration tests for authentication module."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegistration:
    """Integration tests for user registration."""

    def test_register_user(self, api_client):
        """Test user registration."""
        url = reverse("authentication:register")
        data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newuser@example.com"
        assert "password" not in response.data

        # Verify user was created
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_duplicate_email(self, api_client, user):
        """Test that duplicate emails are rejected."""
        url = reverse("authentication:register")
        data = {
            "email": user.email,
            "password": "securepass123",
            "password_confirm": "securepass123",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        """Test that mismatched passwords are rejected."""
        url = reverse("authentication:register")
        data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "differentpass",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMe:
    """Integration tests for /me endpoint."""

    def test_get_me(self, authenticated_client, user):
        """Test getting current user profile."""
        url = reverse("authentication:me")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_update_me(self, authenticated_client, user):
        """Test updating current user profile."""
        url = reverse("authentication:me")
        data = {"first_name": "Updated"}

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_get_me_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("authentication:me")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordChange:
    """Integration tests for password change."""

    def test_change_password(self, authenticated_client, user):
        """Test changing password."""
        url = reverse("authentication:password-change")
        data = {
            "current_password": "testpass123",
            "new_password": "newsecurepass456",
            "new_password_confirm": "newsecurepass456",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password("newsecurepass456")

    def test_change_password_wrong_current(self, authenticated_client):
        """Test that wrong current password is rejected."""
        url = reverse("authentication:password-change")
        data = {
            "current_password": "wrongpassword",
            "new_password": "newsecurepass456",
            "new_password_confirm": "newsecurepass456",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
