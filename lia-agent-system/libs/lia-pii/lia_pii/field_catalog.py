# app/shared/rbac/pii_field_catalog.py
"""Canonical catalog of gateable candidate PII fields (single source of truth).

Mirrors the legacy buckets in candidates_crud.py (_SALARY_FIELDS / _SENSITIVE_PII_FIELDS)
so field-level visibility stays backward-compatible with the Sprint 5/8 boolean grants.
Primary contacts (email/phone/mobile/name) are NEVER gateable (decisão Paulo 2026-06-06).
"""
from __future__ import annotations

SALARY_FIELDS = (
    "current_salary",
    "desired_salary_min",
    "desired_salary_max",
    "salary_expectation_clt",
    "salary_expectation_pj",
    "salary_expectation_freelance",
)

SENSITIVE_FIELDS = (
    "cpf",
    "date_of_birth",
    "address_street",
    "address_number",
    "address_zip",
    "address_complement",
    "secondary_email",
    "secondary_phone",
    "personal_emails",
    "business_emails",
    "best_personal_email",
    "best_business_email",
)

GATEABLE_PII_FIELDS = SALARY_FIELDS + SENSITIVE_FIELDS

ALWAYS_VISIBLE_FIELDS = ("email", "phone", "mobile_phone", "name", "salary_currency")

_GROUP_BY_FIELD = {**{f: "salary" for f in SALARY_FIELDS},
                   **{f: "sensitive" for f in SENSITIVE_FIELDS}}

# Vacancy-level configurable fields — separate from candidate PII to avoid
# polluting candidate redaction logic. Same storage maps (pii_field_visibility,
# pii_visibility_defaults) — just an extra key.
VACANCY_FIELDS = ("vacancy_salary",)

# All fields accepted by the PII visibility matrix (candidate-PII + vacancy data).
# Validators for pii-visibility-defaults endpoints use this (not GATEABLE_PII_FIELDS).
ALL_CONFIGURABLE_FIELDS = GATEABLE_PII_FIELDS + VACANCY_FIELDS

_GROUP_BY_FIELD = {**_GROUP_BY_FIELD, **{f: "vacancy" for f in VACANCY_FIELDS}}


def field_group(field: str) -> str | None:
    """Return the group (salary|sensitive|vacancy) for a field, or None if always-visible."""
    return _GROUP_BY_FIELD.get(field)
