"""Add soft_warnings column to fairness_audit_log (FAR-5).

Revision ID: 048
Revises: 047
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '048'
down_revision = '047'
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona soft_warnings JSONB (nullable) à tabela de auditoria de fairness.
    # Operação instantânea no PostgreSQL (ADD COLUMN nullable sem default).
    op.add_column(
        'fairness_audit_log',
        sa.Column('soft_warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade():
    op.drop_column('fairness_audit_log', 'soft_warnings')
