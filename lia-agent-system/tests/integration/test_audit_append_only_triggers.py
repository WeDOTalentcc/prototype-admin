"""W1-006 part 2 · Integration tests · BEFORE UPDATE/DELETE/TRUNCATE block triggers.

Verifica que audit_execution_metadata é append-only via triggers Postgres
canonical (migration 180_audit_append_only_triggers).

Tampering attempts (UPDATE/DELETE/TRUNCATE) → raise exception ANTES de tocar row.
LGPD Art 37 §1 · integridade do registro de tratamento de dados pessoais.

TDD red→green:
- RED antes da migration 180 (UPDATE/DELETE passariam silenciosamente)
- GREEN após migration 180 (UPDATE/DELETE raise IntegrityError SQLSTATE 23000)

Sensor anti-regressão: scripts/check_audit_append_only_triggers.py
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _get_async_database_url():
    """Return DATABASE_URL adapted for asyncpg, or None to skip."""
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

    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment))
    return url


@pytest.fixture
async def pg_session():
    """PostgreSQL session pra testar triggers. Skip se sem DB."""
    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available (PostgreSQL required for triggers)")

    engine = create_async_engine(url, future=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        # NÃO fazer DELETE pre/pos-test: triggers W1-006 part 2 bloqueiam DELETE.
        # Cada teste usa uuid único; rows acumulam mas só em scope test (cleanup
        # out-of-band requer DROP trigger temporário em maintenance window).
        yield session

    await engine.dispose()


async def _insert_audit_row(session, exec_id, company_id):
    """Helper: insert um audit row genérico (write path canonical)."""
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
async def test_block_update_trigger_exists(pg_session):
    """W1-006 part 2 · trigger BEFORE UPDATE deve estar atachado."""
    result = await pg_session.execute(
        text(
            "SELECT trigger_name FROM information_schema.triggers "
            "WHERE event_object_table = 'audit_execution_metadata' "
            "AND action_timing = 'BEFORE' "
            "AND event_manipulation = 'UPDATE'"
        )
    )
    triggers = [row[0] for row in result.fetchall()]
    assert any("block_update" in t for t in triggers), (
        f"BEFORE UPDATE block trigger missing. Found: {triggers}. "
        "Run migration 180_audit_append_only_triggers."
    )


@pytest.mark.asyncio
async def test_block_delete_trigger_exists(pg_session):
    """W1-006 part 2 · trigger BEFORE DELETE deve estar atachado."""
    result = await pg_session.execute(
        text(
            "SELECT trigger_name FROM information_schema.triggers "
            "WHERE event_object_table = 'audit_execution_metadata' "
            "AND action_timing = 'BEFORE' "
            "AND event_manipulation = 'DELETE'"
        )
    )
    triggers = [row[0] for row in result.fetchall()]
    assert any("block_delete" in t for t in triggers), (
        f"BEFORE DELETE block trigger missing. Found: {triggers}. "
        "Run migration 180_audit_append_only_triggers."
    )


@pytest.mark.asyncio
async def test_block_truncate_trigger_exists(pg_session):
    """W1-006 part 2 · trigger BEFORE TRUNCATE deve estar atachado (statement-level).

    Nota: information_schema.triggers NÃO lista TRUNCATE (limitação SQL standard).
    Usamos pg_trigger system catalog direto.
    """
    result = await pg_session.execute(
        text(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid = 'audit_execution_metadata'::regclass "
            "AND NOT tgisinternal "
            "AND tgname LIKE '%block_truncate%'"
        )
    )
    triggers = [row[0] for row in result.fetchall()]
    assert len(triggers) >= 1, (
        f"BEFORE TRUNCATE block trigger missing. "
        "Run migration 180_audit_append_only_triggers."
    )


@pytest.mark.asyncio
async def test_update_raises_exception(pg_session):
    """W1-006 part 2 · UPDATE em audit_execution_metadata DEVE raise."""
    company_id = f"w1-006-p2-test-update-{uuid.uuid4().hex[:8]}"
    exec_id = f"exec-{uuid.uuid4().hex[:8]}"
    await _insert_audit_row(pg_session, exec_id, company_id)

    with pytest.raises(DBAPIError) as exc_info:
        await pg_session.execute(
            text(
                "UPDATE audit_execution_metadata "
                "SET error = 'tampering attempt' "
                "WHERE execution_id = :eid"
            ),
            {"eid": exec_id},
        )
        await pg_session.commit()

    # Trigger raises with our canonical message
    assert "append-only" in str(exc_info.value).lower(), (
        f"UPDATE should raise append-only exception, got: {exc_info.value}"
    )
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_delete_raises_exception(pg_session):
    """W1-006 part 2 · DELETE em audit_execution_metadata DEVE raise."""
    company_id = f"w1-006-p2-test-delete-{uuid.uuid4().hex[:8]}"
    exec_id = f"exec-{uuid.uuid4().hex[:8]}"
    await _insert_audit_row(pg_session, exec_id, company_id)

    with pytest.raises(DBAPIError) as exc_info:
        await pg_session.execute(
            text("DELETE FROM audit_execution_metadata WHERE execution_id = :eid"),
            {"eid": exec_id},
        )
        await pg_session.commit()

    assert "append-only" in str(exc_info.value).lower(), (
        f"DELETE should raise append-only exception, got: {exc_info.value}"
    )
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_truncate_raises_exception(pg_session):
    """W1-006 part 2 · TRUNCATE em audit_execution_metadata DEVE raise."""
    # Não precisa de row pre-existente — trigger é statement-level
    with pytest.raises(DBAPIError) as exc_info:
        await pg_session.execute(text("TRUNCATE TABLE audit_execution_metadata"))
        await pg_session.commit()

    assert "append-only" in str(exc_info.value).lower(), (
        f"TRUNCATE should raise append-only exception, got: {exc_info.value}"
    )
    await pg_session.rollback()


@pytest.mark.asyncio
async def test_insert_still_works(pg_session):
    """W1-006 part 2 · INSERT deve continuar funcionando (write path canonical)."""
    company_id = f"w1-006-p2-test-insert-{uuid.uuid4().hex[:8]}"
    exec_id = f"exec-{uuid.uuid4().hex[:8]}"
    # No exception → insert path preserved
    await _insert_audit_row(pg_session, exec_id, company_id)

    # Confirm row landed
    result = await pg_session.execute(
        text("SELECT execution_id FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": exec_id},
    )
    rows = result.fetchall()
    assert len(rows) == 1, "INSERT should have created exactly 1 row"
    assert rows[0][0] == exec_id
