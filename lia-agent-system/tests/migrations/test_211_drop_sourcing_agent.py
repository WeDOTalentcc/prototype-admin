"""Sprint 8 — migration 211 sensors.

Valida:
- sourcing_agents table NAO existe pos-upgrade
- custom_agents.legacy_sourcing_agent_id NAO existe pos-upgrade
- sourcing_agent_signals.agent_id NAO existe pos-upgrade
- sourcing_agent_signals.custom_agent_id PRESERVADO (canonical)
- Index uq_custom_agents_legacy_sourcing NAO existe pos-upgrade

Roda contra DB live (mesma config dos outros tests/migrations/).
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


def test_sourcing_agents_table_dropped(engine):
    """Migration 211 drop sourcing_agents (verificado via to_regclass)."""
    with engine.connect() as c:
        reg = c.execute(
            text("SELECT to_regclass('public.sourcing_agents')")
        ).scalar()
        assert reg is None, f"sourcing_agents ainda existe: {reg}"


def test_custom_agents_legacy_column_dropped(engine):
    """Migration 211 drop custom_agents.legacy_sourcing_agent_id."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'custom_agents' "
                "AND column_name = 'legacy_sourcing_agent_id'"
            )
        ).fetchall()
        assert not rows, "legacy_sourcing_agent_id ainda existe em custom_agents"


def test_sourcing_signal_agent_id_dropped(engine):
    """Migration 211 drop sourcing_agent_signals.agent_id (FK dangling apos drop sourcing_agents)."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'sourcing_agent_signals' "
                "AND column_name = 'agent_id'"
            )
        ).fetchall()
        assert not rows, "agent_id ainda existe em sourcing_agent_signals"


def test_sourcing_signal_custom_agent_id_preserved(engine):
    """Canonical column custom_agent_id PRESERVADO (sensor 7B-3a Part 1.5 v2).

    NOTA: Sprint 8 nao toca nullability de custom_agent_id (declarado NOT NULL no
    model SQLAlchemy mas DB live diverge — drift pre-existente fora de escopo).
    """
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'sourcing_agent_signals' "
                "AND column_name = 'custom_agent_id'"
            )
        ).fetchall()
        assert rows, "custom_agent_id NAO existe em sourcing_agent_signals (canonical perdido)"


def test_unique_index_dropped(engine):
    """Migration 211 drop unique index uq_custom_agents_legacy_sourcing."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'custom_agents' "
                "AND indexname = 'uq_custom_agents_legacy_sourcing'"
            )
        ).fetchall()
        assert not rows, "uq_custom_agents_legacy_sourcing ainda existe"


def test_no_dangling_fk_to_sourcing_agents(engine):
    """Nenhum FK aponta para sourcing_agents (table foi dropada)."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT tc.constraint_name "
                "FROM information_schema.table_constraints tc "
                "JOIN information_schema.constraint_column_usage ccu "
                "  ON ccu.constraint_name = tc.constraint_name "
                "WHERE tc.constraint_type = 'FOREIGN KEY' "
                "AND ccu.table_name = 'sourcing_agents'"
            )
        ).fetchall()
        assert not rows, f"FKs ainda apontam pra sourcing_agents: {[r[0] for r in rows]}"
