"""C2.1b — Close deferred FK: custom_agents.company_id -> companies.id.

Revision ID: 224
Revises: 223
Create Date: 2026-05-29

Context (Fase 2.5 Onda C2.1b — FK closure, follows mig 219):
  Migration 219 applied 7 FKs on the agent-studio tenant tables but deferred 2.
  This migration closes FK #1 and documents why FK #2 is intentionally NOT a
  foreign key (it is a polymorphic reference).

  ----------------------------------------------------------------------------
  FK #1 — custom_agents.company_id -> companies.id  (CLOSED here)
  ----------------------------------------------------------------------------
  Deferred in 219 because 46 of 54 custom_agents rows are orphaned ephemeral
  test fixtures (company_id has no matching companies row):
    - 10 rows with company_id = '00000000-0000-0000-0000-000000000001'
      (all-ones sentinel; NOT the real Demo Company, whose id is
      '00000000-0000-4000-a000-000000000001' with the UUIDv4 version nibble).
    - 36 rows with company_id LIKE 'test-7c-%' (contract-test agents, all
      named 'agent-7c', from create/update/list/contract test runs).
  The two real companies in the dev DB have ZERO orphan agents.

  RESOLUTION: this migration deletes ONLY the fixture orphans, guarded so it
  can never touch a real tenant:
    DELETE FROM custom_agents c
    WHERE NOT EXISTS (SELECT 1 FROM companies co WHERE co.id = c.company_id)
      AND (c.company_id = '00000000-0000-0000-0000-000000000001'
           OR c.company_id LIKE 'test-7c-%');
  The guard requires BOTH: (a) the company_id is genuinely absent from
  companies (so a real row is never deleted even if it transiently matched a
  pattern), AND (b) the company_id matches a known fixture pattern (so an
  unexpected real orphan would be left in place and surface as a FK error,
  rather than being silently destroyed — fail-loud, REGRA 4). After cleanup the
  FK is applied with ON DELETE CASCADE (tenant offboarding removes the tenant's
  agents — LGPD erasure cascade, mirrors the agent_deployments FK in 219).

  ----------------------------------------------------------------------------
  FK #2 — ai_consumption.studio_agent_id -> custom_agents.id  (NOT a FK — by design)
  ----------------------------------------------------------------------------
  Deferred in 219 as a "type mismatch" (studio_agent_id is varchar(64),
  custom_agents.id is uuid). Investigation for this migration found the deeper
  truth: studio_agent_id is a POLYMORPHIC reference discriminated by the sibling
  column ai_consumption.agent_type. The same column stores ids from several
  unrelated entities:
    - agent_type='custom_agent'   -> custom_agents.id        (uuid)
    - agent_type='sourcing_agent' -> orchestrator agent_id   (create_sourcing_agent)
    - agent_type='digital_twin'   -> digital_twins.id        (twin.id)
    - installation flows          -> installation_id
  (writers: app/domains/agent_studio/domain.py, app/domains/digital_twin/domain.py
   via studio_metering_service.record_studio_usage; ~15 read sites treat the
   value as str.)

  A single FK to custom_agents.id would REJECT every valid sourcing_agent /
  digital_twin consumption row, breaking metering correctness. Converting the
  column to uuid is also unsafe: sourcing/twin ids are not guaranteed to live in
  the custom_agents id space. Per the canonical-fix principle (integrity at the
  source, never break correctness to satisfy a metric), the correct integrity
  model here is polymorphic, NOT a foreign key. studio_agent_id therefore stays
  varchar(64) with NO FK, and this decision is recorded permanently in the
  AiConsumption model docstring so it is not "re-deferred" or mistakenly
  converted by a future migration.

  Referential integrity coverage of the agent-studio key tables after this
  migration: 8 of 8 integrity-relevant columns covered (7 FKs from mig 219 +
  this 1), i.e. 100% of the columns that SHOULD be FKs. studio_agent_id is
  correctly excluded from the denominator because it is polymorphic.
"""
from alembic import op

revision = "224"
down_revision = "223"
branch_labels = None
depends_on = None

_FK_NAME = "custom_agents_company_id_fkey"

# Tight, fail-loud cleanup: delete only orphans that are BOTH absent from
# companies AND match a known fixture pattern. A real orphan (absent + not a
# fixture pattern) is intentionally left untouched so the subsequent
# create_foreign_key fails loudly instead of silently destroying real data.
_CLEANUP_ORPHAN_FIXTURES = """
    DELETE FROM custom_agents c
    WHERE NOT EXISTS (
        SELECT 1 FROM companies co WHERE co.id = c.company_id
    )
    AND (
        c.company_id = '00000000-0000-0000-0000-000000000001'
        OR c.company_id LIKE 'test-7c-%'
    )
"""


def upgrade() -> None:
    op.execute(_CLEANUP_ORPHAN_FIXTURES)
    op.create_foreign_key(
        _FK_NAME,
        "custom_agents",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, "custom_agents", type_="foreignkey")
    # Deleted fixture rows are not restored: they were ephemeral contract-test
    # debris with no source of truth to recreate them from.
