"""TDD Gap G: CustomAgentRuntime herda TenantAwareAgentMixin + endpoint /execute tem budget gate.

Gap G (auditoria enterprise-readiness 2026-06-08, verificado adversarial
WORSE_THAN_REPORTED):
  1. CustomAgentRuntime herdava (LangGraphReActBase, EnhancedAgentMixin) SEM
     TenantAwareAgentMixin — privando agentes do Studio do strict-mode gate
     (MissingTenantContextError) e do filtro de snippet degradado ("sua empresa").
     execute() chama self._process_langgraph (custom_agent_runtime.py:829), logo
     o override do mixin É exercido — adicionar ao MRO tem efeito real.
  2. O endpoint POST /custom-agents/{id}/execute nunca passava pelo fence diário
     de tokens (check_budget) — caminho paralelo ao chat SSE. Gasto ilimitado.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_custom_agent_runtime_inherits_tenant_aware_mixin():
    """CustomAgentRuntime DEVE ter TenantAwareAgentMixin no MRO (strict-mode gate)."""
    from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
    from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

    assert TenantAwareAgentMixin in CustomAgentRuntime.__mro__, (
        "CustomAgentRuntime nao herda TenantAwareAgentMixin — agentes do Studio "
        "escapam do strict-mode gate de tenant context (Gap G)"
    )
    # mixin deve vir ANTES de LangGraphReActBase no MRO (override de _process_langgraph)
    from lia_agents_core.langgraph_react_base import LangGraphReActBase
    mro = CustomAgentRuntime.__mro__
    assert mro.index(TenantAwareAgentMixin) < mro.index(LangGraphReActBase), (
        "TenantAwareAgentMixin deve preceder LangGraphReActBase no MRO"
    )


@pytest.mark.asyncio
async def test_execute_custom_agent_blocks_when_budget_exhausted():
    """Endpoint /execute deve retornar HTTP 429 quando o budget diario acabou."""
    from fastapi import HTTPException
    from app.api.v1 import custom_agents

    mock_agent = MagicMock()
    mock_agent.id = "ag1"
    mock_agent.name = "Test"
    mock_agent.status = "active"
    mock_agent.system_prompt = "x"
    mock_agent.allowed_tools = []
    mock_agent.domain = "general"
    mock_agent.max_steps = 8
    mock_agent.temperature = 0.0
    mock_agent.model_override = None

    mock_user = MagicMock()
    mock_user.company_id = "comp"
    mock_user.id = "u1"

    body = MagicMock()
    body.context = {}
    body.message = "oi"
    body.session_id = "s1"

    with patch.object(
        custom_agents.agent_marketplace_service, "get_agent",
        new=AsyncMock(return_value=mock_agent),
    ), patch(
        "app.domains.credits.services.token_budget_service.get_plan_for_company",
        new=AsyncMock(return_value="free"),
    ), patch(
        "app.domains.credits.services.token_budget_service.check_budget",
        new=AsyncMock(return_value=(False, 100, 50)),  # exhausted
    ):
        with pytest.raises(HTTPException) as exc_info:
            await custom_agents.execute_custom_agent(
                agent_id="ag1", body=body, current_user=mock_user,
                db=MagicMock(), company_id="comp",
            )
        assert exc_info.value.status_code == 429, (
            "Endpoint /execute deve retornar 429 quando budget exhausted (Gap G)"
        )
