"""behavioral_competencies em company_culture_profiles — fonte DISTINTA.

FASE 1 / E2 (audit 2026-06-06). Decisao Paulo: behavioral_competencies deve ser
fonte propria, separada de core_competencies (antes apontavam p/ a mesma coluna).
Idempotente, additive.

Revision ID: 249
Revises: 248
"""
from alembic import op

revision = "249"
down_revision = "248"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE company_culture_profiles "
        "ADD COLUMN IF NOT EXISTS behavioral_competencies VARCHAR[] NOT NULL DEFAULT '{}'::varchar[]"
    )


def downgrade():
    op.execute(
        "ALTER TABLE company_culture_profiles DROP COLUMN IF EXISTS behavioral_competencies"
    )
