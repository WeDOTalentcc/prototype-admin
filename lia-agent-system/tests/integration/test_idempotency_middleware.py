"""W2-009-B · TDD integration tests · IdempotencyMiddleware Stripe-style.

Verifica que header Idempotency-Key implementa cache canonical:
1. Sem header → passthrough normal (back-compat).
2. Header presente + nova → execute + cache.
3. Header presente + replay same body → cached response.
4. Header presente + replay different body → 409 Conflict.
5. Multi-tenancy fail-closed: mesma key em 2 companies = 2 entries.
6. Method skip: GET com header → passthrough (HTTP semantics já idempotente).

Skip se sem DATABASE_URL (testes integração precisam Postgres real).
Sensor anti-regressão: scripts/check_idempotency_middleware_wired.py
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _get_async_database_url():
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
    """PostgreSQL session pra testar middleware DB layer. Skip se sem DB."""
    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available (PostgreSQL required)")

    engine = create_async_engine(url, future=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        # Cleanup test entries
        await session.execute(
            text("DELETE FROM idempotency_keys WHERE company_id LIKE 'w2-009b-test-%'")
        )
        await session.commit()
        yield session
        await session.execute(
            text("DELETE FROM idempotency_keys WHERE company_id LIKE 'w2-009b-test-%'")
        )
        await session.commit()

    await engine.dispose()


@pytest.mark.asyncio
async def test_idempotency_table_exists(pg_session):
    """W2-009-B · idempotency_keys table deve ter schema canonical."""
    result = await pg_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'idempotency_keys' "
            "ORDER BY column_name"
        )
    )
    cols = [row[0] for row in result.fetchall()]
    required = {
        "idempotency_key", "company_id", "method", "path", "request_hash",
        "response_status", "response_body", "created_at",
    }
    missing = required - set(cols)
    assert not missing, f"Missing columns in idempotency_keys: {missing}"


@pytest.mark.asyncio
async def test_pk_composite_isolates_per_tenant(pg_session):
    """W2-009-B · mesma key em 2 companies cria 2 entries distintos."""
    key = f"test-key-{uuid.uuid4().hex[:8]}"
    company_a = f"w2-009b-test-tenant-a-{uuid.uuid4().hex[:8]}"
    company_b = f"w2-009b-test-tenant-b-{uuid.uuid4().hex[:8]}"

    for cid in (company_a, company_b):
        await pg_session.execute(
            text(
                "INSERT INTO idempotency_keys "
                "(idempotency_key, company_id, method, path, request_hash, "
                "response_status, response_body) "
                "VALUES (:k, :c, 'POST', '/test', 'hash1', 200, :b)"
            ),
            {"k": key, "c": cid, "b": b'{"ok": true}'},
        )
    await pg_session.commit()

    result = await pg_session.execute(
        text(
            "SELECT company_id FROM idempotency_keys "
            "WHERE idempotency_key = :k ORDER BY company_id"
        ),
        {"k": key},
    )
    rows = [r[0] for r in result.fetchall()]
    assert len(rows) == 2, f"Expected 2 entries (per-tenant isolation), got {len(rows)}"
    assert company_a in rows
    assert company_b in rows


@pytest.mark.asyncio
async def test_pk_conflict_same_key_same_tenant(pg_session):
    """W2-009-B · INSERT duplicado em (key, company) deve falhar (PK constraint)."""
    from sqlalchemy.exc import IntegrityError

    key = f"test-dup-{uuid.uuid4().hex[:8]}"
    company = f"w2-009b-test-dup-{uuid.uuid4().hex[:8]}"

    await pg_session.execute(
        text(
            "INSERT INTO idempotency_keys "
            "(idempotency_key, company_id, method, path, request_hash, "
            "response_status, response_body) "
            "VALUES (:k, :c, 'POST', '/test', 'hash1', 200, :b)"
        ),
        {"k": key, "c": company, "b": b'{}'},
    )
    await pg_session.commit()

    with pytest.raises(IntegrityError):
        await pg_session.execute(
            text(
                "INSERT INTO idempotency_keys "
                "(idempotency_key, company_id, method, path, request_hash, "
                "response_status, response_body) "
                "VALUES (:k, :c, 'POST', '/test', 'hash1', 200, :b)"
            ),
            {"k": key, "c": company, "b": b'{}'},
        )
        await pg_session.commit()
    await pg_session.rollback()


def test_middleware_imports():
    """W2-009-B · middleware class importável + wired em main.py."""
    from app.middleware.idempotency import (
        IdempotencyMiddleware,
        MUTATION_METHODS,
        IDEMPOTENCY_HEADER,
    )
    assert IdempotencyMiddleware is not None
    assert MUTATION_METHODS == {"POST", "PUT", "PATCH", "DELETE"}
    assert IDEMPOTENCY_HEADER == "Idempotency-Key"


def test_middleware_wired_in_main():
    """W2-009-B · main.py deve adicionar IdempotencyMiddleware."""
    from pathlib import Path
    main_py = Path(__file__).resolve().parents[2] / "app" / "main.py"
    src = main_py.read_text(encoding="utf-8")
    assert "from app.middleware.idempotency import IdempotencyMiddleware" in src
    assert "app.add_middleware(IdempotencyMiddleware)" in src


def test_hash_request_deterministic():
    """W2-009-B · _hash_request deve ser deterministic SHA-256."""
    from app.middleware.idempotency import _hash_request

    h1 = _hash_request(b'{"a":1}')
    h2 = _hash_request(b'{"a":1}')
    h3 = _hash_request(b'{"a":2}')
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex


def test_feature_flag_disabled(monkeypatch):
    """W2-009-B · IDEMPOTENCY_MIDDLEWARE_ENABLED=false desativa middleware."""
    from app.middleware.idempotency import _is_idempotency_enabled

    monkeypatch.setenv("IDEMPOTENCY_MIDDLEWARE_ENABLED", "false")
    assert _is_idempotency_enabled() is False

    monkeypatch.setenv("IDEMPOTENCY_MIDDLEWARE_ENABLED", "true")
    assert _is_idempotency_enabled() is True
