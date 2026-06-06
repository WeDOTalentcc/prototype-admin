"""Department.defaults JSONB — defaults/template por departamento (cadeia de heranca).

FASE 1 (audit 2026-06-06). Decisao Paulo: departamento vira template com defaults
(work_model, pipeline_template_id, tech_stack, ...) que a criacao de vaga herda —
precedencia vaga > filial > DEPARTAMENTO > empresa > mercado. Consumido por
LiaFieldConfigService (ship-with-consumer, anti-ghost). Idempotente, additive.

Revision ID: 248
Revises: 247
"""
from alembic import op

revision = "248"
down_revision = "247"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE departments "
        "ADD COLUMN IF NOT EXISTS defaults JSONB NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade():
    op.execute("ALTER TABLE departments DROP COLUMN IF EXISTS defaults")
