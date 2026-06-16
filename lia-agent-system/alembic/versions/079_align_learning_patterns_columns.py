"""Add consolidated columns to learning_patterns table

Revision ID: 079_align_learning_patterns_columns
Revises: 078_few_shot_candidates
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

revision = "079_align_learning_patterns_columns"
down_revision = "078_few_shot_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("learning_patterns", sa.Column("pattern_value", sa.JSON, nullable=True))
    op.add_column("learning_patterns", sa.Column("sample_size", sa.Integer, nullable=True, server_default="1"))
    op.add_column("learning_patterns", sa.Column("acceptance_rate", sa.Float, nullable=True, server_default="1.0"))
    op.add_column("learning_patterns", sa.Column("confidence_score", sa.Float, nullable=True, server_default="0.5"))
    op.add_column("learning_patterns", sa.Column("role_filter", sa.String(255), nullable=True))
    op.add_column("learning_patterns", sa.Column("seniority_filter", sa.String(100), nullable=True))
    op.add_column("learning_patterns", sa.Column("department_filter", sa.String(100), nullable=True))
    op.add_column("learning_patterns", sa.Column("location_filter", sa.String(255), nullable=True))
    op.add_column("learning_patterns", sa.Column("expires_at", sa.DateTime, nullable=True))
    op.add_column("learning_patterns", sa.Column("last_applied_at", sa.DateTime, nullable=True))
    op.add_column("learning_patterns", sa.Column("last_confirmed_at", sa.DateTime, nullable=True))

    op.create_index("idx_learning_patterns_created_at", "learning_patterns", ["created_at"])
    op.create_index("idx_learning_patterns_role_filter", "learning_patterns", ["role_filter"])
    op.create_index("ix_learning_patterns_company_type", "learning_patterns", ["company_id", "pattern_type"])
    op.create_index("ix_learning_patterns_key", "learning_patterns", ["company_id", "pattern_key"])
    op.create_index("ix_learning_patterns_active", "learning_patterns", ["company_id", "is_active"])
    op.create_index("ix_learning_patterns_role", "learning_patterns", ["company_id", "role_filter"])


def downgrade() -> None:
    op.drop_index("ix_learning_patterns_role", table_name="learning_patterns")
    op.drop_index("ix_learning_patterns_active", table_name="learning_patterns")
    op.drop_index("ix_learning_patterns_key", table_name="learning_patterns")
    op.drop_index("ix_learning_patterns_company_type", table_name="learning_patterns")
    op.drop_index("idx_learning_patterns_role_filter", table_name="learning_patterns")
    op.drop_index("idx_learning_patterns_created_at", table_name="learning_patterns")

    op.drop_column("learning_patterns", "last_confirmed_at")
    op.drop_column("learning_patterns", "last_applied_at")
    op.drop_column("learning_patterns", "expires_at")
    op.drop_column("learning_patterns", "location_filter")
    op.drop_column("learning_patterns", "department_filter")
    op.drop_column("learning_patterns", "seniority_filter")
    op.drop_column("learning_patterns", "role_filter")
    op.drop_column("learning_patterns", "confidence_score")
    op.drop_column("learning_patterns", "acceptance_rate")
    op.drop_column("learning_patterns", "sample_size")
    op.drop_column("learning_patterns", "pattern_value")
