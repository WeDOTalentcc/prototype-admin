"""Create offer_proposals table.

Revision ID: 116_create_offer_proposals
Revises: 115_bigfive_department_profile
Create Date: 2026-04-26

Contexto
--------
PR-B — implementa a feature de envio de carta-oferta estruturada (card 5.1
do Rail A, auditoria enterprise P0). Tabela armazena:
  - Snapshots JSONB imutaveis dos dados da vaga e do candidato no momento do
    envio (exigencia LGPD de rastreabilidade).
  - Campos estruturados da proposta (salario, bonus, beneficios, data inicio).
  - State machine: draft -> sent -> (accepted|declined|expired|cancelled).
  - Audit trail completo: created_by, sent_by, sent_at, email_log_id.

Multi-tenant: company_id NOT NULL em toda leitura/escrita.

Reversibilidade
---------------
downgrade() dropa a tabela inteira (seguro: dados so existem em dev/staging
enquanto feature nao esta em prod).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "116_create_offer_proposals"
# Renamed during import from agent Repl 70fcc952: original revision id
# "098_create_offer_proposals" did not match its file slot 116_ and the
# previous down_revision "102_bigfive_department_profile" was renamed to
# "115_bigfive_department_profile" by the collision-fix commit. Chained
# after 115 to keep a single coherent imported sub-chain.
down_revision = "115_bigfive_department_profile"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "offer_proposals"):
        return  # idempotente

    op.execute(sa.text("""
        CREATE TABLE offer_proposals (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id              VARCHAR(255) NOT NULL,
            candidate_id            VARCHAR(255) NOT NULL,
            job_id                  UUID NOT NULL,
            template_id             UUID,

            -- Snapshots LGPD-imutaveis apos status=sent
            job_data_snapshot       JSONB NOT NULL DEFAULT '{}',
            candidate_data_snapshot JSONB NOT NULL DEFAULT '{}',

            -- Campos estruturados da carta-oferta
            offered_salary          DECIMAL(12,2),
            offered_salary_currency VARCHAR(10) DEFAULT 'BRL',
            offered_bonus_admission DECIMAL(12,2),
            offered_bonus_variable  JSONB,
            offered_benefits        JSONB,
            offered_start_date      DATE,
            validity_days           INTEGER DEFAULT 7,
            expires_at              TIMESTAMP,

            -- Notas do recrutador (nao enviadas ao candidato)
            recruiter_notes         TEXT,

            -- Estado
            status                  VARCHAR(20) NOT NULL DEFAULT 'draft',
            send_mode               VARCHAR(20),

            -- Referencia ao email enviado
            email_log_id            UUID,

            -- Resposta do candidato
            candidate_response_at      TIMESTAMP,
            candidate_response_message TEXT,
            declined_reason            VARCHAR(50),

            -- Audit trail
            created_by_user_id      VARCHAR(255) NOT NULL,
            sent_by_user_id         VARCHAR(255),
            sent_at                 TIMESTAMP,
            cancelled_at            TIMESTAMP,
            cancelled_by_user_id    VARCHAR(255),

            created_at              TIMESTAMP DEFAULT NOW(),
            updated_at              TIMESTAMP DEFAULT NOW(),

            CONSTRAINT chk_offer_status CHECK (
                status IN ('draft','sent','accepted','declined','expired','cancelled')
            ),
            CONSTRAINT chk_offer_send_mode CHECK (
                send_mode IN ('auto','manual') OR send_mode IS NULL
            )
        )
    """))

    # Indexes
    op.execute(sa.text("CREATE INDEX ix_offer_proposals_company ON offer_proposals(company_id)"))
    op.execute(sa.text("CREATE INDEX ix_offer_proposals_candidate ON offer_proposals(candidate_id)"))
    op.execute(sa.text("CREATE INDEX ix_offer_proposals_job ON offer_proposals(job_id)"))
    op.execute(sa.text("CREATE INDEX ix_offer_proposals_status ON offer_proposals(status)"))
    op.execute(sa.text(
        "CREATE INDEX ix_offer_proposals_company_candidate "
        "ON offer_proposals(company_id, candidate_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_offer_proposals_created_at ON offer_proposals(created_at DESC)"
    ))

    # Unique constraint: um unico draft ativo por (company, candidate, job)
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_offer_draft_active "
        "ON offer_proposals(company_id, candidate_id, job_id) "
        "WHERE status = 'draft'"
    ))

    op.execute(sa.text(
        "COMMENT ON TABLE offer_proposals IS "
        "'Cartas-oferta estruturadas enviadas a candidatos. PR-B (2026-04-26).'"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "offer_proposals"):
        op.execute(sa.text("DROP TABLE offer_proposals CASCADE"))
