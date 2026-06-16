"""Phase 3 — N3 Agente Negociador: TDD sensors (15 testes).

Cobre:
  3.2 OfferService.get_learning_context (LGPD N>=10 gate)
  3.3 _wrap_draft_response_to_candidate (HITL invariante)
  3.5 Portal multi-round state machine (contraproposta schema + rounds)
  3.6 OfferService.check_hitl_threshold (delta% vs threshold)
  3.8 get_learning_context tool registrado
  3.9 OfferConciergeAgent modes N2/N3 gated
"""
import inspect
import pytest


# ── 3.5 — Multi-round state machine ──────────────────────────────────────────

class TestOfferPortalSchema:
    """Tests that the portal request schema accepts contraproposta (3.5)."""

    def test_resposta_request_accepts_contraproposta(self):
        from app.api.public.offer_portal import OfferRespostaRequest
        req = OfferRespostaRequest(acao="contraproposta", counter_salary=8000.0)
        assert req.acao == "contraproposta"
        assert req.counter_salary == 8000.0

    def test_resposta_request_rejects_invalid_acao(self):
        from pydantic import ValidationError
        from app.api.public.offer_portal import OfferRespostaRequest
        with pytest.raises((ValidationError, ValueError)):
            OfferRespostaRequest(acao="aceitar_tudo")  # invalid

    def test_validate_counter_raises_without_salary(self):
        from app.api.public.offer_portal import OfferRespostaRequest
        req = OfferRespostaRequest(acao="contraproposta", counter_salary=None)
        with pytest.raises(ValueError):
            req.validate_counter()

    def test_resposta_request_aceitar_still_works(self):
        from app.api.public.offer_portal import OfferRespostaRequest
        req = OfferRespostaRequest(acao="aceitar")
        assert req.acao == "aceitar"
        assert req.counter_salary is None

    def test_counter_salary_must_be_positive(self):
        from pydantic import ValidationError
        from app.api.public.offer_portal import OfferRespostaRequest
        with pytest.raises((ValidationError, ValueError)):
            OfferRespostaRequest(acao="contraproposta", counter_salary=-500.0)


# ── 3.6 — HITL threshold check ────────────────────────────────────────────────

class TestHITLThreshold:
    """Tests OfferService.check_hitl_threshold (3.6)."""

    def test_within_threshold(self):
        from app.domains.offer.services.offer_service import OfferService
        assert hasattr(OfferService, "check_hitl_threshold"), \
            "OfferService must have check_hitl_threshold method"

    @pytest.mark.asyncio
    async def test_threshold_within(self):
        from unittest.mock import AsyncMock
        from app.domains.offer.services.offer_service import OfferService
        svc = OfferService.__new__(OfferService)
        svc._db = AsyncMock()
        result = await svc.check_hitl_threshold(
            counter_salary=10500.0,
            original_salary=10000.0,
            offer_rules={"negotiation_hitl_threshold_pct": 10.0},
        )
        assert result["within_threshold"] is True
        assert result["delta_pct"] == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_threshold_exceeded(self):
        from unittest.mock import AsyncMock
        from app.domains.offer.services.offer_service import OfferService
        svc = OfferService.__new__(OfferService)
        svc._db = AsyncMock()
        result = await svc.check_hitl_threshold(
            counter_salary=12000.0,
            original_salary=10000.0,
            offer_rules={"negotiation_hitl_threshold_pct": 10.0},
        )
        assert result["within_threshold"] is False
        assert result["delta_pct"] == pytest.approx(20.0)

    @pytest.mark.asyncio
    async def test_threshold_fail_closed_no_salary(self):
        """Without original_salary, within_threshold must be False (fail-closed)."""
        from unittest.mock import AsyncMock
        from app.domains.offer.services.offer_service import OfferService
        svc = OfferService.__new__(OfferService)
        svc._db = AsyncMock()
        result = await svc.check_hitl_threshold(
            counter_salary=5000.0,
            original_salary=0,
            offer_rules={"negotiation_hitl_threshold_pct": 10.0},
        )
        assert result["within_threshold"] is False, \
            "Sem salario base, threshold deve falhar fechado (fail-closed)"


# ── 3.2 — OfferLearningService (LGPD gate N>=10) ─────────────────────────────

class TestOfferLearningContext:
    """Tests get_learning_context respects LGPD N>=10 gate (3.2)."""

    def test_get_learning_context_method_exists(self):
        from app.domains.offer.services.offer_service import OfferService
        assert hasattr(OfferService, "get_learning_context"), \
            "OfferService.get_learning_context must exist (3.2 learning patterns)"

    @pytest.mark.asyncio
    async def test_insufficient_data_gate(self):
        from unittest.mock import AsyncMock, patch
        from app.domains.offer.services.offer_service import OfferService
        svc = OfferService.__new__(OfferService)
        svc._db = AsyncMock()

        with patch(
            "app.domains.offer.repositories.offer_negotiation_event_repository"
            ".OfferNegotiationEventRepository.get_learning_data",
            new=AsyncMock(return_value=[{"event_type": "accepted"}] * 5),  # < 10
        ):
            result = await svc.get_learning_context("company-test")
        assert result["insufficient_data"] is True, \
            "Menos de 10 amostras deve retornar insufficient_data=True (ADR-LGPD-001)"

    @pytest.mark.asyncio
    async def test_sufficient_data_returns_stats(self):
        from unittest.mock import AsyncMock, patch
        from app.domains.offer.services.offer_service import OfferService
        svc = OfferService.__new__(OfferService)
        svc._db = AsyncMock()

        mock_events = (
            [{"event_type": "accepted", "round_number": 1}] * 6 +
            [{"event_type": "counter_proposed", "round_number": 1}] * 3 +
            [{"event_type": "declined", "round_number": 0}] * 1
        )  # total = 10

        with patch(
            "app.domains.offer.repositories.offer_negotiation_event_repository"
            ".OfferNegotiationEventRepository.get_learning_data",
            new=AsyncMock(return_value=mock_events),
        ):
            result = await svc.get_learning_context("company-test")
        assert result["insufficient_data"] is False
        assert "acceptance_rate_pct" in result
        assert result["sample_count"] == 10


# ── 3.3 — draft_response_to_candidate ────────────────────────────────────────

class TestDraftResponseTool:
    """Tests that draft_response_to_candidate has HITL invariant (3.3)."""

    def test_tool_function_exists(self):
        from app.domains.offer.agents.offer_tool_registry import _wrap_draft_response_to_candidate
        assert callable(_wrap_draft_response_to_candidate), \
            "_wrap_draft_response_to_candidate must be callable"

    def test_tool_has_hitl_invariant_in_source(self):
        from app.domains.offer.agents.offer_tool_registry import _wrap_draft_response_to_candidate
        src = inspect.getsource(_wrap_draft_response_to_candidate)
        assert "requires_hitl_approval" in src, \
            "draft_response_to_candidate must return requires_hitl_approval=True (HITL invariant)"
        assert "NUNCA" in src or "never" in src.lower(), \
            "draft_response_to_candidate must warn against direct sending without HITL"


# ── 3.8+3.9 — Tools N3 registradas no agent ──────────────────────────────────

class TestN3ToolsRegistration:
    """Tests that N3 tools are registered in get_offer_concierge_tools (3.8+3.9)."""

    def test_draft_response_tool_in_registry(self):
        from app.domains.offer.agents.offer_tool_registry import get_offer_concierge_tools
        tools = get_offer_concierge_tools()
        tool_names = {t.name for t in tools}
        assert "draft_response_to_candidate" in tool_names, \
            "draft_response_to_candidate deve estar registrado em get_offer_concierge_tools (3.3+3.9)"

    def test_learning_context_tool_in_registry(self):
        from app.domains.offer.agents.offer_tool_registry import get_offer_concierge_tools
        tools = get_offer_concierge_tools()
        tool_names = {t.name for t in tools}
        assert "get_learning_context" in tool_names, \
            "get_learning_context deve estar registrado (3.2+3.8 benefits argumentario)"
