"""Sub-sprint 7A migration 203 sensors.

Pin'a invariantes da data migration sourcing_agents -> custom_agents.
Roda contra DB live (mesma config dos outros tests/migrations/).

Sprint 8 (migration 211) DROPOU sourcing_agents table + custom_agents.legacy_sourcing_agent_id.
Esses sensores 7A pinavam estado pos-backfill 7A; agora obsoletos.
"""
from __future__ import annotations

import os
import pytest

# Sprint 8 (migration 211): sensores Sprint 7A pinavam state intermediario
# (sourcing_agents + legacy_sourcing_agent_id ambos existindo). Pos-Sprint 8 ambos
# foram dropados; sensores obsoletos.
pytestmark = pytest.mark.skip(
    reason="Sprint 8 migration 211 dropou sourcing_agents + legacy_sourcing_agent_id — sensor 7A obsoleto"
)
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return create_engine(url)


def test_sourcing_count_preserved(engine):
    """Cada sourcing_agent tem 1 custom_agent com category='sourcing' (1:1)."""
    with engine.connect() as c:
        sa = c.execute(text("SELECT COUNT(*) FROM sourcing_agents")).scalar()
        ca = c.execute(
            text("SELECT COUNT(*) FROM custom_agents WHERE category = 'sourcing'")
        ).scalar()
        assert sa == ca, f"count mismatch: sourcing={sa} custom_sourcing={ca}"


def test_legacy_back_reference_populated(engine):
    """Todo custom_agent category=sourcing tem legacy_sourcing_agent_id."""
    with engine.connect() as c:
        miss = c.execute(
            text(
                "SELECT COUNT(*) FROM custom_agents "
                "WHERE category = 'sourcing' AND legacy_sourcing_agent_id IS NULL"
            )
        ).scalar()
        assert miss == 0, f"{miss} custom_agents sourcing sem back-reference"


def test_pool_assignments_match(engine):
    """sourcing_agents com talent_pool_id -> mesma quantidade em pool_agent_assignments."""
    with engine.connect() as c:
        with_pool = c.execute(
            text("SELECT COUNT(*) FROM sourcing_agents WHERE talent_pool_id IS NOT NULL")
        ).scalar()
        assignments = c.execute(
            text("SELECT COUNT(*) FROM pool_agent_assignments")
        ).scalar()
        assert with_pool == assignments, (
            f"pool count mismatch: with_pool={with_pool} assignments={assignments}"
        )


def test_pool_assignment_multitenancy(engine):
    """company_id em pool_agent_assignments bate com talent_pools.company_id (invariant)."""
    with engine.connect() as c:
        bad = c.execute(
            text(
                "SELECT COUNT(*) FROM pool_agent_assignments paa "
                "JOIN talent_pools tp ON tp.id = paa.talent_pool_id "
                "WHERE paa.company_id <> tp.company_id"
            )
        ).scalar()
        assert bad == 0, f"{bad} assignments com company_id divergente do pool"


def test_signals_relink_idempotent(engine):
    """sourcing_agent_signals.custom_agent_id, quando set, aponta pro custom_agent
    cujo legacy_sourcing_agent_id == signal.agent_id."""
    with engine.connect() as c:
        bad = c.execute(
            text(
                "SELECT COUNT(*) FROM sourcing_agent_signals s "
                "JOIN custom_agents ca ON ca.id = s.custom_agent_id "
                "WHERE s.agent_id IS NOT NULL "
                "  AND ca.legacy_sourcing_agent_id IS DISTINCT FROM s.agent_id"
            )
        ).scalar()
        assert bad == 0, f"{bad} signals com custom_agent_id divergente do legacy"


def test_runtime_metrics_seed(engine):
    """Toda custom_agent migrada tem runtime_metrics.migrated_from_sourcing=true."""
    with engine.connect() as c:
        good = c.execute(
            text(
                "SELECT COUNT(*) FROM custom_agents "
                "WHERE category = 'sourcing' "
                "  AND runtime_metrics->>'migrated_from_sourcing' = 'true'"
            )
        ).scalar()
        total = c.execute(
            text("SELECT COUNT(*) FROM custom_agents WHERE category = 'sourcing'")
        ).scalar()
        assert good == total, f"{total - good} custom_agents sourcing sem marker"
