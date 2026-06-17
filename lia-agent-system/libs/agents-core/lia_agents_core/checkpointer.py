"""
LangGraph Checkpointer — persistência de estado entre turnos.

Sprint R.1 (2026-05-21) — AsyncPostgresSaver substitui PostgresSaver sync.

Problema anterior:
    ``PostgresSaver`` (sync) NÃO implementa ``aget_tuple``. O wizard
    (``app/domains/job_creation/graph.py::aresume_with_message``) usa
    ``await graph.ainvoke(...)``, e LangGraph internamente chama
    ``await checkpointer.aget_tuple(...)`` no ``AsyncPregelLoop.__aenter__``
    — ``NotImplementedError`` levantava silenciosamente, fallback ia pra
    ``MemorySaver``, wizard perdia estado a cada restart do uvicorn.

Solução canônica:
    ``AsyncPostgresSaver`` (langgraph.checkpoint.postgres.aio) implementa
    ``aget_tuple`` nativamente sobre ``psycopg.AsyncConnection``.

Limitação técnica importante:
    ``AsyncPostgresSaver.__init__`` chama ``asyncio.get_running_loop()`` —
    PRECISA ser instanciado dentro de um event loop. Setup (``pool.open()``
    + ``saver.setup()``) também precisa de await.

Padrão de uso:
    1. ``await initialize_checkpointer_async()`` em ``app.main.lifespan``
       (ANTES de qualquer agente ser construído). Faz open+setup, popula
       cache.
    2. ``get_checkpointer()`` em sites de compile (sync) — retorna do cache.
    3. ``shutdown_checkpointer_async()`` em ``app.main.lifespan`` (FastAPI
       shutdown hook) — fecha pool.

Pool é singleton por processo. Reentrante (chamadas múltiplas ao initialize
não recriam pool).

Histórico:
    Onda 1.F (2026-05-10) — corrigiu ``PostgresSaver.from_conn_string`` →
    ConnectionPool (sync). Mas saver sync não implementa aget_tuple.
    Sprint R.1 (2026-05-21) — migra para AsyncPostgresSaver + AsyncConnectionPool.

Disciplinas CLAUDE.md aplicadas:
    - harness-engineering: REGRA 4 — fallback silent removido; warnings
      explícitos e exception-on-prod.
    - production-quality (ai-architecture): long-lived async pool com
      min/max size; sem conexão por request.
    - canonical-fix: AsyncPostgresSaver direto, não wrapper extra.
"""
import asyncio
import logging
from typing import Any, Optional

from lia_config.config import settings

logger = logging.getLogger(__name__)

# Singletons — populados por ``initialize_checkpointer_async`` e reusados
# pela vida do processo FastAPI.
_POOL_SINGLETON: Any = None
_SAVER_SINGLETON: Any = None
_SAVER_KIND: str = "uninitialized"  # "async_postgres" | "memory" | "uninitialized"


def _supports_async(saver: Any) -> bool:
    """
    Detecta se o saver implementa ``aget_tuple`` (não apenas herda do stub
    abstrato de ``BaseCheckpointSaver``).

    Task #1161 (Bug B) — sem essa checagem, ``PostgresSaver`` (sync) passava
    como "checkpointer válido" mas ``NotImplementedError`` aparecia no
    runtime async.
    """
    cls = type(saver)
    for ancestor in cls.__mro__:
        if ancestor.__module__.endswith("checkpoint.base") and ancestor.__name__ == "BaseCheckpointSaver":
            return False
        if "aget_tuple" in ancestor.__dict__:
            return True
    return False


def _normalize_db_url(db_url: str) -> str:
    """
    Converte URL SQLAlchemy/asyncpg → psycopg3-compatível.

    psycopg-pool (sync e async) usa ``conninfo`` formato libpq.
    """
    return (
        db_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
        .replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )


async def initialize_checkpointer_async() -> Any:
    """
    Inicializa o checkpointer canônico DENTRO de um event loop.

    Deve ser chamado em ``app.main.lifespan`` ANTES de qualquer agente ser
    instanciado (qualquer ``LangGraphBase.__init__`` chama
    ``get_checkpointer()``).

    Em production / staging:
        AsyncPostgresSaver obrigatório; RuntimeError se falhar.

    Em dev:
        AsyncPostgresSaver preferido; fallback para MemorySaver com
        WARNING.

    Idempotente — chamadas subsequentes retornam o saver cacheado.

    Returns:
        AsyncPostgresSaver ou MemorySaver (dev fallback).
    """
    global _POOL_SINGLETON, _SAVER_SINGLETON, _SAVER_KIND

    if _SAVER_SINGLETON is not None:
        return _SAVER_SINGLETON

    app_env = getattr(settings, "APP_ENV", "development")
    is_production_like = app_env in {"production", "staging"}

    # REGRA-4-EXEMPT: bootstrap singleton com fail-loud env-aware. Em
    # production/staging: raise RuntimeError (NAO fallback silent). Em dev:
    # MemorySaver com WARNING log + _SAVER_KIND="memory" (introspectavel
    # pelo caller, NAO mascara). Nao eh LLM call (LangGraph checkpointer
    # bootstrap). Audit anchor: 2026-05-21 P0.D triage.
    try:
        saver = await _build_async_postgres_saver()
    except Exception as exc:
        if is_production_like:
            raise RuntimeError(
                f"[Checkpointer] AsyncPostgresSaver FALHOU em ambiente "
                f"{app_env!r} — checkpoints seriam perdidos em restarts. "
                f"Corrija DATABASE_URL ou verifique "
                f"langgraph-checkpoint-postgres + psycopg-pool. Causa: {exc}"
            ) from exc
        logger.warning(
            "[Checkpointer] AsyncPostgresSaver indisponivel em ambiente %r "
            "(razao: %s). Usando MemorySaver — checkpoints NAO persistem "
            "entre restarts. Em production/staging isso causaria RuntimeError.",
            app_env, exc,
        )
        _SAVER_SINGLETON = _memory_saver()
        _SAVER_KIND = "memory"
        return _SAVER_SINGLETON

    if not _supports_async(saver):
        # Defesa em profundidade: AsyncPostgresSaver SEMPRE implementa
        # aget_tuple (checked em testes). Se essa branch dispara,
        # algo regrediu no langgraph-checkpoint-postgres.
        msg = (
            f"[Checkpointer] {type(saver).__name__} nao implementa "
            f"aget_tuple (regressão suspeita em langgraph-checkpoint-postgres). "
            f"Verificar versão instalada."
        )
        if is_production_like:
            raise RuntimeError(msg)
        logger.warning("%s Fallback dev -> MemorySaver.", msg)
        _SAVER_SINGLETON = _memory_saver()
        _SAVER_KIND = "memory"
        return _SAVER_SINGLETON

    _SAVER_SINGLETON = saver
    _SAVER_KIND = "async_postgres"
    logger.info(
        "[Checkpointer] AsyncPostgresSaver+AsyncConnectionPool ativo — "
        "checkpoints persistem entre restarts (env=%s)", app_env,
    )
    return saver


async def shutdown_checkpointer_async() -> None:
    """
    Fecha o pool async (chamado em FastAPI shutdown).

    Idempotente — seguro chamar múltiplas vezes.
    """
    global _POOL_SINGLETON, _SAVER_SINGLETON, _SAVER_KIND

    if _POOL_SINGLETON is not None:
        try:
            if not getattr(_POOL_SINGLETON, "closed", True):
                await _POOL_SINGLETON.close()
                logger.info("[Checkpointer] AsyncConnectionPool fechado")
        except Exception as exc:
            logger.warning("[Checkpointer] erro ao fechar pool: %s", exc)
        finally:
            _POOL_SINGLETON = None
            _SAVER_SINGLETON = None
            _SAVER_KIND = "uninitialized"


async def _build_async_postgres_saver() -> Any:
    """
    Constrói AsyncPostgresSaver + AsyncConnectionPool dentro do event loop
    atual.

    Pattern canonical:
        pool = AsyncConnectionPool(uri, max_size=N, min_size=M, open=False, ...)
        await pool.open()
        saver = AsyncPostgresSaver(pool)
        await saver.setup()  # idempotente — cria tabelas LangGraph se não existirem

    Pool é singleton em ``_POOL_SINGLETON`` (idempotência em reinicio).

    Raises:
        ImportError: psycopg-pool ou langgraph-checkpoint-postgres ausentes.
        RuntimeError: pool ou setup() falharam.
    """
    global _POOL_SINGLETON

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    except ImportError as exc:
        raise ImportError(
            "langgraph-checkpoint-postgres nao esta instalado. "
            "Execute: pip install langgraph-checkpoint-postgres>=3.0.0"
        ) from exc

    try:
        from psycopg_pool import AsyncConnectionPool
    except ImportError as exc:
        raise ImportError(
            "psycopg-pool nao esta instalado. "
            "Execute: pip install psycopg-pool>=3.3.0"
        ) from exc

    db_url = settings.DATABASE_URL or ""
    if not db_url:
        raise RuntimeError(
            "[Checkpointer] DATABASE_URL nao configurado "
            "(settings.DATABASE_URL vazio)."
        )
    sync_url = _normalize_db_url(db_url)

    try:
        # Reusa pool se ainda aberto (idempotência)
        if _POOL_SINGLETON is None or getattr(_POOL_SINGLETON, "closed", True):
            _POOL_SINGLETON = AsyncConnectionPool(
                conninfo=sync_url,
                max_size=20,
                min_size=2,
                open=False,  # abrimos explicitamente abaixo (dentro do loop)
                kwargs={"autocommit": True, "prepare_threshold": 0},
            )
            await _POOL_SINGLETON.open()
            logger.info(
                "[Checkpointer] AsyncConnectionPool aberto: min=%d max=%d",
                _POOL_SINGLETON.min_size, _POOL_SINGLETON.max_size,
            )

        saver = AsyncPostgresSaver(_POOL_SINGLETON)
        await saver.setup()  # idempotente; cria tabelas LangGraph se necessário
        return saver
    except Exception as exc:
        # Pool pode estar parcialmente inicializado; fecha pra evitar leak
        try:
            if _POOL_SINGLETON is not None and not getattr(_POOL_SINGLETON, "closed", True):
                await _POOL_SINGLETON.close()
        except Exception:
            pass
        _POOL_SINGLETON = None
        raise RuntimeError(
            f"AsyncPostgresSaver(AsyncConnectionPool) falhou: {exc}"
        ) from exc


def _memory_saver() -> Any:
    """Fallback dev-only. NÃO usar em production/staging."""
    try:
        from langgraph.checkpoint.memory import MemorySaver
        saver = MemorySaver()
        logger.debug("[Checkpointer] MemorySaver ativo (dev fallback)")
        return saver
    except ImportError:
        logger.warning("[Checkpointer] LangGraph nao instalado, checkpointer=None")
        return None


def get_checkpointer() -> Any:
    """
    Retorna o checkpointer canônico (sync API).

    Pré-requisito: ``initialize_checkpointer_async()`` deve ter sido chamado
    antes (idealmente em ``app.main.lifespan``).

    Caso seja chamado antes do initialize (e.g., import time em algum agente
    instanciado precocemente), tenta initialize sync via fallback:
      - production/staging: RuntimeError (não-recuperável)
      - dev: MemorySaver fallback com WARNING

    Sites de compile (``graph.compile(checkpointer=saver)``) chamam este;
    saver retornado é AsyncPostgresSaver no caminho canônico, e usos
    posteriores via ``await saver.aget_tuple(...)`` funcionam porque
    AsyncPostgresSaver implementa async nativo.

    Returns:
        AsyncPostgresSaver, MemorySaver, ou None se langgraph ausente.
    """
    global _SAVER_SINGLETON

    if _SAVER_SINGLETON is not None:
        return _SAVER_SINGLETON

    # initialize_checkpointer_async ainda não foi chamado — tentar sync
    # fallback. Em production/staging isso é erro de boot; em dev cai em
    # MemorySaver para não derrubar testes/REPL.
    app_env = getattr(settings, "APP_ENV", "development")
    is_production_like = app_env in {"production", "staging"}

    if is_production_like:
        raise RuntimeError(
            f"[Checkpointer] get_checkpointer() chamado antes de "
            f"initialize_checkpointer_async() em APP_ENV={app_env!r}. "
            f"AsyncPostgresSaver precisa de event loop pra inicializar — "
            f"chame initialize_checkpointer_async() no lifespan da app."
        )

    logger.warning(
        "[Checkpointer] get_checkpointer() chamado antes de "
        "initialize_checkpointer_async() em dev. Retornando MemorySaver "
        "fallback. Em production/staging isso seria RuntimeError."
    )
    _SAVER_SINGLETON = _memory_saver()
    return _SAVER_SINGLETON


def get_checkpointer_kind() -> str:
    """
    Retorna kind do checkpointer ativo: ``async_postgres``, ``memory``,
    ou ``uninitialized``. Usado por health checks (e.g.,
    ``app/api/v1/health_langgraph.py``).
    """
    return _SAVER_KIND


# ───────────────────────────────────────────────────────────────────────────
# Backward-compat shim para tests legados (Onda 1.F) que mockam
# ``_postgres_saver`` como sync. Sprint R.1 substituiu por
# ``_build_async_postgres_saver`` (async). Tests que patcheiam o nome
# antigo continuam funcionando — basta serem migrados para
# ``_build_async_postgres_saver`` quando alguém tocar nesses tests.
# ───────────────────────────────────────────────────────────────────────────
def _postgres_saver() -> Any:  # pragma: no cover — legacy shim, target de patch em tests
    """
    DEPRECATED (Sprint R.1, 2026-05-21): substituído por
    ``_build_async_postgres_saver`` (async). Mantido apenas como alvo de
    patch em tests legados (``test_langgraph_native_regression.py``,
    ``test_langgraph_agents_e2e.py``).
    """
    raise NotImplementedError(
        "_postgres_saver removido em Sprint R.1. Use "
        "initialize_checkpointer_async() para canonical async ou patch "
        "_build_async_postgres_saver em tests."
    )
