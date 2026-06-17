"""Add human review gate columns to vacancy_candidates.

Revision ID: 010_add_human_review_gate
Revises: 009_add_enriched_jd
Create Date: 2026-02-28

L3 — Human Review Gate (LGPD art. 20 / EU AI Act art. 14):
Adds `rejected_by_human` and `human_reviewer_id` to vacancy_candidates so that
every rejection is traceable to a human decision. The API layer blocks automated
rejections (user_id missing) at the endpoint level; these columns store the audit
trail for compliance reporting.
"""
from alembic import op
import sqlalchemy as sa


revision = '010_add_human_review_gate'
down_revision = '009_add_enriched_jd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'vacancy_candidates',
        sa.Column('rejected_by_human', sa.Boolean(), nullable=True)
    )
    op.add_column(
        'vacancy_candidates',
        sa.Column('human_reviewer_id', sa.String(255), nullable=True)
    )
    op.create_index(
        'idx_vc_human_reviewer',
        'vacancy_candidates',
        ['human_reviewer_id'],
        postgresql_where=sa.text('human_reviewer_id IS NOT NULL'),
    )


def downgrade():
    op.drop_index('idx_vc_human_reviewer', table_name='vacancy_candidates')
    op.drop_column('vacancy_candidates', 'human_reviewer_id')
    op.drop_column('vacancy_candidates', 'rejected_by_human')
