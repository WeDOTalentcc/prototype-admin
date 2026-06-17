"""
Unit tests — cross-tenant guard nos endpoints proativos do Teams.

Auditoria 2026-04-27 (P1 hardening): a função `_enforce_company_id_scope`
impede que um recruiter autenticado dispare notificações/digests para
`company_id` de outra empresa via query parameter. Antes deste guard, os 4
endpoints `/teams/proactive/*` aceitavam `company_id` cru e propagavam ao
serviço sem validação contra `current_user.company_id`.

Cenários:
- non-admin sem `company_id` enviado → resolve para o próprio
- non-admin enviando o próprio → permitido
- non-admin enviando outro → 403
- admin enviando qualquer um → permitido
- admin sem nada (allow_none=True) → None (fan-out)
- non-admin sem nada e sem company_id próprio → 403
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.v1.teams import _enforce_company_id_scope
from app.auth.models import UserRole


class _FakeUser:
    """Stub mínimo de app.auth.models.User para o guard."""

    def __init__(self, company_id: str | None, role: UserRole) -> None:
        self.company_id = company_id
        self.role = role


COMPANY_A = "00000000-0000-4000-a000-00000000000a"
COMPANY_B = "00000000-0000-4000-a000-00000000000b"


class TestCompanyIdScopeGuard:
    def test_non_admin_no_request_resolves_to_own(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.recruiter)
        assert _enforce_company_id_scope(None, user) == COMPANY_A

    def test_non_admin_own_company_allowed(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.recruiter)
        assert _enforce_company_id_scope(COMPANY_A, user) == COMPANY_A

    def test_non_admin_cross_tenant_rejected(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.recruiter)
        with pytest.raises(HTTPException) as exc:
            _enforce_company_id_scope(COMPANY_B, user)
        assert exc.value.status_code == 403
        assert "cross-tenant" in str(exc.value.detail)

    def test_admin_can_target_other_company(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.admin)
        assert _enforce_company_id_scope(COMPANY_B, user) == COMPANY_B

    def test_admin_none_with_allow_none_returns_none(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.admin)
        assert _enforce_company_id_scope(None, user, allow_none=True) is None

    def test_admin_none_without_allow_none_resolves_to_own(self) -> None:
        user = _FakeUser(COMPANY_A, UserRole.admin)
        assert _enforce_company_id_scope(None, user) == COMPANY_A

    def test_non_admin_no_request_no_own_rejected(self) -> None:
        user = _FakeUser(None, UserRole.recruiter)
        with pytest.raises(HTTPException) as exc:
            _enforce_company_id_scope(None, user)
        assert exc.value.status_code == 403
        assert "could not be resolved" in str(exc.value.detail)

    def test_non_admin_allow_none_still_rejects_when_no_own(self) -> None:
        user = _FakeUser(None, UserRole.recruiter)
        with pytest.raises(HTTPException) as exc:
            _enforce_company_id_scope(None, user, allow_none=True)
        assert exc.value.status_code == 403
