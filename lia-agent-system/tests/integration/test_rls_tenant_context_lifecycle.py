"""V5: Integration tests for RLS tenant context lifecycle.

Exercises the FULL roundtrip against a real Postgres session (not mocked):
1. set_tenant_context populates app.company_id + db.info
2. INSERT into RLS-bearing table (conversations) succeeds
3. After explicit commit(), naive SELECT is BLOCKED by RLS (proves the bug)
4. After commit_keeping_tenant(), SELECT succeeds (proves the canonical fix)
5. Cross-tenant isolation: tenant B cannot see tenant A's rows

This is the test pattern the chat write path was missing in the original
audit — mocked tests passed because they never exercised the Postgres RLS
machinery.

Skips silently if DATABASE_URL is not configured (CI without DB).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


# Force imports of models so SQLAlchemy registers them on Base.metadata.
import libs.models.lia_models  # noqa: F401

from app.core.database import (
    commit_keeping_tenant,
    set_tenant_context,
)
from app.models.conversation import Conversation


TENANT_A = "11111111-1111-4111-a111-111111111111"
TENANT_B = "22222222-2222-4222-a222-222222222222"
USER_A = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"


def _async_url() -> str | None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(qs), parts.fragment))


@pytest.fixture
async def pg_session_a():
    """Postgres session with RLS role enforced + tenant A context."""
    url = _async_url()
    if not url:
        pytest.skip("DATABASE_URL not available (Postgres required for RLS roundtrip)")

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as session:
        try:
            await session.execute(sa.text("SET ROLE lia_app"))
        except Exception:
            pytest.skip("lia_app role not provisioned in this DB — skip RLS tests")
        await set_tenant_context(session, TENANT_A)
        yield session
        await session.rollback()
        try:
            await session.execute(sa.text("RESET ROLE"))
        except Exception:
            pass
    await engine.dispose()


@pytest.fixture
async def pg_session_b():
    """Postgres session with RLS role enforced + tenant B context (cross-tenant)."""
    url = _async_url()
    if not url:
        pytest.skip("DATABASE_URL not available")
    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as session:
        try:
            await session.execute(sa.text("SET ROLE lia_app"))
        except Exception:
            pytest.skip("lia_app role not provisioned in this DB")
        await set_tenant_context(session, TENANT_B)
        yield session
        await session.rollback()
        try:
            await session.execute(sa.text("RESET ROLE"))
        except Exception:
            pass
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_set_tenant_context_stores_in_session_info(pg_session_a):
    """set_tenant_context populates db.info for after-commit re-injection."""
    assert pg_session_a.info.get("company_id") == TENANT_A


@pytest.mark.asyncio
@pytest.mark.integration
async def test_insert_then_select_same_tx_works(pg_session_a):
    """INSERT + SELECT in same transaction: RLS policy passes."""
    conv = Conversation(
        user_id=USER_A,
        company_id=TENANT_A,
        user_role="recruiter",
        status="active",
    )
    pg_session_a.add(conv)
    await pg_session_a.flush()

    result = await pg_session_a.execute(
        sa.select(Conversation).where(Conversation.id == conv.id)
    )
    row = result.scalar_one_or_none()
    assert row is not None, "Same-tx SELECT must see the just-inserted row"
    assert row.company_id == TENANT_A


@pytest.mark.asyncio
@pytest.mark.integration
async def test_commit_keeping_tenant_preserves_select_visibility(pg_session_a):
    """Canonical commit helper: after commit, SELECT/refresh still works."""
    conv = Conversation(
        user_id=USER_A,
        company_id=TENANT_A,
        user_role="recruiter",
        status="active",
    )
    pg_session_a.add(conv)
    await pg_session_a.flush()
    conv_id = conv.id

    # Canonical commit — preserves tenant context for subsequent reads.
    await commit_keeping_tenant(pg_session_a)

    # refresh() in the new tx must succeed (this was the V4-fixed bug).
    await pg_session_a.refresh(conv)
    assert conv.id == conv_id
    assert conv.company_id == TENANT_A


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cross_tenant_isolation_after_commit(pg_session_a, pg_session_b):
    """Tenant B cannot see tenant A's rows even after explicit commit_keeping_tenant."""
    conv = Conversation(
        user_id=USER_A,
        company_id=TENANT_A,
        user_role="recruiter",
        status="active",
    )
    pg_session_a.add(conv)
    await pg_session_a.flush()
    await commit_keeping_tenant(pg_session_a)
    conv_id = conv.id

    # Tenant B queries the same id.
    result = await pg_session_b.execute(
        sa.select(Conversation).where(Conversation.id == conv_id)
    )
    row = result.scalar_one_or_none()
    assert row is None, (
        "Cross-tenant LEAK: tenant B saw tenant A's row. "
        "RLS SELECT policy must filter by app.company_id."
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_naive_commit_then_refresh_is_broken_without_helper(pg_session_a):
    """Regression pin: plain db.commit() without re-inject still breaks refresh.

    This pins the original V4 defect — if anyone removes commit_keeping_tenant
    and reverts to plain commit() before a refresh, the read becomes invisible.
    The test demonstrates WHY the canonical helper exists.
    """
    conv = Conversation(
        user_id=USER_A,
        company_id=TENANT_A,
        user_role="recruiter",
        status="active",
    )
    pg_session_a.add(conv)
    await pg_session_a.flush()

    # Naive commit (no re-inject) — this is what the V4-fixed bug was.
    await pg_session_a.commit()

    # The row exists in the DB but is invisible to this now-tenant-less tx.
    # SQLAlchemy reports `Could not refresh instance` on object refresh.
    with pytest.raises((InvalidRequestError, Exception)) as exc_info:
        await pg_session_a.refresh(conv)
    # Sanity: error message references refresh or row visibility.
    msg = str(exc_info.value).lower()
    assert "refresh" in msg or "could not" in msg or "instance" in msg, (
        f"Unexpected error: {exc_info.value!r}. Expected 'Could not refresh "
        f"instance' indicating RLS-induced invisibility."
    )
