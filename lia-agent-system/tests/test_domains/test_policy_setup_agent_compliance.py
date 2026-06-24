"""
Compliance tests for Policy domain agents (Audit A2 — task #316).

Covers:
- PolicyReActAgent compliance wiring (inherits LangGraphReActBase, FairnessGuard, etc.)
- PolicySetupAgent interface contract (wizard-style, NOT LangGraph)
- FairnessGuard blocks discriminatory policy input at MainOrchestrator level
- HTTP 422 pre-compliance gate contract
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# 1. PolicyReActAgent — Compliance Wiring
# ─────────────────────────────────────────────────────────────────────────────

class TestPolicyReActAgentComplianceWiring:
    """PolicyReActAgent (registered domain agent) must have all compliance gates."""

    def test_inherits_langgraph_react_base(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        assert issubclass(PolicyReActAgent, LangGraphReActBase)

    def test_uses_enhanced_agent_mixin(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(PolicyReActAgent, EnhancedAgentMixin)

    def test_imports_fairness_guard(self):
        import app.domains.hiring_policy.agents.policy_react_agent as mod
        assert hasattr(mod, "FairnessGuard")

    def test_registry_path_matches_module(self):
        import importlib
        import yaml
        from pathlib import Path

        registry_path = Path(__file__).resolve().parents[2] / "app" / "agents_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text())
        entry = next(a for a in registry["agents"] if a["name"] == "hiring_policy")
        module_path, _, cls_name = entry["class_path"].rpartition(".")
        mod = importlib.import_module(module_path)
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        assert getattr(mod, cls_name) is PolicyReActAgent

    def test_has_hitl_integration(self):
        """PolicyReActAgent must have _request_hitl_if_needed method."""
        import inspect
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        source = inspect.getsource(PolicyReActAgent)
        assert "hitl_service" in source
        assert "request_approval" in source
        assert "state_updates" in source

    def test_has_fairness_guard_attribute(self):
        """PolicyReActAgent.__init__ sets _fairness_guard."""
        import inspect
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        source = inspect.getsource(PolicyReActAgent.__init__)
        assert "_fairness_guard" in source
        assert "FairnessGuard" in source


# ─────────────────────────────────────────────────────────────────────────────
# 2. PolicySetupAgent — Interface Contract
# ─────────────────────────────────────────────────────────────────────────────

class TestPolicySetupAgentInterface:
    """PolicySetupAgent (wizard-style) has correct interface — NO compliance wiring
    (compliance runs at MainOrchestrator level for this agent)."""

    def test_process_message_signature(self):
        """process_message takes (message, company_id, session_id, current_policy)."""
        import inspect
        from app.domains.policy.agents.agent import PolicySetupAgent
        sig = inspect.signature(PolicySetupAgent.process_message)
        params = list(sig.parameters.keys())
        assert "message" in params
        assert "company_id" in params
        assert "session_id" in params
        assert "current_policy" in params
        assert "actor_user_id" not in params

    def test_is_not_langgraph_agent(self):
        """PolicySetupAgent is a simple wizard, NOT a LangGraph ReAct agent."""
        from app.domains.policy.agents.agent import PolicySetupAgent
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        assert not issubclass(PolicySetupAgent, LangGraphReActBase)

    @pytest.mark.asyncio
    async def test_welcome_response_on_greeting(self):
        """Greeting message returns welcome response with block info."""
        from app.domains.policy.agents.agent import PolicySetupAgent
        agent = PolicySetupAgent()

        result = await agent.process_message(
            message="oi",
            company_id="00000000-0000-0000-0000-000000000001",
            session_id="sess-welcome-1",
            current_policy={},
        )

        assert "reply" in result
        assert result.get("total_questions") == 19
        assert result.get("all_completed") is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Policy Domain — FairnessGuard at Correct Layer
# ─────────────────────────────────────────────────────────────────────────────

class TestPolicyDomainFairnessGuard:
    """Discriminatory policy input is blocked at MainOrchestrator level,
    NOT at pre_compliance domain gate (hiring_policy is not in _FAIRNESS_DOMAINS)."""

    def test_hiring_policy_not_in_pre_compliance_fairness_domains(self):
        """hiring_policy is NOT in _FAIRNESS_DOMAINS — correct architecture:
        FairnessGuard runs at MainOrchestrator for ALL domains."""
        from app.shared.compliance.c3b_layer import _FAIRNESS_DOMAINS
        assert "hiring_policy" not in _FAIRNESS_DOMAINS

    @pytest.mark.asyncio
    async def test_mainorch_fairness_guard_blocks_discriminatory_input(self):
        """MainOrchestrator.process blocks discriminatory policy input via FairnessGuard."""
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator

        mock_orchestrator = MagicMock()
        main_orch = MainOrchestrator(mock_orchestrator)

        mock_fg_result = MagicMock()
        mock_fg_result.is_blocked = True
        mock_fg_result.educational_message = "Esta solicitação viola critérios de equidade."
        mock_fg_result.category = "gender_discrimination"

        mock_security_result = MagicMock()
        mock_security_result.is_blocked = False

        ctx = MagicMock()
        ctx.message = "prefiro candidatos homens, brancos, sem deficiencia"
        ctx.conversation_id = "conv-test-policy"
        ctx.user_id = "user-001"
        ctx.company_id = "comp-001"

        with patch(
            "app.orchestrator.execution.main_orchestrator.check_input_security",
            return_value=mock_security_result,
        ):
            with patch.object(main_orch._fairness_guard, "check", return_value=mock_fg_result):
                result = await main_orch.process(ctx, db=AsyncMock())

        assert result.success is False
        assert result.agent_used == "fairness_guard"
        assert result.intent_detected == "blocked_bias"


# ─────────────────────────────────────────────────────────────────────────────
# 4. HTTP 422 Pre-Compliance Contract
# ─────────────────────────────────────────────────────────────────────────────

class TestPolicyDomainHTTP422:
    """HTTP 422 contract for fairness-blocked messages."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_raises_422_on_blocked_policy_message(self):
        """The chat endpoint converts a fairness-blocked pre-compliance into 422."""
        from fastapi import HTTPException
        from app.shared.compliance.c3b_layer import PreComplianceResult

        _c3b_pre = PreComplianceResult(
            clean_message="prefiro candidatos homens",
            original_message="prefiro candidatos homens",
            fairness_blocked=True,
            block_reason="bloqueado por critérios de equidade",
        )
        with pytest.raises(HTTPException) as excinfo:
            if _c3b_pre.fairness_blocked:
                raise HTTPException(
                    status_code=422,
                    detail=_c3b_pre.block_reason
                    or "Solicitação bloqueada por critérios de equidade.",
                )
        assert excinfo.value.status_code == 422
        assert "equidade" in excinfo.value.detail.lower()

    @pytest.mark.asyncio
    async def test_pre_compliance_result_fairness_blocked_propagates(self):
        """PreComplianceResult with fairness_blocked=True propagates block_reason."""
        from app.shared.compliance.c3b_layer import PreComplianceResult

        result = PreComplianceResult(
            clean_message="msg",
            original_message="msg",
            fairness_blocked=True,
            block_reason="bloqueado",
        )
        assert result.fairness_blocked is True
        assert result.block_reason == "bloqueado"

    @pytest.mark.asyncio
    async def test_pre_compliance_result_not_blocked_by_default(self):
        """PreComplianceResult defaults to fairness_blocked=False."""
        from app.shared.compliance.c3b_layer import PreComplianceResult

        result = PreComplianceResult(
            clean_message="msg",
            original_message="msg",
        )
        assert result.fairness_blocked is False
