"""
Task #961 — Regression test for canonical timeout policy in Pearch search.

NOTA (2026-05-31): a política de timeout foi REFATORADA da camada de serviço
(PearchService._build_httpx_timeout / _emit_timeout_audit / settings
PEARCH_CALL_DEADLINE_SECONDS) para a camada de ROTA
(app/api/v1/candidate_search/search.py — `_route_deadline` +
SEARCH_CANDIDATES_DEADLINE_SECONDS + audit inline `pearch.search.timeout`).

Os 3 testes antigos que validavam a implementação na camada de serviço foram
removidos por serem stale (davam patch em métodos/settings que não existem mais:
`_build_httpx_timeout`, `_emit_timeout_audit`, `PEARCH_CALL_DEADLINE_SECONDS`,
`PEARCH_HTTP_*_TIMEOUT_SECONDS`). O comportamento canônico agora vive na rota e é
guardado pelo teste abaixo, que inspeciona o source da rota diretamente.
"""
from __future__ import annotations


def test_search_route_uses_config_deadline_not_hardcoded():
    """Task #961 — garante que a rota /search/candidates lê o deadline e o
    search_time_seconds da config canônica (SEARCH_CANDIDATES_DEADLINE_SECONDS)
    em vez de literais hard-coded como 18.0; e que emite o evento
    ``pearch.search.timeout`` no path degradado."""
    import inspect
    from app.api.v1.candidate_search import search as search_module

    src = inspect.getsource(search_module.search_candidates)

    # 1) deadline da rota vem da config
    assert "_settings.SEARCH_CANDIDATES_DEADLINE_SECONDS" in src, (
        "Route deadline deve ler settings.SEARCH_CANDIDATES_DEADLINE_SECONDS"
    )
    # 2) `timeout=` deve referenciar a variável _route_deadline, não literal
    assert "timeout=_route_deadline" in src
    # 3) search_time_seconds devolvido na resposta degradada usa _route_deadline,
    #    não o literal 18.0 do hotfix anterior.
    assert "search_time_seconds=_route_deadline" in src
    assert "search_time_seconds=18.0" not in src
    # 4) audit explícito do timeout — action_type canônico.
    assert '"pearch.search.timeout"' in src
    # 5) circuit breaker é alimentado quando search_pearch=True na rota.
    assert "PEARCH_CIRCUIT.record_failure" in src
