# tests/contract/test_pii_visibility_defaults_endpoint.py
import pytest
from fastapi import HTTPException
from app.api.v1.pii_visibility_defaults import validate_pii_defaults

def test_accepts_valid_role_and_field():
    validate_pii_defaults({"manager": {"cpf": False}, "recruiter": {"current_salary": True}})  # no raise

def test_rejects_unknown_role():
    with pytest.raises(HTTPException) as e:
        validate_pii_defaults({"superuser": {"cpf": False}})
    assert e.value.status_code == 422

def test_rejects_unknown_field():
    with pytest.raises(HTTPException) as e:
        validate_pii_defaults({"manager": {"nope_field": False}})
    assert e.value.status_code == 422

def test_rejects_non_bool_value():
    with pytest.raises(HTTPException) as e:
        validate_pii_defaults({"manager": {"cpf": "yes"}})
    assert e.value.status_code == 422

def test_rejects_non_dict_role_map():
    with pytest.raises(HTTPException) as e:
        validate_pii_defaults({"manager": "all"})
    assert e.value.status_code == 422
