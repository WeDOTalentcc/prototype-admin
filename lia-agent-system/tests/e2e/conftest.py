"""
Pytest configuration for e2e tests.

O event_loop fixture não é definido aqui — o pytest.ini já configura
asyncio_default_fixture_loop_scope = session, fornecendo um único loop
compartilhado por toda a sessão (evita conflitos com asyncpg/ASGITransport).
"""
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


# ---------------------------------------------------------------------------
# Flag-control fixtures — adicionadas para suíte E2E multi-cenário
# ---------------------------------------------------------------------------
import os
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def federated_flags(monkeypatch):
    """Cenário A: LIA_FEDERATED_PRIMARY=true, supervisor=false."""
    monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "true")
    monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "false")
    monkeypatch.setenv("LIA_HITL_GATE", "on")
    yield
    monkeypatch.delenv("LIA_FEDERATED_PRIMARY", raising=False)
    monkeypatch.delenv("LIA_BUBBLE_VIA_SUPERVISOR", raising=False)
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)


@pytest.fixture
def supervisor_flags(monkeypatch):
    """Cenário B: LIA_BUBBLE_VIA_SUPERVISOR=true, federated=false."""
    monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "false")
    monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "true")
    monkeypatch.setenv("LIA_HITL_GATE", "on")
    yield
    monkeypatch.delenv("LIA_FEDERATED_PRIMARY", raising=False)
    monkeypatch.delenv("LIA_BUBBLE_VIA_SUPERVISOR", raising=False)
    monkeypatch.delenv("LIA_HITL_GATE", raising=False)


@pytest.fixture
def baseline_flags(monkeypatch):
    """Baseline: CascadedRouter isolado (ambas flags false)."""
    monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "false")
    monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "false")
    yield


@pytest.fixture
def mock_company_id():
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def mock_jwt_headers(mock_company_id):
    """Headers com company_id canônico (simulado via JWT)."""
    return {
        "Authorization": "Bearer test-token",
        "X-Company-ID": mock_company_id,
    }
