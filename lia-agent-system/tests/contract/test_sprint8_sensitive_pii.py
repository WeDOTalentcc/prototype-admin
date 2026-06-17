"""
Sprint 8 RBAC — sensitive PII redaction (CPF + DoB + address + secondary contacts).

LGPD Art. 5 II. Plan: ~/.claude/plans/jolly-roaming-moler.md.

Default grant=true (zero-quebra). Admin can opt-out per-user.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.candidates.candidates_crud import (
    _redact_sensitive_pii_for_user,
    _audit_pii_access,
    _SENSITIVE_PII_FIELDS,
)


def _make_user(can_view: bool = True, can_view_salary: bool = False, email="me@a.com"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = email
    u.can_view_sensitive_pii = can_view
    u.can_view_salary = can_view_salary
    return u


def _candidate_dict():
    return {
        "id": "cand-1",
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": "+5511999999999",
        "cpf": "123.456.789-00",
        "date_of_birth": "1990-01-15",
        "address_street": "Rua das Flores",
        "address_number": "123",
        "address_zip": "01234-567",
        "address_complement": "Apto 45",
        "secondary_email": "joao.alt@example.com",
        "secondary_phone": "+5511888888888",
        "personal_emails": ["joao@gmail.com", "joao.silva@outlook.com"],
        "business_emails": ["joao@empresa.com"],
        "best_personal_email": "joao@gmail.com",
        "best_business_email": "joao@empresa.com",
        "location_city": "São Paulo",
        "location_state": "SP",
    }


def test_t1_user_without_grant_redacts_all_sensitive_pii():
    user = _make_user(can_view=False)
    d = _redact_sensitive_pii_for_user(_candidate_dict(), user)
    for f in _SENSITIVE_PII_FIELDS:
        if f.endswith("emails"):
            assert d[f] == [], f"{f} should be empty list"
        else:
            assert d[f] is None, f"{f} should be None"
    assert d["sensitive_pii_masked"] is True
    # Non-sensitive preserved
    assert d["name"] == "João Silva"
    assert d["email"] == "joao@example.com"
    assert d["phone"] == "+5511999999999"
    assert d["location_city"] == "São Paulo"


def test_t2_user_with_grant_sees_sensitive_pii():
    user = _make_user(can_view=True)
    d = _redact_sensitive_pii_for_user(_candidate_dict(), user)
    assert d["cpf"] == "123.456.789-00"
    assert d["date_of_birth"] == "1990-01-15"
    assert d["address_street"] == "Rua das Flores"
    assert d["secondary_email"] == "joao.alt@example.com"
    assert d["personal_emails"] == ["joao@gmail.com", "joao.silva@outlook.com"]
    assert d["sensitive_pii_masked"] is False


def test_t3_non_sensitive_fields_preserved_when_redacted():
    """Critical: workflow fields (name, primary email/phone, city) stay visible."""
    user = _make_user(can_view=False)
    d = _redact_sensitive_pii_for_user(_candidate_dict(), user)
    assert d["name"] == "João Silva"  # workflow
    assert d["email"] == "joao@example.com"  # primary
    assert d["phone"] == "+5511999999999"  # primary
    assert d["location_city"] == "São Paulo"  # contexto profissional


def test_t4_handles_missing_fields_gracefully():
    user = _make_user(can_view=False)
    minimal = {"id": "x", "name": "Test"}
    d = _redact_sensitive_pii_for_user(minimal, user)
    assert d["sensitive_pii_masked"] is True
    assert d["name"] == "Test"
    # Absent fields not added
    for f in _SENSITIVE_PII_FIELDS:
        assert f not in d


def test_t5_list_fields_become_empty_not_none():
    """Sprint 8: lists (personal_emails, business_emails) → [] not None (avoid type confusion)."""
    user = _make_user(can_view=False)
    d = {"personal_emails": ["a@x.com", "b@y.com"], "business_emails": ["c@z.com"], "cpf": "111"}
    redacted = _redact_sensitive_pii_for_user(d, user)
    assert redacted["personal_emails"] == []
    assert redacted["business_emails"] == []
    assert redacted["cpf"] is None


@pytest.mark.asyncio
async def test_t6_audit_fires_for_both_pii_classes_when_user_has_both_grants():
    """Sprint 8: user with both can_view_salary + can_view_sensitive_pii → 2 audit rows."""
    log_calls = []
    fake_svc = AsyncMock()
    fake_svc.log_data_access = AsyncMock(side_effect=lambda **kw: log_calls.append(kw))

    with patch(
        "app.shared.compliance.audit_service.AuditService",
        MagicMock(return_value=fake_svc),
    ):
        user = _make_user(can_view=True, can_view_salary=True)
        await _audit_pii_access(user, "cand-1", "co-1")

    pii_classes = [c["details"]["pii_class"] for c in log_calls]
    assert "financial_salary" in pii_classes
    assert "sensitive_identity" in pii_classes
    assert len(log_calls) == 2


@pytest.mark.asyncio
async def test_t7_audit_fires_only_sensitive_pii_when_no_salary_grant():
    """Sprint 8: default user (sensitive=true, salary=false) → 1 audit row (sensitive only)."""
    log_calls = []
    fake_svc = AsyncMock()
    fake_svc.log_data_access = AsyncMock(side_effect=lambda **kw: log_calls.append(kw))

    with patch(
        "app.shared.compliance.audit_service.AuditService",
        MagicMock(return_value=fake_svc),
    ):
        user = _make_user(can_view=True, can_view_salary=False)
        await _audit_pii_access(user, "cand-1", "co-1")

    assert len(log_calls) == 1
    assert log_calls[0]["details"]["pii_class"] == "sensitive_identity"


@pytest.mark.asyncio
async def test_t8_audit_skipped_when_no_grants():
    """Sprint 8: user with both grants false (rare) → no audit rows (não viu nada)."""
    log_calls = []
    fake_svc = AsyncMock()
    fake_svc.log_data_access = AsyncMock(side_effect=lambda **kw: log_calls.append(kw))

    with patch(
        "app.shared.compliance.audit_service.AuditService",
        MagicMock(return_value=fake_svc),
    ):
        user = _make_user(can_view=False, can_view_salary=False)
        await _audit_pii_access(user, "cand-1", "co-1")

    assert log_calls == []


def test_t9_sensitive_pii_fields_canonical_set():
    """Lock canonical field set. Adding/removing requires intentional change."""
    expected = {
        "cpf", "date_of_birth",
        "address_street", "address_number", "address_zip", "address_complement",
        "secondary_email", "secondary_phone",
        "personal_emails", "business_emails",
        "best_personal_email", "best_business_email",
    }
    assert set(_SENSITIVE_PII_FIELDS) == expected
    # Workflow-critical fields NOT in set
    assert "name" not in _SENSITIVE_PII_FIELDS
    assert "email" not in _SENSITIVE_PII_FIELDS
    assert "phone" not in _SENSITIVE_PII_FIELDS
    assert "location_city" not in _SENSITIVE_PII_FIELDS
