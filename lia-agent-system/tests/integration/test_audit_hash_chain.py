"""
Integration test W1-006 part 1 · Audit hash chain enforcement.

Verifica que audit_execution_metadata table tem hash chain SHA-256
populada via BEFORE INSERT trigger (per-tenant chain).

Requires PostgreSQL + pgcrypto extension (trigger uses digest(text,'sha256')).
Tests skip if DATABASE_URL not available (local SQLite dev).

TDD red→green:
- RED antes da migration 176 (colunas prev_hash + this_hash não existem)
- GREEN após migration 176 + trigger audit_compute_hash_chain

Sensor anti-regressão: scripts/check_audit_hash_chain_exists.py
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _get_async_database_url():
    """Return DATABASE_URL adapted for asyncpg, or None to skip.

    Strip ?sslmode=... query params (libpq-only, asyncpg uses ssl=).
    """
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None

    # Strip libpq-only query params not accepted by asyncpg
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment))
    return url


@pytest.fixture
async def pg_session():
    """PostgreSQL session pra testar trigger + pgcrypto. Skip se sem DB."""
    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available (PostgreSQL required for hash chain trigger)")

    engine = create_async_engine(url, future=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        await session.execute(
            text("DELETE FROM audit_execution_metadata WHERE company_id LIKE 'w1-006-test-%'")
        )
        await session.commit()
        yield session
        await session.execute(
            text("DELETE FROM audit_execution_metadata WHERE company_id LIKE 'w1-006-test-%'")
        )
        await session.commit()

    await engine.dispose()


@pytest.mark.asyncio
async def test_audit_table_has_hash_chain_columns(pg_session):
    """W1-006 · audit_execution_metadata deve ter prev_hash + this_hash columns."""
    result = await pg_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'audit_execution_metadata' "
            "AND column_name IN ('prev_hash', 'this_hash') "
            "ORDER BY column_name"
        )
    )
    columns = [row[0] for row in result.fetchall()]
    assert "prev_hash" in columns, (
        "Column 'prev_hash' missing from audit_execution_metadata. "
        "Run migration 176_audit_hash_chain."
    )
    assert "this_hash" in columns, (
        "Column 'this_hash' missing from audit_execution_metadata. "
        "Run migration 176_audit_hash_chain."
    )


@pytest.mark.asyncio
async def test_audit_table_has_hash_chain_trigger(pg_session):
    """W1-006 · audit_execution_metadata deve ter trigger BEFORE INSERT."""
    result = await pg_session.execute(
        text(
            "SELECT trigger_name FROM information_schema.triggers "
            "WHERE event_object_table = 'audit_execution_metadata' "
            "AND action_timing = 'BEFORE' "
            "AND event_manipulation = 'INSERT'"
        )
    )
    triggers = [row[0] for row in result.fetchall()]
    assert any("hash_chain" in t for t in triggers), (
        f"BEFORE INSERT hash_chain trigger missing. Found: {triggers}. "
        "Run migration 176_audit_hash_chain."
    )


async def _insert_audit_row(session, exec_id, company_id):
    """Helper: insert um audit row genérico."""
    await session.execute(
        text(
            "INSERT INTO audit_execution_metadata "
            "(execution_id, session_id, company_id, user_id, domain, agent_type, "
            "timestamp, duration_ms, nodes_visited, tools_used, success, confidence, "
            "storage_path, error) "
            "VALUES (:eid, :sid, :cid, :uid, :dom, :at, :ts, :dur, "
            ":nodes, :tools, :ok, :conf, :path, :err)"
        ),
        {
            "eid": exec_id, "sid": "s1", "cid": company_id, "uid": "u1",
            "dom": "test", "at": "test_agent", "ts": datetime.now(timezone.utc),
            "dur": 100, "nodes": "[]", "tools": "[]", "ok": True, "conf": 0.95,
            "path": "/tmp/test", "err": None,
        },
    )
    await session.commit()


@pytest.mark.asyncio
async def test_first_audit_record_per_company_has_null_prev_hash(pg_session):
    """Genesis record per company_id tem prev_hash=NULL e this_hash NOT NULL."""
    company_id = f"w1-006-test-genesis-{uuid.uuid4().hex[:8]}"
    exec_id = f"exec-{uuid.uuid4().hex[:8]}"

    await _insert_audit_row(pg_session, exec_id, company_id)

    result = await pg_session.execute(
        text("SELECT prev_hash, this_hash FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": exec_id},
    )
    row = result.fetchone()
    assert row is not None
    prev_hash, this_hash = row
    assert prev_hash is None, f"Genesis prev_hash must be NULL, got: {prev_hash}"
    assert this_hash is not None, "this_hash must be computed by trigger"
    assert len(this_hash) == 64, f"this_hash must be 64-char hex, got: {len(this_hash)}"


@pytest.mark.asyncio
async def test_second_audit_record_chains_to_first(pg_session):
    """Segundo record do mesmo company_id tem prev_hash = first.this_hash."""
    company_id = f"w1-006-test-chain-{uuid.uuid4().hex[:8]}"
    exec_1 = f"exec1-{uuid.uuid4().hex[:8]}"
    exec_2 = f"exec2-{uuid.uuid4().hex[:8]}"

    await _insert_audit_row(pg_session, exec_1, company_id)
    result = await pg_session.execute(
        text("SELECT this_hash FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": exec_1},
    )
    first_this_hash = result.scalar()
    assert first_this_hash is not None

    await _insert_audit_row(pg_session, exec_2, company_id)
    result = await pg_session.execute(
        text("SELECT prev_hash, this_hash FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": exec_2},
    )
    second_prev, second_this = result.fetchone()
    assert second_prev == first_this_hash, (
        f"Chain broken: second.prev_hash ({second_prev}) != first.this_hash ({first_this_hash})"
    )
    assert second_this is not None
    assert second_this != first_this_hash, "this_hash must be unique per record"


@pytest.mark.asyncio
async def test_hash_chain_isolated_per_company(pg_session):
    """Dois company_ids têm chains independentes (multi-tenant isolation)."""
    cid_a = f"w1-006-test-a-{uuid.uuid4().hex[:8]}"
    cid_b = f"w1-006-test-b-{uuid.uuid4().hex[:8]}"

    await _insert_audit_row(pg_session, f"a1-{uuid.uuid4().hex[:8]}", cid_a)

    eid_b = f"b1-{uuid.uuid4().hex[:8]}"
    await _insert_audit_row(pg_session, eid_b, cid_b)

    result = await pg_session.execute(
        text("SELECT prev_hash FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": eid_b},
    )
    prev_hash = result.scalar()
    assert prev_hash is None, (
        f"Company B genesis must have prev_hash=NULL (isolated from A). Got: {prev_hash}"
    )
