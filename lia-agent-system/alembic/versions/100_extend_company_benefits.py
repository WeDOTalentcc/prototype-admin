"""Extend company_benefits to align with Rails contract (22 cols + icon).

Revision ID: 100_extend_company_benefits
Revises: 099_create_offer_proposals
Create Date: 2026-04-30

Contexto
--------
Fase 1 do plano de remediacao Benefits + PRV (vams-conectar-ao-replit-effervescent-fairy.md).

Estende a tabela `company_benefits` para alinhar 1:1 com o contrato Rails canonico
(`ats-api-copia/db/migrate/20250715000005_create_benefits.rb`, 22 colunas + icon).

Adiciona 11 colunas:
  - percentage_value     FLOAT      (valor em %, complementa value/value_details)
  - value_details        TEXT       (texto livre para value_type='informative')
  - applicable_to        TEXT[]     (a quem se aplica: all|interns|clt|pj|...)
  - seniority_levels     TEXT[]     (junior|pleno|senior|staff|principal|all)
  - contract_types       TEXT[]     (clt|pj|estagio|temp|...)
  - departments          JSONB      (mapa departamento -> regras especificas)
  - waiting_period_days  INTEGER    (carencia em dias)
  - is_mandatory         BOOLEAN    (obrigatorio por lei/CCT)
  - is_discount          BOOLEAN    (e desconto, nao beneficio)
  - provider             VARCHAR    (fornecedor: ex "Unimed", "Bradesco")
  - provider_contact     VARCHAR    (PII — mascarar em logs/JD publicada)

Indexes GIN em arrays/jsonb para queries de filtro por elegibilidade.

Idempotencia
------------
Cada ADD COLUMN usa IF NOT EXISTS (Postgres 9.6+). Indexes idem.

Reversibilidade
---------------
downgrade() dropa as 11 colunas + indexes. Dados nessas colunas sao perdidos
(esperado — feature ainda nao usada por usuarios em prod).

LGPD
----
provider_contact e PII. Filtro de masking deve ser aplicado em camadas de
logging e em JD publicada (// TODO(LGPD:001) em jd_template_service.py).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "100_extend_company_benefits"
down_revision = "099_create_offer_proposals"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, col: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c)"
    ), {"t": table, "c": col}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    # 11 ADD COLUMNs idempotentes
    op.execute(sa.text("""
        ALTER TABLE company_benefits
            ADD COLUMN IF NOT EXISTS percentage_value     FLOAT,
            ADD COLUMN IF NOT EXISTS value_details        TEXT,
            ADD COLUMN IF NOT EXISTS applicable_to        TEXT[]   DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS seniority_levels     TEXT[]   DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS contract_types       TEXT[]   DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS departments          JSONB    DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS waiting_period_days  INTEGER,
            ADD COLUMN IF NOT EXISTS is_mandatory         BOOLEAN  DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS is_discount          BOOLEAN  DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS provider             VARCHAR(255),
            ADD COLUMN IF NOT EXISTS provider_contact     VARCHAR(255)
    """))

    # GIN indexes para arrays/jsonb (queries de filtro por elegibilidade)
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_company_benefits_seniority "
        "ON company_benefits USING GIN (seniority_levels)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_company_benefits_applicable "
        "ON company_benefits USING GIN (applicable_to)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_company_benefits_contract "
        "ON company_benefits USING GIN (contract_types)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_company_benefits_departments "
        "ON company_benefits USING GIN (departments)"
    ))

    # Index para is_highlighted (filtro frequente — pre-selecao em vagas Fase 3)
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_company_benefits_highlighted "
        "ON company_benefits(company_id, is_highlighted) "
        "WHERE is_active = TRUE"
    ))

    op.execute(sa.text(
        "COMMENT ON TABLE company_benefits IS "
        "'Beneficios cadastrados por empresa. Schema 1:1 com Rails canonical "
        "(ats-api-copia/db/migrate/20250715000005_create_benefits.rb). "
        "Fase 1 do plano Benefits+PRV (2026-04-30).'"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_highlighted"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_departments"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_contract"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_applicable"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_company_benefits_seniority"))

    op.execute(sa.text("""
        ALTER TABLE company_benefits
            DROP COLUMN IF EXISTS provider_contact,
            DROP COLUMN IF EXISTS provider,
            DROP COLUMN IF EXISTS is_discount,
            DROP COLUMN IF EXISTS is_mandatory,
            DROP COLUMN IF EXISTS waiting_period_days,
            DROP COLUMN IF EXISTS departments,
            DROP COLUMN IF EXISTS contract_types,
            DROP COLUMN IF EXISTS seniority_levels,
            DROP COLUMN IF EXISTS applicable_to,
            DROP COLUMN IF EXISTS value_details,
            DROP COLUMN IF EXISTS percentage_value
    """))
