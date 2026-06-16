"""WT-2022 P3.1 smoke test: PolicyGateService rotea V2 canonical quando engine
expõe `evaluate`, e backcompat V1 quando expõe apenas `validate_request`.

Garante:
1. Feature-detection V1 vs V2 funciona (presença de método `evaluate`).
2. EvaluationResult V2 → PolicyResult conversão preserva semântica.
3. Default instantiation no MainOrchestrator usa V2 canonical.
4. Fail-safe em exception do engine → PolicyResult(allowed=False) com reason.
5. SAFE_INTENTS bypassa engine completamente (fast-path read-only).

Ref:
- ADR-WT-2022-policy-engine-migration.md
- app/orchestrator/services/policy_gate_service.py (impl)
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — mock factories
# ─────────────────────────────────────────────────────────────────────────────


def _mock_v2_engine(decision: str = "ALLOW", requires_approval: bool = False):
    """Cria mock PolicyEngineService V2 com método `evaluate` (sem `validate_request`)."""
    engine = MagicMock(spec=["evaluate", "check_rate_limit"])
    engine.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            decision=decision,
            allowed=(decision == "ALLOW"),
            requires_approval=requires_approval,
            approval_config=None,
            rate_limit_status=None,
            matching_rule=None,
            matching_rule_id=None,
            evaluation_time_ms=12.3,
            rules_evaluated=0,
            reason=f"V2 decision={decision}",
        )
    )
    return engine


def _mock_v1_engine(allowed: bool = True, reason: str = ""):
    """Cria mock PolicyEngine V1 com `validate_request` (sem `evaluate`)."""
    engine = MagicMock(spec=["validate_request", "record_usage"])
    engine.validate_request = AsyncMock(
        return_value={"allowed": allowed, "reason": reason, "constraints": {}}
    )
    engine.record_usage = AsyncMock(return_value=None)
    return engine


# ─────────────────────────────────────────────────────────────────────────────
# Feature detection — V1 vs V2 routing
# ─────────────────────────────────────────────────────────────────────────────


def test_policy_gate_detects_v2_when_engine_has_evaluate():
    """V2 detection via `hasattr(engine, 'evaluate')` + ausência de `validate_request`."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v2_engine()
    gate = PolicyGateService(policy_engine=engine)
    assert gate.engine_version == "v2"


def test_policy_gate_detects_v1_when_engine_has_validate_request_only():
    """V1 backcompat: engine sem `evaluate` mas com `validate_request` → routing v1."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v1_engine()
    gate = PolicyGateService(policy_engine=engine)
    assert gate.engine_version == "v1"


def test_policy_gate_unrecognized_engine_falls_back_to_none():
    """Engine sem nenhum método canonical → routing 'none' (allow-all fallback)."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    bogus_engine = SimpleNamespace(some_unrelated_method=lambda: None)
    gate = PolicyGateService(policy_engine=bogus_engine)
    assert gate.engine_version == "none"


# ─────────────────────────────────────────────────────────────────────────────
# Validate routing — V2 path
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_policy_gate_v2_path_calls_engine_evaluate_with_action_mapping():
    """V2 path mapeia intent → action canonical e chama engine.evaluate."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v2_engine(decision="ALLOW")
    gate = PolicyGateService(policy_engine=engine)

    result = await gate.validate(
        intent="candidate_search",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    assert result.allowed is True
    engine.evaluate.assert_awaited_once()
    call_kwargs = engine.evaluate.await_args.kwargs
    # intent "candidate_search" → action "candidate_search" (1-pra-1 via _INTENT_TO_V2_ACTION)
    assert call_kwargs["action"] == "candidate_search"
    assert call_kwargs["company_id"] == "co-1"
    assert call_kwargs["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_policy_gate_v2_communication_intent_maps_to_send_communication_action():
    """Intent V1 coordinator-style → action V2 generic (boundary explícito)."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v2_engine()
    gate = PolicyGateService(policy_engine=engine)

    await gate.validate(
        intent="communication",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    call_kwargs = engine.evaluate.await_args.kwargs
    assert call_kwargs["action"] == "send_communication"


@pytest.mark.asyncio
async def test_policy_gate_v2_deny_decision_returns_allowed_false():
    """EvaluationResult.decision=DENY → PolicyResult.allowed=False."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v2_engine(decision="DENY")
    gate = PolicyGateService(policy_engine=engine)

    result = await gate.validate(
        intent="candidate_search",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    assert result.allowed is False


# ─────────────────────────────────────────────────────────────────────────────
# SAFE_INTENTS fast-path — não chama engine
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_policy_gate_safe_intent_bypasses_engine():
    """`general_chat`, `help`, etc. são SAFE_INTENTS → fast-path sem engine call."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = _mock_v2_engine()
    gate = PolicyGateService(policy_engine=engine)

    result = await gate.validate(
        intent="general_chat",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    assert result.allowed is True
    engine.evaluate.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Fail-safe — exception nunca propaga ao caller
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_policy_gate_fail_safe_on_v2_engine_exception():
    """Exception em engine.evaluate → PolicyResult(allowed=False) com reason explanatório."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    engine = MagicMock(spec=["evaluate"])
    engine.evaluate = AsyncMock(side_effect=RuntimeError("DB connection lost"))
    gate = PolicyGateService(policy_engine=engine)

    result = await gate.validate(
        intent="candidate_search",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    assert result.allowed is False
    assert result.reason
    reason_lower = result.reason.lower()
    # reason deve mencionar engine/error/runtime — para LLM/oncall diagnosticar
    assert (
        "error" in reason_lower
        or "runtimeerror" in reason_lower
        or "validation" in reason_lower
    )


@pytest.mark.asyncio
async def test_policy_gate_engine_none_returns_allow_all_fallback():
    """Engine None (não inicializado) → allow-all + constraints.engine_unavailable."""
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    # Forçar engine=None via mock que não bate em nenhum spec
    gate = PolicyGateService(policy_engine=SimpleNamespace())
    assert gate.engine_version == "none"

    result = await gate.validate(
        intent="candidate_search",
        user_id="user-1",
        context={"company_id": "co-1"},
    )

    assert result.allowed is True
    assert result.constraints.get("engine_unavailable") is True


# ─────────────────────────────────────────────────────────────────────────────
# Default instantiation — MainOrchestrator boots com V2
# ─────────────────────────────────────────────────────────────────────────────


def test_policy_gate_default_no_arg_instantiates_v2_when_available():
    """`PolicyGateService()` sem argumento → instancia V2 canonical default."""
    from app.orchestrator.services.policy_gate_service import (
        PolicyGateService,
        _V2_AVAILABLE,
    )

    if not _V2_AVAILABLE:
        pytest.skip("V2 PolicyEngineService not importable in this environment")

    gate = PolicyGateService()
    assert gate.engine_version == "v2"
