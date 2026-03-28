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
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from lia_config.config import settings

logger = logging.getLogger(__name__)

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
    echo=settings.DEBUG,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

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

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
