"""Sensor E4 (entrega multi-canal): MonitoringLoop._persist_alerts entrega real.

Causa raiz (2026-06-09): _persist_alerts usava NotificationService.create_notification,
que so persiste UMA linha de sino — os channels (teams/email) eram gravados como
JSON inerte, nunca entregues. Fix: send_multi_channel_notification (fan-out real)
com channels string->enum + company_id em data (Teams per-tenant E2). Estes sao
"alertas de empresa" (user_id=system:) que vao pro canal Teams compartilhado.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_persist_alerts_uses_real_fanout_with_company_for_teams(monkeypatch):
    import lia_messaging.notification_service as ns_mod
    from lia_messaging.notification_service import NotificationChannel
    from app.domains.recruiter_assistant.services.monitoring_loop import (
        AlertCategory,
        AlertSeverity,
        MonitoringLoop,
        ProactiveAlert,
    )

    spec_svc = MagicMock(spec=ns_mod.NotificationService)
    spec_svc.send_multi_channel_notification = AsyncMock()
    monkeypatch.setattr(ns_mod, "NotificationService", lambda: spec_svc)

    loop = MonitoringLoop.get_instance()
    alert = ProactiveAlert(
        alert_id="a1",
        category=AlertCategory.SLA_BREACH,
        severity=AlertSeverity.CRITICAL,
        title="SLA estourado",
        message="Vaga X passou do SLA",
        company_id="company-1",
        channels=["bell", "teams", "email"],
    )

    await loop._persist_alerts("company-1", [alert])

    assert spec_svc.send_multi_channel_notification.called, (
        "alertas do monitoring loop devem usar fan-out real, nao create_notification"
    )
    kw = spec_svc.send_multi_channel_notification.call_args.kwargs
    chans = kw["channels"]
    assert NotificationChannel.TEAMS in chans, "Teams deve entrar (alerta de empresa)"
    assert NotificationChannel.BELL in chans, "Bell deve entrar"
    assert NotificationChannel.EMAIL in chans, "Email deve entrar"
    assert kw["data"]["company_id"] == "company-1", (
        "company_id deve ir em data (Teams per-tenant E2)"
    )
