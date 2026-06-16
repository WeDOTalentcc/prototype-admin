"""add recruiter_decision_feedback

Revision ID: 044
Revises: 043
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '044'
down_revision = '043'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'recruiter_decision_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('job_id', sa.String(255), nullable=False),
        sa.Column('candidate_id', sa.String(255), nullable=False),
        sa.Column('lia_score', sa.Float(), nullable=True),
        sa.Column('decision', sa.String(50), nullable=False),
        sa.Column('decision_by', sa.String(255), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rdf_company_job', 'recruiter_decision_feedback', ['company_id', 'job_id'])
    op.create_index('ix_rdf_decision_at', 'recruiter_decision_feedback', ['company_id', 'decision_at'])
    op.create_index('ix_rdf_candidate', 'recruiter_decision_feedback', ['candidate_id'])

def downgrade():
    op.drop_index('ix_rdf_candidate')
    op.drop_index('ix_rdf_decision_at')
    op.drop_index('ix_rdf_company_job')
    op.drop_table('recruiter_decision_feedback')
