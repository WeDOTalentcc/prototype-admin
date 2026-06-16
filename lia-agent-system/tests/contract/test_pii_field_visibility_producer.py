# tests/contract/test_pii_field_visibility_producer.py
from types import SimpleNamespace
from app.api.v1.candidates.candidates_crud import apply_pii_field_visibility

def _user(role="manager", can_salary=False, can_sensitive=True, override=None):
    return SimpleNamespace(role=role, can_view_salary=can_salary,
                           can_view_sensitive_pii=can_sensitive,
                           pii_field_visibility=override, id="u1", email="u@x.com")

def _cand():
    return {"cpf": "123", "date_of_birth": "1990-01-01", "current_salary": 5000,
            "email": "c@x.com", "phone": "+551199", "address_street": "Rua X",
            "personal_emails": ["a@x.com"], "salary_currency": "BRL"}

def test_role_default_hides_cpf_keeps_address():
    role_defaults = {"manager": {"cpf": False}}
    out = apply_pii_field_visibility(_cand(), _user(role="manager"), role_defaults)
    assert out["cpf"] is None
    assert out["address_street"] == "Rua X"
    assert out["email"] == "c@x.com"

def test_salary_hidden_by_legacy_bucket():
    out = apply_pii_field_visibility(_cand(), _user(can_salary=False), role_defaults={})
    assert out["current_salary"] is None
    assert out["salary_masked"] is True

def test_user_override_shows_cpf_despite_role_default():
    role_defaults = {"manager": {"cpf": False}}
    out = apply_pii_field_visibility(_cand(), _user(role="manager", override={"cpf": True}), role_defaults)
    assert out["cpf"] == "123"

def test_list_field_becomes_empty_when_hidden():
    role_defaults = {"recruiter": {"personal_emails": False}}
    out = apply_pii_field_visibility(_cand(), _user(role="recruiter"), role_defaults)
    assert out["personal_emails"] == []
