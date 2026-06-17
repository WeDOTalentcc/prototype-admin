"""Fase 2.5 Onda C2.1b — FK closure sensors (migration 224).

Validates the two deferred FKs from mig 219 reach their final state:

  FK #1 — custom_agents.company_id -> companies.id : CLOSED (orphan fixtures
          deleted, FK CASCADE applied).
  FK #2 — ai_consumption.studio_agent_id -> custom_agents.id : INTENTIONALLY
          NOT a FK (polymorphic reference discriminated by agent_type). The
          test pins this decision so a future migration cannot silently add the
          wrong FK or convert the column to uuid.

Runs against the live DB (same config as the other tests/migrations/).
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return create_engine(url)


# ---------------------------------------------------------------------------
# FK #1 — custom_agents.company_id -> companies.id  (CLOSED)
# ---------------------------------------------------------------------------
def test_custom_agents_company_id_fk_exists(engine):
    """The deferred FK #1 is now applied with ON DELETE CASCADE."""
    with engine.connect() as c:
        defs = [
            r[0]
            for r in c.execute(
                text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conrelid = to_regclass('custom_agents') AND contype = 'f'"
                )
            ).fetchall()
        ]
    match = [d for d in defs if "company_id" in d and "companies" in d]
    assert match, f"custom_agents.company_id -> companies FK not found in {defs}"
    assert "CASCADE" in match[0], f"expected ON DELETE CASCADE, got {match[0]}"


def test_no_orphan_custom_agents(engine):
    """After cleanup, every custom_agents row references a real company."""
    with engine.connect() as c:
        orphans = c.execute(
            text(
                "SELECT count(*) FROM custom_agents c "
                "WHERE NOT EXISTS (SELECT 1 FROM companies co WHERE co.id = c.company_id)"
            )
        ).scalar()
    assert orphans == 0, f"{orphans} orphan custom_agents rows remain after FK closure"


def test_no_fixture_company_ids_remain(engine):
    """The specific fixture orphans (sentinel + test-7c-*) are gone."""
    with engine.connect() as c:
        n = c.execute(
            text(
                "SELECT count(*) FROM custom_agents "
                "WHERE company_id = '00000000-0000-0000-0000-000000000001' "
                "OR company_id LIKE 'test-7c-%'"
            )
        ).scalar()
    assert n == 0, f"{n} fixture-orphan custom_agents rows still present"


# ---------------------------------------------------------------------------
# FK #2 — ai_consumption.studio_agent_id  (polymorphic — NO FK by design)
# ---------------------------------------------------------------------------
def test_studio_agent_id_has_no_foreign_key(engine):
    """studio_agent_id is a polymorphic reference (discriminated by agent_type);
    it must NOT have a FK to custom_agents (would reject sourcing_agent /
    digital_twin consumption rows). Pins the canonical decision from mig 224."""
    with engine.connect() as c:
        defs = [
            r[0]
            for r in c.execute(
                text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conrelid = to_regclass('ai_consumption') AND contype = 'f'"
                )
            ).fetchall()
        ]
    studio_fk = [d for d in defs if "studio_agent_id" in d]
    assert not studio_fk, (
        "ai_consumption.studio_agent_id must NOT have a FK (it is a polymorphic "
        f"reference discriminated by agent_type). Found: {studio_fk}"
    )


def test_studio_agent_id_stays_varchar(engine):
    """The polymorphic column stays varchar(64); it must not be converted to
    uuid (sourcing/twin ids are not guaranteed to be custom_agents uuids)."""
    with engine.connect() as c:
        dtype = c.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'ai_consumption' AND column_name = 'studio_agent_id'"
            )
        ).scalar()
    assert dtype == "character varying", (
        f"ai_consumption.studio_agent_id is {dtype}, expected varchar "
        "(polymorphic reference — see migration 224)"
    )


def test_agent_type_discriminator_present(engine):
    """The polymorphic model relies on agent_type as the discriminator column."""
    with engine.connect() as c:
        exists = c.execute(
            text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_name = 'ai_consumption' AND column_name = 'agent_type'"
            )
        ).scalar()
    assert exists == 1, "ai_consumption.agent_type discriminator column missing"
