"""Shared app - common utilities used across all modules.

This module provides:
- Base models with common fields
- Role and permission definitions
- Tenant context middleware
- Email backends with graceful degradation
- Health check endpoints
"""

from __future__ import annotations

from .roles import Permission, Role, has_permission

__all__ = [
    "Permission",
    "Role",
    "has_permission",
]
