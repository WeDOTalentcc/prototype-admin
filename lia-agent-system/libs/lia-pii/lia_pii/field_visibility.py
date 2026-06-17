# app/shared/rbac/pii_field_resolver.py
"""Resolve effective per-field PII visibility for a user.

Precedence (per field): user override > role default > legacy bucket grant > show (True).
Pure function — no DB access; callers pass role_defaults loaded from CompanyHiringPolicy.
"""
from __future__ import annotations

from lia_pii.field_catalog import GATEABLE_PII_FIELDS, field_group


def _role_str(user) -> str:
    role = getattr(user, "role", None)
    return role.value if hasattr(role, "value") else (str(role) if role is not None else "")


def _legacy_bucket_value(user, field: str) -> bool:
    group = field_group(field)
    if group == "salary":
        return bool(getattr(user, "can_view_salary", False))
    if group == "sensitive":
        return bool(getattr(user, "can_view_sensitive_pii", True))
    return True


def resolve_field_visibility(user, role_defaults: dict, field: str, default: bool = True) -> bool:
    """Resolve a single field's visibility. Precedence: user override > role default > default.

    Generic single-field helper reused by both candidate PII and vacancy fields.
    """
    user_override = getattr(user, "pii_field_visibility", None) or {}
    if field in user_override:
        return bool(user_override[field])
    role_map = (role_defaults or {}).get(_role_str(user), {}) or {}
    if field in role_map:
        return bool(role_map[field])
    return default


def resolve_pii_field_visibility(user, role_defaults: dict[str, dict[str, bool]]) -> dict[str, bool]:
    """Return {field: can_view_bool} for every gateable PII field."""
    user_override = getattr(user, "pii_field_visibility", None) or {}
    role_map = (role_defaults or {}).get(_role_str(user), {}) or {}

    effective: dict[str, bool] = {}
    for field in GATEABLE_PII_FIELDS:
        if field in user_override:
            effective[field] = bool(user_override[field])
        elif field in role_map:
            effective[field] = bool(role_map[field])
        else:
            effective[field] = _legacy_bucket_value(user, field)
    return effective
