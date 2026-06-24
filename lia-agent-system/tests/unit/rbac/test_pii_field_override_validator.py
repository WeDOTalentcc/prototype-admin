# tests/unit/rbac/test_pii_field_override_validator.py
import pytest
from fastapi import HTTPException
from app.api.v1.pii_visibility_defaults import validate_pii_field_override

def test_accepts_valid_flat_map():
    validate_pii_field_override({"cpf": False, "current_salary": True})  # no raise

def test_rejects_unknown_field():
    with pytest.raises(HTTPException) as e:
        validate_pii_field_override({"nope": False})
    assert e.value.status_code == 422

def test_rejects_non_bool():
    with pytest.raises(HTTPException) as e:
        validate_pii_field_override({"cpf": "no"})
    assert e.value.status_code == 422

def test_accepts_empty():
    validate_pii_field_override({})  # no raise (clears override)
