"""Sensor E1 (entrega multi-canal): ProactiveAlertService ENTREGA de verdade.

Causa raiz (2026-06-09): _send_alert chamava create_proactive_notification,
metodo que NUNCA existiu em NotificationService -> AttributeError engolido pelo
except -> os 15 alertas configuraveis nao chegavam em canal NENHUM (nem bell).
O teste antigo (test_proactive_alert_uses_preference.py::test 5) mascarava o bug
mockando o metodo inexistente (anti-pattern: testar o mock, nao o codigo real).

Este sensor usa MagicMock(spec=NotificationService): so permite metodos que
existem na classe real. Se _send_alert chamar metodo inexistente, o spec'd mock
lanca AttributeError -> entrega nao acontece -> assert .called falha.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


COMPANY_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "user-00000000-0000-0000-0000-000000000001"


def _make_preference_row(
    alert_type,
    *,
    channel_email=True,
    channel_bell=True,
    channel_teams=True,
    channel_whatsapp=False,
):
    row = MagicMock()
    row.company_id = COMPANY_ID
    row.user_id = USER_ID
    row.alert_type = alert_type
    row.is_enabled = True
    row.threshold = None
    row.cooldown_hours = None
    row.channel_email = channel_email
    row.channel_bell = channel_bell
    row.channel_teams = channel_teams
    row.channel_whatsapp = channel_whatsapp
    row.updated_at = datetime.utcnow()
    return row


def _fake_db(rows):
    db = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=rows)
    result_mock = MagicMock()
    result_mock.scalars = MagicMock(return_value=scalars_mock)
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_send_alert_delivers_via_real_multichannel_api():
    """_send_alert deve disparar via send_multi_channel_notification (metodo REAL).

    spec=NotificationService garante que so metodos existentes sao chamaveis.
    Com o bug (create_proactive_notification inexistente), o spec'd mock lanca
    AttributeError -> engolido -> send_multi_channel_notification NAO eh chamado
    -> RED.
    """
    from app.domains.automation.services.proactive_alert_service import (
        AlertCategory,
        AlertCondition,
        ProactiveAlertService,
    )
    from app.services.notification_service import (
        NotificationChannel,
        NotificationService,
        NotificationType,
    )

    svc = ProactiveAlertService()
    svc.notification_service = MagicMock(spec=NotificationService)
    svc.notification_service.send_multi_channel_notification = AsyncMock()

    row = _make_preference_row(
        "ats_sync_failed",
        channel_teams=True,
        channel_email=True,
        channel_bell=True,
    )
    db = _fake_db([row])
    overrides = await svc._load_overrides_for_company(COMPANY_ID, db)
    svc._tenant_overrides_cache = {
        (COMPANY_ID, atype): ov for atype, ov in overrides.items()
    }

    alert = {
        "condition": AlertCondition.ATS_SYNC_FAILED,
        "category": AlertCategory.SYSTEM,
        "title": "Falha sync ATS",
        "message": "Sincronizacao com ATS falhou.",
        "severity": NotificationType.URGENT,
        "data": {},
        "suggested_action": "view_ats",
        "action_label": "Ver ATS",
    }

    await svc._send_alert(alert, USER_ID, company_id=COMPANY_ID)

    assert svc.notification_service.send_multi_channel_notification.called, (
        "Alert deve ser entregue via send_multi_channel_notification (fan-out real)"
    )
    channels = svc.notification_service.send_multi_channel_notification.call_args.kwargs[
        "channels"
    ]
    assert NotificationChannel.TEAMS in channels, (
        "Teams deve estar nos canais (tenant ativou)"
    )
    assert NotificationChannel.EMAIL in channels, "Email deve estar nos canais"


@pytest.mark.asyncio
async def test_send_to_teams_uses_per_tenant_webhook(monkeypatch):
    """E2: _send_to_teams deve resolver o webhook PER-TENANT, nao o global.

    Antes (gap multi-tenant): send_adaptive_card era chamado sem webhook_url ->
    caía no global TEAMS_WEBHOOK_URL -> alerta da empresa A ia pro canal Teams
    errado. Fix: resolve via resolve_tenant_teams_webhook_url(company_id) usando
    o company_id propagado em data (E1).
    """
    import app.core.database as db_mod
    import app.domains.communication.services.teams_service as teams_mod
    from app.services.notification_service import (
        NotificationService,
        NotificationType,
    )

    sent = {}

    async def fake_resolve(company_id, db):
        assert company_id == COMPANY_ID, "deve resolver pro company_id do alerta"
        return ("https://tenant-A-webhook.example/abc", "db")

    async def fake_send_card(card_payload, webhook_url=None):
        sent["webhook_url"] = webhook_url
        return {"success": True}

    class _FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def close(self):
            return None

    monkeypatch.setattr(teams_mod, "resolve_tenant_teams_webhook_url", fake_resolve)
    monkeypatch.setattr(teams_mod.teams_service, "send_adaptive_card", fake_send_card)
    monkeypatch.setattr(db_mod, "AsyncSessionLocal", lambda: _FakeSession())

    svc = NotificationService()
    await svc._send_to_teams(
        user_id=USER_ID,
        title="Falha sync ATS",
        message="Sync falhou",
        notification_type=NotificationType.URGENT,
        data={"company_id": COMPANY_ID, "actions": [{"label": "Ver", "url": "/x"}]},
    )

    assert sent.get("webhook_url") == "https://tenant-A-webhook.example/abc", (
        "Teams deve usar o webhook per-tenant resolvido, nao o global"
    )


def test_notification_service_has_real_delivery_method_not_ghost():
    """Sensor anti-regressao: o metodo de entrega usado por _send_alert existe.

    create_proactive_notification NUNCA existiu (ghost). send_multi_channel_notification
    eh o canonical de fan-out. Este guard impede reintroduzir chamada a metodo inexistente.
    """
    from app.services.notification_service import NotificationService

    assert hasattr(NotificationService, "send_multi_channel_notification"), (
        "NotificationService deve ter send_multi_channel_notification (fan-out canonical)"
    )
    assert not hasattr(NotificationService, "create_proactive_notification"), (
        "create_proactive_notification eh ghost (nunca existiu) - nao reintroduzir"
    )
