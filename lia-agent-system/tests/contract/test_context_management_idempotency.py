"""
Contract sensor — ContextManager idempotency dual-ID canonical (W2-009).

WHY THIS SENSOR EXISTS
======================
Recovery Tri-2 #1 (2026-05-23) descobriu que ``context_management.py`` perdeu
3 peças críticas pelo merge incident 02361f41c (1/mai/2026):
  - ``_DUAL_ID_PARAM_RESOLVERS`` constant (canonical mapping ID → resolver)
  - ``ContextManager._canonicalize_params()`` async classmethod
  - ``ContextManager.generate_idempotency_key_async()`` async method

Caller ``app/shared/robustness/idempotency.py:76`` ainda chama
``await ctx.generate_idempotency_key_async()`` → AttributeError em runtime.

Impact: **24 tests failing em ``test_idempotency_dual_id.py``** desde maio.
Cada retry de operação (Apply/Job/Candidate) com UUID vs Rails bigint
hashava pra keys diferentes — operação executa DUAS vezes em produção.
W2-009 dual-ID idempotency broken por 22 dias.

Pattern: BLOCKING. Idempotency é hard requirement pra Rails sync (ADR 003).
"""
from __future__ import annotations

import inspect


def test_context_manager_has_generate_idempotency_key_async():
    """
    ``ContextManager.generate_idempotency_key_async()`` async method deve
    existir. Sync ``generate_idempotency_key()`` também existe pra non-dual-ID.
    """
    from app.shared.robustness.context_management import ContextManager
    c = ContextManager("sess-1", "user-1")
    assert hasattr(c, "generate_idempotency_key_async"), (
        "generate_idempotency_key_async ausente. idempotency.py:76 chama "
        "await ctx.generate_idempotency_key_async() — sem isso é AttributeError."
    )
    assert inspect.iscoroutinefunction(c.generate_idempotency_key_async), (
        "generate_idempotency_key_async deve ser async (coroutine function)."
    )


def test_context_manager_has_canonicalize_params():
    """
    ``ContextManager._canonicalize_params()`` async classmethod deve existir.
    Função interna que collapsa dual-ID params (UUID/bigint) pra canonical
    Rails bigint antes de hash.
    """
    from app.shared.robustness.context_management import ContextManager
    assert hasattr(ContextManager, "_canonicalize_params"), (
        "_canonicalize_params ausente. generate_idempotency_key_async depende dele."
    )


def test_dual_id_param_resolvers_canonical():
    """
    ``ContextManager._DUAL_ID_PARAM_RESOLVERS`` mapping ID → resolver method
    name. Mínimo 4 keys canonical: candidate_id, job_id, job_vacancy_id,
    application_id (per ADR 003 + Task #486).
    """
    from app.shared.robustness.context_management import ContextManager
    resolvers = ContextManager._DUAL_ID_PARAM_RESOLVERS
    canonical_keys = {
        "candidate_id",
        "candidate",
        "job_id",
        "vacancy_id",
        "job_vacancy_id",  # Task #486
        "application_id",
        "apply_id",
    }
    missing = canonical_keys - set(resolvers.keys())
    assert not missing, (
        f"_DUAL_ID_PARAM_RESOLVERS faltando canonical keys: {sorted(missing)}\n"
        f"Sem essas keys o canonicalization branch silently no-ops e UUID/bigint "
        f"retries hashan pra duas keys diferentes (idempotency violado, ADR 003)."
    )


async def test_generate_idempotency_key_async_same_key_for_same_params():
    """Same op + params → same key (basic determinism)."""
    from app.shared.robustness.context_management import ContextManager
    c = ContextManager("sess-1", "user-1")
    k1 = await c.generate_idempotency_key_async("op", {"x": 1})
    k2 = await c.generate_idempotency_key_async("op", {"x": 1})
    assert k1 == k2, "Same params should produce same key (idempotency basic)"


async def test_generate_idempotency_key_async_no_adapter_passthrough():
    """Without adapter, behavior == sync version (params verbatim hash)."""
    from app.shared.robustness.context_management import ContextManager
    c = ContextManager("sess-1", "user-1")
    sync_key = c.generate_idempotency_key("op", {"candidate_id": "abc"})
    async_key = await c.generate_idempotency_key_async("op", {"candidate_id": "abc"}, adapter=None)
    assert sync_key == async_key, (
        "Sem adapter, async variant deve hash igual ao sync (passthrough). "
        "Garante backward-compat pra callers que ainda não passam adapter."
    )
