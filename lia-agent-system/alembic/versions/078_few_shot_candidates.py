"""Create few_shot_candidates table

Revision ID: 078_few_shot_candidates
Revises: 077_ml_model_registry
Create Date: 2026-04-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "078_few_shot_candidates"
down_revision = "077_ml_model_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "few_shot_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_domain", sa.String(100), nullable=False),
        sa.Column("interaction_id", sa.String(255), nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("example_yaml", sa.Text, nullable=True),
        sa.Column("anonymized", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("company_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_fsc_domain_status", "few_shot_candidates", ["agent_domain", "status"])
    op.create_index("ix_fsc_created", "few_shot_candidates", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_fsc_created", table_name="few_shot_candidates")
    op.drop_index("ix_fsc_domain_status", table_name="few_shot_candidates")
    op.drop_table("few_shot_candidates")
