"""Add scheduled_messages table — GAP-07-007.

Revision ID: 291
Revises: 290
Create Date: 2026-06-16

Enables recruiter-initiated message scheduling (FE UI for future delivery).
LGPD: lgpd_expiry enforces 90-day data retention (Art. 15).
Multi-tenancy: company_id is NOT NULL and indexed.
"""
from alembic import op
import sqlalchemy as sa

revision = "291"
down_revision = "290"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduled_messages",
        sa.Column("id", sa.String(), nullable=False, primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("recruiter_id", sa.String(255), nullable=True),
        sa.Column("candidate_id", sa.String(255), nullable=False),
        sa.Column("candidate_name", sa.String(255), nullable=True),
        sa.Column("vacancy_id", sa.String(255), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("message_content", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("send_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("lgpd_expiry", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_sched_msg_pending_send_at", "scheduled_messages", ["status", "send_at"])
    op.create_index("idx_sched_msg_company_created", "scheduled_messages", ["company_id", "created_at"])
    op.create_index("idx_sched_msg_candidate", "scheduled_messages", ["candidate_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_sched_msg_candidate", "scheduled_messages")
    op.drop_index("idx_sched_msg_company_created", "scheduled_messages")
    op.drop_index("idx_sched_msg_pending_send_at", "scheduled_messages")
    op.drop_table("scheduled_messages")
