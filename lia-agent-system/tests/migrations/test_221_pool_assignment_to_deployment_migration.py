"""C1.5 — sensores da data migration 221 (pool_agent_assignments -> agent_deployments).

Roda contra DB live (mesma config dos outros tests/migrations/). Estratégia:
  - Semeia um grafo REAL e isolado (company + talent_pool + custom_agent +
    pool_agent_assignment + pool_agent_run) com IDs próprios de teste.
  - Invoca o SQL canonical da migration 221 (idempotente via ON CONFLICT) para
    exercitar a transformação contra esse grafo.
  - Assere: deployment equivalente criado (target_type='talent_pool'), run
    vinculado (deployment_id), trigger_mode mapeado, idempotência.
  - Limpa tudo no teardown (ordem reversa de FK).

Cobre o que o estado dev (32 fixtures órfãs, 0 migráveis) NÃO exercita: o caminho
real da transformação quando o company_id existe em companies.

Refs:
  - alembic/versions/221_migrate_pool_assignments_to_deployments.py
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, text

# SQL canonical espelhado da migration 221 (mesmas queries do upgrade()).
# Mantido idêntico de propósito — se a migration mudar, este teste deve mudar junto.
_INSERT_SQL = """
    INSERT INTO agent_deployments (
        id, agent_id, company_id,
        target_type, target_id, target_name,
        trigger_mode, schedule_cron,
        is_active, config_overrides,
        execution_count, candidates_processed,
        created_by, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        a.custom_agent_id,
        a.company_id,
        'talent_pool',
        a.talent_pool_id,
        tp.name,
        CASE a.schedule_type
            WHEN 'cron'         THEN 'scheduled'
            WHEN 'event_driven' THEN 'on_new_candidate'
            ELSE 'manual'
        END,
        NULLIF(a.schedule_config->>'cron', ''),
        (a.status = 'active'),
        COALESCE(a.config_overrides, '{}'::jsonb),
        0, 0,
        a.created_by, a.created_at, a.updated_at
    FROM pool_agent_assignments a
    JOIN companies c ON c.id = a.company_id
    LEFT JOIN talent_pools tp ON tp.id = a.talent_pool_id
    WHERE a.id = :assignment_id
    ON CONFLICT (agent_id, target_type, target_id) DO NOTHING
"""

_BACKFILL_SQL = """
    UPDATE pool_agent_runs r
    SET deployment_id = d.id
    FROM pool_agent_assignments a
    JOIN agent_deployments d
      ON d.agent_id = a.custom_agent_id
     AND d.target_type = 'talent_pool'
     AND d.target_id = a.talent_pool_id
    WHERE r.assignment_id = a.id
      AND r.deployment_id IS NULL
      AND a.id = :assignment_id
"""


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return create_engine(url)


@pytest.fixture()
def seeded(engine):
    """Grafo real isolado: company real + pool + agent + assignment + run."""
    company_id = f"c15test-{uuid.uuid4().hex[:8]}"
    pool_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    run_id = uuid.uuid4()

    with engine.begin() as c:
        # company REAL (satisfaz a FK agent_deployments.company_id -> companies.id)
        c.execute(
            text(
                "INSERT INTO companies (id, name, is_active, created_at) "
                "VALUES (:id, :name, true, now())"
            ),
            {"id": company_id, "name": "C1.5 Test Co"},
        )
        c.execute(
            text(
                "INSERT INTO talent_pools (id, company_id, name, created_at, updated_at) "
                "VALUES (:id, :cid, :name, now(), now())"
            ),
            {"id": pool_id, "cid": company_id, "name": "C1.5 Test Pool"},
        )
        c.execute(
            text(
                "INSERT INTO custom_agents "
                "(id, company_id, created_by, name, role, system_prompt, "
                " allowed_tools, domain, status, version, config, max_steps, "
                " temperature, runtime_metrics, created_at, updated_at) "
                "VALUES (:id, :cid, :cb, :name, 'recruiter', 'test prompt', "
                " '{}'::text[], 'general', 'active', 1, '{}'::jsonb, 5, "
                " 0.7, '{}'::jsonb, now(), now())"
            ),
            {"id": agent_id, "cid": company_id, "cb": company_id,
             "name": "C1.5 Test Agent"},
        )
        c.execute(
            text(
                "INSERT INTO pool_agent_assignments "
                "(id, company_id, talent_pool_id, custom_agent_id, status, "
                " schedule_type, schedule_config, config_overrides, created_by, "
                " created_at, updated_at) "
                "VALUES (:id, :cid, :pid, :aid, 'active', 'cron', "
                " '{\"cron\": \"0 9 * * 1\"}'::jsonb, '{}'::jsonb, :cb, now(), now())"
            ),
            {"id": assignment_id, "cid": company_id, "pid": pool_id,
             "aid": agent_id, "cb": company_id},
        )
        c.execute(
            text(
                "INSERT INTO pool_agent_runs "
                "(id, assignment_id, company_id, trigger_source, status, "
                " dispatch_metadata, results, runtime_metrics, created_at, updated_at) "
                "VALUES (:id, :aid, :cid, 'cron', 'success', "
                " '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, now(), now())"
            ),
            {"id": run_id, "aid": assignment_id, "cid": company_id},
        )

    yield {
        "company_id": company_id,
        "pool_id": pool_id,
        "agent_id": agent_id,
        "assignment_id": assignment_id,
        "run_id": run_id,
    }

    # Teardown ordem reversa de FK. Deletar a company CASCADEia agent_deployments
    # (FK ON DELETE CASCADE); pool_agent_runs/assignments CASCADEiam via seus FKs.
    with engine.begin() as c:
        c.execute(text("DELETE FROM pool_agent_runs WHERE id = :id"), {"id": run_id})
        c.execute(
            text("DELETE FROM agent_deployments WHERE agent_id = :aid "
                 "AND target_type = 'talent_pool' AND target_id = :pid"),
            {"aid": agent_id, "pid": pool_id},
        )
        c.execute(
            text("DELETE FROM pool_agent_assignments WHERE id = :id"),
            {"id": assignment_id},
        )
        c.execute(text("DELETE FROM custom_agents WHERE id = :id"), {"id": agent_id})
        c.execute(text("DELETE FROM talent_pools WHERE id = :id"), {"id": pool_id})
        c.execute(text("DELETE FROM companies WHERE id = :id"), {"id": company_id})


def _run_migration_sql(engine, assignment_id):
    with engine.begin() as c:
        c.execute(text(_INSERT_SQL), {"assignment_id": str(assignment_id)})
        c.execute(text(_BACKFILL_SQL), {"assignment_id": str(assignment_id)})


def test_assignment_becomes_deployment(seeded, engine):
    """Cada assignment com company real vira deployment talent_pool equivalente."""
    _run_migration_sql(engine, seeded["assignment_id"])
    with engine.connect() as c:
        row = c.execute(
            text(
                "SELECT target_type, target_id, agent_id, company_id, is_active "
                "FROM agent_deployments "
                "WHERE agent_id = :aid AND target_type = 'talent_pool' AND target_id = :pid"
            ),
            {"aid": seeded["agent_id"], "pid": seeded["pool_id"]},
        ).fetchone()
    assert row is not None, "deployment não criado pra assignment com company real"
    assert row[0] == "talent_pool"
    assert str(row[1]) == str(seeded["pool_id"])
    assert str(row[2]) == str(seeded["agent_id"])
    assert row[3] == seeded["company_id"]
    assert row[4] is True  # status='active' -> is_active=True


def test_historical_run_gets_deployment_id(seeded, engine):
    """Runs históricos do assignment ganham deployment_id (preserva histórico)."""
    _run_migration_sql(engine, seeded["assignment_id"])
    with engine.connect() as c:
        dep_id = c.execute(
            text("SELECT deployment_id FROM pool_agent_runs WHERE id = :id"),
            {"id": seeded["run_id"]},
        ).scalar()
        expected = c.execute(
            text("SELECT id FROM agent_deployments WHERE agent_id = :aid "
                 "AND target_type = 'talent_pool' AND target_id = :pid"),
            {"aid": seeded["agent_id"], "pid": seeded["pool_id"]},
        ).scalar()
    assert dep_id is not None, "run histórico ficou sem deployment_id"
    assert str(dep_id) == str(expected)


def test_idempotent_no_duplicate(seeded, engine):
    """Rodar a migration 2x não duplica deployments (ON CONFLICT)."""
    _run_migration_sql(engine, seeded["assignment_id"])
    _run_migration_sql(engine, seeded["assignment_id"])
    with engine.connect() as c:
        count = c.execute(
            text("SELECT count(*) FROM agent_deployments WHERE agent_id = :aid "
                 "AND target_type = 'talent_pool' AND target_id = :pid"),
            {"aid": seeded["agent_id"], "pid": seeded["pool_id"]},
        ).scalar()
    assert count == 1, f"esperado 1 deployment, achou {count} (idempotência quebrada)"


def test_trigger_mode_mapped_from_schedule_type(seeded, engine):
    """schedule_type='cron' -> trigger_mode='scheduled' (legacy alias de on_schedule)."""
    _run_migration_sql(engine, seeded["assignment_id"])
    with engine.connect() as c:
        tm, cron = c.execute(
            text("SELECT trigger_mode, schedule_cron FROM agent_deployments "
                 "WHERE agent_id = :aid AND target_type = 'talent_pool' AND target_id = :pid"),
            {"aid": seeded["agent_id"], "pid": seeded["pool_id"]},
        ).fetchone()
    assert tm == "scheduled", f"esperado 'scheduled', achou {tm!r}"
    assert cron == "0 9 * * 1", f"schedule_cron não copiado: {cron!r}"
