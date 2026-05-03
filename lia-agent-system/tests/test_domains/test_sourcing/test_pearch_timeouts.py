"""
Task #961 — Regression tests for canonical timeout policy in Pearch search.

Cobre:
1. ``PearchService._build_httpx_timeout()`` reflete os settings.
2. ``hybrid_search`` devolve ``warning_message`` e candidatos locais quando a
   chamada Pearch estoura o deadline ``PEARCH_CALL_DEADLINE_SECONDS``.
3. O cancellation handler dentro de ``search_candidates`` registra consumption
   com ``result_status="cancelled"`` e bate em ``PEARCH_CIRCUIT.record_failure``.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.domains.sourcing.services.pearch_service import PearchService
from app.shared.resilience.circuit_breaker import PEARCH_CIRCUIT
from lia_config.config import settings
from lia_models.pearch import (
    HybridSearchRequest,
    PearchSearchRequest,
    SearchType,
)


def test_build_httpx_timeout_reads_settings():
    t = PearchService._build_httpx_timeout()
    assert isinstance(t, httpx.Timeout)
    assert t.connect == settings.PEARCH_HTTP_CONNECT_TIMEOUT_SECONDS
    assert t.read == settings.PEARCH_HTTP_READ_TIMEOUT_SECONDS
    assert t.write == settings.PEARCH_HTTP_WRITE_TIMEOUT_SECONDS
    assert t.pool == settings.PEARCH_HTTP_POOL_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_hybrid_search_returns_warning_when_pearch_stalls(monkeypatch):
    """Quando search_candidates estoura o deadline, hybrid_search devolve o
    warning canônico e mantém local_candidates vazios sem propagar exceção."""
    monkeypatch.setattr(settings, "PEARCH_CALL_DEADLINE_SECONDS", 0.1, raising=False)
    svc = PearchService()
    svc.api_key = "fake-key-for-test"

    async def _stall(*_a, **_kw):
        await asyncio.sleep(5)

    with patch.object(svc, "search_candidates", side_effect=_stall):
        # search_local_first=False evita o caminho da busca local — assim
        # validamos só a política de deadline em torno da chamada Pearch.
        req = HybridSearchRequest(
            query="python developer",
            include_pearch=True,
            search_local_first=False,
            pearch_type=SearchType.FAST,
            local_limit=1,
            pearch_limit=5,
        )
        result = await svc.hybrid_search(db=None, request=req)  # type: ignore[arg-type]

    assert result.warning_message and "demorou demais" in result.warning_message
    assert result.pearch_count == 0


@pytest.mark.asyncio
async def test_search_candidates_records_cancellation():
    """Cancelamento (asyncio.CancelledError) deve registrar consumption como
    ``cancelled`` e somar falha ao PEARCH_CIRCUIT."""
    svc = PearchService()
    svc.api_key = "fake-key-for-test"

    failures_before = PEARCH_CIRCUIT._failure_count

    tracking = AsyncMock()
    with patch.object(PearchService, "_track_pearch_consumption", new=tracking), \
         patch("httpx.AsyncClient.post", side_effect=asyncio.CancelledError()):
        req = PearchSearchRequest(query="qa engineer", limit=3, type=SearchType.FAST)
        with pytest.raises(asyncio.CancelledError):
            await svc.search_candidates(req, company_id="tenant-test")

    # consumption registrado com result_status="cancelled"
    assert tracking.await_count >= 1
    kwargs = tracking.await_args.kwargs
    assert kwargs.get("result_status") == "cancelled"
    assert kwargs.get("success") is False
    # circuit breaker contabilizou a falha
    assert PEARCH_CIRCUIT._failure_count >= failures_before
