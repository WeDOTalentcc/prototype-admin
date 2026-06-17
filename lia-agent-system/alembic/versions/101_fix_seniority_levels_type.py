"""Fix seniority_levels column type from jsonb to text[] (Rails contract).

Revision ID: 101_fix_seniority_levels_type
Revises: 100_extend_company_benefits
Create Date: 2026-04-30

Contexto
--------
Em 100_extend_company_benefits.py o ADD COLUMN IF NOT EXISTS para
seniority_levels foi no-op porque a coluna ja existia como JSONB
(criada fora do alembic em algum momento anterior).

Rails canonical (`ats-api-copia/db/migrate/20250715000005_create_benefits.rb`)
define:
    t.string :seniority_levels, array: true, default: []
=> seniority_levels TEXT[] (Postgres)

Como nao ha dados populados (0 de 50 rows tem valor), e seguro DROP + RECREATE.

Reversibilidade
---------------
downgrade() volta para JSONB (estado pre-100). Como nao havia dados, nao perde
nada na ida nem na volta.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "101_fix_seniority_levels_type"
down_revision = "100_extend_company_benefits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_seniority"))
    op.execute(sa.text(
        "ALTER TABLE company_benefits DROP COLUMN IF EXISTS seniority_levels"
    ))
    op.execute(sa.text(
        "ALTER TABLE company_benefits "
        "ADD COLUMN seniority_levels TEXT[] DEFAULT '{}'"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_company_benefits_seniority "
        "ON company_benefits USING GIN (seniority_levels)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_seniority"))
    op.execute(sa.text(
        "ALTER TABLE company_benefits DROP COLUMN IF EXISTS seniority_levels"
    ))
    op.execute(sa.text(
        "ALTER TABLE company_benefits "
        "ADD COLUMN seniority_levels JSONB"
    ))
