"""Contract tests for PoolAgentRunRepository — Sprint 7C Part 1.5a foundation."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.agent_studio.repositories.pool_agent_run_repository import (
    PoolAgentRunRepository,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        pytest.skip("DATABASE_URL not set")
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


async def _seed_assignment(db_session, company_id: str) -> uuid.UUID:
    """Cria deps: pool + custom_agent + pool_agent_assignment com cols NOT NULL satisfeitas."""
    pool_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    user_id = str(uuid.uuid4())

    await db_session.execute(
        text(
            "INSERT INTO talent_pools (id, company_id, name, status, created_at, updated_at) "
            "VALUES (:id, :cid, 'p7c-1.5a', 'active', now(), now())"
        ),
        {"id": pool_id, "cid": company_id},
    )
    await db_session.execute(
        text(
            "INSERT INTO custom_agents ("
            "id, company_id, created_by, name, role, system_prompt, "
            "allowed_tools, domain, status, version, config, max_steps, temperature, "
            "category, created_at, updated_at"
            ") VALUES ("
            ":id, :cid, :uid, 'agent-7c', 'recruiter', 'test prompt', "
            "ARRAY[]::text[], 'sourcing', 'active', 1, '{}'::jsonb, 5, 0.5, "
            "'sourcing', now(), now()"
            ")"
        ),
        {"id": agent_id, "cid": company_id, "uid": user_id},
    )
    await db_session.execute(
        text(
            "INSERT INTO pool_agent_assignments "
            "(id, company_id, talent_pool_id, custom_agent_id, status, "
            "schedule_type, created_at, updated_at, created_by) "
            "VALUES (:id, :cid, :pid, :aid, 'active', 'on_demand', now(), now(), :uid)"
        ),
        {
            "id": assignment_id,
            "cid": company_id,
            "pid": pool_id,
            "aid": agent_id,
            "uid": user_id,
        },
    )
    await db_session.commit()
    return assignment_id


@pytest.mark.asyncio
async def test_require_company_id_fail_closed(db_session):
    """Multi-tenancy fail-closed: empty/None company_id => ValueError."""
    repo = PoolAgentRunRepository(db_session)
    with pytest.raises(ValueError, match="company_id required"):
        await repo.list_by_assignment(
            assignment_id=uuid.uuid4(), company_id=""
        )
    with pytest.raises(ValueError, match="company_id required"):
        await repo.create(
            assignment_id=uuid.uuid4(),
            company_id="",
            trigger_source="cron",
        )


@pytest.mark.asyncio
async def test_create_canonical(db_session):
    """create() canonical inicia run em queued."""
    cid = "test-7c-cr-" + uuid.uuid4().hex[:8]
    assignment_id = await _seed_assignment(db_session, cid)

    repo = PoolAgentRunRepository(db_session)
    run = await repo.create(
        assignment_id=assignment_id,
        company_id=cid,
        trigger_source="cron",
        dispatch_metadata={"cron_expression": "0 9 * * *"},
    )
    assert run.id is not None
    assert run.status == "queued"
    assert run.trigger_source == "cron"
    assert run.company_id == cid
    assert run.dispatch_metadata == {"cron_expression": "0 9 * * *"}
    assert run.started_at is None
    assert run.finished_at is None


@pytest.mark.asyncio
async def test_list_by_assignment_ordering_and_limit(db_session):
    """Lista canonical ordena por created_at DESC + respeita limit/offset."""
    cid = "test-7c-ls-" + uuid.uuid4().hex[:8]
    assignment_id = await _seed_assignment(db_session, cid)

    repo = PoolAgentRunRepository(db_session)
    for i in range(3):
        await repo.create(
            assignment_id=assignment_id,
            company_id=cid,
            trigger_source="on_demand",
            dispatch_metadata={"idx": i},
        )

    runs = await repo.list_by_assignment(assignment_id, cid, limit=10)
    assert len(runs) == 3
    assert runs[0].dispatch_metadata["idx"] == 2  # DESC: latest first

    limited = await repo.list_by_assignment(assignment_id, cid, limit=2)
    assert len(limited) == 2


@pytest.mark.asyncio
async def test_get_by_id_cross_tenant_returns_none(db_session):
    """get_by_id retorna None quando company_id != row.company_id."""
    cid = "test-7c-ct-" + uuid.uuid4().hex[:8]
    cid_other = "test-7c-ot-" + uuid.uuid4().hex[:8]
    assignment_id = await _seed_assignment(db_session, cid)

    repo = PoolAgentRunRepository(db_session)
    run = await repo.create(
        assignment_id=assignment_id,
        company_id=cid,
        trigger_source="on_demand",
    )

    found = await repo.get_by_id(run.id, cid)
    assert found is not None
    assert found.id == run.id

    not_found = await repo.get_by_id(run.id, cid_other)
    assert not_found is None


@pytest.mark.asyncio
async def test_update_status_transitions(db_session):
    """update_status transitions queued -> running -> success com timestamps canonical."""
    cid = "test-7c-up-" + uuid.uuid4().hex[:8]
    assignment_id = await _seed_assignment(db_session, cid)

    repo = PoolAgentRunRepository(db_session)
    run = await repo.create(
        assignment_id=assignment_id,
        company_id=cid,
        trigger_source="cron",
    )
    assert run.started_at is None and run.finished_at is None

    r2 = await repo.update_status(run.id, "running")
    assert r2.status == "running"
    assert r2.started_at is not None
    assert r2.finished_at is None

    r3 = await repo.update_status(
        run.id,
        "success",
        results={"candidates_evaluated": 12},
        runtime_metrics={"latency_ms": 4200},
    )
    assert r3.status == "success"
    assert r3.finished_at is not None
    assert r3.results == {"candidates_evaluated": 12}
    assert r3.runtime_metrics == {"latency_ms": 4200}

    with pytest.raises(ValueError, match="invalid status"):
        await repo.update_status(run.id, "bogus_status_xyz")
