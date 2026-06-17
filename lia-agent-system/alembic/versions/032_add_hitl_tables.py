"""Add HITL persistence tables for Human-in-the-Loop approvals.

Revision ID: 032_add_hitl_tables
Revises: 031_add_pending_actions_table
Create Date: 2026-03-08

Context:
  Sprint F1 — HITL Persistence.

  HITLService previously relied exclusively on Redis for storing approval
  state (TTL 24h) with in-memory fallback. This is insufficient for production:
  - Redis restart loses all pending approvals silently
  - No audit trail of who approved/rejected what and when
  - No queryable history for compliance (SOX, BCB 498)

  This migration creates two tables:
    hitl_pending_actions — current approval state (one row per pending_id)
    hitl_audit_trail     — immutable log of all resolution events

  Redis remains as cache fast-path (TTL 24h). DB is source of truth.
  Multi-tenant: company_id on both tables.
  LGPD: agent_input JSON may contain PII — expires_at limits retention.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "032_add_hitl_tables"
down_revision = "031_add_pending_actions_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── hitl_pending_actions ─────────────────────────────────────────────────
    op.create_table(
        "hitl_pending_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("pending_id", sa.String(255), nullable=False, unique=True),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data", JSONB(), nullable=True, server_default="'{}'"),
        sa.Column("agent_input", JSONB(), nullable=True, server_default="'{}'"),
        sa.Column("ws_session_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        # status: pending | approved | rejected | expired
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '24 hours'")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_hitl_pending_thread_id", "hitl_pending_actions", ["thread_id"])
    op.create_index("ix_hitl_pending_status", "hitl_pending_actions", ["status"])
    op.create_index("ix_hitl_pending_expires_at", "hitl_pending_actions", ["expires_at"])

    # ── hitl_audit_trail ─────────────────────────────────────────────────────
    op.create_table(
        "hitl_audit_trail",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("pending_id", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(255), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        # Immutable — sem update após insert
    )

    op.create_index("ix_hitl_audit_thread_id", "hitl_audit_trail", ["thread_id"])
    op.create_index("ix_hitl_audit_pending_id", "hitl_audit_trail", ["pending_id"])
    op.create_index("ix_hitl_audit_resolved_at", "hitl_audit_trail", ["resolved_at"])


def downgrade() -> None:
    op.drop_index("ix_hitl_audit_resolved_at", table_name="hitl_audit_trail")
    op.drop_index("ix_hitl_audit_pending_id", table_name="hitl_audit_trail")
    op.drop_index("ix_hitl_audit_thread_id", table_name="hitl_audit_trail")
    op.drop_table("hitl_audit_trail")

    op.drop_index("ix_hitl_pending_expires_at", table_name="hitl_pending_actions")
    op.drop_index("ix_hitl_pending_status", table_name="hitl_pending_actions")
    op.drop_index("ix_hitl_pending_thread_id", table_name="hitl_pending_actions")
    op.drop_table("hitl_pending_actions")
