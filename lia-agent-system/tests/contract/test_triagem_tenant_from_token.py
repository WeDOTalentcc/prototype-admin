"""
Sprint 4 B.2 — P0 fix sensor: triagem token resolution under RLS bypass.

Sensor pra regressao Sprint 4 B.1 (commit ca62339cb).

Background:
- Endpoints PUBLIC /api/v1/triagem/{token}/* (candidato sem JWT).
- triagem_sessions tem FORCE RLS + policy filtrando por app.company_id.
- Sem JWT, app.company_id nunca eh setado -> RLS retorna 0 rows -> 404.

Fix: SECURITY DEFINER function resolve_triagem_session_by_token criada na
alembic migration 187_triagem_resolve_tenant_secdef.py (owner postgres,
bypassa RLS via ownership). TriagemSessionRepository.get_session_by_token
usa essa funcao. Depois de resolver, set app.company_id via set_config
para queries subsequentes operarem normalmente sob RLS.

Os testes neste arquivo abrem conexoes diretas via DATABASE_URL para evitar
loop event hazards de fixtures async cross-loop.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.asyncio


def _build_engine():
    """Build a per-test async engine. Skips if DATABASE_URL not set."""
    from sqlalchemy.ext.asyncio import create_async_engine

    url = os.getenv("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg doesn't accept sslmode=disable query param
    url = url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
    return create_async_engine(url, future=True)


async def _postgres_session(engine):
    """Session as postgres role (bypasses RLS) — for test data setup."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return maker()


async def _lia_app_session(engine):
    """Session as lia_app role (RLS enforced), with NULL tenant context."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    session = maker()
    await session.execute(sa.text("SET ROLE lia_app"))
    await session.execute(sa.text("SELECT set_config('app.company_id', '', true)"))
    return session


async def _ensure_test_session(db, token: str, company_id: str) -> str:
    session_id = str(uuid.uuid4())
    candidate_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    await db.execute(
        sa.text(
            """
            INSERT INTO triagem_sessions
                (id, token, candidate_id, job_id, company_id, status,
                 current_block, total_blocks, expires_at, created_at, updated_at,
                 invite_channel)
            VALUES
                (:id, :token, :candidate_id, :job_id, :company_id, 'invited',
                 0, 6, :expires_at, NOW(), NOW(), 'link')
            ON CONFLICT (token) DO UPDATE SET company_id = EXCLUDED.company_id
            """
        ),
        {
            "id": session_id,
            "token": token,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "company_id": company_id,
            "expires_at": expires_at,
        },
    )
    await db.commit()
    return session_id


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Function exists with correct security attributes
# ─────────────────────────────────────────────────────────────────────────────
async def test_resolve_function_exists_with_correct_attrs():
    engine = _build_engine()
    try:
        db = await _postgres_session(engine)
        try:
            result = await db.execute(
                sa.text(
                    """
                    SELECT proname, prosecdef,
                           proowner::regrole::text AS owner
                    FROM pg_proc
                    WHERE proname = 'resolve_triagem_session_by_token'
                    """
                )
            )
            row = result.first()
            assert row is not None, "function missing — migration 187 not applied?"
            assert row.prosecdef is True, "must be SECURITY DEFINER"
            assert row.owner == "postgres", "must be owned by postgres to bypass RLS"
        finally:
            await db.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Function bypasses RLS for lia_app with no app.company_id
# ─────────────────────────────────────────────────────────────────────────────
async def test_resolve_function_returns_session_with_no_tenant_context():
    engine = _build_engine()
    try:
        pg = await _postgres_session(engine)
        try:
            token = f"test-token-{uuid.uuid4()}"
            company_id = "00000000-0000-4000-a000-000000000001"
            await _ensure_test_session(pg, token, company_id)
        finally:
            await pg.close()

        lia = await _lia_app_session(engine)
        try:
            result = await lia.execute(
                sa.text(
                    "SELECT id, company_id FROM resolve_triagem_session_by_token(:t)"
                ),
                {"t": token},
            )
            row = result.first()
            assert row is not None, "SECURITY DEFINER must bypass RLS for token lookup"
            assert str(row.company_id) == company_id
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Direct SELECT still blocked (defense in depth)
# ─────────────────────────────────────────────────────────────────────────────
async def test_direct_select_still_blocked_by_rls():
    engine = _build_engine()
    try:
        pg = await _postgres_session(engine)
        try:
            token = f"test-token-{uuid.uuid4()}"
            company_id = "00000000-0000-4000-a000-000000000001"
            await _ensure_test_session(pg, token, company_id)
        finally:
            await pg.close()

        lia = await _lia_app_session(engine)
        try:
            result = await lia.execute(
                sa.text("SELECT count(*) FROM triagem_sessions WHERE token = :t"),
                {"t": token},
            )
            assert result.scalar() == 0, (
                "Direct SELECT must remain blocked under RLS — confirms "
                "SECURITY DEFINER is the ONLY canonical path for PUBLIC token lookup"
            )
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Invalid token returns 0 rows
# ─────────────────────────────────────────────────────────────────────────────
async def test_invalid_token_returns_empty():
    engine = _build_engine()
    try:
        lia = await _lia_app_session(engine)
        try:
            result = await lia.execute(
                sa.text(
                    "SELECT count(*) FROM resolve_triagem_session_by_token(:t)"
                ),
                {"t": f"nonexistent-{uuid.uuid4()}"},
            )
            assert result.scalar() == 0
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Repository works without JWT context (end-to-end)
# ─────────────────────────────────────────────────────────────────────────────
async def test_repository_get_session_by_token_works_without_jwt_context():
    engine = _build_engine()
    try:
        pg = await _postgres_session(engine)
        try:
            token = f"test-token-{uuid.uuid4()}"
            company_id = "00000000-0000-4000-a000-000000000001"
            await _ensure_test_session(pg, token, company_id)
        finally:
            await pg.close()

        from app.domains.recruitment.repositories.triagem_session_repository import (
            TriagemSessionRepository,
        )

        lia = await _lia_app_session(engine)
        try:
            repo = TriagemSessionRepository(lia)
            session = await repo.get_session_by_token(token)
            assert session is not None, (
                "P0 regression sensor: get_session_by_token must return session "
                "for unauthenticated candidate flow (RLS bypassed via SECURITY DEFINER)"
            )
            assert session.token == token
            assert str(session.company_id) == company_id
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — RLS context is set after token resolution
# ─────────────────────────────────────────────────────────────────────────────
async def test_repository_sets_app_company_id_for_subsequent_queries():
    engine = _build_engine()
    try:
        pg = await _postgres_session(engine)
        try:
            token = f"test-token-{uuid.uuid4()}"
            company_id = "00000000-0000-4000-a000-000000000001"
            await _ensure_test_session(pg, token, company_id)
        finally:
            await pg.close()

        from app.domains.recruitment.repositories.triagem_session_repository import (
            TriagemSessionRepository,
        )

        lia = await _lia_app_session(engine)
        try:
            # Before: app.company_id is empty/NULL
            before = await lia.execute(
                sa.text("SELECT app_current_company_id() IS NULL AS is_null")
            )
            assert before.scalar() is True

            repo = TriagemSessionRepository(lia)
            await repo.get_session_by_token(token)

            after = await lia.execute(
                sa.text("SELECT app_current_company_id() AS cid")
            )
            assert after.scalar() == company_id, (
                "After token resolution, app.company_id must be set for "
                "subsequent RLS-bound queries in the same request"
            )
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Invalid token does not leak app.company_id
# ─────────────────────────────────────────────────────────────────────────────
async def test_invalid_token_does_not_leak_app_company_id():
    engine = _build_engine()
    try:
        from app.domains.recruitment.repositories.triagem_session_repository import (
            TriagemSessionRepository,
        )

        lia = await _lia_app_session(engine)
        try:
            repo = TriagemSessionRepository(lia)
            result = await repo.get_session_by_token(f"nonexistent-{uuid.uuid4()}")
            assert result is None

            after = await lia.execute(
                sa.text("SELECT app_current_company_id() IS NULL AS is_null")
            )
            assert after.scalar() is True, (
                "Invalid token must NOT cause set_config to run with stale values"
            )
        finally:
            await lia.close()
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Test 8 — GRANT scope: EXECUTE only for lia_app, not PUBLIC
# ─────────────────────────────────────────────────────────────────────────────
async def test_security_definer_grant_scope():
    engine = _build_engine()
    try:
        db = await _postgres_session(engine)
        try:
            result = await db.execute(
                sa.text(
                    """
                    SELECT grantee, privilege_type
                    FROM information_schema.routine_privileges
                    WHERE routine_name = 'resolve_triagem_session_by_token'
                    ORDER BY grantee
                    """
                )
            )
            grants = [(r.grantee, r.privilege_type) for r in result.fetchall()]
            grantees = {g[0] for g in grants}

            assert "lia_app" in grantees, "lia_app must have EXECUTE"
            assert "PUBLIC" not in grantees, (
                "PUBLIC must NOT have EXECUTE (migration REVOKEs)"
            )
        finally:
            await db.close()
    finally:
        await engine.dispose()
