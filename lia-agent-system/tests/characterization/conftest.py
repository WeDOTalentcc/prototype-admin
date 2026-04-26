"""
Shared fixtures for Orchestrator V1 characterization tests.

Sprint I — Tarefa C of orchestrator migration plan.
See: Documents/Python/ORCHESTRATOR_MIGRATION_SPRINT_I.md

Lições aplicadas:
- harness-engineering: sensors before guides — testes existem para CAPTURAR comportamento, não validar regras
- production-quality P0: cada fixture cobre multi-tenant + LGPD edge cases por padrão
"""
from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import AsyncMock, MagicMock

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
            module="app.orchestrator.orchestrator",
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
    """DB session mockada."""
    return MagicMock()


@pytest.fixture
def mock_audit_service() -> MagicMock:
    """AuditService mockado — captura chamadas para verificar audit log."""
    mock = MagicMock()
    mock.log_decision = AsyncMock()
    mock.log_action = AsyncMock()
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# V1 Orchestrator factory (lazy import to avoid loading at collection time)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def orchestrator_v1_factory():
    """
    Factory que cria instâncias de V1 Orchestrator com dependencies mockadas.

    Uso:
        async def test_xyz(orchestrator_v1_factory, mock_llm_service):
            v1 = orchestrator_v1_factory(llm_service=mock_llm_service)
            result = await v1.process_request(...)

    NOTA: A assinatura exata de Orchestrator.__init__ pode mudar — fixture deve
    ser ajustada conforme `app/orchestrator/orchestrator.py` evoluir durante
    Sprint I. Por enquanto retorna factory que aceita kwargs e tenta delegar.
    """

    def _factory(**overrides):
        # Lazy import — V1 só é carregado quando teste roda
        from app.orchestrator.orchestrator import Orchestrator

        # NOTE: V1 emite DeprecationWarning no __init__, suppressed pelo autouse fixture.
        # Os kwargs reais devem ser descobertos durante implementação dos tests
        # individuais (test_v1_process_request.py etc).
        return Orchestrator(**overrides)

    return _factory


# ─────────────────────────────────────────────────────────────────────────────
# Marker helpers
# ─────────────────────────────────────────────────────────────────────────────
def pytest_collection_modifyitems(config, items):
    """Marca todos os characterization tests como medium por padrão."""
    for item in items:
        if "characterization" in str(item.fspath):
            item.add_marker(pytest.mark.medium)
