"""Contract tests for PoolAgentAssignmentRepository — Sub-sprint 7A."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.agent_studio.repositories.pool_agent_assignment_repository import (
    CrossTenantError,
    PoolAgentAssignmentRepository,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        pytest.skip("DATABASE_URL not set")
    # Switch to async driver + strip psycopg2-only kwargs (asyncpg doesn't accept sslmode)
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+asyncpg://", 1)
    parts = urlsplit(raw)
    qs = [(k, v) for k, v in parse_qsl(parts.query) if k != "sslmode"]
    url = urlunsplit(parts._replace(query=urlencode(qs)))
    engine = create_async_engine(url, future=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_require_company_id_fail_closed(db_session):
    repo = PoolAgentAssignmentRepository(db_session)
    with pytest.raises(ValueError, match="company_id required"):
        await repo.list_by_pool(pool_id=str(uuid.uuid4()), company_id="")


@pytest.mark.asyncio
async def test_create_cross_tenant_blocked(db_session):
    """Pool de company A + agent de company B + jwt company A -> CrossTenantError."""
    repo = PoolAgentAssignmentRepository(db_session)
    # Seed: 2 tenants, 1 pool A, 1 agent B
    cid_a = "test-cid-7a-" + uuid.uuid4().hex[:8]
    cid_b = "test-cid-7b-" + uuid.uuid4().hex[:8]
    pool_a = uuid.uuid4()
    agent_b = uuid.uuid4()

    await db_session.execute(
        text(
            "INSERT INTO talent_pools (id, company_id, name, status, created_at, updated_at) "
            "VALUES (:id, :cid, 'pool_a', 'active', NOW(), NOW())"
        ),
        {"id": pool_a, "cid": cid_a},
    )
    await db_session.execute(
        text(
            "INSERT INTO custom_agents "
            "(id, company_id, created_by, name, role, system_prompt, allowed_tools, "
            " domain, status, version, config, max_steps, temperature, "
            " enable_memory, context_level, excluded_tools, "
            " voice_enabled, voip_enabled, whatsapp_enabled, triagem_invite_enabled, "
            " runtime_metrics, category) "
            "VALUES (:id, :cid, 'system', 'agent_b', 'sourcing', '', '{}', "
            " 'general', 'draft', 1, '{}'::jsonb, 8, 0.7, "
            " true, 'full', '{}', false, false, false, false, '{}'::jsonb, 'sourcing')"
        ),
        {"id": agent_b, "cid": cid_b},
    )
    await db_session.flush()

    # Try to assign agent_b to pool_a using jwt=cid_a -> CrossTenantError (agent mismatch)
    with pytest.raises(CrossTenantError):
        await repo.create(
            company_id=cid_a,
            pool_id=str(pool_a),
            custom_agent_id=str(agent_b),
            created_by="test",
        )
