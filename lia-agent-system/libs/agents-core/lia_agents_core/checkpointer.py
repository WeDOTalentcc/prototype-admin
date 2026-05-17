"""
LangGraph Checkpointer — persistência de estado entre turnos.

Suporta dois modos:
1. PostgresSaver+ConnectionPool (canonical) — persiste no PostgreSQL via
   tabelas nativas LangGraph; pool long-lived gerencia conexões durante a
   vida do processo FastAPI.
2. MemorySaver (dev fallback) — in-process, perdido ao reiniciar.

Selecionado pelo ambiente (APP_ENV):
  production / staging → PostgresSaver obrigatório; RuntimeError se indisponível.
  outros               → PostgresSaver preferido; fallback para MemorySaver
                         com WARNING explícito.

Uso:
    saver = get_checkpointer()
    graph = graph_builder.compile(checkpointer=saver)

Histórico de correção (Onda 1 — PLAN_FIX_wizard_memory_loss 2026-05-10):
    BUG ANTERIOR: ``PostgresSaver.from_conn_string(uri)`` retornava um
    context manager (``Iterator[PostgresSaver]``) em
    ``langgraph-checkpoint-postgres>=2.0.8``. O código antigo tratava o
    retorno como saver direto e chamava ``.setup()``, levantando
    ``AttributeError: '_GeneratorContextManager' object has no attribute
    'setup'``. O ``except Exception`` em ``get_checkpointer()`` engolia o
    erro → fallback silencioso para ``MemorySaver`` em TODOS os ambientes.

    FIX CANONICAL: usar ``ConnectionPool`` (psycopg-pool) + construir
    ``PostgresSaver(pool)`` diretamente. Pool gerencia conexões long-lived,
    sem fechar no exit do bloco ``with`` — adequado para servidor FastAPI.

    Evidência empírica do bug (auditoria 2026-05-10): tabela ``checkpoints``
    em prod-live tinha TOTAL = 1 row (smoke audit-only) — zero wizards
    reais haviam persistido em todo o histórico antes deste fix.

Disciplinas CLAUDE.md aplicadas:
    - canonical-fix: 2 linhas trocadas (from_conn_string → ConnectionPool +
      PostgresSaver(pool)). Sem refactor além do necessário.
    - harness-engineering: GUIDE canonical do pattern + SENSOR via
      ``tests/integration/test_checkpointer_canonical.py``.
    - production-quality (ai-architecture + integration-patterns):
      long-lived pool com min/max size; sem conexão por request.
"""
import logging
from typing import Any

from lia_config.config import settings

logger = logging.getLogger(__name__)

# Pool singleton — criado uma vez pelo primeiro _postgres_saver() bem-sucedido
# e reutilizado pela vida do processo. None até a primeira chamada bem-sucedida.
_POOL_SINGLETON: Any = None


def _supports_async(saver: Any) -> bool:
    """
    Task #1161 — Bug B root cause guard.

    O wizard (``app/domains/job_creation/graph.py::aresume_with_message``)
    chama ``await self._graph.ainvoke(Command(resume=...))``. LangGraph,
    por sua vez, chama ``await checkpointer.aget_tuple(...)`` dentro do
    ``AsyncPregelLoop.__aenter__``. Se o saver retornado NÃO sobrescrever
    ``aget_tuple`` (caso do ``PostgresSaver`` sync — que herda o stub
    abstrato de ``BaseCheckpointSaver``), o resultado é
    ``NotImplementedError`` silenciado pelo ``_emit_silent_fallback`` do
    ``wizard_session_service`` — exatamente o sintoma do Task #1161.

    Detecta isso checando se ``aget_tuple`` foi sobrescrito em algum lugar
    da MRO além da classe abstrata base.
    """
    cls = type(saver)
    for ancestor in cls.__mro__:
        if ancestor.__module__.endswith("checkpoint.base") and ancestor.__name__ == "BaseCheckpointSaver":
            return False
        if "aget_tuple" in ancestor.__dict__:
            return True
    return False


def get_checkpointer() -> Any:
    """
    Retorna o checkpointer adequado ao ambiente.

    Em produção / staging (``APP_ENV in {"production", "staging"}``):
      - PostgresSaver obrigatório; ``RuntimeError`` se indisponível.

    Em desenvolvimento (``APP_ENV != "production" and != "staging"``):
      - PostgresSaver preferido; fallback para MemorySaver com WARNING.

    Defense in depth: ``app.main.lifespan`` deve abortar boot quando este
    retornar MemorySaver em APP_ENV não-dev (sensor de boot fail-closed).

    Task #1161 (Bug B root cause): se o saver não suportar
    ``aget_tuple`` (caso da classe sync ``PostgresSaver``), em DEV cai
    para ``MemorySaver`` (que é ``InMemorySaver`` e implementa async); em
    prod-like levanta ``RuntimeError`` exigindo migração para
    ``AsyncPostgresSaver``.
    """
    app_env = getattr(settings, "APP_ENV", "development")
    is_production_like = app_env in {"production", "staging"}

    try:
        saver = _postgres_saver()
    except Exception as exc:
        if is_production_like:
            raise RuntimeError(
                f"[Checkpointer] PostgresSaver FALHOU em ambiente {app_env!r} — "
                f"checkpoints seriam perdidos em restarts. Corrija "
                f"DATABASE_URL ou verifique langgraph-checkpoint-postgres + "
                f"psycopg-pool. Causa: {exc}"
            ) from exc
        logger.warning(
            "[Checkpointer] PostgresSaver indisponivel em ambiente %r (razao: %s). "
            "Usando MemorySaver — checkpoints NAO persistem entre restarts. "
            "Em production/staging isso causaria RuntimeError.",
            app_env,
            exc,
        )
        return _memory_saver()

    if not _supports_async(saver):
        msg = (
            f"[Checkpointer] {type(saver).__name__} nao implementa aget_tuple "
            f"(sync-only). O wizard.aresume_with_message usa async ainvoke e "
            f"langgraph chamaria aget_tuple => NotImplementedError (Task #1161 "
            f"Bug B). Use AsyncPostgresSaver para producao."
        )
        if is_production_like:
            raise RuntimeError(msg)
        logger.warning("%s Fallback dev -> MemorySaver.", msg)
        return _memory_saver()

    return saver


def _memory_saver() -> Any:
    """Fallback dev-only. NAO usar em production/staging."""
    try:
        from langgraph.checkpoint.memory import MemorySaver
        saver = MemorySaver()
        logger.debug("[Checkpointer] MemorySaver ativo (dev fallback)")
        return saver
    except ImportError:
        logger.warning("[Checkpointer] LangGraph nao instalado, checkpointer=None")
        return None


def _postgres_saver() -> Any:
    """
    Cria PostgresSaver canonical com ConnectionPool long-lived.

    Pattern canonical para FastAPI long-running:
        pool = ConnectionPool(uri, max_size=N, min_size=M, open=True, ...)
        saver = PostgresSaver(pool)
        saver.setup()  # idempotente — cria tabelas LangGraph se nao existirem

    O pool e singleton (``_POOL_SINGLETON``) para evitar recriar conexoes em
    cada call de ``_postgres_saver()`` durante reload uvicorn (importante em
    dev).

    Levanta excecao em caso de falha — caller decide o comportamento.

    Raises:
        ImportError: psycopg-pool ou langgraph-checkpoint-postgres ausentes.
        RuntimeError: pool ou setup() falharam.
    """
    global _POOL_SINGLETON

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError as exc:
        raise ImportError(
            "langgraph-checkpoint-postgres nao esta instalado. "
            "Execute: pip install langgraph-checkpoint-postgres>=2.0.8"
        ) from exc

    try:
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise ImportError(
            "psycopg-pool nao esta instalado. "
            "Execute: pip install psycopg-pool>=3.3.0"
        ) from exc

    db_url = settings.DATABASE_URL or ""
    # PostgresSaver usa psycopg3 sync via pool; converter async drivers
    sync_url = (
        db_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
        .replace("postgresql+psycopg2://", "postgresql://")
    )
    if not sync_url:
        raise RuntimeError(
            "[Checkpointer] DATABASE_URL nao configurado (settings.DATABASE_URL vazio)."
        )

    try:
        # Reusa pool existente se ainda aberto (idempotencia em reload uvicorn)
        if _POOL_SINGLETON is None or getattr(_POOL_SINGLETON, "closed", True):
            _POOL_SINGLETON = ConnectionPool(
                conninfo=sync_url,
                max_size=20,
                min_size=2,
                open=True,
                # autocommit e mandatory para o setup() do PostgresSaver
                kwargs={"autocommit": True},
            )
            logger.info(
                "[Checkpointer] ConnectionPool criado: min=%d max=%d",
                _POOL_SINGLETON.min_size, _POOL_SINGLETON.max_size,
            )

        saver = PostgresSaver(_POOL_SINGLETON)
        saver.setup()  # idempotente; cria tabelas LangGraph se necessario
        logger.info(
            "[Checkpointer] PostgresSaver+ConnectionPool ativo — "
            "checkpoints persistem entre restarts"
        )
        return saver
    except Exception as exc:
        # Pool pode estar parcialmente inicializado; fecha para evitar leak
        try:
            if _POOL_SINGLETON is not None and not getattr(_POOL_SINGLETON, "closed", True):
                _POOL_SINGLETON.close()
        except Exception:
            pass
        _POOL_SINGLETON = None
        raise RuntimeError(
            f"PostgresSaver(ConnectionPool) falhou: {exc}"
        ) from exc
