"""Add comment column to lia_field_toggles table.

Revision ID: 002_add_comment
Revises: 001_intelligence
Create Date: 2026-01-28

This migration adds a 'comment' column to the lia_field_toggles table.
The comment field allows recruiters to provide additional instructions/context
for AI/LLM agents about how to handle specific fields.
"""
from alembic import op
import sqlalchemy as sa


revision = '002_add_comment'
down_revision = '001_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'lia_field_toggles',
        sa.Column('comment', sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column('lia_field_toggles', 'comment')
