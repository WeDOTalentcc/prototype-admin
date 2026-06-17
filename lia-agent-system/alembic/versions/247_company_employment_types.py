"""employment_types em company_profiles — fonte company-wide p/ heranca na vaga.

FASE 1 (audit 2026-06-06). Decisao Paulo: modelo de contratacao (CLT/PJ/Estagio/
...) vira config first-class em "Dados da Empresa", pra a criacao de vaga herdar.
Idempotente. ARRAY nullable=False default '{}' -> metadata-only, sem rewrite.

Revision ID: 247
Revises: 246
"""
from alembic import op

revision = "247"
down_revision = "246"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE company_profiles "
        "ADD COLUMN IF NOT EXISTS employment_types VARCHAR[] NOT NULL DEFAULT '{}'::varchar[]"
    )


def downgrade():
    op.execute("ALTER TABLE company_profiles DROP COLUMN IF EXISTS employment_types")
