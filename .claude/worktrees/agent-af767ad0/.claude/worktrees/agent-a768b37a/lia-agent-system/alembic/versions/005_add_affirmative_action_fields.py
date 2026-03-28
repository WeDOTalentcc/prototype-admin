"""Add affirmative action fields to job_vacancies table.

Revision ID: 005_add_affirmative_action
Revises: 004_add_detected_language
Create Date: 2026-01-29

This migration adds comprehensive affirmative action support:
- affirmative_criteria_primary: Primary affirmative action criterion
- affirmative_criteria_secondary: Optional second criterion
- affirmative_description: Free text description (e.g., "Mulheres negras")
- affirmative_document_required: Whether document is required for verification
- affirmative_document_types: Array of accepted document types
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '005_add_affirmative_action'
down_revision = '004_add_detected_language'
branch_labels = None
depends_on = None


def upgrade():
    # Add affirmative action fields to job_vacancies table
    op.add_column('job_vacancies', sa.Column('affirmative_criteria_primary', sa.String(50), nullable=True))
    op.add_column('job_vacancies', sa.Column('affirmative_criteria_secondary', sa.String(50), nullable=True))
    op.add_column('job_vacancies', sa.Column('affirmative_description', sa.Text(), nullable=True))
    op.add_column('job_vacancies', sa.Column('affirmative_document_required', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('job_vacancies', sa.Column('affirmative_document_types', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'))


def downgrade():
    # Remove affirmative action fields from job_vacancies table
    op.drop_column('job_vacancies', 'affirmative_document_types')
    op.drop_column('job_vacancies', 'affirmative_document_required')
    op.drop_column('job_vacancies', 'affirmative_description')
    op.drop_column('job_vacancies', 'affirmative_criteria_secondary')
    op.drop_column('job_vacancies', 'affirmative_criteria_primary')
