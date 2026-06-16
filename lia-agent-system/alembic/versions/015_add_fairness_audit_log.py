"""Add fairness_audit_log table for EU AI Act compliance tracking (B-3).

Revision ID: 015_add_fairness_audit_log
Revises: 014_candidate_channel_preferences
Create Date: 2026-02-28

B-3 — FairnessGuard Persistência:
Persiste hits do FairnessGuard para rastreamento temporal exigido pelo EU AI Act.
Cada verificação que bloqueia ou gera aviso é registrada nesta tabela.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '015_add_fairness_audit_log'
down_revision = '014_candidate_channel_preferences'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fairness_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('recruiter_id', UUID(as_uuid=True), nullable=True),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True),
        sa.Column('candidate_id', UUID(as_uuid=True), nullable=True),
        sa.Column('query_hash', sa.String(64), nullable=False),
        sa.Column('category', sa.String(50), nullable=True, index=True),
        sa.Column('blocked_terms', JSONB, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('is_blocked', sa.Boolean, nullable=False, default=False, index=True),
        sa.Column('context', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False, index=True),
    )
    op.create_index(
        'ix_fairness_company_date',
        'fairness_audit_log',
        ['company_id', 'created_at'],
    )


def downgrade():
    op.drop_index('ix_fairness_company_date', table_name='fairness_audit_log')
    op.drop_table('fairness_audit_log')
