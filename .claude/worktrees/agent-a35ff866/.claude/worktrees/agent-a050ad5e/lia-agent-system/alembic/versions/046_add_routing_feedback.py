"""Add routing_feedback table for adaptive routing learning.

Revision ID: 046
Revises: 045
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '046'
down_revision = '045'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'routing_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('message_hash', sa.String(64), nullable=False),
        sa.Column('routed_domain', sa.String(100), nullable=False),
        sa.Column('actual_domain', sa.String(100), nullable=True),
        sa.Column('corrected', sa.String(5), nullable=True),
        sa.Column('corrected_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_routing_feedback_company_domain', 'routing_feedback', ['company_id', 'routed_domain'])
    op.create_index('ix_routing_feedback_corrected_at', 'routing_feedback', ['corrected_at'])


def downgrade():
    op.drop_index('ix_routing_feedback_corrected_at', 'routing_feedback')
    op.drop_index('ix_routing_feedback_company_domain', 'routing_feedback')
    op.drop_table('routing_feedback')
