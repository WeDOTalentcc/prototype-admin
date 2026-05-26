"""
Async helper canonical para evitar `asyncio.run` em sync nodes do LangGraph.

Sprint Pipeline Templates (2026-05-26) revelou Python 3.12+ risk em sync nodes
que tentam executar coroutines via `_asyncio.run()` quando ha event loop ativo.

Pattern canonical:
- Quando ha running loop: `loop.create_task(coro)` fire-and-forget (audit)
                          ou ThreadPoolExecutor + asyncio.run (quando precisa await)
- Quando NAO ha running loop: `asyncio.run(coro)` e seguro

Sites Tipo A (audit puro): use `emit_audit_fire_and_forget()`
Sites Tipo C (need result): use `run_coro_in_threadpool()`

Sensor R5 (`scripts/check_no_asyncio_run_in_sync_nodes.py`) trava regressao.
"""
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


async def _safe_audit_coro(coro: Coroutine[Any, Any, Any]) -> None:
    """Wraps audit coro em try/except sem propagar exception (fire-and-forget)."""
    try:
        await coro
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Audit log fire-and-forget failed silently: %s",
            exc,
            exc_info=True,
        )


def emit_audit_fire_and_forget(
    coro_factory: Callable[[], Coroutine[Any, Any, Any]],
) -> None:
    """Emite audit log SEM bloquear o sync node.

    Pattern canonical (substitui `_asyncio.run(audit.log_decision(...))`):

    ```python
    # ❌ ANTIPATTERN (bloqueia event loop ou raise RuntimeError em Py 3.12+):
    _asyncio.run(audit.log_decision(action="x", ...))

    # ✅ CANONICAL:
    emit_audit_fire_and_forget(
        lambda: audit.log_decision(action="x", ...)
    )
    ```

    Args:
        coro_factory: Callable que retorna a coroutine de audit. Lazy para
            evitar RuntimeWarning de coro nunca-awaited se loop nao estiver
            ativo.

    Behavior:
    - Running loop: agenda como task -> nao bloqueia, excecoes logadas
    - No loop: skip silenciosamente + log warning (audit perdido mas node funciona)
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Nao ha event loop ativo. Audit log perdido — mas raro em producao
        # (sync nodes do LangGraph SEMPRE rodam num event loop).
        logger.warning(
            "emit_audit_fire_and_forget: no running loop, audit skipped",
        )
        return

    try:
        coro = coro_factory()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Audit coro factory raised: %s — skipping audit",
            exc,
            exc_info=True,
        )
        return

    # Fire-and-forget: task roda em background, exceptions vao pra _safe_audit_coro
    loop.create_task(_safe_audit_coro(coro))


def run_coro_in_threadpool(
    coro_factory: Callable[[], Coroutine[Any, Any, Any]],
    timeout: float | None = None,
) -> Any:
    """Executa coroutine que PRECISA retornar resultado em sync node.

    Usado quando: sync node precisa do resultado de uma coro (nao pode
    fire-and-forget) E ha event loop ativo (Python 3.12+ raise se chamar
    `asyncio.run` aqui).

    Pattern canonical (substitui `_asyncio.run(coro)` em sync nodes):

    ```python
    # ANTIPATTERN:
    result = _asyncio.run(fetch_data())  # RuntimeError Py 3.12+

    # CANONICAL:
    result = run_coro_in_threadpool(lambda: fetch_data())
    # com timeout (lanca concurrent.futures.TimeoutError se exceder):
    result = run_coro_in_threadpool(lambda: fetch_data(), timeout=30.0)
    ```

    Args:
        coro_factory: Callable que retorna a coroutine. Lazy para evitar
            RuntimeWarning de coro nunca-awaited.
        timeout: Timeout em segundos para future.result(). None = sem timeout
            (default). Lanca `concurrent.futures.TimeoutError` se exceder
            (apenas quando ha event loop ativo e ThreadPoolExecutor e usado).
            PR-14 (2026-05-26): parametro adicionado para suportar migration
            dos 4 gates do wizard que usavam timeout=30s.

    Behavior:
    - Running loop: ThreadPoolExecutor cria thread separada + novo loop ali,
      executa coro, retorna resultado. Bloqueia sync node ate completar ou
      timeout (esperado — caller precisa do resultado).
    - No loop: usa `asyncio.run(coro)` direto (seguro). timeout ignorado
      neste caminho (coro completa naturalmente).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Sem loop ativo, asyncio.run e seguro
        return asyncio.run(coro_factory())

    # Event loop ativo — ThreadPoolExecutor cria nova thread + novo loop ali
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro_factory())
        return future.result(timeout=timeout)
