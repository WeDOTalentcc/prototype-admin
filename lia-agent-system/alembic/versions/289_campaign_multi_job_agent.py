"""campaign: add job_ids (multi-vacancy) and agent_ids (Studio) arrays.

Revision ID: 289
Revises: 288
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID

revision = "289"
down_revision = "288"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # job_ids: multiple vacancies per campaign (replaces singular job_id)
    op.add_column(
        "recruitment_campaigns",
        sa.Column(
            "job_ids",
            ARRAY(PG_UUID(as_uuid=True)),
            nullable=True,
            server_default="{}",
        ),
    )
    # agent_ids: custom_agents.id (Agent Studio agents assigned to this project)
    op.add_column(
        "recruitment_campaigns",
        sa.Column(
            "agent_ids",
            ARRAY(sa.Text()),
            nullable=True,
            server_default="{}",
        ),
    )
    # GIN index for efficient array containment queries (@>)
    op.create_index(
        "ix_recruitment_campaigns_job_ids",
        "recruitment_campaigns",
        ["job_ids"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_recruitment_campaigns_job_ids", table_name="recruitment_campaigns")
    op.drop_column("recruitment_campaigns", "agent_ids")
    op.drop_column("recruitment_campaigns", "job_ids")
