"""Add scheduled_deletion_at to candidates for LGPD data retention.

Revision ID: 013_add_scheduled_deletion_at
Revises: 012_add_agent_checkpoints_table
Create Date: 2026-02-28

L4 — LGPD Data Cleanup Scheduler:
Adds scheduled_deletion_at to candidates so the cleanup job knows
when each record should be permanently deleted. The job runs daily
and deletes records whose scheduled_deletion_at has passed.
"""
from alembic import op
import sqlalchemy as sa


revision = '013_add_scheduled_deletion_at'
down_revision = '012_add_agent_checkpoints_table'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'candidates',
        sa.Column('scheduled_deletion_at', sa.DateTime(), nullable=True),
    )
    op.create_index(
        'idx_candidates_scheduled_deletion',
        'candidates',
        ['scheduled_deletion_at'],
        postgresql_where=sa.text('scheduled_deletion_at IS NOT NULL'),
    )

    # vacancy_candidates also needs deletion scheduling (holds rejection data / PII)
    op.add_column(
        'vacancy_candidates',
        sa.Column('scheduled_deletion_at', sa.DateTime(), nullable=True),
    )
    op.create_index(
        'idx_vacancy_candidates_scheduled_deletion',
        'vacancy_candidates',
        ['scheduled_deletion_at'],
        postgresql_where=sa.text('scheduled_deletion_at IS NOT NULL'),
    )


def downgrade():
    op.drop_index('idx_vacancy_candidates_scheduled_deletion', table_name='vacancy_candidates')
    op.drop_column('vacancy_candidates', 'scheduled_deletion_at')
    op.drop_index('idx_candidates_scheduled_deletion', table_name='candidates')
    op.drop_column('candidates', 'scheduled_deletion_at')
