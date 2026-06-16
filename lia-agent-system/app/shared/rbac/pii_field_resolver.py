# app/shared/rbac/pii_field_resolver.py
"""PII field resolver — shim de retrocompatibilidade.

EXTRACTED TO: libs/lia-pii/lia_pii/field_visibility.py  (G10-pii, 2026-06-13)

Re-exports all symbols. Migrate consumers to:
    from lia_pii.field_visibility import resolve_pii_field_visibility, ...
"""
# noqa: F401, F403
from lia_pii.field_visibility import *  # noqa: F401, F403
from lia_pii.field_visibility import (
    resolve_field_visibility,
    resolve_pii_field_visibility,
)

__all__ = [
    "resolve_field_visibility",
    "resolve_pii_field_visibility",
]
