"""Add candidate_nurture_sequences and nurture_step_approvals tables.

Revision ID: 290
Revises: 289
Create Date: 2026-06-16

Enables NurtureSequenceAgent multi-touch outreach for passive candidates.
LGPD: lgpd_expiry enforces data retention (default 90 days per LGPD Art. 15).
HITL: nurture_step_approvals gates each touchpoint before send.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "290"
down_revision = "289"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_nurture_sequences",
        sa.Column("sequence_id", sa.String(64), primary_key=True),
        sa.Column("candidate_id", sa.String(64), nullable=False, index=True),
        sa.Column("vacancy_id", sa.String(64), nullable=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="created",
        ),
        sa.Column("total_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("steps_approved", sa.Integer, nullable=False, server_default="0"),
        sa.Column("steps_executed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("steps_data", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        # LGPD Art. 15 — data retention TTL; null = no expiry (legacy data)
        sa.Column("lgpd_expiry", sa.DateTime, nullable=True),
    )
    op.create_index(
        "ix_nurture_seq_company_candidate",
        "candidate_nurture_sequences",
        ["company_id", "candidate_id"],
    )

    op.create_table(
        "nurture_step_approvals",
        sa.Column("approval_id", sa.String(64), nullable=False),
        sa.Column("sequence_id", sa.String(64), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("approved_by", sa.String(64), nullable=True),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("rejected_by", sa.String(64), nullable=True),
        sa.Column("rejected_at", sa.DateTime, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.PrimaryKeyConstraint("sequence_id", "step_number"),
        sa.ForeignKeyConstraint(
            ["sequence_id"],
            ["candidate_nurture_sequences.sequence_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_nurture_step_approvals_sequence",
        "nurture_step_approvals",
        ["sequence_id"],
    )


def downgrade() -> None:
    op.drop_table("nurture_step_approvals")
    op.drop_table("candidate_nurture_sequences")
