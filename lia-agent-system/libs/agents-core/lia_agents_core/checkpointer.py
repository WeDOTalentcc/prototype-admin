"""
LangGraph Checkpointer — persistência de estado entre turnos.

Suporta dois modos:
1. MemorySaver (dev) — in-process, perdido ao reiniciar
2. PostgresSaver (produção) — persiste no PostgreSQL via tabelas nativas LangGraph

Selecionado pelo ambiente (APP_ENV):
  production → PostgresSaver obrigatório; RuntimeError se indisponível
  outros     → PostgresSaver preferido; fallback para MemorySaver com WARNING

Uso:
    saver = get_checkpointer()
    graph = graph_builder.compile(checkpointer=saver)

API note (langgraph-checkpoint-postgres >= 3.x):
    `PostgresSaver.from_conn_string()` retorna um context manager (Iterator),
    não o saver diretamente. Para checkpointers de longa duração (singletons)
    usa-se `ConnectionPool` do psycopg_pool — padrão recomendado pela equipe
    LangGraph para aplicações de produção.
"""
import logging
from typing import Any

from lia_config.config import settings

logger = logging.getLogger(__name__)

# Pool singleton — mantido vivo pelo lifetime da aplicação.
# Acesso apenas via _postgres_saver(); nunca fechar externamente.
_pg_pool = None


def get_checkpointer() -> Any:
    """
    Retorna o checkpointer adequado ao ambiente.

    Em produção (APP_ENV=production):
      - PostgresSaver obrigatório; RuntimeError se indisponível.

    Em desenvolvimento (APP_ENV!=production):
      - PostgresSaver preferido; fallback para MemorySaver com WARNING explícito.
    """
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
    Cria PostgresSaver via ConnectionPool (langgraph-checkpoint-postgres v3.x).

    Mudança de API v3.x:
      - Versões < 3.x: `PostgresSaver.from_conn_string(url)` retornava o saver diretamente.
      - Versões >= 3.x: `from_conn_string` retorna um Iterator (context manager) —
        não pode ser usado fora de `with`, então não serve para singletons de longa duração.

    Solução canônica v3.x:
      `psycopg_pool.ConnectionPool` mantém um pool de conexões persistente que
      sobrevive ao lifetime da aplicação. É o padrão recomendado pela equipe LangGraph
      para checkpointers de produção.

    `saver.setup()` cria as tabelas canônicas v3.x: `checkpoints`, `checkpoint_blobs`,
    `checkpoint_writes`, `checkpoint_migrations` se ainda não existirem (idempotente).
    Nota: as tabelas `langgraph_*` criadas pela migration 027 são distintas e órfãs.

    Levanta exceção em caso de falha — o caller decide o comportamento.
    """
    global _pg_pool

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise ImportError(
            "Dependências ausentes. Execute: "
            "pip install langgraph-checkpoint-postgres>=3.0.0 psycopg_pool"
        ) from exc

    db_url: str = getattr(settings, "DATABASE_URL", "")
    if not db_url:
        raise ValueError("DATABASE_URL não configurado — PostgresSaver não pode inicializar")

    # Converter asyncpg URL → psycopg URL (psycopg_pool usa psycopg, não asyncpg)
    sync_url = (
        db_url
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
    )

    try:
        if _pg_pool is None:
            # open=True: abre conexões imediatamente — falha rápida se DB inacessível.
            # min_size=1: ao menos 1 conexão sempre pronta (psycopg_pool v3 default min=4
            #   mas exige max_size >= min_size — usar 1 para ambientes com conexões limitadas).
            # prepare_threshold=0: desativa prepared statements (compatibilidade com PgBouncer).
            # autocommit=True: obrigatório para PostgresSaver (opera fora de transações).
            _pg_pool = ConnectionPool(
                conninfo=sync_url,
                min_size=1,
                max_size=5,
                open=True,
                kwargs={"autocommit": True, "prepare_threshold": 0},
            )
            logger.debug("[Checkpointer] ConnectionPool aberto (min=1, max=5)")

        saver = PostgresSaver(_pg_pool)
        # setup() é idempotente — cria tabelas se não existem, no-op se já existem.
        saver.setup()
        logger.info(
            "[Checkpointer] PostgresSaver v3.x (ConnectionPool) ativo — "
            "checkpoints persistem no PostgreSQL entre restarts"
        )
        return saver

    except Exception as exc:
        # Fechar o pool em caso de falha para não vazar conexões
        if _pg_pool is not None:
            try:
                _pg_pool.close()
            except Exception:
                pass
            _pg_pool = None
        raise RuntimeError(
            f"PostgresSaver (ConnectionPool) falhou: {exc}"
        ) from exc
