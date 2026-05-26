"""Sprint 7B-3a Part 1.5 v2 — SourcingAgentSignal canonical-only fail-closed.

Decisão Paulo 2026-05-26 (Opção 2): migration 209 relaxa agent_id NOT NULL → NULLABLE
+ model alinha ao schema real (custom_agent_id + assignment_id já adicionados em migration 202).

Pre-step Part 2 full: orchestrator vai escrever signals canonical via custom_agent_id.
"""
from __future__ import annotations

import pytest

# Sprint 8 (migration 211) DELETED agent_id column + sourcing_agents table.
# Subsets dos sensores Sprint 7B-3a Part 1.5 v2 que pinavam comportamento de
# agent_id ficam obsoletos. Tests que validam custom_agent_id canonical ainda
# rodam normalmente; tests sobre agent_id pulam.
pytestmark_legacy_agent_id_obsolete_post_sprint_8 = pytest.mark.skip(
    reason="Sprint 8 migration 211 dropou agent_id column — sensor obsoleto"
)


def test_signal_custom_agent_id_declared_fk_canonical():
    """SourcingAgentSignal.custom_agent_id FK custom_agents.id, nullable=False (canonical fail-closed)."""
    from lia_models.sourcing_agent import SourcingAgentSignal

    col = SourcingAgentSignal.__table__.columns.get("custom_agent_id")
    assert col is not None, "custom_agent_id column must be declared on SourcingAgentSignal"
    assert col.nullable is False, "custom_agent_id must be NOT NULL (canonical fail-closed)"
    fks = list(col.foreign_keys)
    assert len(fks) == 1, "custom_agent_id must have exactly 1 FK"
    assert fks[0].column.table.name == "custom_agents"
    assert fks[0].ondelete == "CASCADE"


@pytestmark_legacy_agent_id_obsolete_post_sprint_8
def test_signal_agent_id_now_nullable():
    """agent_id agora nullable=True (legacy preservado, signals novos via custom_agent_id)."""
    from lia_models.sourcing_agent import SourcingAgentSignal

    col = SourcingAgentSignal.__table__.columns.get("agent_id")
    assert col is not None
    assert col.nullable is True, "agent_id deve ser nullable após migration 209"


def test_signal_assignment_id_declared_fk_optional():
    """SourcingAgentSignal.assignment_id FK pool_agent_assignments.id, nullable=True (assignment opcional)."""
    from lia_models.sourcing_agent import SourcingAgentSignal

    col = SourcingAgentSignal.__table__.columns.get("assignment_id")
    assert col is not None, "assignment_id column must be declared"
    assert col.nullable is True, "assignment_id is optional"
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    assert fks[0].column.table.name == "pool_agent_assignments"
    assert fks[0].ondelete == "SET NULL"


@pytestmark_legacy_agent_id_obsolete_post_sprint_8
def test_signal_relationships_canonical():
    """SourcingAgentSignal expõe relationships custom_agent, assignment, agent (legacy)."""
    from lia_models.sourcing_agent import SourcingAgentSignal

    rels = {r.key for r in SourcingAgentSignal.__mapper__.relationships}
    assert "custom_agent" in rels, "relationship custom_agent obrigatória"
    assert "assignment" in rels, "relationship assignment obrigatória"
    assert "agent" in rels, "relationship agent (legacy) preservada"


def test_custom_agent_has_signals_reverse_relationship():
    """CustomAgent.signals reverse relationship (cascade delete-orphan)."""
    from lia_models.custom_agent import CustomAgent

    rels = {r.key: r for r in CustomAgent.__mapper__.relationships}
    assert "signals" in rels, "CustomAgent precisa de signals reverse relationship"
    rel = rels["signals"]
    assert rel.cascade.delete_orphan, "cascade delete-orphan obrigatório"


@pytestmark_legacy_agent_id_obsolete_post_sprint_8
def test_migration_209_relaxes_agent_id_in_db():
    """Migration 209 aplicada deixa agent_id nullable no DB real."""
    import os
    import asyncio
    import asyncpg

    async def check():
        dsn = os.environ.get("DATABASE_URL", "")
        if "?" in dsn:
            dsn = dsn.split("?")[0]
        conn = await asyncpg.connect(dsn)
        try:
            row = await conn.fetchrow(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = $1 AND column_name = $2",
                "sourcing_agent_signals",
                "agent_id",
            )
            return row["is_nullable"] if row else None
        finally:
            await conn.close()

    is_nullable = asyncio.run(check())
    assert is_nullable == "YES", f"agent_id deve ser nullable após migration 209, got {is_nullable}"
