"""
Sprint III.A tests — DI injection in MainOrchestrator V2.

Garante que V2 funciona em 2 modos:
1. Modo legacy: __init__(orchestrator) — sem services (default, backward compat)
2. Modo Sprint III: __init__(orchestrator, plan_service=..., ...) — com services

Sprint III.A NÃO usa os services ainda. V1 delegation é caminho default.
Sprint III.B vai usar os services com feature flag.

Reference: ADR-019 — Sprint III.A
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator.execution.main_orchestrator import MainOrchestrator


class TestBackwardCompatibility:
    """V2 continua funcional com __init__ antigo (V1 only)."""

    def test_init_with_only_orchestrator(self):
        """Sprint III.A: __init__(orchestrator) sem services — modo legacy."""
        v1_orch = MagicMock()
        v2 = MainOrchestrator(orchestrator=v1_orch)

        # V1 ref preservada
        assert v2._orchestrator is v1_orch

        # Compliance services criados (FairnessGuard, TenantContextService)
        assert v2._fairness_guard is not None
        assert v2._tenant_context_service is not None

    def test_services_default_to_none(self):
        """Default: nenhum service injetado — V1 delegation continua sendo caminho."""
        v1_orch = MagicMock()
        v2 = MainOrchestrator(orchestrator=v1_orch)

        assert v2._plan_service is None
        assert v2._fallback_react_service is None
        # WT-2022 P3.1 (2026-05-21): _policy_gate_service auto-instancia V2
        # default quando não injetado (antes era None) — Phase 0.5 sempre on.
        assert v2._policy_gate_service is not None


class TestServicesInjection:
    """Sprint III.A: __init__ aceita services via DI."""

    def test_inject_plan_service(self):
        v1 = MagicMock()
        plan_svc = MagicMock()
        v2 = MainOrchestrator(orchestrator=v1, plan_service=plan_svc)
        assert v2._plan_service is plan_svc

    def test_inject_fallback_react_service(self):
        v1 = MagicMock()
        fb_svc = MagicMock()
        v2 = MainOrchestrator(orchestrator=v1, fallback_react_service=fb_svc)
        assert v2._fallback_react_service is fb_svc

    def test_inject_policy_gate_service(self):
        v1 = MagicMock()
        policy_svc = MagicMock()
        v2 = MainOrchestrator(orchestrator=v1, policy_gate_service=policy_svc)
        assert v2._policy_gate_service is policy_svc

    def test_inject_all_services(self):
        """Inject all 3 services — pre-condição para Sprint III.B feature flag."""
        v1 = MagicMock()
        plan_svc = MagicMock()
        fb_svc = MagicMock()
        policy_svc = MagicMock()

        v2 = MainOrchestrator(
            orchestrator=v1,
            plan_service=plan_svc,
            fallback_react_service=fb_svc,
            policy_gate_service=policy_svc,
        )

        assert v2._orchestrator is v1
        assert v2._plan_service is plan_svc
        assert v2._fallback_react_service is fb_svc
        assert v2._policy_gate_service is policy_svc

    def test_services_are_keyword_only(self):
        """Services são keyword-only (defesa contra positional misuse)."""
        v1 = MagicMock()
        # Tentar passar plan_service como positional → TypeError
        with pytest.raises(TypeError):
            MainOrchestrator(v1, MagicMock())  # type: ignore[misc]
