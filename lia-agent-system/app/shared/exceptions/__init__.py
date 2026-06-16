"""Canonical, named exceptions used across LIA shared services."""
from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)

__all__ = [
    "InvalidCompanyIdError",
    "MissingTenantContextError",
]
