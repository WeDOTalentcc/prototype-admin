"""Sub-sprint 7A: data migration sourcing_agents -> custom_agents (category=sourcing).

# SOURCING-LEGACY-EXEMPT: data migration sub-sprint 7A canonical.

Revision ID: 203
Revises: 202
Create Date: 2026-05-25

Plan canonical: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_SPRINT7_PLAN.md §2.5

Mudancas (data only — schema imutavel):
1) INSERT INTO custom_agents (category=sourcing) por linha de sourcing_agents.
   COPY system_prompt do template via LEFT JOIN agent_templates (decisao Paulo).
   Defaults seguros: created_by='system', allowed_tools=[], role='sourcing'.
2) INSERT INTO pool_agent_assignments quando sourcing_agent tem talent_pool_id.
   company_id via JOIN talent_pools (multi-tenancy invariant).
3) UPDATE sourcing_agent_signals.custom_agent_id via JOIN legacy_sourcing_agent_id.
4) UPDATE agent_quotas.max_agents = max_sourcing + max_custom (soma transparente).
5) Inline validation (DO block raise EXCEPTION em mismatch).

Idempotencia: cada INSERT e WHERE NOT EXISTS (uq_custom_agents_legacy_sourcing
+ uq_pool_agent guardam belt-and-suspenders).

Downgrade: DELETE pool_agent_assignments e custom_agents migrados (via legacy_id);
UPDATE signals SET custom_agent_id=NULL. agent_quotas.max_agents preservado
(reverter sum quebra orcamento).

NOTA agent_templates.system_prompt: a coluna e 'system_prompt_yaml' (nao system_prompt).
Mas como (a) todos sourcing_agents tem agent_template_id NULL no baseline 2026-05-25 e
(b) ainda que tivessem, system_prompt em custom_agents e TEXT NOT NULL e queremos
seed minimo, usamos COALESCE(at.system_prompt_yaml, '').
"""
from alembic import op
from sqlalchemy import text

revision = "203"
down_revision = "202"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) sourcing_agents -> custom_agents (category=sourcing)
    conn.execute(text("""
        INSERT INTO custom_agents (
            id, company_id, created_by, name, role, system_prompt,
            allowed_tools, domain, status, version, config,
            max_steps, temperature,
            enable_memory, context_level, excluded_tools,
            voice_enabled, voip_enabled, whatsapp_enabled, triagem_invite_enabled,
            total_executions, avg_confidence,
            is_marketplace_published,
            category, runtime_metrics,
            search_strategy, preferences, outreach_config,
            legacy_sourcing_agent_id,
            created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            sa.company_id,
            'system',
            sa.agent_name,
            'sourcing',
            COALESCE(at.system_prompt_yaml, ''),
            ARRAY[]::varchar[],
            'general',
            sa.status,
            1,
            '{}'::jsonb,
            8,
            0.7,
            true, 'full', ARRAY[]::varchar[],
            false, false, false, false,
            0, 0.0,
            false,
            'sourcing',
            jsonb_build_object(
                'profiles_viewed',  COALESCE(sa.profiles_viewed, 0),
                'profiles_approved', COALESCE(sa.profiles_approved, 0),
                'profiles_rejected', COALESCE(sa.profiles_rejected, 0),
                'emails_sent',       COALESCE(sa.emails_sent, 0),
                'calibration_v',     COALESCE(sa.calibration_v, 0),
                'migrated_from_sourcing', true
            ),
            sa.search_strategy,
            sa.preferences,
            sa.outreach_config,
            sa.id,
            sa.created_at, sa.updated_at
        FROM sourcing_agents sa
        LEFT JOIN agent_templates at ON at.id = sa.agent_template_id
        WHERE NOT EXISTS (
            SELECT 1 FROM custom_agents ca
            WHERE ca.legacy_sourcing_agent_id = sa.id
        );
    """))

    # 2) pool_agent_assignments (quando sourcing_agent tinha pool)
    conn.execute(text("""
        INSERT INTO pool_agent_assignments (
            id, company_id, talent_pool_id, custom_agent_id,
            status, schedule_type, schedule_config, config_overrides,
            runtime_metrics, created_by, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            tp.company_id,
            sa.talent_pool_id,
            ca.id,
            CASE WHEN sa.status = 'active' THEN 'active' ELSE 'paused' END,
            'on_demand',
            '{}'::jsonb,
            '{}'::jsonb,
            '{}'::jsonb,
            'system',
            sa.created_at, sa.updated_at
        FROM sourcing_agents sa
        JOIN custom_agents ca ON ca.legacy_sourcing_agent_id = sa.id
        JOIN talent_pools tp ON tp.id = sa.talent_pool_id
        WHERE sa.talent_pool_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM pool_agent_assignments paa
              WHERE paa.talent_pool_id = sa.talent_pool_id
                AND paa.custom_agent_id = ca.id
          );
    """))

    # 3) sourcing_agent_signals.custom_agent_id via JOIN
    conn.execute(text("""
        UPDATE sourcing_agent_signals s
        SET custom_agent_id = ca.id
        FROM custom_agents ca
        WHERE ca.legacy_sourcing_agent_id = s.agent_id
          AND s.custom_agent_id IS NULL;
    """))

    # 4) agent_quotas.max_agents = soma transparente
    conn.execute(text("""
        UPDATE agent_quotas
        SET max_agents = COALESCE(max_sourcing_agents, 0) + COALESCE(max_custom_agents, 0)
        WHERE max_agents IS NULL OR max_agents = 5;
    """))

    # 5) Inline validation (raise se mismatch)
    conn.execute(text("""
        DO $migration_203_validate$
        DECLARE
            sourcing_total INT;
            custom_sourcing_total INT;
            sourcing_with_pool INT;
            assignments_total INT;
        BEGIN
            SELECT COUNT(*) INTO sourcing_total FROM sourcing_agents;
            SELECT COUNT(*) INTO custom_sourcing_total FROM custom_agents WHERE category = 'sourcing';
            SELECT COUNT(*) INTO sourcing_with_pool FROM sourcing_agents WHERE talent_pool_id IS NOT NULL;
            SELECT COUNT(*) INTO assignments_total FROM pool_agent_assignments;

            IF sourcing_total <> custom_sourcing_total THEN
                RAISE EXCEPTION 'Migration 203 FAIL: sourcing_total=% != custom_sourcing_total=%', sourcing_total, custom_sourcing_total;
            END IF;
            IF sourcing_with_pool <> assignments_total THEN
                RAISE EXCEPTION 'Migration 203 FAIL: sourcing_with_pool=% != assignments_total=%', sourcing_with_pool, assignments_total;
            END IF;
            RAISE NOTICE 'Migration 203 OK: % sourcing_agents migrated (% with pool assignments)', sourcing_total, sourcing_with_pool;
        END
        $migration_203_validate$;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        DELETE FROM pool_agent_assignments
        WHERE custom_agent_id IN (
            SELECT id FROM custom_agents WHERE legacy_sourcing_agent_id IS NOT NULL
        );
    """))
    conn.execute(text("""
        UPDATE sourcing_agent_signals SET custom_agent_id = NULL;
    """))
    conn.execute(text("""
        DELETE FROM custom_agents WHERE legacy_sourcing_agent_id IS NOT NULL;
    """))
    # Nota: agent_quotas.max_agents NAO e revertido (orcamento ja comunicado
    # ao cliente; reverter quebra contract). Sprint 8 trata cleanup final.
