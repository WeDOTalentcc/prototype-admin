"""Add enriched_jd column to job_vacancies.

Revision ID: 009_add_enriched_jd
Revises: 008_add_evaluation_criteria
Create Date: 2026-02-10

Stores the AI-enriched version of the Job Description created during
WSI screening question configuration. Separate from the official JD
so recruiters can choose when to sync changes back.
"""
from alembic import op
import sqlalchemy as sa


revision = '009_add_enriched_jd'
down_revision = '008_add_evaluation_criteria'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'job_vacancies',
        sa.Column('enriched_jd', sa.JSON, nullable=True)
    )


def downgrade():
    op.drop_column('job_vacancies', 'enriched_jd')
