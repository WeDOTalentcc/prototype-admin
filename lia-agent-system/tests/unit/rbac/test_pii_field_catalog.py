# tests/unit/rbac/test_pii_field_catalog.py
from app.shared.rbac.pii_field_catalog import (
    GATEABLE_PII_FIELDS, SALARY_FIELDS, SENSITIVE_FIELDS,
    ALWAYS_VISIBLE_FIELDS, field_group,
)

def test_salary_fields_match_legacy():
    assert SALARY_FIELDS == (
        "current_salary", "desired_salary_min", "desired_salary_max",
        "salary_expectation_clt", "salary_expectation_pj", "salary_expectation_freelance",
    )

def test_sensitive_fields_match_legacy():
    assert "cpf" in SENSITIVE_FIELDS and "date_of_birth" in SENSITIVE_FIELDS
    assert "personal_emails" in SENSITIVE_FIELDS

def test_gateable_is_union_of_groups():
    assert set(GATEABLE_PII_FIELDS) == set(SALARY_FIELDS) | set(SENSITIVE_FIELDS)

def test_primary_contacts_never_gateable():
    for f in ("email", "phone", "mobile_phone", "name", "salary_currency"):
        assert f in ALWAYS_VISIBLE_FIELDS
        assert f not in GATEABLE_PII_FIELDS

def test_field_group_maps_to_legacy_bucket():
    assert field_group("current_salary") == "salary"
    assert field_group("cpf") == "sensitive"
    assert field_group("email") is None
