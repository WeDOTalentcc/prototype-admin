"""Add observability fields to external_api_consumption

Revision ID: 076_consumption_obs
Revises: 075_external_api
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "076_consumption_obs"
down_revision = "075_external_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "external_api_consumption",
        sa.Column("pipeline_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "external_api_consumption",
        sa.Column("search_session_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "external_api_consumption",
        sa.Column("actor_id", sa.String(200), nullable=True),
    )
    op.add_column(
        "external_api_consumption",
        sa.Column("tokens_input", sa.Integer, nullable=True),
    )
    op.add_column(
        "external_api_consumption",
        sa.Column("tokens_output", sa.Integer, nullable=True),
    )
    op.add_column(
        "external_api_consumption",
        sa.Column("model_name", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_extapi_pipeline",
        "external_api_consumption",
        ["pipeline_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_extapi_pipeline", table_name="external_api_consumption")
    op.drop_column("external_api_consumption", "model_name")
    op.drop_column("external_api_consumption", "tokens_output")
    op.drop_column("external_api_consumption", "tokens_input")
    op.drop_column("external_api_consumption", "actor_id")
    op.drop_column("external_api_consumption", "search_session_id")
    op.drop_column("external_api_consumption", "pipeline_id")
