"""Add user_agent_preferences table — Sprint J3

Revision ID: 035_add_user_agent_preferences
Revises: 034_add_agent_quality_evaluations
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "035_add_user_agent_preferences"
down_revision = "034_add_agent_quality_evaluations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_agent_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False,
                  comment="ex: pipeline, job_management"),
        sa.Column("action_type", sa.String(100), nullable=False,
                  comment="ex: move_candidate, create_job"),
        sa.Column("auto_confirm", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.UniqueConstraint(
            "user_id", "company_id", "domain", "action_type",
            name="uq_user_agent_pref"
        ),
    )
    op.create_index("ix_uap_user_company", "user_agent_preferences",
                    ["user_id", "company_id"])


def downgrade() -> None:
    op.drop_index("ix_uap_user_company", "user_agent_preferences")
    op.drop_table("user_agent_preferences")
