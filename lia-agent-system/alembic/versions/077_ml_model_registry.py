"""Create ml_model_registry table

Revision ID: 077_ml_model_registry
Revises: 076_consumption_obs
Create Date: 2026-04-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "077_ml_model_registry"
down_revision = "076_consumption_obs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("model_path", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=False, server_default="system"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metrics", postgresql.JSONB, nullable=True),
        sa.Column("parameters", postgresql.JSONB, nullable=True),
        sa.Column("features", postgresql.JSONB, nullable=True),
        sa.Column("predictions_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("correct_predictions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_error", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("last_evaluated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("training_samples", sa.Integer, nullable=True),
        sa.Column("company_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_mlreg_name_version_company",
        "ml_model_registry",
        ["name", "version", "company_id"],
        unique=True,
    )
    op.create_index(
        "ix_mlreg_name_default",
        "ml_model_registry",
        ["name", "is_default"],
    )
    op.create_index("ix_mlreg_company", "ml_model_registry", ["company_id"])
    op.create_index("ix_mlreg_status", "ml_model_registry", ["status"])


def downgrade() -> None:
    op.drop_index("ix_mlreg_status", table_name="ml_model_registry")
    op.drop_index("ix_mlreg_company", table_name="ml_model_registry")
    op.drop_index("ix_mlreg_name_default", table_name="ml_model_registry")
    op.drop_index("ix_mlreg_name_version_company", table_name="ml_model_registry")
    op.drop_table("ml_model_registry")
