"""Sensor E6: WeeklyDigest entrega tambem por EMAIL (era so bell+chat+teams).

deliver_digest ja entregava bell+chat+teams (Teams per-tenant — padrao-ouro),
mas faltava email. Requisito Paulo: todo alerta/resumo chega em teams+bell+email.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_weekly_digest_delivers_email_channel(monkeypatch):
    import lia_messaging.notification_service as ns_mod
    import app.domains.analytics.services.digest_formatter as fmt_mod
    import app.domains.communication.services.teams_service as teams_mod
    from lia_messaging.notification_service import NotificationChannel
    from app.domains.analytics.services.weekly_digest_service import (
        WeeklyDigestService,
    )

    # --- formatters retornam payloads simples ---
    class _Fmt:
        def format(self, digest):
            return {"title": "Resumo", "message": "corpo", "action_url": "/chat"}

    monkeypatch.setattr(fmt_mod, "BellDigestFormatter", lambda: _Fmt())
    monkeypatch.setattr(fmt_mod, "ChatDigestFormatter", lambda: _Fmt())
    monkeypatch.setattr(fmt_mod, "TeamsDigestFormatter", lambda: _Fmt())

    # --- NotificationService spec mock (mesma instancia em toda instanciacao) ---
    ns = MagicMock(spec=ns_mod.NotificationService)
    ns.create_notification = AsyncMock(return_value={"id": "b1"})
    ns.send_multi_channel_notification = AsyncMock(return_value={"sent_to": []})
    monkeypatch.setattr(ns_mod, "NotificationService", lambda *a, **k: ns)

    # --- TeamsService + resolver mockados ---
    ts = MagicMock()
    ts.send_adaptive_card = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(teams_mod, "TeamsService", lambda *a, **k: ts)
    monkeypatch.setattr(
        teams_mod, "resolve_tenant_teams_webhook_url", AsyncMock(return_value=(None, "none"))
    )

    # --- db.execute (lookup company_id no bloco teams) ---
    res = MagicMock()
    res.scalar_one_or_none = MagicMock(return_value=None)
    db = MagicMock()
    db.execute = AsyncMock(return_value=res)

    svc = WeeklyDigestService()
    results = await svc.deliver_digest(
        digest={"generated_at": "2026-06-09T00:00:00Z"},
        recruiter_id="user-1",
        recruiter_name="Recrutador",
        db=db,
    )

    assert "email" in results, "deliver_digest deve reportar o canal email"
    email_calls = [
        c
        for c in ns.send_multi_channel_notification.call_args_list
        if NotificationChannel.EMAIL in c.kwargs.get("channels", [])
    ]
    assert email_calls, "WeeklyDigest deve entregar por email (canal EMAIL no fan-out)"
