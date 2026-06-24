"""
Contract tests — Context Type Routing (Phase 4c).

Verifica que os domínios/context_types do WebSocket roteiam
para os agentes corretos no agent_chat_ws dispatcher.

Camada 5 — Contrato (pytest)
"""
import pytest


# ---------------------------------------------------------------------------
# _get_agent domain dispatcher
# ---------------------------------------------------------------------------


class TestAgentDomainDispatcher:
    """_get_agent() deve retornar a instância correta para cada domain."""

    def test_wizard_domain_returns_wizard_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("wizard")
        assert agent is not None
        assert "wizard" in type(agent).__name__.lower() or "Wizard" in type(agent).__name__

    def test_talent_domain_returns_talent_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("talent")
        assert agent is not None
        assert "talent" in type(agent).__name__.lower() or "Talent" in type(agent).__name__

    def test_pipeline_domain_returns_pipeline_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("pipeline")
        assert agent is not None

    def test_kanban_domain_returns_kanban_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("kanban")
        assert agent is not None

    def test_sourcing_domain_returns_sourcing_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("sourcing")
        assert agent is not None

    def test_unknown_domain_falls_back_to_talent_agent(self):
        """Float envia 'general' para contexto geral — deve usar fallback (talent)."""
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("general")
        assert agent is not None
        # fallback é TalentReActAgent
        assert "talent" in type(agent).__name__.lower() or "Talent" in type(agent).__name__

    def test_empty_domain_falls_back_gracefully(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("")
        assert agent is not None

    def test_jobs_management_domain(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("jobs_management")
        assert agent is not None

    def test_policy_domain(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("policy")
        assert agent is not None

    def test_analytics_domain(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("analytics")
        assert agent is not None
        assert "analytics" in type(agent).__name__.lower() or "Analytics" in type(agent).__name__

    def test_communication_domain(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("communication")
        assert agent is not None
        assert "communication" in type(agent).__name__.lower() or "Communication" in type(agent).__name__

    def test_comms_alias(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("comms")
        assert agent is not None

    def test_ats_integration_domain(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("ats_integration")
        assert agent is not None
        assert "ats" in type(agent).__name__.lower() or "ATS" in type(agent).__name__

    def test_ats_alias(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("ats")
        assert agent is not None


# ---------------------------------------------------------------------------
# ContextAdapter — PAGE_TO_CONTEXT_TYPE
# ---------------------------------------------------------------------------


class TestContextAdapterMapping:
    """PAGE_TO_CONTEXT_TYPE deve cobrir os domínios usados pelo float."""

    def test_wizard_maps_to_job_management(self):
        from app.orchestrator.context.context_adapter import PAGE_TO_CONTEXT_TYPE
        assert PAGE_TO_CONTEXT_TYPE.get("wizard") == "job_management"

    def test_general_maps_to_general(self):
        from app.orchestrator.context.context_adapter import PAGE_TO_CONTEXT_TYPE
        assert PAGE_TO_CONTEXT_TYPE.get("general") == "general"

    def test_talent_maps_to_talent_funnel(self):
        from app.orchestrator.context.context_adapter import PAGE_TO_CONTEXT_TYPE
        assert PAGE_TO_CONTEXT_TYPE.get("talent") == "talent_funnel"

    def test_pipeline_maps_to_pipeline(self):
        from app.orchestrator.context.context_adapter import PAGE_TO_CONTEXT_TYPE
        assert PAGE_TO_CONTEXT_TYPE.get("pipeline") == "pipeline"


# ---------------------------------------------------------------------------
# UniversalContext
# ---------------------------------------------------------------------------


class TestUniversalContextContract:
    """UniversalContext deve aceitar context_type passado pelo float."""

    def test_universal_context_accepts_general(self):
        from app.orchestrator.context.context_adapter import UniversalContext
        ctx = UniversalContext(
            message="olá",
            user_id="u1",
            company_id="c1",
            context_type="general",
        )
        assert ctx.context_type == "general"

    def test_universal_context_accepts_job_management(self):
        from app.orchestrator.context.context_adapter import UniversalContext
        ctx = UniversalContext(
            message="criar vaga",
            user_id="u1",
            company_id="c1",
            context_type="job_management",
        )
        assert ctx.context_type == "job_management"

    def test_universal_context_default_is_general(self):
        from app.orchestrator.context.context_adapter import UniversalContext
        ctx = UniversalContext(message="test", user_id="u1", company_id="c1")
        assert ctx.context_type == "general"

    def test_universal_context_has_conversation_id_optional(self):
        """Float sempre passa conversation_id — deve ser Optional."""
        from app.orchestrator.context.context_adapter import UniversalContext
        ctx = UniversalContext(message="test", user_id="u1", company_id="c1")
        assert ctx.conversation_id is None
        ctx2 = UniversalContext(
            message="test", user_id="u1", company_id="c1",
            conversation_id="conv-123"
        )
        assert ctx2.conversation_id == "conv-123"


# ---------------------------------------------------------------------------
# _build_agent_input
# ---------------------------------------------------------------------------


class TestAgentInputBuilderContract:
    """_build_agent_input deve construir AgentInput com os campos corretos."""

    def test_agent_input_has_message(self):
        from app.api.v1.chat_shared import _build_agent_input
        agent_input = _build_agent_input(
            content="criar vaga",
            context={"context_type": "wizard"},
            session_id="sess-1",
            company_id="co-1",
            user_id="usr-1",
            conversation_history=[],
        )
        assert agent_input.message == "criar vaga"

    def test_agent_input_has_company_id(self):
        from app.api.v1.chat_shared import _build_agent_input
        agent_input = _build_agent_input(
            content="test",
            context={},
            session_id="sess-1",
            company_id="co-42",
            user_id="usr-1",
            conversation_history=[],
        )
        assert agent_input.company_id == "co-42"

    def test_agent_input_has_session_id(self):
        from app.api.v1.chat_shared import _build_agent_input
        agent_input = _build_agent_input(
            content="test",
            context={},
            session_id="sess-xyz",
            company_id="co-1",
            user_id="usr-1",
            conversation_history=[],
        )
        assert agent_input.session_id == "sess-xyz"
