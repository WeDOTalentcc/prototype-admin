"""Onda 2B.2 (audit 2026-06-06): add city column to job_vacancies.

Cidade canônica (global, dataset IBGE) persistida na vaga, separada de location (Endereço).
Idempotente — a coluna pode ter sido adicionada via DDL direta (gestão de schema estilo
create_all do projeto). Coluna nullable → metadata-only, sem lock/rewrite.

Revision ID: 246
Revises: 245
"""
from alembic import op

revision = "246"
down_revision = "245"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS city VARCHAR(255)")


def downgrade():
    op.execute("ALTER TABLE job_vacancies DROP COLUMN IF EXISTS city")
