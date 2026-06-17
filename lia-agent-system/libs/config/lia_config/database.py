"""
Core database session management.

Exports:
    engine            — SQLAlchemy async engine
    AsyncSessionLocal — async session factory
    Base              — declarative base for models
    get_db            — FastAPI dependency (yields AsyncSession)
    async_session_factory — context-manager factory for background tasks
"""
import os
import logging
from contextvars import ContextVar
from typing import AsyncGenerator
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event
from sqlalchemy import text as _sa_text
from sqlalchemy.orm import declarative_base

from lia_config.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# N+1 query detection (GAP-12-006) --- development mode only
# Counts SQL statements per HTTP request via SQLAlchemy sync event.
# ContextVar is async-safe: each coroutine scope has its own token.
# Disabled in production or when N_PLUS_ONE_DETECT=0.
# -------------------------------------------------------------------
_request_query_count: ContextVar[int] = ContextVar("_request_query_count", default=0)

N_PLUS_ONE_THRESHOLD: int = int(os.getenv("N_PLUS_ONE_THRESHOLD", "10"))
N_PLUS_ONE_ENABLED: bool = (
    os.getenv("APP_ENV", "development") != "production"
    and os.getenv("N_PLUS_ONE_DETECT", "1") != "0"
)


def get_request_query_count() -> int:
    """Return the SQL statement count accumulated for the current ContextVar scope."""
    return _request_query_count.get(0)


def reset_request_query_count() -> None:
    """Reset the SQL statement counter for the current ContextVar scope."""
    _request_query_count.set(0)


def _get_current_company_id() -> str:
    """Get company_id from AuthEnforcementMiddleware contextvar."""
    try:
        from app.middleware.auth_enforcement import _current_company_id
        return _current_company_id.get("")
    except (ImportError, LookupError):
        return ""


# Get DATABASE_URL from environment (Replit secrets or .env)
database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

# SQLAlchemy 2.0 requires postgresql+asyncpg for async
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg doesn't support sslmode parameter — strip it
if database_url and "sslmode=" in database_url:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    query_params.pop("sslmode", None)
    new_query = urlencode(query_params, doseq=True)
    database_url = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))

# Async engine
engine = create_async_engine(
    database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    # Task #1060: opt-in via DATABASE_ECHO (default OFF). Antes era
    # `settings.DEBUG`, o que ligava echo automaticamente em dev e gerava
    # storm de logs SQL durante runs de Playwright (workflow `lia-backend`
    # morria por OOM/log flooding após alguns minutos).
    echo=settings.DATABASE_ECHO,
)

# Defense-in-depth: mesmo se algum import legado virar `echo` ON,
# manter o handler de SQLAlchemy em WARNING+ por padrão. Quem quiser ver
# SQL precisa setar tanto DATABASE_ECHO=1 quanto SQLALCHEMY_LOG_LEVEL=INFO.
_sqla_level = os.environ.get("SQLALCHEMY_LOG_LEVEL", "WARNING").upper()
for _name in ("sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects"):
    logging.getLogger(_name).setLevel(getattr(logging, _sqla_level, logging.WARNING))

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Producer fix RLS (2026-06-04) — canonical-fix #3 (fix no produtor).
#
# Root cause: ~226 tools do agentic loop (LIA-A04) abrem AsyncSessionLocal CRU,
# fora do middleware HTTP get_db, sem setar o GUC app.company_id. RLS habilitado
# + FORCED em ~241 tabelas ve app_current_company_id()=NULL e BLOQUEIA tudo ->
# a tool retorna 0 ("chat nao ve vagas/candidatos"). get_db ja resolvia isso no
# produtor para o caminho HTTP; este listener replica a MESMA logica para TODA
# transacao do app (inclui sessoes cruas em tools/jobs/loops), de uma vez +
# futuras. set_config(is_local=true) e TX-scoped: limpo no fim da transacao
# (sem vazamento entre tenants no pool). No-op quando o contextvar esta vazio
# (jobs cross-tenant legitimos seguem status quo; RLS fail-closed).
# ---------------------------------------------------------------------------
@event.listens_for(engine.sync_engine, "begin")
def _inject_tenant_guc_on_begin(conn):
    cid = _get_current_company_id()
    if not cid:
        return
    try:
        conn.execute(
            _sa_text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": str(cid)},
        )
    except Exception as exc:  # fail-closed: sem GUC, RLS bloqueia (nunca vaza)
        logger.warning("[RLS] auto-inject app.company_id no begin falhou: %s", exc)


# -------------------------------------------------------------------
# N+1 query counter event (GAP-12-006) --- wired only when N_PLUS_ONE_ENABLED.
# Fires synchronously before every SQL cursor execute in the pool.
# ContextVar makes this async-safe: each request increments its own
# counter without interfering with others (no mutex needed).
# -------------------------------------------------------------------
if N_PLUS_ONE_ENABLED:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _count_sql_query(conn, cursor, statement, parameters, context, executemany):
        _request_query_count.set(_request_query_count.get(0) + 1)


# Declarative base for all SQLAlchemy models
Base = declarative_base()


def async_session_factory():
    """
    Returns an async session context manager.
    Used for background tasks that need their own database sessions.
    """
    return AsyncSessionLocal()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an AsyncSession, commits on success,
    rolls back on exception.

    Automatically injects tenant context (company_id) for RLS isolation
    if set by AuthEnforcementMiddleware via contextvar.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # RLS automatically filters by tenant
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            try:
                await session.execute(sa.text("RESET ROLE"))
            except Exception:
                pass

            _cid = _get_current_company_id()
            if _cid:
                try:
                    await session.execute(sa.text("SET ROLE lia_app"))
                except Exception as role_err:
                    logger.error("[RLS] SET ROLE lia_app failed: %s — request blocked (fail-closed)", role_err)
                    raise RuntimeError("RLS role enforcement failed") from role_err
                await session.execute(
                    sa.text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": _cid},
                )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.execute(sa.text("RESET ROLE"))
            except Exception:
                pass
            await session.close()
