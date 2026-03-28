"""Add detected_language field to job_drafts table.

Revision ID: 004_add_detected_language
Revises: 003_add_learning_system
Create Date: 2026-01-28

This migration adds automatic language detection tracking:
- detected_language: Stores the automatically detected language (pt-BR, en-US, es)
- Default value is 'pt-BR' for backward compatibility
"""
from alembic import op
import sqlalchemy as sa


revision = '004_add_detected_language'
down_revision = '003_add_learning_system'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('job_drafts', sa.Column('detected_language', sa.String(10), nullable=True, server_default='pt-BR'))
    op.create_index(op.f('ix_job_drafts_detected_language'), 'job_drafts', ['detected_language'])


def downgrade():
    op.drop_index(op.f('ix_job_drafts_detected_language'), table_name='job_drafts')
    op.drop_column('job_drafts', 'detected_language')
