"""WT-2022 P0.CANDIDATE: candidates.company_id backfill + NOT NULL (cross-tenant lockdown).

Revision ID: 164_candidate_company_id_not_null
Revises: 163_seed_marketplace_listings
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy + ADR-LGPD-001):
Candidate eh PII critico per-tenant. Coluna company_id era nullable=True
desde migration 082 (back-compat com rows pre-multi-tenancy). Esta migration
fecha o gap: backfill via vacancy_candidates.company_id (canonical NOT NULL)
+ ALTER NOT NULL.

Backfill strategy:
1. vacancy_candidates.company_id -> candidates.company_id (FK indireta via
   candidate_id; vacancy_candidates ja eh NOT NULL na coluna).
2. Linhas remanescentes orfas (sem qualquer pipeline assignment): DELETADAS.
   Decisao operacional: candidato sem company_id nao pode ser exibido em
   nenhum kanban (repos filtram por company_id) e violaria LGPD se aparecesse
   em pipeline cross-tenant.

NOT NULL constraint impede regressao via writes SQL diretos.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "164_candidate_company_id_not_null"
down_revision: Union[str, None] = "163_seed_marketplace_listings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Backfill via vacancy_candidates.company_id (canonical NOT NULL)
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            UPDATE candidates
            SET company_id = vc.company_id
            FROM vacancy_candidates AS vc
            WHERE vc.candidate_id = candidates.id
              AND candidates.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Orfas restantes: DELETADAS (decisao operacional segura)
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM candidates WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        print(
            f"[WT-2022 P0.CANDIDATE] {null_count} candidates orfaos "
            f"(company_id IS NULL sem vacancy_candidate vinculado) sao "
            f"DELETADOS para satisfazer NOT NULL constraint. Decisao: rows "
            f"nao-scopaveis a tenant violariam LGPD se aparecessem em "
            f"qualquer pipeline cross-tenant."
        )
        conn.execute(sa.text("DELETE FROM candidates WHERE company_id IS NULL"))

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL (defesa em camada DB)
    # ------------------------------------------------------------------
    op.alter_column(
        "candidates",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "candidates",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
