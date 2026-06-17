"""Integration test pinning the MissingGreenlet silent-degradation bug.

Context (smoke runtime diagnosis): ``build_company_agent_context`` is wired
into every agent invocation (via ``tenant_context_service.get_context``). It
delegates to ``LiaFieldConfigService.get_field_config`` ->
``_get_company_value(field_key, profile)``, which does a blind
``getattr(profile, field_key)`` for canonical field_keys ``departments`` and
``benefits``. Those are ORM ``relationship()`` attributes on ``CompanyProfile``;
on a profile loaded by ``LiaFieldConfigRepository.get_company_profile`` (no
eager-load), the getattr triggers an *async lazy-load* outside the active
greenlet -> ``sqlalchemy.exc.MissingGreenlet``. The error is swallowed by the
``except Exception`` in ``lia_agent_context_builder`` -> the toggle-filtered
company context arrives EMPTY at the LLM for every tenant (silent degradation,
anti-pattern REGRA 4).

These tests touch the real PostgreSQL container (DATABASE_URL) and seed an
isolated CompanyProfile + departments + benefits so they stay independent from
the canonical Demo Company seed. RED state: ``_get_company_value`` raises
MissingGreenlet (or the values come back empty). GREEN: relationships are
selectinload-ed in the repository and a guard prevents lazy-load regressions.
"""
from __future__ import annotations

import os
import re
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.cv_screening.services.lia_field_config_service import (
    LiaFieldConfigService,
)
from app.shared.services.lia_agent_context_builder import build_company_agent_context

pytestmark = pytest.mark.asyncio


def _async_db_url_and_args() -> tuple[str, dict]:
    """Translate the canonical libpq DSN into asyncpg-compatible form.

    Mirrors tests/integration/test_tenant_context_enriched.py.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set; integration test requires Postgres")

    sslmode_match = re.search(r"[?&]sslmode=([^&]+)", url)
    sslmode = sslmode_match.group(1) if sslmode_match else None

    for unsupported in ("sslmode", "channel_binding", "options"):
        url = re.sub(rf"[?&]{unsupported}=[^&]+", "", url)
    url = re.sub(r"\?&", "?", url).rstrip("?&")

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args: dict = {}
    if sslmode and sslmode.lower() in {"require", "verify-ca", "verify-full"}:
        connect_args["ssl"] = True
    return url, connect_args


@pytest.fixture
async def db() -> AsyncSession:
    url, connect_args = _async_db_url_and_args()
    engine = create_async_engine(url, future=True, connect_args=connect_args)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def company_with_relations(db):
    """Seed an isolated CompanyProfile + departments + benefits.

    Yields the company_id (uuid str). Cleans up children + profile afterwards.
    """
    company_id = str(uuid.uuid4())
    # company_profiles is the canonical table the repository queries.
    await db.execute(
        text(
            "INSERT INTO company_profiles (id, name, is_active, is_default) "
            "VALUES (:id, :name, TRUE, FALSE)"
        ),
        {"id": company_id, "name": f"RelTest {company_id[:8]}"},
    )
    for i in range(3):
        await db.execute(
            text(
                "INSERT INTO departments (id, company_id, name, is_active) "
                "VALUES (:id, :cid, :name, TRUE)"
            ),
            {"id": str(uuid.uuid4()), "cid": company_id, "name": f"Engenharia {i}"},
        )
    for i in range(2):
        await db.execute(
            text(
                "INSERT INTO benefits (id, company_id, name, category, is_active) "
                "VALUES (:id, :cid, :name, :cat, TRUE)"
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": company_id,
                "name": f"Vale Refeicao {i}",
                "cat": "alimentacao",
            },
        )
    await db.commit()
    try:
        yield company_id
    finally:
        await db.execute(
            text("DELETE FROM benefits WHERE company_id = :id"), {"id": company_id}
        )
        await db.execute(
            text("DELETE FROM departments WHERE company_id = :id"), {"id": company_id}
        )
        await db.execute(
            text("DELETE FROM company_profiles WHERE id = :id"), {"id": company_id}
        )
        await db.commit()


async def test_get_company_value_does_not_trigger_missing_greenlet(
    db, company_with_relations
):
    """RED: getattr on departments/benefits relationships lazy-loads outside
    the greenlet -> MissingGreenlet. After the fix (selectinload + guard) the
    relationships are loaded eagerly and return the seeded children.
    """
    svc = LiaFieldConfigService(db)
    profile = await svc._load_company_profile(uuid.UUID(company_with_relations))
    assert profile is not None

    # These two attribute reads are exactly what get_field_config does in its
    # DEFAULT_FIELD_TOGGLES loop. They must not raise MissingGreenlet.
    departments = svc._get_company_value("departments", profile)
    benefits = svc._get_company_value("benefits", profile)

    assert departments, "departments relationship came back empty/None"
    assert len(list(departments)) == 3
    assert benefits, "benefits relationship came back empty/None"
    assert len(list(benefits)) == 2


async def test_get_field_config_marks_relationships_as_company_config(
    db, company_with_relations
):
    """get_field_config must classify departments/benefits as COMPANY_CONFIG
    (value present), not NOT_AVAILABLE — proving the value actually reached the
    config result instead of being silently dropped by a swallowed greenlet.
    """
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(company_with_relations)

    # active_fields contains only fields with a usable company value.
    assert "departments" in result.active_fields
    assert "benefits" in result.active_fields


async def test_build_company_agent_context_not_empty(db, company_with_relations):
    """End-to-end: the public entry-point used by every agent must return a
    non-empty, toggle-filtered fragment. RED state returns "" because the
    MissingGreenlet is swallowed in build_company_agent_context.
    """
    context = await build_company_agent_context(company_with_relations, db)
    assert context, "build_company_agent_context returned empty (silent degradation)"
    # The seeded department/benefit names must be rendered by NAME, not as the
    # useless ORM object repr (<...Department object at 0x...>).
    assert "Engenharia" in context, context
    assert "Vale Refeicao" in context, context
    assert "object at 0x" not in context, "ORM repr leaked into prompt"
