# tests/unit/rbac/test_pii_field_resolver.py
from types import SimpleNamespace
from app.shared.rbac.pii_field_resolver import resolve_pii_field_visibility
from app.shared.rbac.pii_field_catalog import GATEABLE_PII_FIELDS

def _user(role="recruiter", can_salary=False, can_sensitive=True, override=None):
    return SimpleNamespace(role=role, can_view_salary=can_salary,
                           can_view_sensitive_pii=can_sensitive,
                           pii_field_visibility=override)

def test_default_recruiter_legacy_buckets():
    eff = resolve_pii_field_visibility(_user(can_salary=False, can_sensitive=True), role_defaults={})
    assert eff["current_salary"] is False
    assert eff["cpf"] is True
    assert set(eff.keys()) == set(GATEABLE_PII_FIELDS)

def test_role_default_overrides_legacy_bucket():
    role_defaults = {"manager": {"cpf": False}}
    eff = resolve_pii_field_visibility(_user(role="manager", can_sensitive=True), role_defaults)
    assert eff["cpf"] is False
    assert eff["date_of_birth"] is True

def test_user_override_wins_over_role_default():
    role_defaults = {"manager": {"cpf": False}}
    eff = resolve_pii_field_visibility(_user(role="manager", override={"cpf": True}), role_defaults)
    assert eff["cpf"] is True

def test_partial_override_falls_through_per_field():
    role_defaults = {"recruiter": {"current_salary": False, "cpf": False}}
    eff = resolve_pii_field_visibility(_user(role="recruiter", override={"current_salary": True}), role_defaults)
    assert eff["current_salary"] is True
    assert eff["cpf"] is False

def test_admin_role_default_show_all_when_unset():
    eff = resolve_pii_field_visibility(_user(role="admin", can_salary=True, can_sensitive=True), role_defaults={})
    assert all(eff[f] is True for f in GATEABLE_PII_FIELDS)
