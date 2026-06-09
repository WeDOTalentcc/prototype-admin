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


def test_timeout_degraded_response_not_blocked_by_audit():
    """Fix 504: a resposta degradada do deadline NAO pode esperar o audit/circuit (DB
    pode estar lento quando o Pearch estoura). Efeitos colaterais vao para background
    (asyncio.create_task) e a resposta degradada retorna na hora."""
    import inspect
    from app.api.v1.candidate_search import search as search_module

    src = inspect.getsource(search_module.search_candidates)
    # efeitos colaterais do timeout encapsulados e disparados em background
    assert "_emit_timeout_side_effects" in src
    assert "asyncio.create_task(_emit_timeout_side_effects())" in src
    # o audit do timeout vive dentro da funcao de side-effects (nao awaited inline antes do return)
    _idx_fn = src.index("_emit_timeout_side_effects")
    _idx_ret = src.index("returning degraded response")
    # a definicao da funcao de side-effects aparece depois do log de degraded
    assert _idx_fn > _idx_ret


def test_pearch_call_deadline_covers_api_latency():
    """BUG-PEARCH-TIMEOUT (2026-06-09): API Pearch v2 /v2/search demora ~26s
    em prod (retrieval ~14s + scoring ~5s + insights ~4s). O deadline anterior
    era 12s — cancelava TODAS as buscas globais silenciosamente.
    Ratchet: PEARCH_CALL_DEADLINE_SECONDS >= 30s (margem sobre 26s medidos)."""
    from lia_config.config import Settings
    s = Settings()
    assert s.PEARCH_CALL_DEADLINE_SECONDS >= 30.0, (
        f"PEARCH_CALL_DEADLINE_SECONDS={s.PEARCH_CALL_DEADLINE_SECONDS} < 30s. "
        "A API Pearch v2 /v2/search demora ~26s — deadline insuficiente cancela "
        "TODA busca global silenciosamente. Manter >= 30s."
    )


def test_route_deadline_exceeds_pearch_call_deadline():
    """Invariante: SEARCH_CANDIDATES_DEADLINE_SECONDS > PEARCH_CALL_DEADLINE_SECONDS.
    Garante que o timeout interno da chamada Pearch dispara ANTES do deadline
    da rota — preservando candidatos locais ja encontrados em vez de cancelar
    a coroutine inteira e retornar vazio."""
    from lia_config.config import Settings
    s = Settings()
    assert s.SEARCH_CANDIDATES_DEADLINE_SECONDS > s.PEARCH_CALL_DEADLINE_SECONDS, (
        f"SEARCH_CANDIDATES_DEADLINE_SECONDS ({s.SEARCH_CANDIDATES_DEADLINE_SECONDS}) "
        f"nao eh maior que PEARCH_CALL_DEADLINE_SECONDS ({s.PEARCH_CALL_DEADLINE_SECONDS}). "
        "O deadline da rota deve ser maior para preservar candidatos locais."
    )



def test_pearch_called_even_when_local_exceeds_pearch_limit():
    import inspect
    from app.domains.sourcing.services import pearch_service as ps_module
    hs_src = inspect.getsource(ps_module.PearchService.hybrid_search)
    assert '_target = request.pearch_limit' in hs_src, (
        'BUG-PEARCH-TARGET regressao: hybrid_search deve usar '
        '_target = request.pearch_limit sem subtrair local_candidates. '
        'Quando local >= pearch_limit, _target ficava 0 e Pearch nao era chamado.'
    )
    old_formula = '_target = max(0, request.pearch_limit - len(local_candidates))'
    assert old_formula not in hs_src, (
        'BUG-PEARCH-TARGET: formula antiga reintroduzida. '
        'Ela zerava _target quando local >= pearch_limit -- Pearch nunca chamado.'
    )
