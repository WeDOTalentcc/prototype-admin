"""Sensor E3 (entrega multi-canal): briefing dispatch entrega de verdade.

Causa raiz (2026-06-09): _dispatch_for_frequency_async chamava
notification_service.send_notification(channel="bell"), metodo que NUNCA existiu
em NotificationService -> AttributeError engolido pelo except -> briefing nao
chegava NEM no sino. Alem disso era hardcoded bell (sem email/teams).

Fix: helper _dispatch_briefing_notification usa send_multi_channel_notification
(fan-out real) em bell+email+teams; company_id em data habilita Teams per-tenant.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_briefing_dispatched_via_real_multichannel_all_channels():
    from app.jobs.tasks.briefing_dispatch import _dispatch_briefing_notification
    from app.services.notification_service import (
        NotificationChannel,
        NotificationService,
    )

    ns = MagicMock(spec=NotificationService)
    ns.send_multi_channel_notification = AsyncMock()

    await _dispatch_briefing_notification(
        ns,
        user_id="user-1",
        company_id="company-1",
        freq="daily",
        briefing={"date": "2026-06-09", "urgent_actions": [1, 2]},
        db=MagicMock(),
    )

    assert ns.send_multi_channel_notification.called, (
        "briefing deve ser entregue via send_multi_channel_notification (fan-out real)"
    )
    kw = ns.send_multi_channel_notification.call_args.kwargs
    assert NotificationChannel.BELL in kw["channels"], "briefing deve ir pro sino"
    assert NotificationChannel.EMAIL in kw["channels"], "briefing deve ir por email"
    assert NotificationChannel.TEAMS in kw["channels"], "briefing deve ir pro Teams"
    assert kw["data"]["company_id"] == "company-1", (
        "company_id deve ir em data (Teams per-tenant E2)"
    )


def test_notification_service_has_no_ghost_send_notification():
    """Guard anti-ghost: NotificationService nao tem send_notification.

    send_notification existe em OUTRAS classes (data_request_service, teams_bot)
    mas NAO em NotificationService. O briefing chamava esse metodo-fantasma.
    """
    from app.services.notification_service import NotificationService

    assert not hasattr(NotificationService, "send_notification"), (
        "send_notification eh ghost em NotificationService - usar send_multi_channel_notification"
    )
    assert hasattr(NotificationService, "send_multi_channel_notification")
