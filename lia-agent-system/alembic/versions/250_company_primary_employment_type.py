"""primary_employment_type em company_profiles — contratacao primaria (default).

FASE 1 / E3 (audit 2026-06-06). Decisao Paulo: employment_types e uma LISTA + um
PRIMARIO. A criacao de vaga, quando o recrutador nao especifica, herda o primario
(cadeia: parsed > departamento > empresa). Idempotente, additive, nullable.

Revision ID: 250
Revises: 249
"""
from alembic import op

revision = "250"
down_revision = "249"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE company_profiles "
        "ADD COLUMN IF NOT EXISTS primary_employment_type VARCHAR(50)"
    )


def downgrade():
    op.execute("ALTER TABLE company_profiles DROP COLUMN IF EXISTS primary_employment_type")
