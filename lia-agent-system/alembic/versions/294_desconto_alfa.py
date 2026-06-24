"""Add desconto_pct + desconto_validade to subscriptions (ALFA discount, admin-only).

Revision ID: 294
Revises: 293

Desconto ALFA é um override por-empresa configurado exclusivamente pelo admin
WeDOTalent via admin-api. Clientes ALFA recebem desconto percentual no plano.
Coluna desconto_pct=0 por padrão → zero impacto para não-ALFA.
"""
from alembic import op
import sqlalchemy as sa

revision = '294'
down_revision = '293'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'subscriptions',
        sa.Column('desconto_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
    )
    op.add_column(
        'subscriptions',
        sa.Column('desconto_validade', sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_column('subscriptions', 'desconto_validade')
    op.drop_column('subscriptions', 'desconto_pct')
