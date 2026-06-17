"""
Shared fixtures for Orchestrator V1 characterization tests.

Sprint I — Tarefa C of orchestrator migration plan.
See: Documents/Python/ORCHESTRATOR_MIGRATION_SPRINT_I.md

Lições aplicadas:
- harness-engineering: sensors before guides — testes existem para CAPTURAR comportamento, não validar regras
- production-quality P0: cada fixture cobre multi-tenant + LGPD edge cases por padrão

## Fixtures de orquestrador

Há DUAS estratégias de mocking. Escolha conforme o tipo de test:

1. `v1_with_minimal_mocks` — só LLM + cache mockados, resto é real
   Use para: testes de métodos PUROS (heurísticas, getters, métodos sem I/O)

2. `v1_with_all_internal_mocks` — mocka policy_engine, state_manager, router, etc.
   Use para: testes de FLUXO (process_request, transições de estado, contracts)

## Convenção LGPD

Atributos protegidos NUNCA aparecem em fixtures. `lgpd_protected_attributes`
é a lista canônica que tests usam para validar que código não vaza esses
atributos em prompts/logs/spans.
"""
from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Suppress LIA-D06 DeprecationWarning during characterization tests
# (V1 IS deprecated — that's the whole point of this test suite)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _silence_lia_d06_deprecation():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module="app.orchestrator.legacy.orchestrator",
        )
        yield


# ─────────────────────────────────────────────────────────────────────────────
# Multi-tenant context fixtures
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def tenant_a_context() -> dict[str, Any]:
    """Contexto multi-tenant base para tenant A."""
    return {
        "company_id": "company-a-uuid",
        "user_id": "user-a1",
        "user_role": "recruiter",
        "scope": "recruiter_assistant",
    }


@pytest.fixture
def tenant_b_context() -> dict[str, Any]:
    """Contexto multi-tenant base para tenant B (para testar isolation)."""
    return {
        "company_id": "company-b-uuid",
        "user_id": "user-b1",
        "user_role": "recruiter",
        "scope": "recruiter_assistant",
    }


@pytest.fixture
def admin_context() -> dict[str, Any]:
    """Contexto super_admin (scope=null implica all tools)."""
    return {
        "company_id": "company-admin-uuid",
        "user_id": "admin-1",
        "user_role": "super_admin",
        "scope": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LGPD edge cases — atributos protegidos não podem vazar
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def lgpd_protected_attributes() -> list[str]:
    """Atributos LGPD que NUNCA podem aparecer em prompt de ranking."""
    return [
        "race", "raca",
        "religion", "religiao",
        "gender", "genero",
        "ethnicity", "etnia",
        "marital_status", "estado_civil",
        "health", "saude",
        "sexual_orientation", "orientacao_sexual",
    ]


@pytest.fixture
def message_with_protected_attribute() -> str:
    """Mensagem que tenta usar atributo protegido — deve ser bloqueada."""
    return "Filtre candidatos pela raça branca"


# ─────────────────────────────────────────────────────────────────────────────
# Mocked services (sem hit em DB/LLM real)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def mock_llm_service() -> MagicMock:
    """LLM service mockado — retornos previsíveis."""
    mock = MagicMock()
    mock.complete = AsyncMock(return_value={"content": "mocked response", "tokens": 10})
    mock.complete_with_tools = AsyncMock(
        return_value={
            "content": "mocked response with tools",
            "tools_used": [],
            "tokens": 12,
        }
    )
    return mock


@pytest.fixture
def mock_db_session() -> MagicMock:
    """DB session mockada (síncrona)."""
    return MagicMock()


@pytest.fixture
def async_db() -> MagicMock:
    """DB session com commit/rollback async (para process_request_with_memory)."""
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_audit_service() -> MagicMock:
    """AuditService mockado — captura chamadas para verificar audit log."""
    mock = MagicMock()
    mock.log_decision = AsyncMock()
    mock.log_action = AsyncMock()
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL ORCHESTRATOR V1 FIXTURES — escolha conforme tipo de test
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def v1_with_minimal_mocks():
    """
    V1 Orchestrator com mocks MÍNIMOS — apenas LLM + cache.

    Use quando o teste exercita lógica PURA do V1 (heurísticas, getters,
    métodos sem I/O DB). Os componentes reais (`TaskPlanner`, `PolicyEngine`,
    `StateManager`, `CascadedRouter`, `DomainWorkflow`) são instanciados.

    Exemplos de uso adequado:
        - test_is_technical_response (heurística pura)
        - test_is_cv_matching_request (heurística pura)
        - test_get_metrics (getter)
        - test_get_cache_stats (getter delegando para cache mockado)
        - test_get_scope_system_prompt (lookup determinístico)
        - test_is_tool_allowed (lookup com tool_registry real)
        - test_get_available_tools (filtro com tool_registry real)
    """
    from app.orchestrator.legacy.orchestrator import Orchestrator

    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(return_value={"content": "ok", "tokens": 5})

    with patch("app.orchestrator.legacy.orchestrator.response_cache_service") as mock_cache:
        mock_cache.is_enabled.return_value = False
        mock_cache.get_stats.return_value = {"hits": 0, "misses": 0, "size": 0}
        v1 = Orchestrator(llm_service=mock_llm, db_service=None)
    return v1


@pytest.fixture
def v1_with_all_internal_mocks():
    """
    V1 Orchestrator com TODOS os componentes internos mockados.

    Use quando o teste exercita FLUXO completo do `process_request` ou
    `process_request_with_memory` — onde policy/state/router/domain são
    chamados em sequência. Mockar tudo dá controle previsível sobre o flow.

    Componentes mockados:
        - llm_service (já no fixture base)
        - response_cache_service (já patched)
        - state_manager (MagicMock — sem DB)
        - policy_engine (validate_request retorna allowed=True por padrão)
        - _cascaded_router (route retorna RouteResult test estável)
        - _domain_workflow (execute retorna DomainResponseStub)
        - _plan_detector (detect retorna None — sem plan)

    Exemplos de uso adequado:
        - test_returns_dict_with_required_keys (process_request happy path)
        - test_cancel_message_returns_cancelled_flag (early return)
        - test_company_id_propagated_to_router (multi-tenant flow)
        - test_context_overrides_routing (hardcoded mapping)
        - test_policy_denied_returns_failure (policy gate)
    """
    from app.orchestrator.legacy.orchestrator import Orchestrator

    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(return_value={"content": "ok", "tokens": 5})

    with patch("app.orchestrator.legacy.orchestrator.response_cache_service") as mock_cache:
        mock_cache.is_enabled.return_value = False
        mock_cache.get_stats.return_value = {"hits": 0, "misses": 0}

        v1 = Orchestrator(llm_service=mock_llm, db_service=None)

        # state_manager — sem DB
        v1.state_manager = MagicMock()
        v1.state_manager.get_state.return_value = None
        v1.state_manager.create_conversation.return_value = "conv-test-1"
        v1.state_manager.add_message = MagicMock()
        v1.state_manager.update_state = MagicMock()
        v1.state_manager.clear_state = MagicMock()

        # policy_engine — allowed por padrão
        v1.policy_engine = MagicMock()
        v1.policy_engine.validate_request = AsyncMock(
            return_value={"allowed": True, "constraints": {}}
        )

        # cascaded_router — RouteResult previsível
        from app.orchestrator.routing.cascaded_router import RouteResult
        v1._cascaded_router = MagicMock()
        v1._cascaded_router.route = AsyncMock(
            return_value=RouteResult(
                domain_id="recruiter_assistant",
                confidence=0.9,
                source="test",
                intent_details={"raw_intent": "test_intent"},
            )
        )

        # domain_workflow — DomainResponseStub-like
        v1._domain_workflow = MagicMock()
        _stub = MagicMock()
        _stub.success = True
        _stub.message = "domain workflow response"
        _stub.data = {"items": []}
        _stub.suggestions = []
        _stub.next_actions = []
        v1._domain_workflow.execute = AsyncMock(return_value=_stub)

        # plan_detector — sem plano por padrão
        v1._plan_detector = MagicMock()
        v1._plan_detector.detect.return_value = None

        yield v1


# ─────────────────────────────────────────────────────────────────────────────
# Marker helpers
# ─────────────────────────────────────────────────────────────────────────────
def pytest_collection_modifyitems(config, items):
    """Marca todos os characterization tests como medium por padrão."""
    for item in items:
        if "characterization" in str(item.fspath):
            item.add_marker(pytest.mark.medium)
