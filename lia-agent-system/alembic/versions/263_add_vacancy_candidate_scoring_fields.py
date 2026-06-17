"""P0-2: add cv_score, cv_fit_score, sub_status, screening_completed_at, ai_analysis to vacancy_candidates

Revision ID: 263_add_vacancy_candidate_scoring_fields
Revises: 262_add_digest_schedule_preferences
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "263_add_vacancy_candidate_scoring_fields"
down_revision = "262"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vacancy_candidates",
        sa.Column("cv_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "vacancy_candidates",
        sa.Column("cv_fit_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "vacancy_candidates",
        sa.Column("sub_status", sa.String(100), nullable=True),
    )
    op.add_column(
        "vacancy_candidates",
        sa.Column("screening_completed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "vacancy_candidates",
        sa.Column("ai_analysis", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("vacancy_candidates", "ai_analysis")
    op.drop_column("vacancy_candidates", "screening_completed_at")
    op.drop_column("vacancy_candidates", "sub_status")
    op.drop_column("vacancy_candidates", "cv_fit_score")
    op.drop_column("vacancy_candidates", "cv_score")
