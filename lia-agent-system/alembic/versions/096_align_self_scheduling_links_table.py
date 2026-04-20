"""Align self-scheduling persistence with the SelfSchedulingLink model.

Revision ID: 096_align_self_scheduling_links_table
Revises: 095_create_ai_consumption_outbox
Create Date: 2026-04-20

Context
-------
Migration 063 created an orphan ``scheduling_links`` table (narrow schema:
candidate_id, job_id, token, duration_minutes, is_used, used_at, expires_at,
created_at) that nothing in the codebase ever read from. Meanwhile the
``SelfSchedulingLink`` SQLAlchemy model targets ``self_scheduling_links``
with a much richer schema (candidate_email, available_slots, status,
max_uses, etc.) and is the table actually queried by the zero-touch
scheduling service and the domain scheduling service.

This forward migration creates ``self_scheduling_links`` matching the
model and drops the orphan ``scheduling_links`` table. It is idempotent:
- Fresh databases: simply create ``self_scheduling_links``; the orphan
  ``DROP IF EXISTS`` is a no-op.
- Databases that ran 063: the orphan is removed and the real table is
  created. There is no production data to migrate because no consumer
  ever read from ``scheduling_links``.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "096_align_self_scheduling_links_table"
down_revision = "095_create_ai_consumption_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the orphan table from migration 063 if it exists. It was never
    # read from, so no data migration is required.
    op.execute("DROP TABLE IF EXISTS scheduling_links CASCADE")

    # Guard against partial state: only create if missing, so the
    # migration can be safely re-run on environments that may have
    # received an out-of-band fix.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_exists = "self_scheduling_links" in inspector.get_table_names()

    if table_exists:
        # Table was created out-of-band. Ensure the expected indexes exist
        # so partial states still converge to the model's schema.
        existing_indexes = {ix["name"] for ix in inspector.get_indexes("self_scheduling_links")}
        if "ix_self_scheduling_links_token" not in existing_indexes:
            op.create_index(
                "ix_self_scheduling_links_token",
                "self_scheduling_links",
                ["token"],
                unique=True,
            )
        if "ix_self_scheduling_links_status" not in existing_indexes:
            op.create_index(
                "ix_self_scheduling_links_status", "self_scheduling_links", ["status"]
            )
        if "ix_self_scheduling_links_created_at" not in existing_indexes:
            op.create_index(
                "ix_self_scheduling_links_created_at",
                "self_scheduling_links",
                ["created_at"],
            )
        return

    op.create_table(
        "self_scheduling_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_name", sa.String(255), nullable=False),
        sa.Column("candidate_email", sa.String(255), nullable=False),
        sa.Column("job_vacancy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("interviewer_emails", sa.JSON, nullable=True),
        sa.Column("organizer_email", sa.String(255), nullable=True),
        sa.Column("interview_type", sa.String(50), nullable=True, server_default="hr"),
        sa.Column("interview_mode", sa.String(50), nullable=True, server_default="video"),
        sa.Column("duration_minutes", sa.Integer, nullable=True, server_default="60"),
        sa.Column("available_slots", sa.JSON, nullable=True),
        sa.Column("selected_slot", sa.JSON, nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, server_default="pending"),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("max_uses", sa.Integer, nullable=True, server_default="1"),
        sa.Column("use_count", sa.Integer, nullable=True, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_self_scheduling_links_token", "self_scheduling_links", ["token"], unique=True
    )
    op.create_index(
        "ix_self_scheduling_links_status", "self_scheduling_links", ["status"]
    )
    op.create_index(
        "ix_self_scheduling_links_created_at", "self_scheduling_links", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_self_scheduling_links_created_at", table_name="self_scheduling_links")
    op.drop_index("ix_self_scheduling_links_status", table_name="self_scheduling_links")
    op.drop_index("ix_self_scheduling_links_token", table_name="self_scheduling_links")
    op.drop_table("self_scheduling_links")

    # Recreate the orphan table so 063 stays a valid restore point.
    op.create_table(
        "scheduling_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(24), nullable=False, unique=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("used_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_scheduling_links_candidate_id", "scheduling_links", ["candidate_id"])
