"""Add domain column to routing_cache_vectors for RAG domain separation.

Revision ID: 045
Revises: 044
"""
from alembic import op
import sqlalchemy as sa

revision = '045'
down_revision = '044'
branch_labels = None
depends_on = None


def upgrade():
    # Add domain column to routing_cache_vectors (the embeddings table used by RAG)
    op.add_column('routing_cache_vectors',
        sa.Column('domain', sa.String(50), nullable=True, server_default='general')
    )
    # Index for filtered domain search
    op.create_index(
        'ix_routing_cache_vectors_domain',
        'routing_cache_vectors',
        ['domain', 'company_id'],
    )


def downgrade():
    op.drop_index('ix_routing_cache_vectors_domain', 'routing_cache_vectors')
    op.drop_column('routing_cache_vectors', 'domain')
