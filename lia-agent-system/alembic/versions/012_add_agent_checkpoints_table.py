"""Add agent_checkpoints table for persistent agent state.

Revision ID: 012_add_agent_checkpoints_table
Revises: 011_add_interview_notes_table
Create Date: 2026-02-28

A3 — LangGraph State Persistence:
Adds agent_checkpoints table so that JobWizardGraph (and any other
agent) can restore state after a process restart. Replaces the
"state is lost on restart" behaviour with checkpoint-based recovery.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = '012_add_agent_checkpoints_table'
down_revision = '011_add_interview_notes_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'agent_checkpoints',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('company_id', sa.String(255), nullable=True),
        sa.Column('state_json', JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_agent_checkpoints_session', 'agent_checkpoints', ['session_id'])
    op.create_index('idx_agent_checkpoints_company', 'agent_checkpoints', ['company_id'],
                    postgresql_where=sa.text('company_id IS NOT NULL'))
    op.create_unique_constraint(
        'uq_agent_checkpoints_session_type',
        'agent_checkpoints',
        ['session_id', 'agent_type'],
    )


def downgrade():
    op.drop_constraint('uq_agent_checkpoints_session_type', 'agent_checkpoints')
    op.drop_index('idx_agent_checkpoints_company', table_name='agent_checkpoints')
    op.drop_index('idx_agent_checkpoints_session', table_name='agent_checkpoints')
    op.drop_table('agent_checkpoints')
