"""Type aliases for common types."""
from __future__ import annotations

from typing import NewType
from uuid import UUID

# Typed IDs for better type safety
TenantId = NewType("TenantId", UUID)
UserId = NewType("UserId", UUID)
MemberId = NewType("MemberId", UUID)
InviteId = NewType("InviteId", UUID)
PlanId = NewType("PlanId", str)
FeatureCode = NewType("FeatureCode", str)
