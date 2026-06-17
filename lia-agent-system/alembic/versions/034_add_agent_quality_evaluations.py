"""Add agent_quality_evaluations table — Sprint J1

Revision ID: 034_add_agent_quality_evaluations
Revises: 033_merge_migration_heads
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "034_add_agent_quality_evaluations"
down_revision = "033_merge_migration_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_quality_evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("scores", JSONB, nullable=False,
                  comment="Ex: {task_completion: 0.9, fairness: 1.0, ...}"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_aqe_company_agent", "agent_quality_evaluations",
                    ["company_id", "agent_id"])
    op.create_index("ix_aqe_evaluated_at", "agent_quality_evaluations",
                    ["evaluated_at"])


def downgrade() -> None:
    op.drop_index("ix_aqe_evaluated_at", "agent_quality_evaluations")
    op.drop_index("ix_aqe_company_agent", "agent_quality_evaluations")
    op.drop_table("agent_quality_evaluations")
