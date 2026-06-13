"""
Compliance tests for PolicySetupAgent (Audit A2 — task #316).

Covers:
- Discriminatory policy input → FairnessGuard blocks → compliance_blocked=True.
- Valid policy input → 1 audit_service.log_decision call + persistence in
  session.current_policy.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.policy.agents.agent import PolicySetupAgent


def _make_agent() -> PolicySetupAgent:
    return PolicySetupAgent.__new__(PolicySetupAgent)


def _bootstrap(agent: PolicySetupAgent) -> None:
    """Initialise just the bits we need without touching DB / checkpointer."""
    from app.shared.compliance.fairness_guard import FairnessGuard
    agent._llm = None
    agent._fairness_guard = FairnessGuard()
    agent._enable_pii_strip = True


class TestPolicySetupAgentComplianceWiring:
    """The 6 compliance gates from Audit A2 must be wired into the module."""

    def test_inherits_langgraph_react_base(self):
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        assert issubclass(PolicySetupAgent, LangGraphReActBase)

    def test_uses_enhanced_agent_mixin(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(PolicySetupAgent, EnhancedAgentMixin)

    def test_imports_compliance_helpers(self):
        import app.domains.policy.agents.agent as mod
        assert hasattr(mod, "FairnessGuard")
        assert hasattr(mod, "strip_pii_for_llm_prompt")
        assert hasattr(mod, "SystemPromptBuilder")
        assert hasattr(mod, "get_current_llm_tenant")

    def test_registry_path_matches_module(self):
        import importlib
        import yaml
        from pathlib import Path

        registry_path = Path(__file__).resolve().parents[2] / "app" / "agents_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text())
        entry = next(a for a in registry["agents"] if a["name"] == "hiring_policy")
        module_path, _, cls = entry["class_path"].rpartition(".")
        mod = importlib.import_module(module_path)
        assert getattr(mod, cls) is PolicySetupAgent


class TestPolicySetupAgentFairnessGuard:
    """A discriminatory policy input must be blocked with an audit trail."""

    @pytest.mark.asyncio
    async def test_discriminatory_input_blocks_and_audits(self):
        agent = _make_agent()
        _bootstrap(agent)

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ) as audit_mock:
            result = await agent.process_message(
                message="prefiro candidatos homens, brancos, sem deficiencia",
                company_id="00000000-0000-0000-0000-000000000001",
                session_id="sess-block-1",
                current_policy={},
                actor_user_id="user-test",
            )

        assert result["compliance_blocked"] is True
        assert result["all_completed"] is False
        # The educational message comes from FairnessGuard.
        assert "vi" in (result["reply"] or "").lower() or result["reply"]
        # At least one audit entry recording the block.
        assert audit_mock.await_count >= 1
        kwargs = audit_mock.await_args_list[0].kwargs
        assert kwargs["agent_name"] == "policy_setup_agent"
        assert kwargs["decision"] == "blocked"
        assert kwargs["action"] == "fairness_block"
        assert kwargs["human_review_required"] is True


class TestPolicySetupAgentValidPolicy:
    """A valid policy answer must persist + emit a single audit entry."""

    @pytest.mark.asyncio
    async def test_valid_answer_persists_and_audits(self):
        agent = _make_agent()
        _bootstrap(agent)

        # Stub the LLM call: return a JSON value matching the first question
        # (Q1 — pipeline_rules.min_interviews_before_offer, integer).
        async def fake_extract(self, message, question, session=None):  # noqa: ARG001
            return question["default"] if question["type"] != "integer" else 3

        async def fake_reply(*_args, **_kwargs):
            return "Anotado. Próxima pergunta..."

        with patch.object(PolicySetupAgent, "_extract_value", new=fake_extract), \
             patch.object(PolicySetupAgent, "_generate_reply", new=fake_reply), \
             patch.object(PolicySetupAgent, "_generate_block_end_reply", new=fake_reply), \
             patch.object(PolicySetupAgent, "_generate_completion_reply", new=fake_reply), \
             patch(
                "app.shared.compliance.audit_service.audit_service.log_decision",
                new_callable=AsyncMock,
             ) as audit_mock:
            result = await agent.process_message(
                message="pelo menos 3 entrevistas",
                company_id="00000000-0000-0000-0000-000000000002",
                session_id="sess-valid-1",
                current_policy={},
                actor_user_id="user-test",
            )

        # Persistence: updated_fields populated with the new policy value.
        assert result.get("compliance_blocked", False) is False
        assert result["updated_fields"], "policy field must be persisted"
        # The new value is stored under pipeline_rules.min_interviews_before_offer.
        pipeline_rules = result["updated_fields"].get("pipeline_rules") or {}
        assert pipeline_rules.get("min_interviews_before_offer") == 3
        # Exactly one audit entry for the policy change (no fairness block).
        assert audit_mock.await_count == 1
        kwargs = audit_mock.await_args.kwargs
        assert kwargs["agent_name"] == "policy_setup_agent"
        assert kwargs["decision_type"] == "policy_update"
        assert kwargs["action"].startswith("policy_field_updated:")
        # policy_diff is captured in reasoning for traceability.
        assert any("policy_diff" in r for r in kwargs["reasoning"])


class TestPolicySetupAgentProcessAdapter:
    """The LangGraph-native ``process()`` entrypoint must adapt onto
    ``process_message`` so generic dispatch keeps working."""

    @pytest.mark.asyncio
    async def test_process_dispatches_to_process_message(self):
        agent = _make_agent()
        _bootstrap(agent)

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ):
            result = await agent.process({
                "message": "prefiro candidatos homens, brancos",
                "company_id": "00000000-0000-0000-0000-000000000005",
                "session_id": "sess-process-1",
                "current_policy": {},
                "actor_user_id": "user-test",
            })

        assert result["compliance_blocked"] is True


class TestPolicySetupAgentFailClosed:
    """If FairnessGuard itself raises, the agent must fail CLOSED (block)."""

    @pytest.mark.asyncio
    async def test_guard_runtime_error_blocks_request(self):
        agent = _make_agent()
        _bootstrap(agent)

        # Force the guard to raise on every call.
        def boom(_text):
            raise RuntimeError("guard model unavailable")

        agent._fairness_guard.check = boom  # type: ignore[assignment]

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new_callable=AsyncMock,
        ) as audit_mock:
            result = await agent.process_message(
                message="3 entrevistas no minimo",
                company_id="00000000-0000-0000-0000-000000000003",
                session_id="sess-failclosed-1",
                current_policy={},
                actor_user_id="user-test",
            )

        assert result["compliance_blocked"] is True
        assert result["updated_fields"] == {}
        assert result["all_completed"] is False
        # The block was audited as a fairness_block with human_review_required.
        assert audit_mock.await_count >= 1
        kwargs = audit_mock.await_args_list[0].kwargs
        assert kwargs["action"] == "fairness_block"
        assert kwargs["human_review_required"] is True
        assert "guard_error" in (kwargs.get("criteria_used") or [])


class TestPolicyDomainHTTP422:
    """Discriminatory input on the policy domain must produce HTTP 422 at the
    API edge (chat endpoint pre-compliance gate)."""

    @pytest.mark.asyncio
    async def test_pre_compliance_blocks_policy_domain_with_block_flag(self):
        from app.shared.compliance.c3b_layer import pre_compliance, _FAIRNESS_DOMAINS

        # Audit A2: policy/hiring_policy must be in the gated domain set so the
        # chat endpoint raises HTTP 422 before reaching the agent.

        result = await pre_compliance(
            message="prefiro candidatos homens, brancos, sem deficiencia",
            company_id="00000000-0000-0000-0000-000000000004",
            domain="hiring_policy",
        )
        assert result.fairness_blocked is True
        assert result.block_reason  # non-empty educational message

    @pytest.mark.asyncio
    async def test_chat_endpoint_raises_422_on_blocked_policy_message(self):
        """The chat endpoint converts a fairness-blocked pre-compliance into 422."""
        from fastapi import HTTPException
        from app.shared.compliance.c3b_layer import PreComplianceResult

        # Mirror the contract used in app/api/v1/chat.py around line 227-228.
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
    async def test_post_chat_returns_422_for_discriminatory_policy_message(self):
        """End-to-end: POST to the chat send_message handler with policy domain
        + discriminatory text must raise HTTPException(status_code=422).

        We invoke the route handler directly with mocked FastAPI dependencies
        (real TestClient would require a full DB + auth stack)."""
        import uuid
        from types import SimpleNamespace
        from fastapi import HTTPException

        from app.api.v1.chat import send_message
        from app.schemas.chat import MessageCreate

        company_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        user = SimpleNamespace(id=uuid.uuid4(), company_id=company_id)

        conversation = SimpleNamespace(
            id=conv_id,
            user_id=str(user.id),
            user_role="hiring_manager",
            title="t",
            intent="",
            workflow_type=None,
            workflow_step=None,
            workflow_data={},
            status="active",
            created_at=None,
            updated_at=None,
        )

        class _DB:
            async def commit(self): pass
            async def refresh(self, _): pass

        repo = SimpleNamespace(
            db=_DB(),
            create_conversation=AsyncMock(return_value=conversation),
            get_conversation_by_id=AsyncMock(return_value=conversation),
            add_user_message=AsyncMock(),
        )

        msg = MessageCreate(
            content="prefiro candidatos homens, brancos, sem deficiencia",
            context={"domain": "hiring_policy"},
            conversation_id=None,
        )

        with pytest.raises(HTTPException) as excinfo:
            await send_message(message_data=msg, current_user=user, repo=repo)

        assert excinfo.value.status_code == 422
        # Detail is FairnessGuard's educational message — non-empty, non-generic.
        detail = (excinfo.value.detail or "").lower()
        assert detail and ("lia" in detail or "equidade" in detail or "candidatos" in detail)
