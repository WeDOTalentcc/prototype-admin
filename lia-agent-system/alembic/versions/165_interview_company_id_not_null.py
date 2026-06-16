"""WT-2022 P0.INTERVIEW: interviews.company_id backfill + NOT NULL (cross-tenant lockdown).

Revision ID: 165_interview_company_id_not_null
Revises: 164_candidate_company_id_not_null
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy + ADR-LGPD-001):
Interview contem PII critico (emails encriptados de candidate, interviewer,
graph organizer). Coluna company_id era nullable=True (legacy). Esta migration
fecha o gap usando candidates.company_id (NOT NULL apos migration 164) como
FK indireta de backfill.

Backfill strategy:
1. candidates.company_id -> interviews.company_id (via candidate_id).
2. Linhas restantes orfas (interview sem candidate vinculado ou candidate ja
   deletado): DELETADAS. Decisao: interview sem company_id nao pode ser
   exibido em nenhum dashboard tenant-scoped.

Encadeamento: depende de 164 (candidates ja NOT NULL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "165_interview_company_id_not_null"
down_revision: Union[str, None] = "164_candidate_company_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Backfill via candidates.company_id (NOT NULL apos migration 164)
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            UPDATE interviews
            SET company_id = c.company_id
            FROM candidates AS c
            WHERE interviews.candidate_id = c.id
              AND interviews.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Orfas restantes: DELETADAS (operationally safe)
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM interviews WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        print(
            f"[WT-2022 P0.INTERVIEW] {null_count} interviews orfas "
            f"(company_id IS NULL sem candidate resolvivel) sao DELETADAS. "
            f"PII encriptado dessas rows tambem cai junto (LGPD art. 18 "
            f"erasure cascade)."
        )
        conn.execute(sa.text("DELETE FROM interviews WHERE company_id IS NULL"))

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL
    # ------------------------------------------------------------------
    op.alter_column(
        "interviews",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "interviews",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
