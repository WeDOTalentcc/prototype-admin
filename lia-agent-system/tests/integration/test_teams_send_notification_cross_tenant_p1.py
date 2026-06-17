"""
Integration test — IDOR/cross-tenant guard em POST /teams/send-notification.

Auditoria 2026-04-27 (P1): o endpoint declarava `Depends(get_current_user)`
mas buscava `TeamsConversation` por `user_id` (vindo do request body) sem
validar que a conversation pertence à empresa do caller. Um recruiter
autenticado podia enviar notificações Teams para qualquer usuário de
qualquer empresa enumerando `user_id`.

Cenários:
- recruiter da empresa A tentando notificar Teams user da empresa B → 403.
- recruiter da empresa A notificando Teams user da empresa A → 200 (ou
  segue o fluxo normal de envio).
- admin pode notificar qualquer empresa.

Esses testes usam stubs leves para evitar setup completo do Bot Framework.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1 import teams as teams_module
from app.auth.models import UserRole


COMPANY_A = uuid.UUID("00000000-0000-4000-a000-00000000000a")
COMPANY_B = uuid.UUID("00000000-0000-4000-a000-00000000000b")


def _make_user(company_id: uuid.UUID | None, role: UserRole = UserRole.recruiter):
    return SimpleNamespace(
        id=uuid.uuid4(),
        company_id=company_id,
        role=role,
    )


def _make_conv(company_id: uuid.UUID | None):
    return SimpleNamespace(
        company_id=company_id,
        conversation_reference={"conversation": {"id": "x"}},
        user_id="teams_user_x",
    )


@pytest.mark.asyncio
async def test_cross_tenant_send_notification_blocked() -> None:
    """Recruiter da empresa A tenta notificar conversation da empresa B → 403."""
    caller = _make_user(COMPANY_A, UserRole.recruiter)
    target_conv = _make_conv(COMPANY_B)

    with patch.object(teams_module, "TeamsRepository") as RepoCls:
        repo = RepoCls.return_value
        repo.get_conversation_by_user_id = AsyncMock(return_value=target_conv)

        with pytest.raises(HTTPException) as exc:
            await teams_module.send_proactive_notification(
                notification_data={"user_id": "teams_user_x", "data": {}},
                db=AsyncMock(),  # passa por causa do Depends override
                current_user=caller,
            )

    assert exc.value.status_code == 403
    assert "cross-tenant" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_admin_can_notify_any_tenant() -> None:
    """Admin da empresa A pode notificar conversation da empresa B."""
    caller = _make_user(COMPANY_A, UserRole.admin)
    target_conv = _make_conv(COMPANY_B)

    with (
        patch.object(teams_module, "TeamsRepository") as RepoCls,
        patch.object(teams_module, "SimpleTeamsBot", create=True) as _Bot,
    ):
        repo = RepoCls.return_value
        repo.get_conversation_by_user_id = AsyncMock(return_value=target_conv)
        bot_inst = _Bot.return_value
        bot_inst.send_card = AsyncMock(return_value=True)

        # Não deve levantar 403 — pode levantar erro a jusante (envio falhar),
        # o que é OK; o que importa é que não bloqueie por cross-tenant.
        try:
            await teams_module.send_proactive_notification(
                notification_data={"user_id": "teams_user_x", "data": {}},
                db=AsyncMock(),
                current_user=caller,
            )
        except HTTPException as exc:
            assert exc.status_code != 403, (
                "admin não deveria ser bloqueado por cross-tenant"
            )


@pytest.mark.asyncio
async def test_same_tenant_passes_guard() -> None:
    """Recruiter da empresa A notifica conversation da empresa A → não bloqueia."""
    caller = _make_user(COMPANY_A, UserRole.recruiter)
    target_conv = _make_conv(COMPANY_A)

    with (
        patch.object(teams_module, "TeamsRepository") as RepoCls,
        patch.object(teams_module, "SimpleTeamsBot", create=True) as _Bot,
    ):
        repo = RepoCls.return_value
        repo.get_conversation_by_user_id = AsyncMock(return_value=target_conv)
        bot_inst = _Bot.return_value
        bot_inst.send_card = AsyncMock(return_value=True)

        try:
            await teams_module.send_proactive_notification(
                notification_data={"user_id": "teams_user_x", "data": {}},
                db=AsyncMock(),
                current_user=caller,
            )
        except HTTPException as exc:
            assert exc.status_code != 403, (
                "same-tenant não deveria ser bloqueado pelo guard"
            )


@pytest.mark.asyncio
async def test_caller_without_company_blocked_for_non_admin() -> None:
    """Recruiter sem company_id não pode notificar ninguém."""
    caller = _make_user(None, UserRole.recruiter)
    target_conv = _make_conv(COMPANY_A)

    with patch.object(teams_module, "TeamsRepository") as RepoCls:
        repo = RepoCls.return_value
        repo.get_conversation_by_user_id = AsyncMock(return_value=target_conv)

        with pytest.raises(HTTPException) as exc:
            await teams_module.send_proactive_notification(
                notification_data={"user_id": "teams_user_x", "data": {}},
                db=AsyncMock(),
                current_user=caller,
            )

    assert exc.value.status_code == 403
