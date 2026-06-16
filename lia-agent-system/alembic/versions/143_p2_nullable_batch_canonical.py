"""P2 nullable batch: add 34 missing canonical columns across 11 tables.

Revision ID: 143_p2_nullable_batch_canonical
Revises: 141_outcome_correlations_canonical_columns
Create Date: 2026-05-20

Batch P2 nullable adds. Drops schema drift baseline by ~34.

Selection criteria (all met):
  - Tables have <100 rows (all 0 or 12, audited via psycopg2 2026-05-20)
  - All columns nullable=True in canonical model (libs/models/lia_models/*.py)
  - No FK columns touched
  - Tables in skip-list NOT included: webhook_logs, teams_conversations,
    offer_proposals, pattern_cache, outcome_correlations, calibration_events,
    calibration_weights, recruiter_field_preferences

Tables affected:
  1. ats_connections          (0 rows)  +1 col
  2. communication_settings   (0 rows)  +1 col
  3. data_request_configs     (0 rows)  +7 cols
  4. job_embeddings           (12 rows) +2 cols
  5. lia_field_toggles        (0 rows)  +1 col
  6. intelligence_insights    (0 rows)  +7 cols (+2 indices)
  7. personalization_settings (0 rows)  +9 cols
  8. bias_audit_snapshots     (0 rows)  +1 col
  9. client_users             (7 rows)  +2 cols (+1 index)
 10. fairness_audit_log       (0 rows)  +1 col
 11. talent_pool_candidates   (0 rows)  +2 cols (+2 indices)

Total: 34 columns + 5 indices.

Skipped from initial scope:
  - ai_consumption.agent_category (NOT NULL in model — needs separate P0 batch)
  - whatsapp_conversations columns (deferred to next batch — 13 cols)
  - recruiter_field_preferences columns (skip-list)
  - pattern_cache.updated_at (skip-list)
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


revision = "143_p2_nullable_batch_canonical"
down_revision = "141_outcome_correlations_canonical_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- 1. ats_connections (0 rows) ---
    # JSON, default=[] em model
    op.add_column(
        "ats_connections",
        sa.Column("field_mappings", sa.JSON(), nullable=True, server_default="[]"),
    )

    # --- 2. communication_settings (0 rows) ---
    # Boolean, default=True em model
    op.add_column(
        "communication_settings",
        sa.Column("mailgun_enabled", sa.Boolean(), nullable=True, server_default=sa.true()),
    )

    # --- 3. data_request_configs (0 rows) ---
    op.add_column(
        "data_request_configs",
        sa.Column("collection_mode", sa.String(50), nullable=True, server_default="portal_only"),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("collection_messages", sa.JSON(), nullable=True, server_default="{}"),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("lgpd_require_consent", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("lgpd_consent_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("lgpd_disclaimer_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("lgpd_data_retention_days", sa.Integer(), nullable=True, server_default="365"),
    )
    op.add_column(
        "data_request_configs",
        sa.Column("lgpd_allow_data_deletion", sa.Boolean(), nullable=True, server_default=sa.true()),
    )

    # --- 4. job_embeddings (12 rows) ---
    op.add_column(
        "job_embeddings",
        sa.Column("embedding_provider", sa.String(50), nullable=True),
    )
    op.add_column(
        "job_embeddings",
        sa.Column("embedding_model", sa.String(100), nullable=True),
    )

    # --- 5. lia_field_toggles (0 rows) ---
    op.add_column(
        "lia_field_toggles",
        sa.Column("comment", sa.Text(), nullable=True),
    )

    # --- 6. intelligence_insights (0 rows) ---
    op.add_column(
        "intelligence_insights",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("field", sa.String(100), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("original_value", sa.JSON(), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("suggested_value", sa.JSON(), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("reasoning", sa.Text(), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("was_accepted", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "intelligence_insights",
        sa.Column("final_value", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_intelligence_insights_job_id",
        "intelligence_insights",
        ["job_id"],
    )
    op.create_index(
        "ix_intelligence_insights_field",
        "intelligence_insights",
        ["field"],
    )

    # --- 7. personalization_settings (0 rows) ---
    op.add_column(
        "personalization_settings",
        sa.Column("enable_personalization", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("use_correction_history", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("use_preference_detection", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("use_outcome_data", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("show_confidence_indicators", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("explain_suggestions", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("auto_approve_high_confidence", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("high_confidence_threshold", sa.Float(), nullable=True, server_default="0.90"),
    )
    op.add_column(
        "personalization_settings",
        sa.Column("data_retention_months", sa.Integer(), nullable=True, server_default="24"),
    )

    # --- 8. bias_audit_snapshots (0 rows) ---
    op.add_column(
        "bias_audit_snapshots",
        sa.Column("disparate_impact_data", sa.JSON(), nullable=True),
    )

    # --- 9. client_users (7 rows) ---
    # email_encrypted = LargeBinary (BLOB), email_hash = VARCHAR(64) indexed
    op.add_column(
        "client_users",
        sa.Column("email_encrypted", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "client_users",
        sa.Column("email_hash", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_client_users_email_hash",
        "client_users",
        ["email_hash"],
    )

    # --- 10. fairness_audit_log (0 rows) ---
    op.add_column(
        "fairness_audit_log",
        sa.Column("soft_warnings", postgresql.JSONB(), nullable=True),
    )

    # --- 11. talent_pool_candidates (0 rows) ---
    op.add_column(
        "talent_pool_candidates",
        sa.Column("candidate_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "talent_pool_candidates",
        sa.Column("moved_to_job_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_talent_pool_candidates_candidate_uuid",
        "talent_pool_candidates",
        ["candidate_uuid"],
    )
    op.create_index(
        "ix_talent_pool_candidates_moved_to_job_uuid",
        "talent_pool_candidates",
        ["moved_to_job_uuid"],
    )


def downgrade() -> None:
    # Reverse order of upgrade
    # 11. talent_pool_candidates
    op.drop_index("ix_talent_pool_candidates_moved_to_job_uuid", table_name="talent_pool_candidates")
    op.drop_index("ix_talent_pool_candidates_candidate_uuid", table_name="talent_pool_candidates")
    op.drop_column("talent_pool_candidates", "moved_to_job_uuid")
    op.drop_column("talent_pool_candidates", "candidate_uuid")

    # 10. fairness_audit_log
    op.drop_column("fairness_audit_log", "soft_warnings")

    # 9. client_users
    op.drop_index("ix_client_users_email_hash", table_name="client_users")
    op.drop_column("client_users", "email_hash")
    op.drop_column("client_users", "email_encrypted")

    # 8. bias_audit_snapshots
    op.drop_column("bias_audit_snapshots", "disparate_impact_data")

    # 7. personalization_settings
    op.drop_column("personalization_settings", "data_retention_months")
    op.drop_column("personalization_settings", "high_confidence_threshold")
    op.drop_column("personalization_settings", "auto_approve_high_confidence")
    op.drop_column("personalization_settings", "explain_suggestions")
    op.drop_column("personalization_settings", "show_confidence_indicators")
    op.drop_column("personalization_settings", "use_outcome_data")
    op.drop_column("personalization_settings", "use_preference_detection")
    op.drop_column("personalization_settings", "use_correction_history")
    op.drop_column("personalization_settings", "enable_personalization")

    # 6. intelligence_insights
    op.drop_index("ix_intelligence_insights_field", table_name="intelligence_insights")
    op.drop_index("ix_intelligence_insights_job_id", table_name="intelligence_insights")
    op.drop_column("intelligence_insights", "final_value")
    op.drop_column("intelligence_insights", "was_accepted")
    op.drop_column("intelligence_insights", "reasoning")
    op.drop_column("intelligence_insights", "suggested_value")
    op.drop_column("intelligence_insights", "original_value")
    op.drop_column("intelligence_insights", "field")
    op.drop_column("intelligence_insights", "job_id")

    # 5. lia_field_toggles
    op.drop_column("lia_field_toggles", "comment")

    # 4. job_embeddings
    op.drop_column("job_embeddings", "embedding_model")
    op.drop_column("job_embeddings", "embedding_provider")

    # 3. data_request_configs
    op.drop_column("data_request_configs", "lgpd_allow_data_deletion")
    op.drop_column("data_request_configs", "lgpd_data_retention_days")
    op.drop_column("data_request_configs", "lgpd_disclaimer_text")
    op.drop_column("data_request_configs", "lgpd_consent_message")
    op.drop_column("data_request_configs", "lgpd_require_consent")
    op.drop_column("data_request_configs", "collection_messages")
    op.drop_column("data_request_configs", "collection_mode")

    # 2. communication_settings
    op.drop_column("communication_settings", "mailgun_enabled")

    # 1. ats_connections
    op.drop_column("ats_connections", "field_mappings")
