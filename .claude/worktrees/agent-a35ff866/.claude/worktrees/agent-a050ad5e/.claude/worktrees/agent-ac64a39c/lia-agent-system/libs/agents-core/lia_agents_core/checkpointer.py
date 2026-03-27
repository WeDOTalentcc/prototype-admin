"""
LangGraph Checkpointer — persistência de estado entre turnos.

Suporta dois modos:
1. MemorySaver (padrão dev) — in-process, perdido ao reiniciar
2. PostgresSaver (produção) — persiste no PostgreSQL via tabelas nativas LangGraph

Selecionado pela flag USE_LANGGRAPH_NATIVE:
  False → MemorySaver (sem deps extras)
  True  → tenta PostgresSaver; comportamento em falha depende de APP_ENV:
           - dev: WARNING + fallback para MemorySaver
           - production: RuntimeError (checkpoints não podem se perder silenciosamente)

Uso:
    saver = get_checkpointer()
    graph = graph_builder.compile(checkpointer=saver)
"""
import logging
from typing import Any

from lia_config.config import settings

logger = logging.getLogger(__name__)


def get_checkpointer() -> Any:
    """
    Retorna o checkpointer adequado ao ambiente.

    Em produção (APP_ENV=production + USE_LANGGRAPH_NATIVE=True):
      - PostgresSaver obrigatório; RuntimeError se indisponível.

    Em desenvolvimento (USE_LANGGRAPH_NATIVE=True, APP_ENV!=production):
      - PostgresSaver preferido; fallback para MemorySaver com WARNING explícito.

    Com USE_LANGGRAPH_NATIVE=False:
      - Sempre MemorySaver (checkpointer da Fase 2 legado).
    """
    if not settings.USE_LANGGRAPH_NATIVE:
        return _memory_saver()

    try:
        return _postgres_saver()
    except Exception as exc:
        is_production = getattr(settings, "APP_ENV", "development") == "production"
        if is_production:
            raise RuntimeError(
                f"[Checkpointer] PostgresSaver FALHOU em produção — checkpoints seriam perdidos "
                f"em restarts. Corrija a configuração DATABASE_URL ou verifique "
                f"langgraph-checkpoint-postgres. Causa: {exc}"
            ) from exc
        # Dev/staging: WARNING explícito + fallback
        logger.warning(
            "[Checkpointer] PostgresSaver indisponível em ambiente '%s' (razão: %s). "
            "Usando MemorySaver — checkpoints NÃO persistem entre restarts. "
            "Em produção isso causaria RuntimeError.",
            getattr(settings, "APP_ENV", "development"),
            exc,
        )
        return _memory_saver()


def _memory_saver() -> Any:
    try:
        from langgraph.checkpoint.memory import MemorySaver
        saver = MemorySaver()
        logger.debug("[Checkpointer] MemorySaver ativo")
        return saver
    except ImportError:
        logger.warning("[Checkpointer] LangGraph não instalado, checkpointer=None")
        return None


def _postgres_saver() -> Any:
    """
    Cria PostgresSaver usando langgraph-checkpoint-postgres.

    Converte DATABASE_URL de asyncpg para psycopg2 (sync) pois o PostgresSaver
    usa psycopg2 internamente para setup das tabelas.

    Levanta exceção em caso de falha — o caller decide o comportamento.
    """
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError as exc:
        raise ImportError(
            "langgraph-checkpoint-postgres não está instalado. "
            "Execute: pip install langgraph-checkpoint-postgres>=2.0.0"
        ) from exc

    # Converte URL asyncpg → psycopg2 sync (PostgresSaver usa psycopg2)
    db_url = settings.DATABASE_URL
    sync_url = (
        db_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
    )

    try:
        saver = PostgresSaver.from_conn_string(sync_url)
        saver.setup()  # cria tabelas se não existirem (idempotente)
        logger.info(
            "[Checkpointer] PostgresSaver (langgraph-checkpoint-postgres) ativo — "
            "checkpoints persistem entre restarts"
        )
        return saver
    except Exception as exc:
        raise RuntimeError(
            f"PostgresSaver.from_conn_string() falhou: {exc}"
        ) from exc
