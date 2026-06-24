"""Unit — hybrid_search: timeout do Pearch preserva candidatos LOCAIS (P1-11).

Antes: hybrid_search chamava self.search_candidates SEM deadline interno. Um
Pearch lento estourava o deadline da ROTA (asyncio.wait_for em search.py), que
cancelava a coroutine inteira -> o except retornava candidates=[] e local=0,
descartando ate os candidatos locais ja materializados.

Fix: deadline interno (_PEARCH_CALL_DEADLINE_SECONDS) ao redor de
search_candidates. Pearch lento vira TimeoutError CAPTURADO pelo except
existente -> candidatos locais preservados + warning honesto, e a coroutine
retorna RAPIDO (nao estoura o deadline da rota).
"""
import asyncio
import time

import pytest

from app.domains.sourcing.services import pearch_service as ps
from lia_models.pearch import CandidateProfile, HybridSearchRequest


@pytest.mark.asyncio
async def test_pearch_lento_preserva_locais_e_retorna_rapido(monkeypatch):
    # deadline interno curto; raising=False p/ funcionar mesmo no estado Red (sem o fix)
    monkeypatch.setattr(ps, "_PEARCH_CALL_DEADLINE_SECONDS", 0.15, raising=False)

    svc = ps.PearchService()
    svc.api_key = "fake-key"  # entra no bloco Pearch

    local = CandidateProfile(name="ZZ Local Tester", current_title="Product Manager", docid=None)

    async def _fake_local(**kwargs):
        return ([local], 1)

    async def _slow_pearch(_req):
        await asyncio.sleep(2.0)  # excede o deadline interno
        return None

    monkeypatch.setattr(svc, "search_local_candidates", _fake_local)
    monkeypatch.setattr(svc, "search_candidates", _slow_pearch)

    req = HybridSearchRequest(
        query="product manager",
        include_pearch=True,
        search_local_first=True,
        require_emails=False,
        pearch_limit=5,
        local_limit=50,
    )

    t0 = time.monotonic()
    resp = await svc.hybrid_search(db=object(), request=req)
    elapsed = time.monotonic() - t0

    # Sem o fix: o Pearch lento (2s) roda inteiro -> elapsed ~2s (FALHA aqui).
    # Com o fix: o wait_for corta em ~0.15s -> elapsed << 1s.
    assert elapsed < 1.0, f"hybrid_search nao limitou o Pearch lento (elapsed={elapsed:.2f}s)"
    assert resp.local_count == 1, "candidatos locais deveriam sobreviver ao timeout do Pearch"
    assert resp.pearch_count == 0
    assert resp.warning_message and "externa" in resp.warning_message.lower()
