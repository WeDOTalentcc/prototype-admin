"""
Tests for AUD-4 completion:
- HITL in SourcingReActAgent (outreach stage)
- HITL in CommunicationReActAgent (initial_contact, rejection_feedback)
- Circuit breakers in domain-level ATS clients
- Circuit breakers in domain-level email providers
"""
import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# AUD-4 — Circuit breakers in domain-level ATS clients
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Fixture canônica (Onda 4 / Sprint HITL): patch get_checkpointer para teste
# unit. Em production APP_ENV, get_checkpointer() levanta RuntimeError antes
# de initialize_checkpointer_async(). Tests instanciam agentes diretamente →
# precisam do patch. Padrão: test_langgraph_base_streaming.py (autouse).
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_checkpointer_for_unit_tests():
    """Substitui get_checkpointer() por None e tenant context para todos os testes do módulo.

    Agentes armazenam self._checkpointer = get_checkpointer() no __init__.
    Tests mockam process() individualmente — o checkpointer real não é usado.

    Também patcha _get_tenant_context_snippet para retornar "" em modo strict:
    testes de SEG-5/audit usam company_id="c1"/"c2" (slugs inválidos) e não
    precisam do snippet real — o comportamento testado é o audit log, não o
    tenant resolution.
    """
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock
    with (
        _patch(
            "lia_agents_core.langgraph_base.get_checkpointer",
            return_value=None,
        ),
        _patch(
            "app.shared.agents.tenant_aware_agent.TenantAwareAgentMixin._get_tenant_context_snippet",
            new_callable=_AsyncMock,
            return_value="",
        ),
    ):
        yield
class TestDomainATSCircuitBreakers:
    """Domain-level ATS clients must use circuit breakers."""

    def test_domain_gupy_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.gupy as mod
        source = inspect.getsource(mod)
        assert "GUPY_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_domain_pandape_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.pandape as mod
        source = inspect.getsource(mod)
        assert "PANDAPE_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_domain_merge_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.merge as mod
        source = inspect.getsource(mod)
        assert "MERGE_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source


class TestDomainEmailCircuitBreakers:
    """Domain communication email providers must use circuit breakers."""

    def test_domain_mailgun_imports_circuit_breaker(self):
        import app.services.email_providers.mailgun_provider as mod
        source = inspect.getsource(mod)
        assert "MAILGUN_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_domain_resend_imports_circuit_breaker(self):
        import app.services.email_providers.resend_provider as mod
        source = inspect.getsource(mod)
        assert "RESEND_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source


# ---------------------------------------------------------------------------
# AUD-4 — HITL in SourcingReActAgent
# ---------------------------------------------------------------------------

class TestSourcingHITL:
    """SourcingReActAgent must request HITL approval for outreach sends."""

    def _make_input(self, message: str, stage: str, hitl_approved: bool = False):
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message=message,
            session_id="test-session-src",
            company_id="company-123",
            user_id="user-1",
            context={
                "current_stage": stage,
                "hitl_approved": hitl_approved,
                "selected_candidates": ["cand-1", "cand-2"],
                "job_id": "job-42",
            },
            conversation_history=[],
        )

    @pytest.mark.asyncio
    async def test_outreach_send_confirmation_triggers_hitl(self):
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

        agent = SourcingReActAgent()
        agent._memory_service = MagicMock()
        inp = self._make_input("sim, pode enviar", stage="outreach")

        mock_pending_id = "pending-123"
        with (
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
            patch("app.shared.compliance.audit_service.audit_service") as mock_audit,
        ):
            mock_hitl.request_approval = AsyncMock(return_value=mock_pending_id)
            mock_hitl.store_resume_info = AsyncMock()
            mock_audit.log_decision = AsyncMock()

            result = await agent.process(inp)

        assert result.metadata.get("hitl_pending") is True
        assert result.metadata.get("hitl_pending_id") == mock_pending_id
        assert "Aguardando aprovação" in result.message
        mock_hitl.request_approval.assert_called_once()
        call_kwargs = mock_hitl.request_approval.call_args.kwargs
        assert call_kwargs["action"] == "send_outreach"
        assert call_kwargs["domain"] == "sourcing"

    @pytest.mark.asyncio
    async def test_outreach_with_hitl_approved_skips_hitl(self):
        """When hitl_approved=True, the agent skips HITL and runs normally."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

        agent = SourcingReActAgent()
        inp = self._make_input("sim, pode enviar", stage="outreach", hitl_approved=True)

        mock_output = MagicMock()

        with (
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=mock_output)) as mock_loop,
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
        ):
            mock_hitl.request_approval = AsyncMock()
            result = await agent.process(inp)

        mock_hitl.request_approval.assert_not_called()
        mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_outreach_stage_no_hitl(self):
        """HITL is NOT triggered for stages other than outreach."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

        agent = SourcingReActAgent()
        inp = self._make_input("sim", stage="talent-search")

        with (
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
        ):
            mock_hitl.request_approval = AsyncMock()
            await agent.process(inp)

        mock_hitl.request_approval.assert_not_called()

    @pytest.mark.asyncio
    async def test_hitl_failure_is_fail_open(self):
        """If HITL service fails, agent continues processing (fail-open)."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

        agent = SourcingReActAgent()
        inp = self._make_input("pode enviar", stage="outreach")

        with (
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
        ):
            mock_hitl.request_approval = AsyncMock(side_effect=Exception("Redis unavailable"))
            result = await agent.process(inp)

        # fail-open: loop is still called
        mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_outreach_non_confirmation_message_no_hitl(self):
        """HITL not triggered if outreach message is a question, not a send confirmation."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent

        agent = SourcingReActAgent()
        inp = self._make_input("quais candidatos estão disponíveis?", stage="outreach")

        with (
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
        ):
            mock_hitl.request_approval = AsyncMock()
            await agent.process(inp)

        mock_hitl.request_approval.assert_not_called()
        mock_loop.assert_called_once()


# ---------------------------------------------------------------------------
# AUD-4 — HITL in CommunicationReActAgent
# ---------------------------------------------------------------------------

class TestCommunicationHITL:
    """CommunicationReActAgent must request HITL for sensitive message types."""

    def _make_input(self, message_type: str, hitl_approved: bool = False):
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message="Enviar mensagem de contato inicial",
            session_id="test-session-comm",
            company_id="company-456",
            user_id="user-2",
            context={
                "message_type": message_type,
                "hitl_approved": hitl_approved,
                "candidate_id": "cand-42",
                "channel": "email",
            },
            conversation_history=[],
        )

    @pytest.mark.asyncio
    async def test_initial_contact_triggers_hitl(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent

        agent = CommunicationReActAgent()
        inp = self._make_input("initial_contact")

        mock_pending_id = "comm-pending-42"
        with (
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
            patch("app.shared.compliance.audit_service.audit_service") as mock_audit,
        ):
            mock_hitl.request_approval = AsyncMock(return_value=mock_pending_id)
            mock_hitl.store_resume_info = AsyncMock()
            mock_audit.log_decision = AsyncMock()

            result = await agent.process(inp)

        assert result.metadata.get("hitl_pending") is True
        assert result.metadata.get("message_type") == "initial_contact"
        assert "Aguardando aprovação" in result.message
        call_kwargs = mock_hitl.request_approval.call_args.kwargs
        assert call_kwargs["action"] == "send_communication"
        assert call_kwargs["domain"] == "communication"

    @pytest.mark.asyncio
    async def test_rejection_feedback_triggers_hitl(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent

        agent = CommunicationReActAgent()
        inp = self._make_input("rejection_feedback")

        with (
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
            patch("app.shared.compliance.audit_service.audit_service") as mock_audit,
        ):
            mock_hitl.request_approval = AsyncMock(return_value="pending-456")
            mock_hitl.store_resume_info = AsyncMock()
            mock_audit.log_decision = AsyncMock()

            result = await agent.process(inp)

        assert result.metadata.get("hitl_pending") is True
        mock_hitl.request_approval.assert_called_once()

    @pytest.mark.asyncio
    async def test_hitl_approved_skips_check(self):
        """When hitl_approved=True, HITL check is skipped."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent

        agent = CommunicationReActAgent()
        inp = self._make_input("initial_contact", hitl_approved=True)

        with (
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
        ):
            mock_hitl.request_approval = AsyncMock()
            await agent.process(inp)

        mock_hitl.request_approval.assert_not_called()
        mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_message_type_no_hitl(self):
        """Generic message types (general, reminder) do NOT trigger HITL."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent

        agent = CommunicationReActAgent()
        inp = self._make_input("general")

        with (
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
        ):
            mock_hitl.request_approval = AsyncMock()
            await agent.process(inp)

        mock_hitl.request_approval.assert_not_called()

    @pytest.mark.asyncio
    async def test_hitl_constants_defined(self):
        """Confirm HITL_MESSAGE_TYPES includes initial_contact and rejection_feedback."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        hitl_types = CommunicationReActAgent._HITL_MESSAGE_TYPES
        assert "initial_contact" in hitl_types
        assert "rejection_feedback" in hitl_types
        assert "offer_letter" in hitl_types
        assert "general" not in hitl_types

    @pytest.mark.asyncio
    async def test_hitl_failure_is_fail_open(self):
        """If HITL fails, communication agent continues (fail-open)."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent

        agent = CommunicationReActAgent()
        inp = self._make_input("initial_contact")

        with (
            patch("app.services.hitl_service.hitl_service") as mock_hitl,
            patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=MagicMock())) as mock_loop,
        ):
            mock_hitl.request_approval = AsyncMock(side_effect=Exception("HITL service down"))
            await agent.process(inp)

        mock_loop.assert_called_once()


# ---------------------------------------------------------------------------
# SEG-5 — _process_langgraph override in CommunicationReActAgent
# ---------------------------------------------------------------------------

class TestCommunicationLangGraphAudit:
    """CommunicationReActAgent must have _process_langgraph override with AuditService."""

    def test_communication_agent_has_process_langgraph_override(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        import inspect
        source = inspect.getsource(CommunicationReActAgent._process_langgraph)
        assert "audit_service" in source
        assert "AuditService" in source or "audit_service.log_decision" in source

    @pytest.mark.asyncio
    async def test_langgraph_override_calls_audit(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        from lia_agents_core.agent_interface import AgentInput

        agent = CommunicationReActAgent()
        inp = AgentInput(
            message="Oi",
            session_id="s1",
            company_id="c1",
            user_id="u1",
            context={"current_stage": "send-message"},
            conversation_history=[],
        )

        mock_output = MagicMock()
        mock_output.confidence = 0.9

        with (
            patch("lia_agents_core.langgraph_react_base.LangGraphReActBase._process_langgraph",
                  new_callable=AsyncMock, return_value=mock_output),
            patch("app.shared.compliance.audit_service.audit_service") as mock_audit,
        ):
            mock_audit.log_decision = AsyncMock()
            result = await agent._process_langgraph(inp)

        mock_audit.log_decision.assert_called_once()
        call_kwargs = mock_audit.log_decision.call_args.kwargs
        assert call_kwargs["agent_name"] == "communication_react_agent"
        assert call_kwargs["decision_type"] == "send_communication"
        assert result is mock_output

    @pytest.mark.asyncio
    async def test_langgraph_override_audit_fail_safe(self):
        """Audit failure must not break the langgraph execution."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        from lia_agents_core.agent_interface import AgentInput

        agent = CommunicationReActAgent()
        inp = AgentInput(
            message="teste",
            session_id="s2",
            company_id="c2",
            user_id="u2",
            context={},
            conversation_history=[],
        )
        mock_output = MagicMock()

        with (
            patch("lia_agents_core.langgraph_react_base.LangGraphReActBase._process_langgraph",
                  new_callable=AsyncMock, return_value=mock_output),
            patch("app.shared.compliance.audit_service.audit_service") as mock_audit,
        ):
            mock_audit.log_decision = AsyncMock(side_effect=Exception("DB down"))
            result = await agent._process_langgraph(inp)

        assert result is mock_output
