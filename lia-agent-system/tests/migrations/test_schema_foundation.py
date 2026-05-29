"""Fase 2.5 Onda C2 — schema foundation sensors (migrations 217/218/219).

Validates the structural hardening applied to the agent-studio data layer:
- 217: ai_consumption + ai_credits_balance company_id is varchar (no uuid mismatch)
- 218: pool_agent_runs cross-target (deployment_id col, assignment_id nullable,
       chk_par_source_present CHECK, deployment index)
- 219: foreign keys on the agent-studio tenant tables (C2.1)

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


# ---------------------------------------------------------------------------
# 217 — type mismatch fix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("table", ["ai_consumption", "ai_credits_balance"])
def test_company_id_is_varchar(engine, table):
    """C2.3: company_id must be varchar (was uuid) to FK to companies.id."""
    with engine.connect() as c:
        dtype = c.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = 'company_id'"
            ),
            {"t": table},
        ).scalar()
    assert dtype == "character varying", f"{table}.company_id is {dtype}, expected varchar"


@pytest.mark.parametrize("table", ["ai_consumption", "ai_credits_balance"])
def test_rls_preserved_after_type_change(engine, table):
    """217 drops+recreates RLS policies around the type change — must survive."""
    with engine.connect() as c:
        relrowsecurity, relforce = c.execute(
            text(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname = :t"
            ),
            {"t": table},
        ).fetchone()
        npolicies = c.execute(
            text("SELECT count(*) FROM pg_policy WHERE polrelid = to_regclass(:t)"),
            {"t": table},
        ).scalar()
    assert relrowsecurity, f"{table} RLS not enabled"
    assert relforce, f"{table} RLS not forced"
    assert npolicies == 4, f"{table} has {npolicies} policies, expected 4"


# ---------------------------------------------------------------------------
# 218 — pool_agent_runs cross-target
# ---------------------------------------------------------------------------
def test_pool_agent_runs_has_deployment_id(engine):
    with engine.connect() as c:
        nullable = c.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'pool_agent_runs' AND column_name = 'deployment_id'"
            )
        ).scalar()
    assert nullable == "YES", f"deployment_id nullable={nullable}, expected YES (or missing)"


def test_pool_agent_runs_assignment_id_nullable(engine):
    """C1.4: a deployment-sourced run has no assignment, so assignment_id is nullable."""
    with engine.connect() as c:
        nullable = c.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'pool_agent_runs' AND column_name = 'assignment_id'"
            )
        ).scalar()
    assert nullable == "YES", f"assignment_id nullable={nullable}, expected YES"


def test_pool_agent_runs_source_check_constraint(engine):
    """chk_par_source_present: at least one of (assignment_id, deployment_id)."""
    with engine.connect() as c:
        defn = c.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'chk_par_source_present' "
                "AND conrelid = 'pool_agent_runs'::regclass"
            )
        ).scalar()
    assert defn is not None, "chk_par_source_present missing"
    assert "assignment_id" in defn and "deployment_id" in defn


def test_pool_agent_runs_deployment_fk(engine):
    with engine.connect() as c:
        defn = c.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'pool_agent_runs_deployment_id_fkey' "
                "AND conrelid = 'pool_agent_runs'::regclass"
            )
        ).scalar()
    assert defn is not None, "deployment_id FK missing"
    assert "agent_deployments" in defn and "CASCADE" in defn


def test_pool_agent_runs_deployment_index(engine):
    with engine.connect() as c:
        names = {
            r[0]
            for r in c.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE tablename = 'pool_agent_runs'"
                )
            ).fetchall()
        }
    assert "idx_pool_agent_runs_deployment" in names, f"have {names}"


def test_source_check_rejects_orphan_run(engine):
    """A run with neither assignment_id nor deployment_id violates the CHECK."""
    from sqlalchemy.exc import IntegrityError

    with engine.connect() as c:
        trans = c.begin()
        try:
            with pytest.raises(IntegrityError):
                c.execute(
                    text(
                        "INSERT INTO pool_agent_runs "
                        "(id, company_id, trigger_source, status, "
                        " dispatch_metadata, results, runtime_metrics, "
                        " created_at, updated_at) "
                        "VALUES (gen_random_uuid(), 'test-co', 'cron', 'queued', "
                        " '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, now(), now())"
                    )
                )
        finally:
            trans.rollback()


# ---------------------------------------------------------------------------
# 219 — foreign keys (C2.1)
# ---------------------------------------------------------------------------
# Each tuple: (table, fk_column, referenced_table). The 7 FKs applied directly
# by mig 219 are asserted here. The deferred FKs are validated in
# tests/migrations/test_fk_closure.py (mig 224): custom_agents.company_id was
# closed (orphans cleaned + FK CASCADE); ai_consumption.studio_agent_id stays
# without a FK by design (polymorphic reference discriminated by agent_type).
_EXPECTED_FKS = [
    ("digital_twins", "company_id", "companies"),
    ("ai_consumption", "company_id", "companies"),
    ("ai_credits_balance", "company_id", "companies"),
    ("agent_deployments", "company_id", "companies"),
    ("agent_deployments", "agent_id", "custom_agents"),
    ("agent_execution_logs", "agent_id", "custom_agents"),
    ("agent_execution_logs", "deployment_id", "agent_deployments"),
]


@pytest.mark.parametrize("table,column,ref", _EXPECTED_FKS)
def test_foreign_key_exists(engine, table, column, ref):
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = to_regclass(:t) AND contype = 'f'"
            ),
            {"t": table},
        ).fetchall()
    defs = [r[0] for r in rows]
    match = [d for d in defs if column in d and ref in d]
    assert match, f"FK {table}.{column} -> {ref} not found in {defs}"
