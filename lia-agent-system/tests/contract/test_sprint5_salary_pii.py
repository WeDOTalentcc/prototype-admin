"""
Sprint 5 RBAC — Financial PII privilege canonical contract.

LGPD Art. 6 III (minimização): salary fields gated by explicit can_view_salary
grant. Default FALSE — admin grants per-user via UI.

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md.

Cases:
  T1. User without grant → salary fields nulled + salary_masked=true
  T2. User WITH grant → salary fields untouched + salary_masked=false
  T3. salary_currency NOT redacted (contextual, not PII per LGPD)
  T4. _audit_pii_access fires only when user has grant (no fake audit rows)
  T5. _audit_pii_access non-blocking on exception
  T6. Helper handles missing fields gracefully (key not in dict)
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.candidates.candidates_crud import (
    _redact_salary_for_user,
    _audit_pii_access,
    _SALARY_FIELDS,
)


def _make_user(can_view_salary: bool, email="user@acme.com", can_view_sensitive_pii: bool = False):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = email
    u.can_view_salary = can_view_salary
    # Sprint 8: explicit pra não interferir nos tests Sprint 5 (default=False aqui)
    u.can_view_sensitive_pii = can_view_sensitive_pii
    return u


def _candidate_dict():
    return {
        "id": "cand-123",
        "name": "João Silva",
        "current_salary": 8000.0,
        "desired_salary_min": 9000.0,
        "desired_salary_max": 12000.0,
        "salary_currency": "BRL",
        "salary_expectation_clt": 8500.0,
        "salary_expectation_pj": 11000.0,
        "salary_expectation_freelance": 150.0,
        "email": "joao@example.com",
    }


def test_t1_user_without_grant_redacts_all_salary_fields():
    user = _make_user(can_view_salary=False)
    d = _redact_salary_for_user(_candidate_dict(), user)
    for f in _SALARY_FIELDS:
        assert d[f] is None, f"{f} should be None for unprivileged user"
    assert d["salary_masked"] is True
    # Non-salary fields untouched
    assert d["name"] == "João Silva"
    assert d["email"] == "joao@example.com"


def test_t2_user_with_grant_sees_salary():
    user = _make_user(can_view_salary=True)
    d = _redact_salary_for_user(_candidate_dict(), user)
    assert d["current_salary"] == 8000.0
    assert d["desired_salary_min"] == 9000.0
    assert d["desired_salary_max"] == 12000.0
    assert d["salary_expectation_clt"] == 8500.0
    assert d["salary_masked"] is False


def test_t3_salary_currency_not_redacted():
    """salary_currency is contextual (BRL/USD/EUR), not PII per LGPD."""
    user_no_grant = _make_user(can_view_salary=False)
    d = _redact_salary_for_user(_candidate_dict(), user_no_grant)
    assert d["salary_currency"] == "BRL"


def test_t6_handles_missing_fields_gracefully():
    user = _make_user(can_view_salary=False)
    minimal = {"id": "cand-1", "name": "Test"}  # no salary fields at all
    d = _redact_salary_for_user(minimal, user)
    assert d["salary_masked"] is True
    assert d["name"] == "Test"
    # No KeyError raised
    for f in _SALARY_FIELDS:
        assert f not in d  # absent fields stay absent (not added as None)


@pytest.mark.asyncio
async def test_t4_audit_pii_access_fires_only_when_grant_present():
    """Non-privileged user → no audit row (default-redacted, no PII viewed)."""
    log_calls = []
    fake_svc = AsyncMock()
    fake_svc.log_data_access = AsyncMock(side_effect=lambda **kw: log_calls.append(kw))

    with patch(
        "app.shared.compliance.audit_service.AuditService",
        MagicMock(return_value=fake_svc),
    ):
        # Without grant — no audit
        await _audit_pii_access(_make_user(can_view_salary=False), "cand-1", "co-1")
        assert log_calls == []

        # With grant — audit fires
        await _audit_pii_access(_make_user(can_view_salary=True), "cand-2", "co-1")
        assert len(log_calls) == 1
        assert log_calls[0]["resource_type"] == "candidate"
        assert log_calls[0]["resource_id"] == "cand-2"
        assert log_calls[0]["action"] == "view_pii"
        assert log_calls[0]["details"]["pii_class"] == "financial_salary"


@pytest.mark.asyncio
async def test_t5_audit_pii_access_non_blocking_on_exception():
    """Audit failure cannot break PII access (LGPD Art. 37 V audit is non-blocking)."""
    with patch(
        "app.shared.compliance.audit_service.AuditService",
        MagicMock(side_effect=RuntimeError("DB down")),
    ):
        # Must NOT raise
        await _audit_pii_access(_make_user(can_view_salary=True), "cand-1", "co-1")
