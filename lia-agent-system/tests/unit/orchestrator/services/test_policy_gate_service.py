"""
Unit tests for PolicyGateService — Sprint II.5 of LIA-D06 migration.

Tests garantem:
- API type-safe via PolicyResult dataclass
- Backward compat com PolicyEngine legacy dict format
- Fast-path para SAFE_INTENTS (sem chamar engine)
- Multi-tenant safety (P0 LGPD)
- Fail-safe behavior (exceções viram allowed=False)

Reference: ADR-019 — Sprint II.5
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator.services.policy_gate_service import (
    SAFE_INTENTS,
    PolicyGateService,
    PolicyResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# PolicyResult — type-safe wrapper tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyResult:
    """Validações da PolicyResult dataclass."""

    def test_default_values(self):
        """Defaults seguros: vazia, denied implicitly via allowed=False explicit."""
        result = PolicyResult(allowed=True)
        assert result.allowed is True
        assert result.reason == ""
        assert result.constraints == {}
        assert result.intent == ""
        assert result.user_id == ""

    def test_is_frozen(self):
        """PolicyResult é imutável (frozen dataclass)."""
        result = PolicyResult(allowed=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.allowed = False  # type: ignore[misc]

    def test_constraints_default_is_empty_dict_not_none(self):
        """P0: constraints sempre dict, nunca None (evita None checks no caller)."""
        result = PolicyResult(allowed=False, reason="denied")
        assert result.constraints == {}
        assert isinstance(result.constraints, dict)

    def test_requires_approval_property_true(self):
        result = PolicyResult(
            allowed=True,
            reason="HITL required",
            constraints={"requires_approval": True},
        )
        assert result.requires_approval is True

    def test_requires_approval_property_false_default(self):
        """Sem constraint requires_approval, retorna False."""
        result = PolicyResult(allowed=True)
        assert result.requires_approval is False

    def test_from_legacy_dict_allowed(self):
        """Conversão de dict legado para PolicyResult (allowed)."""
        legacy = {"allowed": True, "reason": "", "constraints": {}}
        result = PolicyResult.from_legacy_dict(legacy, intent="test", user_id="u1")
        assert result.allowed is True
        assert result.intent == "test"
        assert result.user_id == "u1"

    def test_from_legacy_dict_denied_with_reason(self):
        legacy = {"allowed": False, "reason": "Daily limit reached"}
        result = PolicyResult.from_legacy_dict(legacy, intent="search", user_id="u2")
        assert result.allowed is False
        assert result.reason == "Daily limit reached"

    def test_from_legacy_dict_with_constraints(self):
        legacy = {
            "allowed": False,
            "reason": "Bulk action requires approval",
            "constraints": {"requires_approval": True, "max_bulk": 10},
        }
        result = PolicyResult.from_legacy_dict(legacy, intent="bulk", user_id="u3")
        assert result.requires_approval is True
        assert result.constraints["max_bulk"] == 10

    def test_from_legacy_dict_handles_missing_keys(self):
        """from_legacy_dict é defensive — keys ausentes têm defaults seguros."""
        legacy: dict = {}  # dict vazio
        result = PolicyResult.from_legacy_dict(legacy, intent="x", user_id="y")
        assert result.allowed is False  # Default seguro
        assert result.reason == ""
        assert result.constraints == {}

    def test_to_legacy_dict_round_trip(self):
        """Round-trip: PolicyResult → dict → PolicyResult preserva valores."""
        original = PolicyResult(
            allowed=True,
            reason="ok",
            constraints={"max_tokens": 1000},
            intent="general_chat",
            user_id="u1",
        )
        legacy = original.to_legacy_dict()
        assert legacy == {
            "allowed": True,
            "reason": "ok",
            "constraints": {"max_tokens": 1000},
        }

    def test_to_legacy_dict_creates_copy(self):
        """to_legacy_dict cria cópia — modificar não afeta original (frozen)."""
        result = PolicyResult(allowed=True, constraints={"k": "v"})
        legacy = result.to_legacy_dict()
        legacy["constraints"]["k"] = "modified"
        # PolicyResult frozen — original.constraints intacto
        assert result.constraints == {"k": "v"}


# ─────────────────────────────────────────────────────────────────────────────
# PolicyGateService — fast path tests (SAFE_INTENTS)
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyGateServiceSafeIntents:
    """Fast-path: SAFE_INTENTS bypassam o engine."""

    @pytest.fixture
    def mock_engine(self) -> MagicMock:
        engine = MagicMock()
        engine.validate_request = AsyncMock(return_value={"allowed": True})
        return engine

    @pytest.mark.asyncio
    async def test_general_chat_is_safe_intent(self, mock_engine):
        """general_chat é SAFE → não chama engine."""
        gate = PolicyGateService(policy_engine=mock_engine)
        result = await gate.validate(
            intent="general_chat", user_id="u1", context={"company_id": "tenant-a"}
        )
        assert result.allowed is True
        # Engine NÃO foi chamado
        mock_engine.validate_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_navigation_is_safe_intent(self, mock_engine):
        gate = PolicyGateService(policy_engine=mock_engine)
        result = await gate.validate(
            intent="navigation", user_id="u1", context={"company_id": "tenant-a"}
        )
        assert result.allowed is True
        mock_engine.validate_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_help_is_safe_intent(self, mock_engine):
        gate = PolicyGateService(policy_engine=mock_engine)
        result = await gate.validate(
            intent="help", user_id="u1", context={"company_id": "tenant-a"}
        )
        assert result.allowed is True
        mock_engine.validate_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_feedback_is_safe_intent(self, mock_engine):
        gate = PolicyGateService(policy_engine=mock_engine)
        result = await gate.validate(intent="feedback", user_id="u1")
        assert result.allowed is True

    def test_safe_intents_constant_is_frozen(self):
        """SAFE_INTENTS é frozenset (imutável em runtime)."""
        assert isinstance(SAFE_INTENTS, frozenset)
        assert "general_chat" in SAFE_INTENTS


# ─────────────────────────────────────────────────────────────────────────────
# PolicyGateService — engine delegation tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyGateServiceDelegation:
    """Quando intent não é SAFE, delega para PolicyEngine."""

    @pytest.fixture
    def mock_engine_allow(self) -> MagicMock:
        engine = MagicMock()
        engine.validate_request = AsyncMock(
            return_value={"allowed": True, "reason": "", "constraints": {}}
        )
        return engine

    @pytest.fixture
    def mock_engine_deny(self) -> MagicMock:
        engine = MagicMock()
        engine.validate_request = AsyncMock(
            return_value={
                "allowed": False,
                "reason": "Daily search limit reached",
                "constraints": {"daily_limit": 50, "current_usage": 50},
            }
        )
        return engine

    @pytest.mark.asyncio
    async def test_candidate_search_delegates_to_engine(self, mock_engine_allow):
        """candidate_search NÃO é safe → delega ao engine."""
        gate = PolicyGateService(policy_engine=mock_engine_allow)
        result = await gate.validate(
            intent="candidate_search",
            user_id="u1",
            context={"company_id": "tenant-a"},
        )
        assert result.allowed is True
        mock_engine_allow.validate_request.assert_called_once()
        # Verifica que kwargs corretos foram passados
        call = mock_engine_allow.validate_request.call_args
        assert call.kwargs["intent"] == "candidate_search"
        assert call.kwargs["user_id"] == "u1"

    @pytest.mark.asyncio
    async def test_engine_denial_returns_denied_result(self, mock_engine_deny):
        gate = PolicyGateService(policy_engine=mock_engine_deny)
        result = await gate.validate(
            intent="candidate_search",
            user_id="u1",
            context={"company_id": "tenant-a"},
        )
        assert result.allowed is False
        assert "limit" in result.reason.lower()
        assert result.constraints["daily_limit"] == 50

    @pytest.mark.asyncio
    async def test_intent_and_user_id_in_result(self, mock_engine_allow):
        """PolicyResult inclui intent e user_id (não está no dict legado)."""
        gate = PolicyGateService(policy_engine=mock_engine_allow)
        result = await gate.validate(
            intent="screening_request",
            user_id="user-abc",
            context={"company_id": "tenant-a"},
        )
        assert result.intent == "screening_request"
        assert result.user_id == "user-abc"


# ─────────────────────────────────────────────────────────────────────────────
# PolicyGateService — fail-safe behavior
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyGateServiceFailSafe:
    """Engine exceções viram allowed=False com reason — nunca propagam."""

    @pytest.fixture
    def mock_engine_raises(self) -> MagicMock:
        engine = MagicMock()
        engine.validate_request = AsyncMock(side_effect=ConnectionError("DB down"))
        return engine

    @pytest.mark.asyncio
    async def test_engine_exception_returns_denied(self, mock_engine_raises):
        gate = PolicyGateService(policy_engine=mock_engine_raises)
        result = await gate.validate(
            intent="candidate_search",
            user_id="u1",
            context={"company_id": "tenant-a"},
        )
        assert result.allowed is False
        assert "ConnectionError" in result.reason or "DB down" in result.reason
        assert result.constraints.get("error") is True

    @pytest.mark.asyncio
    async def test_engine_exception_does_not_propagate(self, mock_engine_raises):
        """Caller jamais recebe exceção — sempre PolicyResult."""
        gate = PolicyGateService(policy_engine=mock_engine_raises)
        # Não deve lançar — apenas retornar denied
        try:
            await gate.validate(
                intent="candidate_search", user_id="u1", context={"company_id": "x"}
            )
        except ConnectionError:
            pytest.fail("PolicyGateService deveria ter capturado a exceção")


# ─────────────────────────────────────────────────────────────────────────────
# PolicyGateService — usage tracking
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyGateServiceUsageTracking:
    """record_usage delega ao engine para rate limiting tracking."""

    def test_record_usage_delegates_to_engine(self):
        engine = MagicMock()
        engine.record_usage = MagicMock()
        gate = PolicyGateService(policy_engine=engine)
        gate.record_usage(tenant_id="tenant-a", usage_type="chat_requests")
        engine.record_usage.assert_called_once_with(
            tenant_id="tenant-a", usage_type="chat_requests"
        )

    def test_record_usage_default_usage_type(self):
        engine = MagicMock()
        engine.record_usage = MagicMock()
        gate = PolicyGateService(policy_engine=engine)
        gate.record_usage(tenant_id="tenant-a")
        # Default usage_type = "chat_requests"
        engine.record_usage.assert_called_once_with(
            tenant_id="tenant-a", usage_type="chat_requests"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PolicyGateService — DI + access to underlying engine
# ─────────────────────────────────────────────────────────────────────────────


class TestPolicyGateServiceDI:
    """Dependency injection + access to underlying engine."""

    def test_underlying_engine_accessor(self):
        """underlying_engine permite acesso para casos especiais e testes."""
        engine = MagicMock()
        gate = PolicyGateService(policy_engine=engine)
        assert gate.underlying_engine is engine

    def test_init_without_engine_creates_v2_default(self):
        """WT-2022 P3.1: engine é OPCIONAL — sem engine, cria V2 default
        (PolicyEngineService) em vez de exigir injeção. Não levanta
        TypeError (docstring de PolicyGateService.__init__ confirma)."""
        gate = PolicyGateService()
        assert gate is not None
