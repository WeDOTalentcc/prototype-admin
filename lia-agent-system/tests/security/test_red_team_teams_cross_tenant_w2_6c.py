"""
Regression net — W2.6.c: RBAC tests for _enforce_company_id_scope.

Auditoria 2026-04-27 (commit 365bfab8f por Replit auto): Cross-tenant em
/teams/proactive/* — 4 endpoints aceitavam company_id por query sem cruzar
com current_user.company_id. Recruiter podia disparar notificacoes para
outra empresa. Fix: nova funcao _enforce_company_id_scope em teams.py.

A funcao existe (commit 365bfab8f) mas SEM testes especificos validando o
RBAC. Esta suite e regression net retroativo: os 7 testes devem passar com
o fix atual; se alguem regredir o comportamento, eles falharao.

Pattern Hashimoto (harness-engineering): nunca mais cross-tenant em
/teams/proactive/* sem teste cobrindo. Sensor computacional.

Cenarios:
  1. non-admin com proprio company_id      -> retorna o valor
  2. non-admin com OUTRO company_id        -> 403 cross-tenant
  3. non-admin sem requested              -> retorna own
  4. non-admin sem User.company_id        -> 403 cannot resolve
  5. admin com OUTRO company_id            -> retorna o valor (admin pode)
  6. admin sem requested + allow_none=True -> retorna None (fan-out)
  7. admin sem requested + allow_none=False -> retorna own
"""
from __future__ import annotations
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock


@pytest.fixture
def admin_user():
    """Admin user com company_id 'comp_admin'."""
    from app.auth.models import UserRole
    u = MagicMock()
    u.role = UserRole.admin
    u.company_id = "comp_admin"
    return u


@pytest.fixture
def recruiter_user():
    """Recruiter com company_id 'comp_own'."""
    from app.auth.models import UserRole
    u = MagicMock()
    u.role = UserRole.recruiter
    u.company_id = "comp_own"
    return u


@pytest.fixture
def recruiter_no_company():
    """Recruiter sem company_id (edge — usuario mal configurado)."""
    from app.auth.models import UserRole
    u = MagicMock()
    u.role = UserRole.recruiter
    u.company_id = None
    return u


class TestEnforceCompanyIdScopeNonAdmin:
    """Non-admin RBAC: only own company_id allowed."""

    def test_non_admin_with_own_company_id_returns_value(self, recruiter_user):
        from app.api.v1.teams import _enforce_company_id_scope
        result = _enforce_company_id_scope("comp_own", recruiter_user)
        assert result == "comp_own"

    def test_non_admin_with_other_company_id_raises_403(self, recruiter_user):
        from app.api.v1.teams import _enforce_company_id_scope
        with pytest.raises(HTTPException) as exc:
            _enforce_company_id_scope("comp_OTHER", recruiter_user)
        assert exc.value.status_code == 403
        assert "cross-tenant" in exc.value.detail.lower()

    def test_non_admin_without_requested_returns_own(self, recruiter_user):
        """Recruiter sem company_id no query → resolve para own."""
        from app.api.v1.teams import _enforce_company_id_scope
        result = _enforce_company_id_scope(None, recruiter_user)
        assert result == "comp_own"

    def test_non_admin_no_user_company_id_raises_403(self, recruiter_no_company):
        """Recruiter sem company_id no User → 403 (não pode resolver)."""
        from app.api.v1.teams import _enforce_company_id_scope
        with pytest.raises(HTTPException) as exc:
            _enforce_company_id_scope(None, recruiter_no_company)
        assert exc.value.status_code == 403
        assert "could not be resolved" in exc.value.detail.lower()


class TestEnforceCompanyIdScopeAdmin:
    """Admin RBAC: any value (including None for fan-out)."""

    def test_admin_with_other_company_id_returns_value(self, admin_user):
        """Admin pode operar em qualquer company."""
        from app.api.v1.teams import _enforce_company_id_scope
        result = _enforce_company_id_scope("comp_OTHER", admin_user)
        assert result == "comp_OTHER"

    def test_admin_none_with_allow_none_true_returns_none(self, admin_user):
        """Admin com allow_none=True e sem requested → None (fan-out)."""
        from app.api.v1.teams import _enforce_company_id_scope
        result = _enforce_company_id_scope(None, admin_user, allow_none=True)
        assert result is None

    def test_admin_none_with_allow_none_false_returns_own(self, admin_user):
        """Admin sem requested e sem allow_none → resolve para own."""
        from app.api.v1.teams import _enforce_company_id_scope
        result = _enforce_company_id_scope(None, admin_user, allow_none=False)
        assert result == "comp_admin"


class TestEnforceCompanyIdScopeCallsites:
    """Validate the 4 proactive endpoints call _enforce_company_id_scope."""

    @pytest.mark.parametrize("fn_name,allow_none_expected", [
        ("run_proactivity_checks", True),
        ("notify_new_candidate", False),
        ("notify_screening_complete", False),
        ("send_daily_digest", True),
    ])
    def test_endpoint_calls_enforce_scope(self, fn_name, allow_none_expected):
        import inspect
        import app.api.v1.teams as mod
        fn = getattr(mod, fn_name)
        src = inspect.getsource(fn)
        assert "_enforce_company_id_scope" in src, (
            f"{fn_name} must call _enforce_company_id_scope (cross-tenant guard)"
        )
        if allow_none_expected:
            assert "allow_none=True" in src, (
                f"{fn_name} should pass allow_none=True (admin fan-out endpoint)"
            )
