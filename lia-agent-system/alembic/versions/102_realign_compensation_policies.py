"""Realign compensation_policies to Rails canonical contract (23 cols + updated_by + RLS).

Revision ID: 102_realign_compensation_policies
Revises: 101_fix_seniority_levels_type
Create Date: 2026-04-30

Contexto
--------
Fase 2 do plano Benefits + PRV (~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md).

Tabela `compensation_policies` ja existia no DB (schema draft com 25 cols
nao-Rails: department, role_pattern, seniority_level singulares, salary_min/
max/target inline, bonus_*pct inline, total_comp_*, source) MAS sem migration
alembic e com 0 rows em prod.

Esta migration:
  1. DROPa colunas do schema draft (12 cols a remover).
  2. ADDa colunas do schema Rails canonical (15 cols a adicionar).
  3. PRESERVA: id, company_id (UUID FK), name, variable_compensation jsonb,
     is_active, effective_from/until, created_at, updated_at, created_by.
  4. ATIVA RLS + 4 policies (SELECT/INSERT/UPDATE/DELETE) com
     app_current_company_id() — espelha padrao de company_benefits.
  5. Cria GIN indexes em arrays/jsonb (queries de elegibilidade).
  6. ADD coluna `updated_by` em company_benefits (auditabilidade —
     achado P1 da auditoria pos-Fase 1).

Idempotencia
------------
0 rows em compensation_policies — drop+add seguro. Migration usa
IF NOT EXISTS para indexes/columns onde Postgres aceita.

Reversibilidade
---------------
downgrade() restaura schema draft anterior em compensation_policies + drop
updated_by em company_benefits + drop policies/indexes. Como nao ha dados
em compensation_policies, downgrade nao perde nada.

LGPD/Fairness
-------------
- approved_by / created_by / updated_by: armazenam user_id (UUID-like
  string), nao texto livre. Mascarados em logs (Fase 4).
- // TODO(FAIRNESS:001): validador de termos discriminatorios em
  applicable_*[] sera plantado no Pydantic do router (Fase 2.4).

Refs:
- Plan: ~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md (Fase 2.3)
- Best practices: docs/COMPENSATION_BEST_PRACTICES.md (a2b209c91)
- Rails canonical: ats-api-copia/db/migrate/20250715000009_create_compensation_policies.rb (READ-ONLY)
- Sibling migrations: 100_extend_company_benefits, 101_fix_seniority_levels_type
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "102_realign_compensation_policies"
down_revision = "101_fix_seniority_levels_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # PART 1 — compensation_policies: DROP draft cols + ADD Rails cols
    # ---------------------------------------------------------------
    op.execute(sa.text("""
        ALTER TABLE compensation_policies
            DROP COLUMN IF EXISTS department,
            DROP COLUMN IF EXISTS role_pattern,
            DROP COLUMN IF EXISTS seniority_level,
            DROP COLUMN IF EXISTS salary_min,
            DROP COLUMN IF EXISTS salary_max,
            DROP COLUMN IF EXISTS salary_target,
            DROP COLUMN IF EXISTS bonus_enabled,
            DROP COLUMN IF EXISTS bonus_type,
            DROP COLUMN IF EXISTS bonus_min_pct,
            DROP COLUMN IF EXISTS bonus_target_pct,
            DROP COLUMN IF EXISTS bonus_max_pct,
            DROP COLUMN IF EXISTS bonus_criteria,
            DROP COLUMN IF EXISTS total_comp_annual_min,
            DROP COLUMN IF EXISTS total_comp_annual_max,
            DROP COLUMN IF EXISTS source
    """))

    op.execute(sa.text("""
        ALTER TABLE compensation_policies
            ADD COLUMN IF NOT EXISTS description            TEXT,
            ADD COLUMN IF NOT EXISTS policy_type            VARCHAR(50),
            ADD COLUMN IF NOT EXISTS currency               VARCHAR(10) NOT NULL DEFAULT 'BRL',
            ADD COLUMN IF NOT EXISTS salary_bands           JSONB       NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS bonus_structure        JSONB       NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS equity_rules           JSONB       NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS benefits_package       JSONB       NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS applicable_departments TEXT[]      NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS applicable_seniority   TEXT[]      NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS applicable_roles       TEXT[]      NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS is_default             BOOLEAN     NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS approved_by            VARCHAR(255),
            ADD COLUMN IF NOT EXISTS approved_at            TIMESTAMP WITHOUT TIME ZONE,
            ADD COLUMN IF NOT EXISTS version                INTEGER     NOT NULL DEFAULT 1,
            ADD COLUMN IF NOT EXISTS revision_history       JSONB       NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS updated_by             VARCHAR(255)
    """))

    # variable_compensation existia como JSON; promover a JSONB se ainda nao for
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'compensation_policies'
                  AND column_name = 'variable_compensation'
                  AND data_type = 'json'
            ) THEN
                ALTER TABLE compensation_policies
                    ALTER COLUMN variable_compensation TYPE JSONB
                    USING variable_compensation::jsonb;
            END IF;
        END$$;
    """))

    op.execute(sa.text("""
        ALTER TABLE compensation_policies
            ALTER COLUMN variable_compensation SET DEFAULT '{}'::jsonb,
            ALTER COLUMN variable_compensation SET NOT NULL
    """))

    # ---------------------------------------------------------------
    # PART 2 — RLS policies (espelha company_benefits)
    # ---------------------------------------------------------------
    op.execute(sa.text(
        "ALTER TABLE compensation_policies ENABLE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "ALTER TABLE compensation_policies FORCE ROW LEVEL SECURITY"
    ))

    # Postgres nao suporta CREATE POLICY IF NOT EXISTS — usar DO blocks
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'compensation_policies'
                  AND policyname = 'compensation_policies_tenant_select'
            ) THEN
                CREATE POLICY compensation_policies_tenant_select
                    ON compensation_policies FOR SELECT
                    USING (company_id::text = app_current_company_id());
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'compensation_policies'
                  AND policyname = 'compensation_policies_tenant_insert'
            ) THEN
                CREATE POLICY compensation_policies_tenant_insert
                    ON compensation_policies FOR INSERT
                    WITH CHECK (company_id::text = app_current_company_id());
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'compensation_policies'
                  AND policyname = 'compensation_policies_tenant_update'
            ) THEN
                CREATE POLICY compensation_policies_tenant_update
                    ON compensation_policies FOR UPDATE
                    USING (company_id::text = app_current_company_id())
                    WITH CHECK (company_id::text = app_current_company_id());
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'compensation_policies'
                  AND policyname = 'compensation_policies_tenant_delete'
            ) THEN
                CREATE POLICY compensation_policies_tenant_delete
                    ON compensation_policies FOR DELETE
                    USING (company_id::text = app_current_company_id());
            END IF;
        END$$;
    """))

    # ---------------------------------------------------------------
    # PART 3 — Indexes (GIN para arrays/jsonb + btree compostos)
    # ---------------------------------------------------------------
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_company "
        "ON compensation_policies(company_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_active_default "
        "ON compensation_policies(company_id, is_active, is_default) "
        "WHERE is_active = TRUE"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_seniority "
        "ON compensation_policies USING GIN (applicable_seniority)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_departments "
        "ON compensation_policies USING GIN (applicable_departments)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_roles "
        "ON compensation_policies USING GIN (applicable_roles)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_compensation_policies_variable_comp "
        "ON compensation_policies USING GIN (variable_compensation jsonb_path_ops)"
    ))

    op.execute(sa.text(
        "COMMENT ON TABLE compensation_policies IS "
        "'Politicas de remuneracao por empresa (PRV). Schema 1:1 com Rails "
        "canonical (ats-api-copia/db/migrate/20250715000009). variable_compensation "
        "jsonb usa kind discriminator: plr|ppr|bonus|commission|spot_bonus|equity. "
        "Fase 2 do plano Benefits+PRV (2026-04-30).'"
    ))

    # ---------------------------------------------------------------
    # PART 4 — auditabilidade: ADD updated_by em company_benefits
    # (resposta a P1 da auditoria pos-Fase 1)
    # ---------------------------------------------------------------
    op.execute(sa.text("""
        ALTER TABLE company_benefits
            ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255),
            ADD COLUMN IF NOT EXISTS created_by VARCHAR(255)
    """))


def downgrade() -> None:
    # PART 4 reverse
    op.execute(sa.text("""
        ALTER TABLE company_benefits
            DROP COLUMN IF EXISTS created_by,
            DROP COLUMN IF EXISTS updated_by
    """))

    # PART 3 reverse
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_variable_comp"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_roles"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_departments"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_seniority"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_active_default"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_compensation_policies_company"))

    # PART 2 reverse
    op.execute(sa.text("DROP POLICY IF EXISTS compensation_policies_tenant_delete ON compensation_policies"))
    op.execute(sa.text("DROP POLICY IF EXISTS compensation_policies_tenant_update ON compensation_policies"))
    op.execute(sa.text("DROP POLICY IF EXISTS compensation_policies_tenant_insert ON compensation_policies"))
    op.execute(sa.text("DROP POLICY IF EXISTS compensation_policies_tenant_select ON compensation_policies"))
    op.execute(sa.text("ALTER TABLE compensation_policies NO FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE compensation_policies DISABLE ROW LEVEL SECURITY"))

    # PART 1 reverse — drop Rails cols + restore draft cols
    op.execute(sa.text("""
        ALTER TABLE compensation_policies
            DROP COLUMN IF EXISTS updated_by,
            DROP COLUMN IF EXISTS revision_history,
            DROP COLUMN IF EXISTS version,
            DROP COLUMN IF EXISTS approved_at,
            DROP COLUMN IF EXISTS approved_by,
            DROP COLUMN IF EXISTS is_default,
            DROP COLUMN IF EXISTS applicable_roles,
            DROP COLUMN IF EXISTS applicable_seniority,
            DROP COLUMN IF EXISTS applicable_departments,
            DROP COLUMN IF EXISTS benefits_package,
            DROP COLUMN IF EXISTS equity_rules,
            DROP COLUMN IF EXISTS bonus_structure,
            DROP COLUMN IF EXISTS salary_bands,
            DROP COLUMN IF EXISTS currency,
            DROP COLUMN IF EXISTS policy_type,
            DROP COLUMN IF EXISTS description
    """))

    # Restore draft cols (vazias — 0 rows entao nao perde dados)
    op.execute(sa.text("""
        ALTER TABLE compensation_policies
            ADD COLUMN IF NOT EXISTS department            VARCHAR(255),
            ADD COLUMN IF NOT EXISTS role_pattern          VARCHAR(255),
            ADD COLUMN IF NOT EXISTS seniority_level       VARCHAR(100),
            ADD COLUMN IF NOT EXISTS salary_min            DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS salary_max            DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS salary_target         DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS bonus_enabled         BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS bonus_type            VARCHAR(100),
            ADD COLUMN IF NOT EXISTS bonus_min_pct         DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS bonus_target_pct      DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS bonus_max_pct         DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS bonus_criteria        JSON DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS total_comp_annual_min DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS total_comp_annual_max DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS source                VARCHAR(255)
    """))
