"""
F-A TDD: pipeline SSE routing + context flow verification.

Tests:
1. _subagent_for_pipeline returns "pipeline_transition" as fail-safe default
2. _subagent_for_pipeline routes action keywords → pipeline_action
3. _subagent_for_pipeline routes decision keywords → pipeline_decision
4. All 4 pipeline agent domains registered in AgentRegistry (class check, no instantiation)
5. Context fields from /interpret-context REST flow via SSE passthrough
"""
import pytest


class TestSubagentForPipelineRouting:
    """Z1-02: verify _subagent_for_pipeline routing logic."""

    def test_default_routes_to_pipeline_transition_not_context(self):
        """Fail-safe default must be pipeline_transition (full tools + HITL + Fairness),
        NOT pipeline_context (read-only 7-tool sub-agent).
        Matches REST behavior where PipelineTransitionAgent handles everything.
        Matches code comment: 'Fail-safe: retorna pipeline_transition'.
        """
        from app.api.v1.chat_shared import _subagent_for_pipeline
        result = _subagent_for_pipeline("qual o melhor caminho aqui?")
        assert result == "pipeline_transition", (
            f"Expected 'pipeline_transition' as fail-safe default, got '{result}'. "
            "Fix: change 'return \"pipeline_context\"' to 'return \"pipeline_transition\"' "
            "in _subagent_for_pipeline in app/api/v1/chat_shared.py."
        )

    def test_action_keywords_route_to_pipeline_action(self):
        from app.api.v1.chat_shared import _subagent_for_pipeline
        assert _subagent_for_pipeline("atualizar candidato agora") == "pipeline_action"

    def test_decision_keywords_route_to_pipeline_decision(self):
        from app.api.v1.chat_shared import _subagent_for_pipeline
        assert _subagent_for_pipeline("validar transição para entrevista") == "pipeline_decision"

    def test_all_pipeline_domains_registered_in_agent_registry(self):
        """All 4 pipeline agent domains must be registered (class check — no instantiation).
        Uses is_registered() to avoid LangGraph checkpointer async init in unit tests.
        """
        from app.shared.agents.agent_registry import AgentRegistry
        # Trigger imports so decorators run
        from app.api.v1.chat_shared import _ensure_agents_loaded
        _ensure_agents_loaded()

        registry = AgentRegistry()
        for domain in ("pipeline_transition", "pipeline_context", "pipeline_action", "pipeline_decision"):
            assert registry.is_registered(domain), (
                f"Domain '{domain}' not registered in AgentRegistry. "
                "Check @register_agent decorator and _ensure_agents_loaded import."
            )


class TestSSEContextPassthrough:
    """Verify that context fields from /interpret-context REST match what SSE passes to AgentInput."""

    def test_build_agent_input_preserves_transition_context(self):
        """context dict with transition fields must reach AgentInput.context verbatim.

        REST endpoint (/interpret-context) builds AgentInput with:
          context={action_behavior, candidate_id, candidate_name, job_id, job_title,
                   from_stage, to_stage, company_id}
        SSE passthrough: req.context → context = req.context or {} → _build_agent_input(context=context)
        Both must produce the same AgentInput.context for context-aware behavior.
        """
        from app.api.v1.chat_shared import _build_agent_input

        transition_ctx = {
            "action_behavior": "active",
            "candidate_id": "cand-uuid-123",
            "candidate_name": "Maria Silva",
            "job_id": "job-uuid-456",
            "job_title": "Engenheira de Software",
            "from_stage": "triagem",
            "to_stage": "entrevista",
            "company_id": "comp-uuid-789",
        }

        agent_input = _build_agent_input(
            content="Mover a candidata para entrevista",
            context=transition_ctx,
            session_id="session-abc",
            company_id="comp-uuid-789",
            user_id="user-uuid-001",
            conversation_history=[],
        )

        for key, expected in transition_ctx.items():
            assert agent_input.context.get(key) == expected, (
                f"Context field '{key}' lost in passthrough: "
                f"expected {expected!r}, got {agent_input.context.get(key)!r}"
            )
