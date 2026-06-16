"""Offer proposals: hybrid canonical schema (Sprint F.4 #42/#46).

Revision ID: 139_offer_proposals_hybrid_canonical
Revises: 138_candidate_experience_highlights_canonical
Create Date: 2026-05-20

User-decision (Paulo, 2026-05-20): manter o schema do DB como canonical
(multi-round, approval, multi-channel send, eventos E11/E12, conteudo
renderizado da carta) e adicionar 4 melhorias non-destructive que existiam
na versao Python "new":

  1. ``job_data_snapshot`` / ``candidate_data_snapshot`` JSONB NOT NULL DEFAULT '{}'
     — snapshot LGPD imutavel apos status=sent (ADR-LGPD-001 Art. 12).
  2. ``salary`` double precision -> Numeric(12, 2). Tabela tem 0 rows, cast direto seguro.
  3. CHECK constraint ``chk_offer_status`` (enum-like enforcement no DB).
  4. ``cancelled_at`` TIMESTAMP NULL + ``cancelled_by_user_id`` VARCHAR(255) NULL.

DB tem 0 rows em offer_proposals — operacao 100% segura, sem preservacao de dado.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "139_offer_proposals_hybrid_canonical"
down_revision = "138_candidate_experience_highlights_canonical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. LGPD snapshots (Sprint F.4 #42/#46 — ADR-LGPD-001 Art. 12)
    op.add_column(
        "offer_proposals",
        sa.Column(
            "job_data_snapshot",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "offer_proposals",
        sa.Column(
            "candidate_data_snapshot",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
    )

    # 2. salary: double precision -> Numeric(12,2). DB has 0 rows so cast is safe.
    op.alter_column(
        "offer_proposals",
        "salary",
        type_=sa.Numeric(12, 2),
        existing_type=sa.Float(),
        postgresql_using="salary::numeric(12,2)",
    )

    # 3. CHECK constraint on status (enum-like enforcement at DB level)
    op.create_check_constraint(
        "chk_offer_status",
        "offer_proposals",
        "status IN ('draft','sent','accepted','declined','expired','cancelled')",
    )

    # 4. Cancellation tracking
    op.add_column(
        "offer_proposals",
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "offer_proposals",
        sa.Column("cancelled_by_user_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("offer_proposals", "cancelled_by_user_id")
    op.drop_column("offer_proposals", "cancelled_at")
    op.drop_constraint("chk_offer_status", "offer_proposals", type_="check")
    op.alter_column(
        "offer_proposals",
        "salary",
        type_=sa.Float(),
        existing_type=sa.Numeric(12, 2),
        postgresql_using="salary::double precision",
    )
    op.drop_column("offer_proposals", "candidate_data_snapshot")
    op.drop_column("offer_proposals", "job_data_snapshot")
