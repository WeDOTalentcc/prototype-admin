"""Unit tests — tenant_errors (T-A canonical infra)."""
from __future__ import annotations

from app.shared.errors import LIATenantError
from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)


def test_invalid_company_id_inherits_lia_tenant_error():
    err = InvalidCompanyIdError("bad", details={"reason": "empty"})
    assert isinstance(err, LIATenantError)
    assert err.code == "INVALID_COMPANY_ID"
    assert err.recoverable is False
    assert err.details["reason"] == "empty"


def test_missing_tenant_context_inherits_lia_tenant_error():
    err = MissingTenantContextError(details={"agent": "wizard", "company_id_raw": "None"})
    assert isinstance(err, LIATenantError)
    assert err.code == "MISSING_TENANT_CONTEXT"
    assert err.recoverable is False
    assert err.details["agent"] == "wizard"


def test_to_dict_serializable_for_api_responses():
    err = MissingTenantContextError(details={"agent": "wizard"})
    payload = err.to_dict()
    assert payload["error"] == "MISSING_TENANT_CONTEXT"
    assert payload["recoverable"] is False
    assert payload["details"]["agent"] == "wizard"


def test_default_messages_are_pt_br():
    assert "obrigatório" in InvalidCompanyIdError().message.lower() or "inválido" in InvalidCompanyIdError().message.lower()
    assert "tenant" in MissingTenantContextError().message.lower()
