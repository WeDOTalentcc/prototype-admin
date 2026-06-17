# app/shared/rbac/pii_field_catalog.py
"""PII field catalog — shim de retrocompatibilidade.

EXTRACTED TO: libs/lia-pii/lia_pii/field_catalog.py  (G10-pii, 2026-06-13)

Re-exports all symbols. Migrate consumers to:
    from lia_pii.field_catalog import GATEABLE_PII_FIELDS, field_group, ...
"""
# noqa: F401, F403
from lia_pii.field_catalog import *  # noqa: F401, F403
from lia_pii.field_catalog import (
    ALL_CONFIGURABLE_FIELDS,
    ALWAYS_VISIBLE_FIELDS,
    GATEABLE_PII_FIELDS,
    SALARY_FIELDS,
    SENSITIVE_FIELDS,
    VACANCY_FIELDS,
    field_group,
)

__all__ = [
    "ALL_CONFIGURABLE_FIELDS",
    "ALWAYS_VISIBLE_FIELDS",
    "GATEABLE_PII_FIELDS",
    "SALARY_FIELDS",
    "SENSITIVE_FIELDS",
    "VACANCY_FIELDS",
    "field_group",
]
