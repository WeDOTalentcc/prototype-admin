"""Add domain_events table for immutable event sourcing.

Revision ID: 047
Revises: 046
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '047'
down_revision = '046'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'domain_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('aggregate_type', sa.String(100), nullable=False),
        sa.Column('aggregate_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('sequence_number', sa.BigInteger, nullable=False, server_default='0'),
        sa.UniqueConstraint('aggregate_type', 'aggregate_id', 'sequence_number',
                           name='uq_domain_events_sequence'),
    )
    op.create_index('ix_domain_events_aggregate', 'domain_events',
                   ['aggregate_type', 'aggregate_id', 'created_at'])
    op.create_index('ix_domain_events_company', 'domain_events',
                   ['company_id', 'created_at'])
    op.create_index('ix_domain_events_event_type', 'domain_events', ['event_type'])

def downgrade():
    op.drop_index('ix_domain_events_event_type', 'domain_events')
    op.drop_index('ix_domain_events_company', 'domain_events')
    op.drop_index('ix_domain_events_aggregate', 'domain_events')
    op.drop_table('domain_events')
