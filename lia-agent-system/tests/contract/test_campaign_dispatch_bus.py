"""P0 regression sensor (audit ultracode 2026-06-14): campaign auto-action
dispatch must call ``AgentBus.publish`` with the REAL signature.

Bug pinned: ``_dispatch_auto_action`` chamava ``bus.publish(channel=..., message=...)``
mas a assinatura canonical e ``publish(from_agent, to_agent, event_type, payload,
company_id)``. O kwarg errado levantava TypeError, silenciado pelo ``except`` —
nenhuma auto-action jamais era despachada. Este contrato falha se alguem
reintroduzir channel/message ou remover company_id.

NOTE: este teste valida o PRODUTOR (campaign -> AgentBus). O consumidor
downstream (subscriber em sourcing/cv_screening) e Fase 2 e nao e coberto aqui.

Strategy: pure-unit. AgentBus e importado dentro do metodo, entao patchamos
``app.shared.agents.agent_bus.AgentBus``. Instanciamos o domain via
``object.__new__`` para nao depender do construtor de ComplianceDomainPrompt.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.recruitment_campaign.domain import RecruitmentCampaignDomain


def _domain():
    return object.__new__(RecruitmentCampaignDomain)


def _campaign():
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        job_id="22222222-2222-2222-2222-222222222222",
        name="Time de Engenharia Q3",
    )


@pytest.mark.asyncio
async def test_dispatch_uses_canonical_agentbus_signature():
    bus_instance = MagicMock()
    bus_instance.publish = AsyncMock(return_value=True)

    with patch(
        "app.shared.agents.agent_bus.AgentBus", return_value=bus_instance
    ):
        ok = await _domain()._dispatch_auto_action(
            db=MagicMock(),
            campaign=_campaign(),
            stage_name="sourcing",
            action_name="search_candidates",
            company_id="company-abc",
            user_id="user-xyz",
        )

    assert ok is True
    bus_instance.publish.assert_awaited_once()
    kwargs = bus_instance.publish.await_args.kwargs

    # Canonical signature — these MUST be present.
    assert kwargs["from_agent"] == "recruitment_campaign"
    assert kwargs["to_agent"] == "sourcing"
    assert kwargs["event_type"] == "search_candidates"
    assert kwargs["company_id"] == "company-abc"
    assert isinstance(kwargs["payload"], dict)
    assert kwargs["payload"]["campaign_id"] == str(_campaign().id)
    assert kwargs["payload"]["triggered_by"] == "user-xyz"
    assert kwargs["payload"]["source"] == "recruitment_campaign"

    # The buggy kwargs MUST NOT come back.
    assert "channel" not in kwargs
    assert "message" not in kwargs


@pytest.mark.asyncio
async def test_unknown_action_returns_false_without_publish():
    bus_instance = MagicMock()
    bus_instance.publish = AsyncMock(return_value=True)
    with patch(
        "app.shared.agents.agent_bus.AgentBus", return_value=bus_instance
    ):
        ok = await _domain()._dispatch_auto_action(
            db=MagicMock(),
            campaign=_campaign(),
            stage_name="sourcing",
            action_name="does_not_exist",
            company_id="company-abc",
            user_id="user-xyz",
        )
    assert ok is False
    bus_instance.publish.assert_not_awaited()
