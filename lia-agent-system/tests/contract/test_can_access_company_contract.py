"""
Contract sensor — User.can_access_company role gating (Onda 1.1).

WHY THIS SENSOR EXISTS
======================
Onda 1.1 (2026-05-23) fixou ``User.can_access_company`` para reconhecer
``UserRole.wedotalent_admin`` como cross-tenant. Antes, staff WeDOTalent com
essa role era negado em endpoints como ``GET /lia/wsi/audit-trail`` (Recovery
#3 descobriu — workaround pontual aplicado no endpoint mas raiz aqui).

Esse sensor garante:
1. ``wedotalent_admin`` → True para qualquer company_id (cross-tenant)
2. ``admin`` → True para qualquer company_id (transitional, mantido ate migration)
3. ``recruiter`` → True apenas para self company_id
4. ``viewer`` → True apenas para self company_id

Pattern: BLOCKING. Multi-tenancy LGPD critical.

TODO follow-up: depois da migration admin→wedotalent_admin no banco,
atualizar este sensor pra ``admin`` retornar False quando company_id
diverge (privilege escalation fix).
"""
from __future__ import annotations


def _can_access(role_value: str, user_company_id: str, target_company_id: str) -> bool:
    """Invoca User.can_access_company sem instanciar SQLAlchemy model.

    A logica de can_access_company nao precisa do model real — usa apenas
    self.role e self.company_id. Pra testar sem DB, fazemos bind direto
    do unbound method com um objeto namespace.
    """
    from types import SimpleNamespace
    from app.auth.models import User, UserRole

    fake_user = SimpleNamespace(
        role=UserRole(role_value),
        company_id=user_company_id,
    )
    return User.can_access_company(fake_user, target_company_id)


def test_wedotalent_admin_can_access_any_company():
    """``wedotalent_admin`` → True para qualquer company_id (cross-tenant)."""
    assert _can_access("wedotalent_admin", "company-A", "company-A") is True
    assert _can_access("wedotalent_admin", "company-A", "company-B") is True
    assert _can_access("wedotalent_admin", "company-A", "any-other-company") is True


def test_admin_currently_can_access_any_company_transitional():
    """``admin`` transicional → True (mantido ate migration de staff).

    TODO: quando admin→wedotalent_admin migration ocorrer no banco,
    flipar para assert is False quando company_id diverge.
    """
    assert _can_access("admin", "company-A", "company-A") is True
    assert _can_access("admin", "company-A", "company-B") is True  # TRANSITIONAL


def test_recruiter_only_accesses_own_company():
    """``recruiter`` (tenant role) → True apenas para self company_id."""
    assert _can_access("recruiter", "company-A", "company-A") is True
    assert _can_access("recruiter", "company-A", "company-B") is False
    assert _can_access("recruiter", "company-A", "any-other") is False


def test_viewer_only_accesses_own_company():
    """``viewer`` (tenant role) → True apenas para self company_id."""
    assert _can_access("viewer", "company-A", "company-A") is True
    assert _can_access("viewer", "company-A", "company-B") is False


def test_role_canonical_set_unchanged():
    """UserRole canonical set: 4 roles. Adicionar role nova exige update
    aqui + decisao explicita em can_access_company."""
    from app.auth.models import UserRole
    expected = {"admin", "recruiter", "viewer", "wedotalent_admin"}
    actual = {r.value for r in UserRole}
    assert actual == expected, (
        f"UserRole enum mudou: {actual ^ expected}. "
        "Atualizar can_access_company + este sensor."
    )
