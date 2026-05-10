"""Integration tests for Task #969 / T-C: TenantContextService now reads
the enriched ``companies`` schema (sector/plan/timezone/persona) from the
DB instead of falling back to defaults.

Touches the real PostgreSQL container; uses a unique slug per test to
stay isolated from the canonical Demo Company seed.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.shared.services.tenant_context_service import TenantContextService

pytestmark = pytest.mark.asyncio


def _async_db_url_and_args() -> tuple[str, dict]:
    """Translate the canonical libpq DSN into asyncpg-compatible form.

    Replit/Neon DSNs ship with libpq-style query params (``sslmode=...``,
    ``channel_binding=...``) that asyncpg's connect() rejects with
    ``TypeError: connect() got an unexpected keyword argument 'sslmode'``
    — so this fixture strips them out and converts ``sslmode=require``
    into a SSL-enabled ``connect_args``. Local Postgres rejects SSL
    upgrades, so when stripping yields no SSL we leave it off entirely.
    """
    import re

    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set; integration test requires Postgres")

    sslmode_match = re.search(r"[?&]sslmode=([^&]+)", url)
    sslmode = sslmode_match.group(1) if sslmode_match else None

    # Drop libpq-only params asyncpg doesn't accept.
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
async def enriched_tenant(db):
    """Insert a temporary enriched tenant; clean up afterwards."""
    slug = f"t969_{uuid.uuid4().hex[:8]}"
    await db.execute(text(
        """
        INSERT INTO companies (
            id, name, display_name, is_active, is_demo,
            sector, industry_segment, plan, timezone,
            headcount_range, lia_persona_override
        ) VALUES (
            :id, 'Acme Saude', 'Acme Saude S.A.', TRUE, FALSE,
            'Saude', 'HealthTech', 'professional', 'America/Recife',
            '200-500', 'Persona customizada da Acme.'
        )
        """
    ), {"id": slug})
    await db.commit()
    try:
        yield slug
    finally:
        await db.execute(text(
            "DELETE FROM companies WHERE id = :id"
        ), {"id": slug})
        await db.commit()


async def test_canonical_demo_company_returns_rich_context(db):
    """Canonical Demo Company UUID must yield the seeded rich values,
    NOT the legacy defaults (sector=geral, plan=standard).
    """
    svc = TenantContextService()
    ctx = await svc.get_context(
        company_id="00000000-0000-4000-a000-000000000001", db=db
    )

    assert ctx.company_name == "Demo Company"
    assert ctx.sector == "Tecnologia"
    assert ctx.plan == "enterprise"
    assert ctx.timezone == "America/Sao_Paulo"
    assert ctx.custom_persona is not None
    assert "WeDo Talent" in (ctx.custom_persona or "")

    snippet = ctx.to_prompt_snippet()
    assert "Tecnologia" in snippet
    assert "enterprise" in snippet
    assert "geral" not in snippet  # the bug-symptom literal


async def test_enriched_tenant_returns_db_values(db, enriched_tenant):
    """Any enriched tenant gets DB values; defaults must not leak in."""
    svc = TenantContextService()
    ctx = await svc.get_context(company_id=enriched_tenant, db=db)

    assert ctx.company_name == "Acme Saude"
    assert ctx.sector == "Saude"
    assert ctx.plan == "professional"
    assert ctx.timezone == "America/Recife"
    assert ctx.custom_persona == "Persona customizada da Acme."

    snippet = ctx.to_prompt_snippet()
    assert "Acme Saude" in snippet
    assert "Saude" in snippet
    assert "professional" in snippet
    assert "America/Recife" in snippet


async def test_unknown_company_falls_back_to_defaults(db):
    """Service stays fail-safe for truly unknown ids."""
    svc = TenantContextService()
    unknown = f"t969_unknown_{uuid.uuid4().hex[:8]}"
    ctx = await svc.get_context(company_id=unknown, db=db)

    assert ctx.company_name == "sua empresa"
    assert ctx.sector == "geral"
    assert ctx.plan == "standard"


async def test_consolidation_script_is_idempotent(db):
    """Two back-to-back runs of ``consolidate()`` against an already
    consolidated DB must yield identical "no-op" reports — proves the
    script is safe to re-run from CI / post-merge / operator console
    without producing duplicate side effects (architect review #2).
    """
    from scripts.migrate_demo_company_consolidation import consolidate

    bind = await db.connection()

    report1 = await consolidate(bind)
    report2 = await consolidate(bind)

    # Idempotent invariants:
    assert report1["rewrites"] == {}, f"first run rewrote rows: {report1!r}"
    assert report2["rewrites"] == {}, f"second run rewrote rows: {report2!r}"
    assert report1["leftovers"] == [] and report2["leftovers"] == []
    assert report1["seeded_canonical"] is True
    assert report2["seeded_canonical"] is True
    # FK enumeration is purely descriptive — must be deterministic
    # across runs against the same schema.
    assert report1["fk_targets_companies_id"] == report2["fk_targets_companies_id"]
    # Defaults already point at the canonical UUID, so neither run
    # should issue ALTER ... SET DEFAULT statements.
    assert report1["defaults_updated"] == []
    assert report2["defaults_updated"] == []

    # And the canonical row is still present and correctly enriched
    # after both runs — no UPSERT-induced corruption.
    row = (await db.execute(text(
        "SELECT name, sector, plan, timezone FROM companies WHERE id = :id"
    ), {"id": "00000000-0000-4000-a000-000000000001"})).one()
    assert row.name == "Demo Company"
    assert row.sector == "Tecnologia"
    assert row.plan == "enterprise"
    assert row.timezone == "America/Sao_Paulo"


async def test_id_format_check_rejects_invalid_literals(db):
    """The CHECK constraint installed by migration 127 mirrors
    CompanyId.parse() — empty, 'default', and whitespace-bearing ids
    must all be rejected at insert time.
    """
    # The set below mixes regex-violating ids ("", "Has Spaces", "UPPER",
    # "x") with reserved-literal ids ("default", "none", "null",
    # "undefined", "system", "anonymous") — the latter list is locked
    # in step with ``_FORBIDDEN_LITERALS`` in CompanyId.parse().
    invalid_ids = [
        "", "Has Spaces", "UPPER", "x",
        "default", "none", "null", "undefined", "system", "anonymous",
    ]
    for bad in invalid_ids:
        with pytest.raises(Exception):  # asyncpg/psycopg raises check_violation
            await db.execute(text(
                "INSERT INTO companies (id, name) VALUES (:id, 'x')"
            ), {"id": bad})
            await db.commit()
        await db.rollback()
