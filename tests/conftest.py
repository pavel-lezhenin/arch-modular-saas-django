"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from django.test import Client
from rest_framework.test import APIClient


@pytest.fixture
def client() -> Client:
    """Django test client."""
    return Client()


@pytest.fixture
def api_client() -> APIClient:
    """DRF API test client."""
    return APIClient()
