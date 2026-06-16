"""Reconcile missing schemas from migrations 010, 014, 015, 016 and 017.

Revision ID: 022_reconcile_missing_schemas
Revises: 021_add_can_comment_can_rate_shared_searches
Create Date: 2026-03-04

Context:
  Migrations 010, 014, 015, 016 and 017 were never applied to the DB — their
  DDL was likely executed manually, but the alembic_version record was never
  updated. When the discrepancy was found (alembic_version = 008 while the
  schema was already at 021) the version was stamped to 021 and this migration
  was created to apply only what is actually missing.

  All statements use IF NOT EXISTS / ADD COLUMN IF NOT EXISTS so the migration
  is fully idempotent and safe to run even if some elements already exist.

Missing elements per original migration:
  010 — vacancy_candidates: rejected_by_human, human_reviewer_id + index
  014 — candidates: preferred_channels, channel_opt_out + GIN indexes
  015 — fairness_audit_log table + composite index
  016 — ai_consumption: scheduled_deletion_at + backfill existing rows
  017 — company_calendar_credentials table + interviews: google_event_id, google_meet_link
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "022_reconcile_missing_schemas"
down_revision = "021_add_can_comment_can_rate_shared_searches"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 010 — Human Review Gate (LGPD art. 20 / EU AI Act art. 14)
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE vacancy_candidates
        ADD COLUMN IF NOT EXISTS rejected_by_human BOOLEAN
        """
    )
    op.execute(
        """
        ALTER TABLE vacancy_candidates
        ADD COLUMN IF NOT EXISTS human_reviewer_id VARCHAR(255)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vc_human_reviewer
        ON vacancy_candidates (human_reviewer_id)
        WHERE human_reviewer_id IS NOT NULL
        """
    )

    # ------------------------------------------------------------------
    # 014 — Candidate Channel Preferences (N3)
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS preferred_channels JSON DEFAULT '["email"]'
        """
    )
    op.execute(
        """
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS channel_opt_out JSON DEFAULT '[]'
        """
    )
    # Converter para JSONB (necessário para GIN index); idempotente — JSONB já aceita cast de JSONB
    op.execute(
        """
        ALTER TABLE candidates
        ALTER COLUMN preferred_channels TYPE JSONB USING preferred_channels::text::jsonb
        """
    )
    op.execute(
        """
        ALTER TABLE candidates
        ALTER COLUMN channel_opt_out TYPE JSONB USING channel_opt_out::text::jsonb
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_candidates_preferred_channels
        ON candidates USING GIN (preferred_channels)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_candidates_channel_opt_out
        ON candidates USING GIN (channel_opt_out)
        """
    )

    # ------------------------------------------------------------------
    # 015 — FairnessGuard Audit Log (B-3 / EU AI Act)
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fairness_audit_log (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id  UUID,
            recruiter_id UUID,
            job_id      UUID,
            candidate_id UUID,
            query_hash  VARCHAR(64) NOT NULL,
            category    VARCHAR(50),
            blocked_terms JSONB,
            confidence  FLOAT,
            is_blocked  BOOLEAN NOT NULL DEFAULT FALSE,
            context     VARCHAR(100),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_audit_log_company_id "
        "ON fairness_audit_log (company_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_audit_log_category "
        "ON fairness_audit_log (category)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_audit_log_is_blocked "
        "ON fairness_audit_log (is_blocked)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_audit_log_created_at "
        "ON fairness_audit_log (created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_company_date "
        "ON fairness_audit_log (company_id, created_at)"
    )

    # ------------------------------------------------------------------
    # 016 — AI Consumption Log: scheduled_deletion_at (L-6 / LGPD)
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE ai_consumption
        ADD COLUMN IF NOT EXISTS scheduled_deletion_at TIMESTAMP
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_consumption_scheduled_deletion_at "
        "ON ai_consumption (scheduled_deletion_at)"
    )
    # Backfill: registros existentes recebem deletion = created_at + 365 dias
    op.execute(
        """
        UPDATE ai_consumption
        SET scheduled_deletion_at = created_at + INTERVAL '365 days'
        WHERE scheduled_deletion_at IS NULL
        """
    )

    # ------------------------------------------------------------------
    # 017 — Company Calendar Credentials + Interviews Google fields
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS company_calendar_credentials (
            id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id           UUID NOT NULL,
            provider             VARCHAR(20) NOT NULL,
            encrypted_credentials TEXT NOT NULL,
            is_active            BOOLEAN NOT NULL DEFAULT TRUE,
            timezone             VARCHAR(100) NOT NULL DEFAULT 'America/Sao_Paulo',
            created_at           TIMESTAMP DEFAULT now(),
            updated_at           TIMESTAMP DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_company_calendar_credentials_company_provider
        ON company_calendar_credentials (company_id, provider)
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_company_calendar_credentials_company_id "
        "ON company_calendar_credentials (company_id)"
    )
    op.execute(
        """
        ALTER TABLE interviews
        ADD COLUMN IF NOT EXISTS google_event_id VARCHAR(255)
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_interviews_google_event_id "
        "ON interviews (google_event_id) WHERE google_event_id IS NOT NULL"
    )
    op.execute(
        """
        ALTER TABLE interviews
        ADD COLUMN IF NOT EXISTS google_meet_link VARCHAR(500)
        """
    )


def downgrade():
    # 017
    op.execute("DROP INDEX IF EXISTS ix_interviews_google_event_id")
    op.drop_column("interviews", "google_meet_link")
    op.drop_column("interviews", "google_event_id")
    op.execute("DROP INDEX IF EXISTS ix_company_calendar_credentials_company_provider")
    op.execute("DROP INDEX IF EXISTS ix_company_calendar_credentials_company_id")
    op.drop_table("company_calendar_credentials")

    # 016
    op.execute("DROP INDEX IF EXISTS ix_ai_consumption_scheduled_deletion_at")
    op.drop_column("ai_consumption", "scheduled_deletion_at")

    # 015
    op.execute("DROP INDEX IF EXISTS ix_fairness_company_date")
    op.execute("DROP INDEX IF EXISTS ix_fairness_audit_log_created_at")
    op.execute("DROP INDEX IF EXISTS ix_fairness_audit_log_is_blocked")
    op.execute("DROP INDEX IF EXISTS ix_fairness_audit_log_category")
    op.execute("DROP INDEX IF EXISTS ix_fairness_audit_log_company_id")
    op.drop_table("fairness_audit_log")

    # 014
    op.execute("DROP INDEX IF EXISTS idx_candidates_channel_opt_out")
    op.execute("DROP INDEX IF EXISTS idx_candidates_preferred_channels")
    op.drop_column("candidates", "channel_opt_out")
    op.drop_column("candidates", "preferred_channels")

    # 010
    op.execute("DROP INDEX IF EXISTS idx_vc_human_reviewer")
    op.drop_column("vacancy_candidates", "human_reviewer_id")
    op.drop_column("vacancy_candidates", "rejected_by_human")
