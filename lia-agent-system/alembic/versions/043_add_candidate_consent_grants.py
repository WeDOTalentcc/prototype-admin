"""add candidate_consent_grants

Revision ID: 043
Revises: 042
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '043'
down_revision = '042'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'candidate_consent_grants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('candidate_id', sa.String(255), nullable=False),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, default=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_consent_grants_candidate_company', 'candidate_consent_grants', ['candidate_id', 'company_id'])
    op.create_index('ix_consent_grants_category', 'candidate_consent_grants', ['category'])

def downgrade():
    op.drop_index('ix_consent_grants_category')
    op.drop_index('ix_consent_grants_candidate_company')
    op.drop_table('candidate_consent_grants')
