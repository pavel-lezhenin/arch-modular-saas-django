"""Base models with common fields."""

from __future__ import annotations

import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base model with common fields.

    Provides:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
