"""Add f11_report_json cache column to wsi_results (migration 244).

Revision ID: 244
Revises: 243
Create Date: 2026-06-05

O endpoint /wsi/f11-report cacheia o relatório F11 em
``wsi_results.f11_report_json``, mas a coluna era criada via ``ALTER TABLE``
inline no request path (reports.py). Esse DDL adquire um lock ACCESS EXCLUSIVE
em ``wsi_results`` e, sob leitura concorrente, falhava silenciosamente
(try/except + rollback) — a coluna nunca persistia e o ``SELECT`` de cache
seguinte derrubava o endpoint inteiro com ``UndefinedColumnError`` (HTTP 500).

Esta migração cria a coluna de forma canônica (fora do hot path). O DDL inline
foi removido do reports.py em lockstep e o cache-read passou a ser graceful
(regenera em vez de 500 quando a coluna estiver ausente). Idempotente.
"""
from alembic import op

revision = "244"
down_revision = "243"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE wsi_results ADD COLUMN IF NOT EXISTS f11_report_json JSONB"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE wsi_results DROP COLUMN IF EXISTS f11_report_json")
